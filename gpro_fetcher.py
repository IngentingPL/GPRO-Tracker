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
import re
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

# Plik z aktywnym kontekstem sezonu/wyścigu (Office + Calendar)
CURRENT_CONTEXT_FILE = "data/current_context.json"

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


def fetch_practice():
    """
    Pobiera dane praktyk z bieżącego wyścigu (Practice endpoint).
    
    Mini-lekcja: Ten endpoint zwraca dane podczas trwania tygodnia wyścigowego,
    gdy praktyki są w toku. Pozwala śledzić postępy między treningami.
    Działa TYLKO gdy wyścig jest w fazie praktyk/kwalifikacji,
    lub gdy jesteśmy zalogowani i mamy aktywny wyścig w toku.
    """
    print("  Pobieram dane praktyk (Practice)...")
    return api_get("Practice")


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
            "tyres": setup.get("setTyres", ""),
            "feedback": setup.get("feedback", "")
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


def extract_practice_data(practice, office_context=None, driver_raw=None):
    """
    Wyciąga dane setupów z praktyk/Q1 do kompaktowego formatu.
    
    Mini-lekcja: Ten endpoint zwraca dane w innym formacie niż RaceAnalysis.
    Musimy znormalizować je do tego samego formatu co pliki wyścigowe.
    
    Args:
        practice: Surowe dane z endpointu /Practice
        office_context: Słownik z season/race z Office API (fallback)
        driver_raw: Surowe dane z endpointu DriProfile (dane kierowcy)
    """
    if not practice:
        return None
    
    # Sprawdź czy jesteśmy zalogowani (praktyka działa tylko gdy wyścig trwa)
    if practice.get("loggedOut"):
        return None
    
    office_context = office_context or {}
    driver_raw = driver_raw or {}
    
    # Wyciągamy dane setupów z praktyk
    # UWAGA: Dane są w lapsDone, nie w setups!
    setups = []
    for lap in practice.get("lapsDone", []):
        # Nazwa sesji - zakładamy że to praktyka ( Training )
        # W GPRO kolejne okrążenia = kolejne sesje praktyk
        lap_idx = lap.get("idx", 0)
        session_name = f"Trening {lap_idx}" if lap_idx else "Trening 1"
        
        # Wyciągnij setup z każdego lap (setFWing, setEngine, etc.)
        # Każde to obiekt z {value, color, comment}
        fw_data = lap.get("setFWing", {})
        rw_data = lap.get("setRWing", {})
        eng_data = lap.get("setEngine", {})
        bra_data = lap.get("setBrakes", {})
        gear_data = lap.get("setGear", {})
        susp_data = lap.get("setSusp", {})
        
        # Zbuduj komentarz z driComments - połącz wszystkie komentarze
        comments = []
        for c in lap.get("driComments", []):
            text = c.get("text", "")
            if text:
                # Dekoduj HTML entities
                text = text.replace("&#281;", "ą").replace("&#347;", "ś")
                text = text.replace("&#261;", "ą").replace("&#322;", "ł")
                text = text.replace("&#281;", "ą")
                comments.append(text)
        feedback = "; ".join(comments) if comments else ""
        
        # Określ kolor (dla backwards compatibility)
        # color: "lime" = green/satisfied, "yellow" = marginal, "red" = bad
        tyre_count = practice.get("setDryTyres", "3")
        
        setups.append({
            "session": session_name,
            "fw": fw_data.get("value", 0),
            "rw": rw_data.get("value", 0),
            "eng": eng_data.get("value", 0),
            "bra": bra_data.get("value", 0),
            "gear": gear_data.get("value", 0),
            "susp": susp_data.get("value", 0),
            "tyres": tyre_count,
            "feedback": feedback,
            # Dodatkowe pola z API
            "lap_time": lap.get("lapTime", ""),
            "mistake_time": lap.get("misTime", "")
        })
    
    # Pobierz podstawowe info o wyścigu
    # Practice API NIE zwraca sezonu/wyścigu - używamy Office jako fallback
    season = office_context.get("season")
    race = office_context.get("race")
    track = practice.get("trackName", "")
    track_id = practice.get("trackId", "")
    track_country = practice.get("trackNat", "")
    
    # Wyciągnij dane kierowcy z DriProfile
    # Format zgodny z extract_race_data() - kluczowe pola dla predictora
    driver = driver_raw.get("driver", driver_raw)
    driver_oa = driver.get("OA", "")
    driver_con = driver.get("con", "")
    driver_agr = driver.get("agr", "")
    driver_exp = driver.get("exp", "")
    driver_tei = driver.get("tei", "")
    driver_sta = driver.get("sta", "")
    driver_cha = driver.get("cha", "")
    driver_mot = driver.get("mot", "")
    driver_wei = driver.get("wei", "")
    driver_agr_age = driver.get("age") or driver_raw.get("age")
    driver_agr_overall = driver.get("overall") or driver_raw.get("overall") or driver_oa
    driver_info = {
        "name": driver.get("name", ""),
        "id": driver.get("id"),
        "OA": driver_oa,
        "age": driver_agr_age,
        "concentration": driver_con,
        "talent": driver.get("tal", ""),
        "aggressiveness": driver_agr,
        "experience": driver_exp,
        "technical_insight": driver_tei,
        "stamina": driver_sta,
        "charisma": driver_cha,
        "motivation": driver_mot,
        "weight": driver_wei
    }
    
    # Pobierz pogodę
    weather_data = practice.get("weather", {})
    weather = {}
    if weather_data:
        weather = {
            "q1": {
                "condition": weather_data.get("q1WeatherTransl") or weather_data.get("q1Weather", ""),
                "temp": weather_data.get("q1Temp"),
                "humidity": weather_data.get("q1Hum")
            },
            "q2": {
                "condition": weather_data.get("q2WeatherTransl") or weather_data.get("q2Weather", ""),
                "temp": weather_data.get("q2Temp"),
                "humidity": weather_data.get("q2Hum")
            }
        }
    
    return {
        "season": season,
        "race": race,
        "track": track,
        "track_country": track_country,
        "track_id": track_id,
        "setups": setups,
        "weather": weather,
        "driver": driver_info,  # Dane kierowcy dla predictora
        "fetched_at": datetime.utcnow().isoformat() + "Z"
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
# POMOCNICZE FUNKCJE KONTEKSTU SEZONU / KALENDARZA
# ============================================================

def load_json_safe(filepath):
    """Wczytuje JSON jeśli plik istnieje i ma poprawny format."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [OSTRZEŻENIE] Nie udało się wczytać {filepath}: {e}")
        return None


def normalize_int(value):
    """Konwertuje wartość do int jeśli to możliwe."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else None


def extract_office_context(office_raw):
    """Wyciąga sezon i numer aktywnego wyścigu z endpointu Office."""
    if not isinstance(office_raw, dict):
        return {"season": None, "race": None}

    season = None
    race = None

    # Sezon
    for key in ["season", "selSeasonNb", "currentSeason", "curSeason", "seasonNb"]:
        val = office_raw.get(key)
        if isinstance(val, dict):
            season = normalize_int(val.get("season") or val.get("seasonNb") or val.get("number"))
        else:
            season = normalize_int(val)
        if season is not None:
            break

    # Wyścig
    for key in ["nextRace", "race", "selRaceNb", "currentRace", "curRace", "raceNb"]:
        val = office_raw.get(key)
        if isinstance(val, dict):
            # Jeśli to obiekt (np. nextRace), szukamy w środku
            race = normalize_int(val.get("race") or val.get("raceNb") or val.get("number") or val.get("idx"))
        else:
            race = normalize_int(val)
        if race is not None:
            break

    return {"season": season, "race": race}


def extract_calendar_races(calendar_payload):
    """Zwraca listę eventów z kalendarza niezależnie od formatu."""
    if isinstance(calendar_payload, list):
        return calendar_payload

    if isinstance(calendar_payload, dict):
        data = calendar_payload.get("data", calendar_payload)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ["races", "calendar", "events", "schedule", "items", "data"]:
                value = data.get(key)
                if isinstance(value, list):
                    return value
        for key in ["races", "calendar", "events", "schedule", "items"]:
            value = calendar_payload.get(key)
            if isinstance(value, list):
                return value

    return []


def extract_calendar_season(calendar_payload):
    """Próbuje ustalić sezon zapisany w kalendarzu."""
    if isinstance(calendar_payload, dict):
        for key in ["season", "selSeasonNb", "currentSeason", "seasonNb"]:
            season = normalize_int(calendar_payload.get(key))
            if season is not None:
                return season

    for event in extract_calendar_races(calendar_payload):
        if not isinstance(event, dict):
            continue
        for key in ["season", "selSeasonNb", "seasonNb"]:
            season = normalize_int(event.get(key))
            if season is not None:
                return season

    return None


def build_calendar_payload(calendar_raw, office_context=None):
    """Normalizuje odpowiedź kalendarza do spójnego formatu JSON."""
    office_context = office_context or {}
    race_data = extract_calendar_races(calendar_raw)
    season = office_context.get("season") or extract_calendar_season(calendar_raw)

    return {
        "season": season,
        "office_race": office_context.get("race"),
        "data": race_data,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }


def is_transfer_market_event(event):
    """Zwraca True dla eventów typu rynek transferowy / nie-race."""
    if not isinstance(event, dict):
        return True

    event_type = str(event.get("eventType", "")).strip().upper()
    if event_type and event_type != "R":
        return True

    name = str(event.get("trackName") or event.get("track") or event.get("name") or event.get("raceName") or "").strip().lower()
    blocked = ["transfer market", "rynek transferowy", "market #", "transferowy #"]
    return any(fragment in name for fragment in blocked)


def build_current_context(calendar_payload, office_context=None, latest_completed=None):
    """Buduje aktywny kontekst sezonu/wyścigu z Office + Calendar."""
    office_context = office_context or {}
    latest_completed = latest_completed or {}

    office_season = normalize_int(office_context.get("season"))
    office_race = normalize_int(office_context.get("race"))
    calendar_season = extract_calendar_season(calendar_payload) or office_season

    normalized = []
    for event in extract_calendar_races(calendar_payload):
        if not isinstance(event, dict) or is_transfer_market_event(event):
            continue

        season = (
            normalize_int(event.get("season"))
            or normalize_int(event.get("selSeasonNb"))
            or normalize_int(event.get("seasonNb"))
            or calendar_season
            or office_season
        )
        race = (
            normalize_int(event.get("race"))
            or normalize_int(event.get("raceNb"))
            or normalize_int(event.get("round"))
            or normalize_int(event.get("number"))
            or normalize_int(event.get("idx"))
            or normalize_int(event.get("selRaceNb"))
        )
        track = event.get("trackName") or event.get("track") or event.get("name") or event.get("raceName")
        if season is None or race is None or not track:
            continue

        normalized.append({
            "season": season,
            "race": race,
            "track": track,
            "track_id": event.get("trackId") or event.get("trackID") or event.get("id"),
            "total_laps": normalize_int(event.get("totalLaps")) or normalize_int(event.get("total_laps")) or normalize_int(event.get("laps")) or normalize_int(event.get("lapNb")) or 72,
            "is_current": normalize_int(event.get("isCurrentRace")) == 1 or event.get("current") is True or event.get("upcoming") is True
        })

    normalized.sort(key=lambda x: (x["season"], x["race"]))

    latest_season = normalize_int(latest_completed.get("season"))
    latest_race = normalize_int(latest_completed.get("race"))

    selected = None

    # 1. Priorytet: Office API (najbardziej aktualne dane o tym co widzi manager)
    if office_season is not None and office_race is not None:
        selected = next((event for event in normalized if event["season"] == office_season and event["race"] == office_race), None)

    # 2. Jeśli brak w Office lub Office wskazuje na już ukończony wyścig, szukamy następnego po latest_completed
    if latest_season is not None:
        is_office_stale = False
        if selected:
            if office_season < latest_season:
                is_office_stale = True
            elif office_season == latest_season and office_race is not None and latest_race is not None and office_race <= latest_race:
                is_office_stale = True

        if not selected or is_office_stale:
            for event in normalized:
                if event["season"] > latest_season:
                    selected = event
                    break
                if event["season"] == latest_season and latest_race is not None and event["race"] > latest_race:
                    selected = event
                    break

    # 3. Jeśli nadal brak, szukamy flagi isCurrent z kalendarza
    if not selected:
        selected = next((event for event in normalized if event.get("is_current")), None)

    if not selected and normalized:
        selected = normalized[0]

    if not selected:
        return {
            "season": office_season or calendar_season or latest_season,
            "race": office_race,
            "track": None,
            "track_id": None,
            "total_laps": 72,
            "phase": "unknown",
            "latest_completed": latest_completed,
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }

    return {
        **selected,
        "phase": "upcoming",
        "latest_completed": latest_completed,
        "office_season": office_season,
        "office_race": office_race,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }

# ============================================================
# GŁÓWNA LOGIKA SKRYPTU
# ============================================================

def fetch_and_cache_calendar():
    """
    Pobiera kalendarz z API i zapisuje do osobnego pliku.
    Odświeża cache nie tylko wg wieku pliku, ale też przy zmianie sezonu
    lub gdy Office wskazuje początek nowego sezonu (wyścig 1).
    """
    cached_calendar = load_json_safe(CALENDAR_FILE)
    file_exists = os.path.exists(CALENDAR_FILE)
    file_age = time.time() - os.path.getmtime(CALENDAR_FILE) if file_exists else None

    office_raw = fetch_office()
    office_context = extract_office_context(office_raw)
    office_season = office_context.get("season")
    office_race = office_context.get("race")
    cached_season = extract_calendar_season(cached_calendar)

    refresh_reasons = []
    if not file_exists:
        refresh_reasons.append("brak pliku")
    elif file_age is not None and file_age >= CALENDAR_MAX_AGE:
        refresh_reasons.append(f"wiek {file_age / 3600:.0f}h")

    if office_race == 1:
        refresh_reasons.append("Office wskazuje początek sezonu (Race 1)")

    if office_season is not None and cached_season is not None and office_season != cached_season:
        refresh_reasons.append(f"zmiana sezonu: cache S{cached_season} -> Office S{office_season}")

    if not refresh_reasons and file_exists:
        print(f"  Kalendarz aktualny (wiek: {file_age / 3600:.0f}h). Pomijam pobieranie.")
        return cached_calendar

    reason_text = ", ".join(refresh_reasons) if refresh_reasons else "wymuszony refresh"
    print(f"  Odświeżam kalendarz ({reason_text}).")
    if office_raw:
        pause_between_requests()

    calendar_raw = fetch_calendar()
    if not calendar_raw:
        print("  [OSTRZEŻENIE] Nie udało się pobrać kalendarza.")
        return cached_calendar

    normalized_calendar = build_calendar_payload(calendar_raw, office_context)
    save_json(normalized_calendar, CALENDAR_FILE)
    return normalized_calendar

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
    calendar_payload = fetch_and_cache_calendar()
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

    # 8.5. Zapisujemy aktywny kontekst sezonu/wyścigu z Office + Calendar
    latest_completed = {"season": season, "race": race, "track": track}
    office_context = {
        "season": normalize_int(calendar_payload.get("season")) if isinstance(calendar_payload, dict) else None,
        "race": normalize_int(calendar_payload.get("office_race")) if isinstance(calendar_payload, dict) else None
    }
    current_context = build_current_context(calendar_payload or {}, office_context, latest_completed)
    save_json(current_context, CURRENT_CONTEXT_FILE)

    # 9. Pobierz profil aktywnego następnego toru (jeśli znamy track_id)
    next_track_id = current_context.get("track_id") if isinstance(current_context, dict) else None
    try:
        if next_track_id:
            pause_between_requests()
            fetch_track_profile(next_track_id)
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


def fetch_current_week_data():
    """
    Pobiera dane z bieżącego tygodnia wyścigowego (praktyki, Q1).
    
    Mini-lekcja: Ten endpoint działa w trakcie tygodnia wyścigowego,
    gdy praktyki są w toku. Pozwala aktualizować dane między treningami.
    Jeśli wyścig jest po finale (brak praktyk), endpoint zwraca loggedOut=1.
    """
    print("=" * 60)
    print("GPRO Current Week Data Fetcher")
    print("=" * 60)
    
    if not API_TOKEN:
        print("[BŁĄD] Brak tokenu API!")
        print("Ustaw zmienną środowiskową GPRO_TOKEN lub GitHub Secret.")
        return
    
    # 1. Pobierz Office żeby wiedzieć jaki jest bieżący wyścig
    print("\n1. Pobieranie Office...")
    office_raw = fetch_office()
    
    if not office_raw:
        print("  [OSTRZEŻENIE] Nie udało się pobrać danych Office.")
        return
    
    # Sprawdź czy jesteśmy zalogowani
    if office_raw.get("loggedOut"):
        print("  [INFO] Nie jesteś zalogowany do GPRO.")
        return
    
    office_context = extract_office_context(office_raw)
    season = office_context.get("season")
    race = office_context.get("race")
    
    if not season or not race:
        print("  [INFO] Brak aktywnego wyścigu w Office.")
        return
    
    print(f"  Office wskazuje na: S{season}R{race}")
    
    # 2. Spróbuj pobrać dane praktyk
    print("\n2. Pobieranie danych praktyk (Practice endpoint)...")
    pause_between_requests()
    practice_raw = fetch_practice()
    
    if not practice_raw:
        print("  [OSTRZEŻENIE] Nie udało się pobrać danych praktyk.")
        return
    
    # 2b. Pobierz dane kierowcy (potrzebne dla predictora)
    print("\n2b. Pobieranie profilu kierowcy (DriProfile)...")
    pause_between_requests()
    driver_raw = fetch_driver_profile()
    
    # Sprawdź czy jesteśmy zalogowani (endpoint działa tylko gdy praktyki trwają)
    if practice_raw.get("loggedOut"):
        print("  [INFO] Praktyki nie są dostępne (wyścig zakończony lub przed startem).")
        print("  Pomijam zapis danych praktyk.")
        return
    
    # 3. Wyciągnij dane (przekaż office_context i driver_raw)
    print("\n3. Przetwarzanie danych praktyk...")
    practice_data = extract_practice_data(practice_raw, office_context, driver_raw)
    
    if not practice_data:
        print("  [OSTRZEŻENIE] Nie udało się przetworzyć danych praktyk.")
        return
    
    s = practice_data.get("season")
    r = practice_data.get("race")
    track = practice_data.get("track", "")
    setups_count = len(practice_data.get("setups", []))
    
    print(f"  Sezon: {s}, Wyścig: {r}, Tor: {track}")
    print(f"  Znaleziono {setups_count} ukończonych sesji.")
    
    if setups_count == 0:
        print("  [INFO] Brak ukończonych sesji - nic do zapisania.")
        return
    
    # 4. Zapisz do pliku bieżącego wyścigu
    practice_file = f"{DATA_DIR}/S{s}R{r}.json"
    
    # Jeśli plik już istnieje, wczytaj go żeby nie nadpisać innych danych
    existing_data = load_json_safe(practice_file)
    
    # Pobierz driver_raw do zapisania jako driver_profile
    driver_for_profile = driver_raw if driver_raw else None
    
    if existing_data:
        print(f"  Plik {practice_file} już istnieje - aktualizuję setups.")
        # Zachowaj existing data ale zaktualizuj race_data.setups
        existing_data.setdefault("race_data", {})
        existing_data["race_data"]["setups"] = practice_data.get("setups", [])
        existing_data["race_data"]["weather"] = practice_data.get("weather", {})
        existing_data["race_data"]["track"] = track
        existing_data["race_data"]["track_id"] = practice_data.get("track_id", "")
        existing_data["race_data"]["track_country"] = practice_data.get("track_country", "")
        # Zachowaj też driver jeśli już istnieje
        if practice_data.get("driver") and not existing_data["race_data"].get("driver"):
            existing_data["race_data"]["driver"] = practice_data.get("driver")
        # Zachowaj też driver_profile jeśli już istnieje
        if driver_for_profile and not existing_data.get("driver_profile"):
            existing_data["driver_profile"] = driver_for_profile
        combined = existing_data
    else:
        # Nowy plik - utwórz pełną strukturę z driverem i driver_profile
        combined = {
            "race_data": {
                "season": str(s),
                "race": str(r),
                "track": track,
                "track_country": practice_data.get("track_country", ""),
                "track_id": practice_data.get("track_id", ""),
                "setups": practice_data.get("setups", []),
                "weather": practice_data.get("weather", {}),
                "driver": practice_data.get("driver", {}),
                "fetched_at": practice_data.get("fetched_at", "")
            },
            "race_summary": None,
            "driver_profile": driver_for_profile,
            "standings": None,
            "car_status": None
        }
    
    # Zapisz
    save_json(combined, practice_file)
    print(f"  ✓ Zapisano dane praktyk do: {practice_file}")
    
    print("\n" + "=" * 60)
    print(f"Gotowe! Dane praktyk zapisane do {practice_file}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GPRO Data Fetcher")
    parser.add_argument("--mode", choices=["post-race", "current-week"], default="post-race",
                        help="Tryb działania: post-race (po wyścigu) lub current-week (w trakcie tygodnia)")
    args = parser.parse_args()
    
    if args.mode == "current-week":
        fetch_current_week_data()
    else:
        fetch_post_race()
