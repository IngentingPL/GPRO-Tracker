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
    pause_between_requests()

    # 7. Pobieramy kalendarz
    calendar_raw = fetch_calendar()

    # Łączymy wszystko w jeden plik
    combined = {
        "race_data": race_data,
        "race_summary": summary_data,
        "driver_profile": driver_raw,
        "standings": standings_raw,
        "car_status": car_raw,
        "calendar": calendar_raw
    }

    # 8. Zapisujemy dane wyścigu
    save_json(combined, race_file)

    # 9. Zapisujemy też "latest.json" - zawsze wskazuje na ostatni wyścig
    save_json(combined, f"{DATA_DIR}/latest.json")

    print("\n" + "=" * 60)
    print(f"Gotowe! Dane zapisane do {race_file}")
    print(f"Pozostałe zapytania API: {analysis_raw.get('apiRequestsRemaining', '?')}")
    print("=" * 60)

    return race_file


if __name__ == "__main__":
    fetch_post_race()
