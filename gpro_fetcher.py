#!/usr/bin/env python3
"""
GPRO Race Data Fetcher
======================
Pobiera dane wyścigowe z GPRO API i zapisuje je jako pliki JSON.
Uruchamiany automatycznie przez GitHub Actions po każdym wyścigu
(wtorek i piątek po 20:00 CET).

Mini-lekcja: Ten skrypt to przykład wzorca "Extract-Transform-Load" (ETL).
Pobieramy surowe dane z API (Extract), przetwarzamy je do potrzebnego
formatu (Transform), i zapisujemy lokalnie (Load). To jeden z najczęstszych
wzorców w programowaniu danych.
"""

import json
import os
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime


# ============================================================
# KONFIGURACJA
# ============================================================

# Bazowy URL API GPRO
BASE_URL = "https://gpro.net"

# Język (pl = polski)
LANG = "pl"

# Folder na dane wyścigowe
DATA_DIR = "data/races"

# Folder na profile torów (cache)
# Mini-lekcja: Profile torów zmieniają się rzadko, więc trzymamy
# je w cache przez 30 dni. Oszczędza to limity API.
TRACKS_DIR = "data/tracks"

# Plik kalendarza (oddzielny od danych wyścigowych)
# Mini-lekcja: Kalendarz to dane współdzielone między wyścigami,
# więc trzymamy go w osobnym pliku zamiast kopiować do każdego JSONa.
CALENDAR_FILE = "data/calendar.json"

# Jak często odświeżać kalendarz (w sekundach) - 7 dni
CALENDAR_MAX_AGE = 7 * 24 * 60 * 60

# Jak często odświeżać profile torów (w sekundach) - 30 dni
TRACK_PROFILE_MAX_AGE = 30 * 24 * 60 * 60

# Token API - pobierany ze zmiennej środowiskowej (GitHub Secret)
# Mini-lekcja: Tokeny i hasła NIGDY nie powinny być zapisane w kodzie.
# Zamiast tego używamy zmiennych środowiskowych (environment variables).
# Na GitHubie ustawiamy je jako "Secrets" w ustawieniach repozytorium.
API_TOKEN = os.environ.get("GPRO_TOKEN", "")


# ============================================================
# POMOCNICZE FUNKCJE DO KOMUNIKACJI Z API
# ============================================================

def api_get(endpoint, params=None):
    """
    Wysyła zapytanie GET do GPRO API.

    Mini-lekcja: Funkcje powinny robić jedną rzecz dobrze.
    Ta funkcja zajmuje się TYLKO komunikacją z API -
    buduje URL, dodaje nagłówki, obsługuje błędy.
    Reszta kodu nie musi wiedzieć JAK działa API.
    """
    # Budujemy pełny URL z parametrami
    url = f"{BASE_URL}/{LANG}/backend/api/v2/{endpoint}"

    if params:
        # Łączymy parametry w format ?klucz=wartość&klucz2=wartość2
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query_string}"

    # Tworzymy żądanie HTTP z tokenem autoryzacyjnym
    req = Request(url)
    req.add_header("Authorization", f"Bearer {API_TOKEN}")
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except HTTPError as e:
        print(f"  [BŁĄD] HTTP {e.code} dla {endpoint}: {e.reason}")
        return None
    except URLError as e:
        print(f"  [BŁĄD] Nie udało się połączyć z {endpoint}: {e.reason}")
        return None
    except json.JSONDecodeError:
        print(f"  [BŁĄD] Nieprawidłowa odpowiedź JSON z {endpoint}")
        return None


def pause_between_requests():
    """
    Krótka pauza między zapytaniami, żeby nie przeciążyć API.
    GPRO ma limit zapytań — szanujemy to.
    """
    time.sleep(1)


# ============================================================
# POBIERANIE DANYCH Z POSZCZEGÓLNYCH ENDPOINTÓW
# ============================================================

def fetch_office():
    """Pobiera dane z głównego biura - info o bieżącym sezonie/wyścigu."""
    print("  Pobieram dane biura (Office)...")
    return api_get("office")


def fetch_race_analysis(season=None, race=None):
    """
    Pobiera pełną analizę wyścigu - setupy, pit stopy,
    zużycie paliwa/opon, pogoda, finanse, stan auta.
    To najważniejszy endpoint w grze!
    """
    print("  Pobieram analizę wyścigu (RaceAnalysis)...")
    params = {}
    if season and race:
        params["sr"] = f"{season},{race}"
    return api_get("RaceAnalysis", params if params else None)


def fetch_race_summary(season=None, race=None):
    """Pobiera wyniki wyścigu całej grupy - pozycje, czasy, pit stopy."""
    print("  Pobieram podsumowanie wyścigu (RaceSummary)...")
    params = {}
    if season:
        params["season"] = str(season)
    if race:
        params["race"] = str(race)
    return api_get("RaceSummary", params if params else None)


def fetch_driver_profile():
    """Pobiera profil kierowcy - statystyki, umiejętności."""
    print("  Pobieram profil kierowcy (DriProfile)...")
    return api_get("DriProfile")


def fetch_standings():
    """Pobiera klasyfikację sezonu - pozycje w grupie."""
    print("  Pobieram klasyfikację (Standings)...")
    return api_get("Standings")


def fetch_calendar():
    """Pobiera kalendarz sezonu - lista torów i dat wyścigów."""
    print("  Pobieram kalendarz (Calendar)...")
    return api_get("Calendar")


def fetch_car():
    """Pobiera dane o stanie bolidu - poziomy części, zużycie."""
    print("  Pobieram dane bolidu (UpdateCar)...")
    return api_get("UpdateCar")


def fetch_track_profile(track_id):
    """
    Pobiera profil toru z API z cachowaniem.

    Mini-lekcja: To jest wzorzec "cache" - sprawdzamy czy mamy
    aktualne dane lokalnie przed pobraniem z API. Profile torów
    zmieniają się rzadko, więc trzymamy je przez 30 dni.

    Zwraca dane profilu toru lub None jeśli błąd.
    """
    if not track_id:
        print("  [OSTRZEŻENIE] Brak track_id - pomijam pobieranie profilu toru.")
        return None

    # Ścieżka do pliku cache
    track_file = f"{TRACKS_DIR}/{track_id}.json"

    # Sprawdzamy czy plik istnieje i jest wystarczająco świeży
    if os.path.exists(track_file):
        file_age = time.time() - os.path.getmtime(track_file)
        if file_age < TRACK_PROFILE_MAX_AGE:
            print(f"  Profil toru {track_id} aktualny (wiek: {file_age / 3600:.0f}h). Wczytuję z cache...")
            try:
                with open(track_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"  [BŁĄD] Błąd wczytywania cache: {e}. Pobieram z API...")

    # Pobieramy z API
    print(f"  Pobieram profil toru {track_id} (TrackProfile)...")
    profile_data = api_get(f"TrackProfile?id={track_id}")

    if profile_data:
        # Zapisujemy do cache
        os.makedirs(os.path.dirname(track_file), exist_ok=True)
        with open(track_file, "w", encoding="utf-8") as f:
            json.dump({
                "data": profile_data,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            }, f, ensure_ascii=False, indent=2)
        print(f"  Zapisano profil toru do: {track_file}")
        return profile_data
    else:
        print(f"  [BŁĄD] Nie udało się pobrać profilu toru {track_id}.")
        return None


# ============================================================
# PRZETWARZANIE I EKSTRAKCJA KLUCZOWYCH DANYCH
# ============================================================

def extract_race_data(analysis):
    """
    Wyciąga najważniejsze dane z RaceAnalysis do kompaktowego formatu.

    Mini-lekcja: To jest część "Transform" w ETL.
    Surowe dane z API zawierają mnóstwo pól, których nie potrzebujemy.
    Wyciągamy tylko to, co jest istotne do analizy i dashboardu.
    Dzięki temu nasze pliki JSON są mniejsze i łatwiejsze do czytania.
    """
    if not analysis:
        return None

    # Wyciągamy dane pit stopów
    pits = []
    for pit in analysis.get("pits", []):
        pits.append({
            "lap": pit.get("lap"),
            "reason": pit.get("reason", ""),
            "tyre_condition": pit.get("tyreCond"),
            "fuel_left": pit.get("fuelLeft"),
            "refilled_to": pit.get("refilledTo"),
            "pit_time": pit.get("pitTime", "")
        })

    # Wyciągamy dane setupów z poszczególnych sesji
    setups = []
    for setup in analysis.get("setupsUsed", []):
        setups.append({
            "session": setup.get("session", ""),
            "fw": setup.get("setFWing", ""),
            "rw": setup.get("setRWing", ""),
            "eng": setup.get("setEng", ""),
            "bra": setup.get("setBra", ""),
            "gear": setup.get("setGear", ""),
            "susp": setup.get("setSusp", ""),
            "tyres": setup.get("setTyres", "")
        })

    # Wyciągamy dane pogodowe
    weather_data = analysis.get("weather", {})
    weather = {
        "q1": {
            "condition": weather_data.get("q1Weather", ""),
            "temp": weather_data.get("q1Temp"),
            "humidity": weather_data.get("q1Hum")
        },
        "q2": {
            "condition": weather_data.get("q2Weather", ""),
            "temp": weather_data.get("q2Temp"),
            "humidity": weather_data.get("q2Hum")
        },
        "race": {
            "temp_range": [
                weather_data.get("raceQ1TempLow"),
                weather_data.get("raceQ4TempHigh")
            ],
            "humidity_range": [
                weather_data.get("raceQ1HumLow"),
                weather_data.get("raceQ4HumHigh")
            ]
        }
    }

    # Wyciągamy stan części po wyścigu
    car_parts = {}
    for part_name in ["chassis", "engine", "FWing", "RWing", "underbody",
                       "sidepods", "cooling", "gear", "brakes", "susp",
                       "electronics"]:
        part = analysis.get(part_name, {})
        if part:
            car_parts[part_name] = {
                "level": part.get("lvl"),
                "start_wear": part.get("startWear"),
                "finish_wear": part.get("finishWear")
            }

    # Wyciągamy dane finansowe
    transactions = []
    for t in analysis.get("transactions", []):
        transactions.append({
            "description": t.get("desc", ""),
            "amount": t.get("amount", 0)
        })

    # Wyciągamy dane kierowcy
    driver = analysis.get("driver", {})
    driver_info = {
        "name": driver.get("name", ""),
        "id": driver.get("id"),
        "OA": driver.get("OA", ""),
        "concentration": driver.get("con", ""),
        "talent": driver.get("tal", ""),
        "aggressiveness": driver.get("agr", ""),
        "experience": driver.get("exp", ""),
        "technical_insight": driver.get("tei", ""),
        "stamina": driver.get("sta", ""),
        "charisma": driver.get("cha", ""),
        "motivation": driver.get("mot", ""),
        "weight": driver.get("wei", "")
    }

    # Wyciągamy dane dostawcy opon
    tyre_sup = analysis.get("tyreSupplier", {})

    return {
        "season": analysis.get("selSeasonNb", ""),
        "race": analysis.get("selRaceNb", ""),
        "group": analysis.get("group", ""),
        "track": analysis.get("trackName", ""),
        "track_country": analysis.get("trackCountry", ""),
        "track_id": analysis.get("trackId", ""),
        "q1_time": analysis.get("q1Time", ""),
        "q1_pos": analysis.get("q1Pos", ""),
        "q2_time": analysis.get("q2Time", ""),
        "q2_pos": analysis.get("q2Pos", ""),
        "start_fuel": analysis.get("startFuel"),
        "finish_tyres": analysis.get("finishTyres"),
        "finish_fuel": analysis.get("finishFuel"),
        "overtake_attempts": analysis.get("otAttempts", ""),
        "overtakes": analysis.get("overtakes", ""),
        "setups": setups,
        "pits": pits,
        "weather": weather,
        "car_parts": car_parts,
        "car_power": analysis.get("carPower"),
        "car_handling": analysis.get("carHandl"),
        "car_acceleration": analysis.get("carAccel"),
        "tyre_supplier": {
            "name": tyre_sup.get("name", ""),
            "peak_temp": tyre_sup.get("peakTemp"),
            "dry_perf": tyre_sup.get("dryPerf"),
            "wet_perf": tyre_sup.get("wetPerf"),
            "durability": tyre_sup.get("durability"),
            "warmup": tyre_sup.get("warmup")
        },
        "driver": driver_info,
        "risks": {
            "q1": analysis.get("q1Risk", ""),
            "q2": analysis.get("q2Risk", ""),
            "start": analysis.get("startRisk", ""),
            "overtake": analysis.get("overtakeRisk", ""),
            "defend": analysis.get("defendRisk", ""),
            "clear_dry": analysis.get("clearDryRisk", ""),
            "clear_wet": analysis.get("clearWetRisk", ""),
            "problem": analysis.get("problemRisk", "")
        },
        "energy": {
            "q1": analysis.get("q1Energy", {}),
            "q2": analysis.get("q2Energy", {}),
            "race": analysis.get("raceEnergy", {})
        },
        "finances": {
            "transactions": transactions,
            "total": analysis.get("total", 0),
            "balance": analysis.get("currentBalance", 0)
        },
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }


def extract_summary_data(summary):
    """Wyciąga wyniki wyścigu z RaceSummary."""
    if not summary:
        return None

    results = []
    for entry in summary.get("data", []):
        results.append({
            "position": entry.get("pos"),
            "manager": entry.get("manName", ""),
            "nationality": entry.get("manNatCode", ""),
            "race_time": entry.get("raceTime", ""),
            "gap": entry.get("gap", ""),
            "laps": entry.get("laps"),
            "pits": entry.get("pits"),
            "best_lap": entry.get("bestLap", ""),
            "tyres": entry.get("tyres", ""),
            "progress": entry.get("progress", "")
        })

    return {
        "track": summary.get("trackName", ""),
        "season": summary.get("selSeasonNb", ""),
        "race": summary.get("selRaceNb", ""),
        "results": results
    }


# ============================================================
# ZAPIS DANYCH DO PLIKÓW JSON
# ============================================================

def save_json(data, filepath):
    """
    Zapisuje dane do pliku JSON z ładnym formatowaniem.

    Mini-lekcja: indent=2 sprawia, że JSON jest czytelny dla ludzi.
    ensure_ascii=False pozwala na polskie znaki (ą, ę, ś...).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Zapisano: {filepath}")


# ============================================================
# GŁÓWNA LOGIKA SKRYPTU
# ============================================================

def fetch_and_cache_calendar():
    """
    Pobiera kalendarz z API i zapisuje do osobnego pliku.
    Odświeża tylko jeśli plik nie istnieje lub jest starszy niż 7 dni.

    Mini-lekcja: To jest wzorzec "cache" - zamiast pobierać dane za każdym
    razem, sprawdzamy najpierw czy mamy aktualną kopię. Dzięki temu
    oszczędzamy limity API i przyspieszamy działanie.
    """
    # Sprawdzamy czy plik istnieje i czy jest wystarczająco świeży
    if os.path.exists(CALENDAR_FILE):
        file_age = time.time() - os.path.getmtime(CALENDAR_FILE)
        if file_age < CALENDAR_MAX_AGE:
            print(f"  Kalendarz aktualny (wiek: {file_age / 3600:.0f}h). Pomijam pobieranie.")
            return

    print("  Kalendarz nieaktualny lub brak pliku. Pobieram...")
    calendar_raw = fetch_calendar()

    if calendar_raw:
        # Walidacja: kalendarz powinien być listą
        if isinstance(calendar_raw, list):
            save_json({
                "data": calendar_raw,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            }, CALENDAR_FILE)
        else:
            print(f"  [BŁĄD] Nieprawidłowy format kalendarza (oczekiwano listy, otrzymano: {type(calendar_raw).__name__})")
    else:
        print("  [OSTRZEŻENIE] Nie udało się pobrać kalendarza.")


def fetch_post_race():
    """
    Pobiera wszystkie dane po wyścigu i zapisuje je jako JSON.
    To jest główna funkcja wywoływana przez GitHub Actions.
    """
    print("=" * 60)
    print("GPRO Race Data Fetcher")
    print("=" * 60)

    if not API_TOKEN:
        print("[BŁĄD] Brak tokenu API!")
        print("Ustaw zmienną środowiskową GPRO_TOKEN lub GitHub Secret.")
        sys.exit(1)

    # 0. Pobieramy/odświeżamy kalendarz (osobny plik z cache)
    fetch_and_cache_calendar()
    pause_between_requests()

    # 1. Pobieramy analizę ostatniego wyścigu
    analysis_raw = fetch_race_analysis()
    pause_between_requests()

    if not analysis_raw:
        print("[BŁĄD] Nie udało się pobrać analizy wyścigu.")
        sys.exit(1)

    # Wyciągamy numer sezonu i wyścigu
    season = analysis_raw.get("selSeasonNb", "unknown")
    race = analysis_raw.get("selRaceNb", "unknown")
    track = analysis_raw.get("trackName", "unknown")

    print(f"\n  Sezon {season}, Wyścig {race}: {track}")
    print("-" * 40)

    # Sprawdzamy, czy dane już istnieją (żeby nie pobierać dwa razy)
    race_file = f"{DATA_DIR}/S{season}R{race}.json"
    if os.path.exists(race_file):
        print(f"  Dane dla S{season}R{race} już istnieją. Nadpisuję...")

    # 2. Przetwarzamy dane analizy
    race_data = extract_race_data(analysis_raw)

    # 3. Pobieramy wyniki wyścigu (ranking grupy)
    summary_raw = fetch_race_summary()
    pause_between_requests()
    summary_data = extract_summary_data(summary_raw)

    # 4. Pobieramy profil kierowcy
    driver_raw = fetch_driver_profile()
    pause_between_requests()

    # 5. Pobieramy klasyfikację sezonu
    standings_raw = fetch_standings()
    pause_between_requests()

    # 6. Pobieramy stan bolidu
    car_raw = fetch_car()

    # Łączymy wszystko w jeden plik (bez kalendarza - jest w osobnym pliku)
    combined = {
        "race_data": race_data,
        "race_summary": summary_data,
        "driver_profile": driver_raw,
        "standings": standings_raw,
        "car_status": car_raw
    }

    # 7. Zapisujemy dane wyścigu
    save_json(combined, race_file)

    # 8. Zapisujemy też "latest.json" - zawsze wskazuje na ostatni wyścig
    save_json(combined, f"{DATA_DIR}/latest.json")

    # 9. Pobierz profil następnego toru (jeśli mamy info z kalendarza)
    # Mini-lekcja: Próbujemy znaleźć track_id następnego toru z kalendarza.
    # Dzięki temu predictor może użyć bardziej szczegółowych danych o torze.
    next_track_id = None
    try:
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                calendar = json.load(f)

            next_race_num = (int(race) if race.isdigit() else 0) + 1
            calendar_races = calendar.get("data", calendar.get("races", []))

            for event in calendar_races:
                if str(event.get("raceNb", event.get("race", ""))) == str(next_race_num):
                    next_track_id = event.get("trackId")
                    if next_track_id:
                        pause_between_requests()
                        fetch_track_profile(next_track_id)
                        break
    except Exception as e:
        print(f"  [OSTRZEŻENIE] Błąd podczas pobierania profilu następnego toru: {e}")

    # 10. Uruchom predictor
    # Mini-lekcja: Używamy subprocess żeby uruchomić predictor.py
    # jako osobny proces. check=False oznacza, że nie crashujemy
    # workflow jeśli predictor się nie powiedzie.
    print("\n  Uruchamiam predictor.py...")
    try:
        result = subprocess.run(
            [sys.executable, "predictor.py"],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  Predictor zakończony pomyślnie.")
        else:
            print(f"  [OSTRZEŻENIE] Predictor zakończony z błędem: {result.returncode}")
            if result.stderr:
                print(f"  Stderr: {result.stderr}")
    except Exception as e:
        print(f"  [BŁĄD] Nie udało się uruchomić predictora: {e}")

    print("\n" + "=" * 60)
    print(f"Gotowe! Dane zapisane do {race_file}")
    print(f"Pozostałe zapytania API: {analysis_raw.get('apiRequestsRemaining', '?')}")
    print("=" * 60)

    return race_file


if __name__ == "__main__":
    fetch_post_race()
