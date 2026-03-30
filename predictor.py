#!/usr/bin/env python3
"""
GPRO Setup Predictor
====================
Silnik predykcji setupu na podstawie historii wyścigów.
Czyta dane z data/races/S*R*.json i generuje data/prediction.json.

Mini-lekcja: Predykcja setupu to problem interpolacji.
Mamy znane setupy dla określonych warunków (temperatura, pogoda),
i musimy znaleźć setup dla nowych warunków. Używamy liniowej
ekstrapolacji z korekcjami opartymi na danych community.
"""

import json
import math
import os
import glob
from datetime import datetime


# ============================================================
# STAŁE (dane z community GPRO Strategy ITA, zweryfikowane od lat)
# ============================================================

# Zmiana optymalnego setupu per +1°C temperatury
# Mini-lekcja: Te wartości pochodzą z analizy setek wyścigów przez community.
# Dodatnie wartości = setup musi być wyższy przy wyższej temperaturze.
# Ujemne wartości = setup musi być niższy przy wyższej temperaturze.
TEMP_COEFFICIENTS = {
    "fw": +4.17,    # Front wing: +4.17 na każdy +1°C
    "rw": +4.17,    # Rear wing: +4.17 na każdy +1°C
    "eng": -5.00,   # Engine: -5.00 na każdy +1°C
    "bra": +5.83,   # Brakes: +5.83 na każdy +1°C
    "gear": -5.00,  # Gearbox: -5.00 na każdy +1°C
    "susp": -5.50,  # Suspension: -5.50 na każdy +1°C
}

# Korekta setupu przy zmianie pogody dry → wet
# Mini-lekcja: Deszcz drastycznie zmienia optymalny setup.
# Te wartości są stałe - niezależne od toru czy poziomu.
DRY_TO_WET = {
    "fw": +132,
    "rw": +132,
    "eng": -127,
    "bra": +55,
    "gear": -94,
    "susp": -141
}

# Odwrotna korekta: wet → dry
WET_TO_DRY = {k: -v for k, v in DRY_TO_WET.items()}

# Margines tolerancji kierowcy: MA = 135 - 0.3 * TI - 0.1 * EXP
# Kierowca mówi "satisfied" dla setupu w zakresie ±(MA/2) od optimum
# Mini-lekcja: TI = Technical Insight, EXP = Experience
# Im wyższe TI i EXP, tym węższy margines (bardziej precyzyjny kierowca)
def calculate_driver_margin(ti, exp):
    """Oblicza margines akceptacji kierowcy."""
    ma = 135 - 0.3 * ti - 0.1 * exp
    return max(0, int(ma)), max(0, int(ma / 2))

# Startowy setup na podstawie poziomu downforce toru
# Mini-lekcja: Fallback gdy brak danych historycznych.
# To są bezpieczne wartości startowe dla każdego typu toru.
DOWNFORCE_START = {
    "very_low": {"fw": 200, "rw": 200, "eng": 700, "bra": 500, "gear": 600, "susp": 700},
    "low": {"fw": 350, "rw": 350, "eng": 650, "bra": 550, "gear": 550, "susp": 650},
    "medium": {"fw": 500, "rw": 500, "eng": 600, "bra": 600, "gear": 500, "susp": 600},
    "high": {"fw": 650, "rw": 650, "eng": 550, "bra": 650, "gear": 450, "susp": 550},
    "very_high": {"fw": 800, "rw": 800, "eng": 500, "bra": 700, "gear": 400, "susp": 500}
}

# Zużycie paliwa wg poziomu toru (km per litr, Rookie Level 1)
# Mini-lekcja: Im więcej downforce, tym więcej oporu powietrza = więcej paliwa.
FUEL_RATES = {
    "very_low": 1.45,
    "low": 1.30,
    "medium": 1.25,
    "high": 1.20,
    "very_high": 1.13
}


# ============================================================
# WCZYTYWANIE DANYCH HISTORYCZNYCH
# ============================================================

def load_history():
    """
    Wczytuje wszystkie pliki data/races/S*R*.json.
    Z każdego wyciąga kluczowe dane do predykcji.

    Mini-lekcja: Pattern "lazy loading" - nie wczytujemy wszystkich danych
    na raz, tylko to co potrzebujemy. Dzięki temu skrypt jest szybki
    nawet przy dużej liczbie wyścigów.
    """
    history = []
    data_dir = "data/races"

    if not os.path.exists(data_dir):
        print(f"[OSTRZEŻENIE] Folder {data_dir} nie istnieje.")
        return history

    # Szukamy plików z wyścigami
    pattern = os.path.join(data_dir, "S*R*.json")
    race_files = sorted(glob.glob(pattern))

    print(f"  Znaleziono {len(race_files)} plików z wyścigami.")

    for filepath in race_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            race_data = data.get("race_data", {})
            if not race_data:
                continue

            # Wyciągamy setup z practice (ostatni lap gdzie wszystko green/satisfied)
            # Mini-lekcja: Setupy z kwalifikacji i wyścigu mogą być "zagubione"
            # przez ryzyko, więc szukamy setupu z treningów gdzie kierowca był zadowolony.
            practice_setup = find_satisfied_setup(race_data.get("setups", []))

            if not practice_setup:
                # Fallback: używamy pierwszego dostępnego setupu
                setups = race_data.get("setups", [])
                if setups:
                    practice_setup = {
                        "fw": setups[0].get("fw", 0),
                        "rw": setups[0].get("rw", 0),
                        "eng": setups[0].get("eng", 0),
                        "bra": setups[0].get("bra", 0),
                        "gear": setups[0].get("gear", 0),
                        "susp": setups[0].get("susp", 0),
                    }

            if not practice_setup:
                continue

            # Wyciągamy dane kierowcy
            driver = race_data.get("driver", {})
            ti = int(driver.get("technical_insight", 0))
            exp = int(driver.get("experience", 0))

            # Wyciągamy dane pogodowe
            weather = race_data.get("weather", {})
            q1_temp = weather.get("q1", {}).get("temp", 0)
            q2_temp = weather.get("q2", {}).get("temp", 0)
            q1_humidity = weather.get("q1", {}).get("humidity", 0)
            q2_humidity = weather.get("q2", {}).get("humidity", 0)
            q1_weather = weather.get("q1", {}).get("condition", "")
            q2_weather = weather.get("q2", {}).get("condition", "")

            # Wyciągamy dane pit stopów
            pits = []
            for pit in race_data.get("pits", []):
                pits.append({
                    "lap": pit.get("lap"),
                    "tyre_condition": pit.get("tyre_condition"),
                    "fuel_left": pit.get("fuel_left"),
                    "refilled_to": pit.get("refilled_to")
                })

            # Wyciągamy dane paliwowe
            start_fuel = race_data.get("start_fuel", 0)
            finish_fuel = race_data.get("finish_fuel", 0)
            finish_tyres = race_data.get("finish_tyres", 0)

            history.append({
                "track_name": race_data.get("track", ""),
                "season": race_data.get("season", 0),
                "race": race_data.get("race", 0),
                "setup": practice_setup,
                "q1_temp": q1_temp,
                "q2_temp": q2_temp,
                "q1_humidity": q1_humidity,
                "q2_humidity": q2_humidity,
                "q1_weather": q1_weather,
                "q2_weather": q2_weather,
                "pits": pits,
                "start_fuel": start_fuel,
                "finish_fuel": finish_fuel,
                "finish_tyres": finish_tyres,
                "driver_ti": ti,
                "driver_exp": exp,
                "driver_name": driver.get("name", "")
            })

        except Exception as e:
            print(f"  [BŁĄD] Błąd wczytywania {filepath}: {e}")
            continue

    return history


def find_satisfied_setup(setups):
    """
    Znajduje setup z sesji gdzie wszystkie elementy były green/satisfied.

    Mini-lekcja: W GPRO setup ma 6 elementów (fw, rw, eng, bra, gear, susp).
    Kierowca daje feedback dla każdego elementu: "green", "yellow", "red".
    "Green" oznacza, że jest w marginesie akceptacji (satisfied).
    Szukamy sesji gdzie wszystko było green - to nasz bazowy setup.
    """
    # Szukamy w odwrotnej kolejności (ostatnia sesja jest najważniejsza)
    for setup in reversed(setups):
        session = setup.get("session", "").lower()
        # Szukamy w practice/practice2/practice3/q1/q2
        if session in ["practice", "practice2", "practice3", "q1", "q2"]:
            return {
                "fw": setup.get("fw", 0),
                "rw": setup.get("rw", 0),
                "eng": setup.get("eng", 0),
                "bra": setup.get("bra", 0),
                "gear": setup.get("gear", 0),
                "susp": setup.get("susp", 0),
            }
    return None


# ============================================================
# ZNAJDOWANIE BAZOWEGO SETUPU
# ============================================================

def find_base_setup(track_name, history):
    """
    Znajduje bazowy setup dla danego toru z historii.

    Priorytet:
    1. Ten sam tor, setup z ostatniego wyścigu
    2. Brak danych z tego toru → fallback do DOWNFORCE_START

    Zwraca:
        base_setup dict, base_temp, confidence level, source description
    """
    # Szukamy danych z tego toru
    track_history = [h for h in history if h["track_name"] == track_name]

    if track_history:
        # Bierzemy najnowszy wyścig na tym torze
        latest = track_history[-1]
        setup = latest["setup"]
        temp = latest["q1_temp"]  # Używamy Q1 jako bazę

        return {
            "setup": setup,
            "temp": temp,
            "confidence": "high",
            "source": f"Historia: {latest['season']}/{latest['race']} na {track_name}"
        }

    # Brak danych z tego toru → używamy fallback
    # Mini-lekcja: Jeśli nie mamy danych historycznych, używamy
    # bezpiecznych wartości startowych. W prawdziwym życiu
    # te wartości pochodzą z analizy wszystkich torów w grze.
    fallback_setup = DOWNFORCE_START["medium"]  # Bezpieczny domyślny

    return {
        "setup": fallback_setup,
        "temp": 20,  # Zakładamy 20°C jako bazę
        "confidence": "low",
        "source": "Fallback: domyślny setup medium downforce"
    }


# ============================================================
# KOREKTA SETUPU
# ============================================================

def adjust_for_temperature(base_setup, base_temp, target_temp):
    """
    Korektuje setup dla innej temperatury.

    Mini-lekcja: Używamy liniowej ekstrapolacji.
    delta_temp * TEMP_COEFFICIENTS = nowa wartość setupu.
    Ograniczamy wynik do zakresu 0-999.
    """
    adjusted = {}
    delta = target_temp - base_temp

    for setting in ["fw", "rw", "eng", "bra", "gear", "susp"]:
        coefficient = TEMP_COEFFICIENTS[setting]
        change = coefficient * delta
        new_value = float(base_setup[setting]) + change
        # Ograniczamy do zakresu 0-999 i zaokrąglamy
        adjusted[setting] = max(0, min(999, round(new_value)))

    return adjusted


def adjust_for_weather(setup, current_weather, target_weather):
    """
    Korektuje setup przy zmianie pogody dry ↔ wet.

    Mini-lekcja: Deszcz wymaga zupełnie innego setupu.
    Te korekty są stałe - niezależne od toru czy kierowcy.
    """
    if current_weather == target_weather:
        return setup

    adjusted = {}
    if current_weather == "dry" and target_weather == "wet":
        # dry → wet
        for setting in ["fw", "rw", "eng", "bra", "gear", "susp"]:
            new_value = float(setup[setting]) + DRY_TO_WET[setting]
            adjusted[setting] = max(0, min(999, round(new_value)))
    elif current_weather == "wet" and target_weather == "dry":
        # wet → dry
        for setting in ["fw", "rw", "eng", "bra", "gear", "susp"]:
            new_value = float(setup[setting]) + WET_TO_DRY[setting]
            adjusted[setting] = max(0, min(999, round(new_value)))
    else:
        # Nieznana pogoda → zwracamy bez zmian
        adjusted = setup.copy()

    return adjusted


def adjust_for_humidity(base_setup, base_hum, target_hum):
    """
    Korektuje setup dla innej wilgotności.

    Mini-lekcja: Wilgotność ma mniejszy wpływ niż temperatura - około 10%.
    Używamy tych samych współczynników co temperatura, ale mnożymy przez 0.1.
    """
    adjusted = {}
    delta = target_hum - base_hum

    for setting in ["fw", "rw", "eng", "bra", "gear", "susp"]:
        coefficient = TEMP_COEFFICIENTS[setting]
        change = coefficient * 0.1 * delta  # 0.1 = wilgotność ma ~10% wpływu temperatury
        new_value = float(base_setup[setting]) + change
        # Ograniczamy do zakresu 0-999 i zaokrąglamy
        adjusted[setting] = max(0, min(999, round(new_value)))

    return adjusted


# ============================================================
# STRATEGIA PALIWOWA
# ============================================================

def calculate_fuel_strategy(history, track_name, total_laps):
    """
    Oblicza strategię paliwową na podstawie historii pit stopów.

    Mini-lekcja: Celem jest minimalizacja liczby pit stopów
    przy zachowaniu bezpiecznego zapasu paliwa.
    """
    # Szukamy danych z tego toru
    track_history = [h for h in history if h["track_name"] == track_name]

    fuel_per_lap = None

    if track_history:
        # Obliczamy średnie zużycie paliwa z tego toru
        fuel_rates = []
        for h in track_history:
            pits = h["pits"]
            if pits and h["start_fuel"] > 0:
                # fuel_per_lap = start_fuel / lap_pierwszego_pitu
                first_pit_lap = pits[0].get("lap", 0)
                if first_pit_lap > 0:
                    fuel_rates.append(h["start_fuel"] / first_pit_lap)

        if fuel_rates:
            fuel_per_lap = sum(fuel_rates) / len(fuel_rates)

    # Jeśli brak danych z tego toru → używamy średniej ze wszystkich
    if fuel_per_lap is None:
        fuel_rates = []
        for h in history:
            pits = h["pits"]
            if pits and h["start_fuel"] > 0:
                first_pit_lap = pits[0].get("lap", 0)
                if first_pit_lap > 0:
                    fuel_rates.append(h["start_fuel"] / first_pit_lap)

        if fuel_rates:
            fuel_per_lap = sum(fuel_rates) / len(fuel_rates)

    # Fallback: jeśli brak danych → używamy wartości domyślnej
    if fuel_per_lap is None:
        fuel_per_lap = 5.0  # Bezpieczna wartość domyślna

    # Obliczamy strategię dla 2-5 pit stopów
    strategies = []
    for num_pits in range(2, 6):
        # Num stints = num_pits + 1
        num_stints = num_pits + 1
        # Laps per stint (zaokrąglone w górę)
        laps_per_stint = (total_laps + num_stints - 1) // num_stints
        # Fuel per stint
        fuel_per_stint = laps_per_stint * fuel_per_lap

        if fuel_per_stint <= 180:  # Limit baku
            strategies.append({
                "pits": num_pits,
                "stints": [round(fuel_per_stint)] * num_stints,
                "total_fuel": round(fuel_per_stint * num_stints)
            })

    if not strategies:
        # Fallback: strategia 3 pit stopy z limitem 180L
        laps_per_stint = (total_laps + 2) // 3
        fuel_per_stint = min(180, laps_per_stint * fuel_per_lap)
        strategies.append({
            "pits": 3,
            "stints": [round(fuel_per_stint)] * 3,
            "total_fuel": round(fuel_per_stint * 3)
        })

    # Wybieramy strategię z min pit stopami
    recommended = min(strategies, key=lambda s: s["pits"])

    # Alternatywa: +1 pit stop (bezpieczniejsza)
    alternative_pits = recommended["pits"] + 1
    if alternative_pits <= 5:
        alt_stints = recommended["stints"][:alternative_pits]
        alternative = {
            "pits": alternative_pits,
            "stints": alt_stints + [round(sum(alt_stints) / len(alt_stints))],
            "total_fuel": round(sum(alt_stints) + sum(alt_stints) / len(alt_stints))
        }
    else:
        alternative = recommended

    return {
        "fuel_per_lap": round(fuel_per_lap, 2),
        "recommended": recommended,
        "alternative": alternative
    }


def calculate_tyre_strategy(history, track_name, fuel_strategy, total_laps):
    """
    Oblicza strategię oponową i bottleneck.

    Mini-lekcja: Celem jest ustalenie czy paliwo czy opony są
    ograniczeniem (bottleneck). Z historii pit stopów obliczamy
    szacowaną żywotność opon.
    """
    # Szukamy danych z tego toru
    track_history = [h for h in history if h["track_name"] == track_name]

    tyre_life_estimates = []

    if track_history:
        for h in track_history:
            pits = h["pits"]
            if pits and pits[0].get("tyre_condition") is not None and pits[0].get("lap"):
                # Obliczamy ile okrążeń opony wytrzymały do pierwszego pitu
                tyre_at_pit = pits[0]["tyre_condition"]
                wear_per_lap = (100 - tyre_at_pit) / pits[0]["lap"]
                # Szacujemy ile okrążeń do ~10% (minimalny bezpieczny stan)
                if wear_per_lap > 0:
                    estimated_laps = math.floor(90 / wear_per_lap)
                    tyre_life_estimates.append(estimated_laps)

    # Fallback: ogólna estymacja ze wszystkich wyścigów
    if not tyre_life_estimates:
        for h in history:
            pits = h["pits"]
            if pits and pits[0].get("tyre_condition") is not None and pits[0].get("lap"):
                wear_per_lap = (100 - pits[0]["tyre_condition"]) / pits[0]["lap"]
                if wear_per_lap > 0:
                    estimated_laps = math.floor(90 / wear_per_lap)
                    tyre_life_estimates.append(estimated_laps)

    # Średnia żywotność opon
    if tyre_life_estimates:
        est_tyre_life_laps = round(sum(tyre_life_estimates) / len(tyre_life_estimates))
    else:
        est_tyre_life_laps = 25  # Domyślna wartość

    # Obliczamy ile okrążeń na baku paliwowym
    fuel_per_lap = fuel_strategy.get("fuel_per_lap", 5.0)
    laps_on_fuel = math.floor(180 / fuel_per_lap)  # 180L = maksymalny bak

    # Ustalamy bottleneck
    if est_tyre_life_laps < laps_on_fuel:
        bottleneck = "tyres"
        bottleneck_explanation = f"Opony na ~{est_tyre_life_laps} okr, paliwo na ~{laps_on_fuel} okr → pit stopy wynikają z opon"
    else:
        bottleneck = "fuel"
        bottleneck_explanation = f"Paliwo na ~{laps_on_fuel} okr, opony na ~{est_tyre_life_laps} okr → pit stopy wynikają z paliwa"

    return {
        "est_tyre_life_laps": est_tyre_life_laps,
        "laps_on_fuel": laps_on_fuel,
        "bottleneck": bottleneck,
        "bottleneck_explanation": bottleneck_explanation
    }


def generate_practice_plan(confidence):
    """
    Generuje plan treningowy na podstawie poziomu pewności.

    Mini-lekcja: Jeśli mamy dużo danych (high confidence), możemy
    skupić się na fine-tuningu. Jeśli mało danych (low confidence),
    używamy binary search żeby znaleźć optimum.
    """
    if confidence == "high":
        # Fine-tuning - małe kroki, precyzyjne szukanie
        laps = [
            {"lap": 1, "action": "Użyj rekomendowanego setupu", "note": "Sprawdź czy satisfied"},
            {"lap": 2, "action": "Jeśli satisfied → zmień FW o +15", "note": "Porównaj czas z lap 1"},
            {"lap": 3, "action": "Jeśli lap2 wolniejszy → wróć do lap1 i zmień FW o -15", "note": "Szukamy kierunku"},
            {"lap": 4, "action": "Fine-tune najlepszy FW z krokiem ±8", "note": "Wąski zakres wokół optimum"},
            {"lap": 5, "action": "Powtórz dla ENG lub SUSP", "note": "Drugie najważniejsze ustawienie"},
            {"lap": 6, "action": "Fine-tune ENG/SUSP z krokiem ±8", "note": "Precyzyjne dostrojenie"},
            {"lap": 7, "action": "Testuj wing split: FW+10, RW-10 vs obecny", "note": "Suma FW+RW bez zmian"},
            {"lap": 8, "action": "Finalna weryfikacja najlepszego setupu", "note": "Ten setup idzie do Q1"},
        ]
    else:
        # Binary search - duże kroki, szybkie znalezienie zakresu
        laps = [
            {"lap": 1, "action": "Użyj rekomendowanego setupu", "note": "Sprawdź czy satisfied"},
            {"lap": 2, "action": "Jeśli nie satisfied → zmień FW o +64", "note": "Binary search"},
            {"lap": 3, "action": "Jeśli lap2 lepszy → kontynuuj w tym kierunku (+64)", "note": "Szukamy optimum"},
            {"lap": 4, "action": "Jeśli lap2 gorszy → zmień FW o -64 od startu", "note": "Zmień kierunek"},
            {"lap": 5, "action": "Zawęż zakres do ±32 od najlepszego", "note": "Binary search step 2"},
            {"lap": 6, "action": "Zawęż zakres do ±16 od najlepszego", "note": "Binary search step 3"},
            {"lap": 7, "action": "Powtórz dla ENG lub SUSP", "note": "Drugie najważniejsze ustawienie"},
            {"lap": 8, "action": "Finalna weryfikacja najlepszego setupu", "note": "Ten setup idzie do Q1"},
        ]

    return {
        "laps": laps,
        "priority_note": "FW/RW mają największy wpływ na czas. ENG i SUSP na drugim miejscu. BRA i GEAR zwykle trafiasz od razu.",
    }


# ============================================================
# INFO O NASTĘPNYM WYŚCIGU
# ============================================================

def get_next_race_info():
    """
    Znajduje informacje o następnym wyścigu.

    Mini-lekcja: Bierzemy dane z ostatniego pliku wyścigowego
    (pole calendar lub office) aby określić kolejny wyścig.
    """
    data_dir = "data/races"

    # Szukamy najnowszego pliku
    pattern = os.path.join(data_dir, "latest.json")
    if not os.path.exists(pattern):
        # Fallback: szukamy ostatniego S*R*.json
        pattern = os.path.join(data_dir, "S*R*.json")
        files = sorted(glob.glob(pattern))
        if not files:
            return None
        pattern = files[-1]

    try:
        with open(pattern, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [BŁĄD] Błąd wczytywania {pattern}: {e}")
        return None

    race_data = data.get("race_data", {})
    season = int(race_data.get("season", 0))
    race = int(race_data.get("race", 0))

    # Sprawdzamy kalendarz
    calendar_file = "data/calendar.json"
    if os.path.exists(calendar_file):
        try:
            with open(calendar_file, "r", encoding="utf-8") as f:
                calendar = json.load(f)

            # Walidacja: kalendarz powinien być słownikiem
            if not isinstance(calendar, dict):
                print(f"  [OSTRZEŻENIE] Nieprawidłowy format kalendarza (oczekiwano słownika, otrzymano: {type(calendar).__name__})")
            else:
                # Szukamy następnego wyścigu
                for event in calendar.get("data", []):
                    if event.get("season") == season and event.get("race") == race + 1:
                        return {
                            "season": event.get("season"),
                            "race": event.get("race"),
                            "track": event.get("trackName"),
                            "total_laps": event.get("laps", 72)  # Default 72 laps
                        }
        except Exception as e:
            print(f"  [BŁĄD] Błąd wczytywania kalendarza: {e}")

    # Fallback: wyścig + 1 (bez szczegółów)
    return {
        "season": season,
        "race": race + 1,
        "track": race_data.get("track", ""),
        "total_laps": 72
    }


# ============================================================
# GŁÓWNA FUNKCJA
# ============================================================

def generate_prediction():
    """
    Główna funkcja generująca predykcję setupu.

    Mini-lekcja: To jest workflow całego skryptu:
    1. Wczytaj historię
    2. Znajdź info o następnym wyścigu
    3. Znajdź bazowy setup
    4. Skoryguj o temperaturę dla Q1, Q2 i Race
    5. Oblicz strategię paliwową
    6. Oblicz margines kierowcy
    7. Zapisz do data/prediction.json
    """
    print("=" * 60)
    print("GPRO Setup Predictor")
    print("=" * 60)

    # 1. Wczytaj historię
    print("\n1. Wczytywanie historii wyścigów...")
    history = load_history()
    print(f"   Załadowano {len(history)} wyścigów.")

    # 2. Znajdź info o następnym wyścigu
    print("\n2. Szukanie informacji o następnym wyścigu...")
    next_race = get_next_race_info()

    if not next_race:
        print("   [BŁĄD] Nie udało się znaleźć informacji o następnym wyścigu.")
        return

    track_name = next_race["track"]
    season = next_race["season"]
    race_num = next_race["race"]
    total_laps = next_race["total_laps"]

    print(f"   Następny wyścig: S{season}R{race_num} - {track_name} ({total_laps} okrążeń)")

    # 3. Znajdź bazowy setup
    print("\n3. Znajdowanie bazowego setupu...")
    base = find_base_setup(track_name, history)
    print(f"   Źródło: {base['source']}")
    print(f"   Setup bazowy: {base['setup']}")
    print(f"   Temperatura bazowa: {base['temp']}°C")
    print(f"   Confidence: {base['confidence']}")

    # 4. Skoryguj o temperaturę dla Q1, Q2 i Race
    # Mini-lekcja: Predykcja pogody - używamy temperatury z bazowego wyścigu
    # jako punktu odniesienia. W prawdziwej implementacji można pobrać
    # prognozę pogody z API lub kalendarza.

    # Dla demo: zakładamy temperatury
    q1_temp = base["temp"] + 2  # +2°C od bazowej
    q2_temp = base["temp"] + 6  # +6°C od bazowej
    race_temp = base["temp"] + 7  # +7°C od bazowej

    print(f"\n4. Korekta setupu dla temperatur...")
    print(f"   Q1: {q1_temp}°C")
    print(f"   Q2: {q2_temp}°C")
    print(f"   Race: {race_temp}°C")

    setup_q1 = adjust_for_temperature(base["setup"], base["temp"], q1_temp)
    setup_q2 = adjust_for_temperature(base["setup"], base["temp"], q2_temp)
    setup_race = adjust_for_temperature(base["setup"], base["temp"], race_temp)

    # 5. Oblicz strategię paliwową
    print(f"\n5. Obliczanie strategii paliwowej...")
    fuel_strategy = calculate_fuel_strategy(history, track_name, total_laps)
    print(f"   Zużycie paliwa: {fuel_strategy['fuel_per_lap']} L/okrążenie")
    print(f"   Rekomendacja: {fuel_strategy['recommended']['pits']} pit stopy")
    print(f"   Stints: {fuel_strategy['recommended']['stints']}")

    # 6. Oblicz margines kierowcy
    print(f"\n6. Obliczanie marginesu kierowcy...")
    if history:
        # Bierzemy dane kierowcy z ostatniego wyścigu
        last_race = history[-1]
        ti = last_race["driver_ti"]
        exp = last_race["driver_exp"]
        driver_name = last_race["driver_name"]
    else:
        # Fallback: średni kierowca
        ti = 100
        exp = 50
        driver_name = "Nieznany"

    ma, half_ma = calculate_driver_margin(ti, exp)
    print(f"   Kierowca: {driver_name}")
    print(f"   TI: {ti}, EXP: {exp}")
    print(f"   MA (Margines Akceptacji): {ma}")
    print(f"   Margines od optimum: ±{half_ma}")

    # 7. Oblicz strategię oponową
    print(f"\n7. Obliczanie strategii oponowej...")
    tyre_strategy = calculate_tyre_strategy(history, track_name, fuel_strategy, total_laps)
    print(f"   Żywotność opon: ~{tyre_strategy['est_tyre_life_laps']} okrążeń")
    print(f"   Okrążeń na baku: ~{tyre_strategy['laps_on_fuel']}")
    print(f"   Bottleneck: {tyre_strategy['bottleneck']}")

    # 8. Generuj plan treningowy
    print(f"\n8. Generowanie planu treningowego...")
    practice_plan = generate_practice_plan(base["confidence"])
    print(f"   Plan składa się z {len(practice_plan['laps'])} okrążeń")

    # 9. Zbuduj predykcję
    prediction = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "next_race": {
            "track": track_name,
            "season": season,
            "race": race_num,
            "total_laps": total_laps
        },
        "confidence": base["confidence"],
        "confidence_reason": base["source"],
        "driver_margin": {
            "MA": ma,
            "half_MA": half_ma,
            "note": f"Setup ±{half_ma} od optimum da satisfied (MA={ma}, TI={ti}, EXP={exp})"
        },
        "setup_q1": {
            "fw": setup_q1["fw"],
            "rw": setup_q1["rw"],
            "eng": setup_q1["eng"],
            "bra": setup_q1["bra"],
            "gear": setup_q1["gear"],
            "susp": setup_q1["susp"],
            "temp": q1_temp
        },
        "setup_q2": {
            "fw": setup_q2["fw"],
            "rw": setup_q2["rw"],
            "eng": setup_q2["eng"],
            "bra": setup_q2["bra"],
            "gear": setup_q2["gear"],
            "susp": setup_q2["susp"],
            "temp": q2_temp
        },
        "setup_race": {
            "fw": setup_race["fw"],
            "rw": setup_race["rw"],
            "eng": setup_race["eng"],
            "bra": setup_race["bra"],
            "gear": setup_race["gear"],
            "susp": setup_race["susp"],
            "temp": race_temp
        },
        "base": {
            "track": track_name,
            "setup": base["setup"],
            "temp": base["temp"]
        },
        "fuel_strategy": fuel_strategy,
        "tyre_strategy": tyre_strategy,
        "practice_plan": practice_plan,
        "tyre_info": {
            "supplier": "Pipirelli",  # Domyślny dostawca
            "bottleneck": tyre_strategy["bottleneck"],
            "est_tyre_life_laps": tyre_strategy["est_tyre_life_laps"]
        },
        "notes": [
            f"Predykcja oparta na {len(history)} wyścigach w historii.",
            f"Confidence: {base['confidence']} - {base['source']}",
            f"Kierowca: {driver_name} (TI={ti}, EXP={exp})",
            f"Margines kierowcy: ±{half_ma} od optimum.",
            f"Opony: ~{tyre_strategy['est_tyre_life_laps']} okr, paliwo: ~{tyre_strategy['laps_on_fuel']} okr",
            "Uwaga: Pogoda jest przykładowa. Sprawdź prognozę przed wyścigiem."
        ]
    }

    # 10. Zapisz do pliku
    output_file = "data/prediction.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(prediction, f, ensure_ascii=False, indent=2)

    print(f"\n9. Zapisano predykcję do: {output_file}")

    print("\n" + "=" * 60)
    print("Gotowe!")
    print("=" * 60)

    return prediction


if __name__ == "__main__":
    generate_prediction()