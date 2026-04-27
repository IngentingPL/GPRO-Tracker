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
import html
from datetime import datetime

CURRENT_CONTEXT_FILE = "data/current_context.json"


# ============================================================
# MAPOWANIE KOMENTARZY KIEROWCY -> KOREKTY SETUPU
# ============================================================

# Mini-lekcja: Komentarze kierowcy to klucz do znalezienia optimum setupu.
# Na podstawie słów kluczowych w komentarzu korygujemy konkretne parametry.
# Jeden komentarz może sugerować zmianę kilku parametrów.

COMMENT_KEYWORDS = {
    # Wings - docisk
    "grip": {"fw": +20, "rw": +20},           # Brak przyczepności = więcej docisku
    "unstable": {"fw": +30, "rw": +30},       # Niestały = więcej docisku
    "understeer": {"fw": +15},                # Understeer = więcej docisku z przodu
    "oversteer": {"rw": +15},                 # Oversteer = więcej docisku z tyłu
    "understeering": {"fw": +15},
    "oversteering": {"rw": +15},
    "too much front downforce": {"fw": -20},  # Za dużo docisku = zmniejsz
    "too much rear downforce": {"rw": -20},
    "missing grip": {"fw": +20, "rw": +20},
    
    # Engine - moc
    "engine power": {"eng": +20},             # Za mało mocy = zwiększ
    "engine feels weak": {"eng": +25},
    "not enough engine": {"eng": +20},
    "engine too strong": {"eng": -20},        # Za dużo mocy = zmniejsz
    "engine powerful": {"eng": -15},
    "engine feel": {"eng": +15},              # Ogólne odczucie mocy
    
    # Suspension - zawieszenie
    "rigid": {"susp": -20},                   # Za sztywne = zmniejsz
    "too rigid": {"susp": -25},
    "too soft": {"susp": +20},                # Za miękkie = zwiększ
    "soft": {"susp": +15},
    "bounces": {"susp": -30},                # Podskakuje = dużo mniej sztywne
    "suspension": {"susp": +10},             # Ogólne uwagi o zawieszeniu
    
    # Brakes - hamulce
    "brakes": {"bra": +15},                   # Problemy z hamulcami = więcej
    "not effective": {"bra": +20},            # Słabe hamowanie = więcej
    "locking": {"bra": -20},                   # Blokuje się = mniej
    "brake pressure": {"bra": -15},
    "braking": {"bra": +10},
    
    # Gear - przełożenie
    "gear": {"gear": +10},                    # Ogólne uwagi o przełożeniu
    "top speed": {"gear": +15},               # Brak prędkości max = wyższe przełożenie
    "acceleration": {"gear": -15},            # Słabe przyspieszenie = niższe przełożenie
    "ratio": {"gear": +10},
    
    # Satisfied - zadowolony
    "satisfied": {},                           # Brak zmian
    "happy": {},
    "perfect": {},
    "happy with the setup": {},
}

# Słowa kluczowe dla "satisfied" - najczęstszefrazy oznaczające zgodę
SATISFIED_KEYWORDS = ["satisfied", "happy", "perfect setup", "all good", "nothing to change"]


def interpret_driver_comment(comment):
    """
    Interpretuje komentarz kierowcy i zwraca słownik z proponowanymi zmianami.
    
    Mini-lekcja: W GPRO kierowca mówi po angielsku, np.:
    - "Wings: I am missing a bit of grip in the curves" (potrzeba więcej docisku)
    - "Engine: I feel that I do not have enough engine power in the straights" (więcej ENG)
    - "Suspension: The car is too rigid" (mniej SUSP)
    - "I am satisfied with the setup of the car" (nic nie zmieniaj)
    
    Funkcja szuka słów kluczowych i sumuje proponowane zmiany.
    """
    if not comment:
        return {}
    
    # Normalizuj komentarz (małe litery, usuń polskie znaki)
    normalized = comment.lower()
    # Obsłuż polskie znaki w komentarzach z API (choć API zwraca po angielsku)
    normalized = normalized.replace("ć", "c").replace("ę", "e").replace("ł", "l")
    normalized = normalized.replace("ś", "s").replace("ą", "a").replace("ó", "o")
    normalized = normalized.replace("ź", "z").replace("ż", "z")
    
    # Sprawdź czy kierowca jest zadowolony (najpierw - to ma najwyższy priorytet)
    for keyword in SATISFIED_KEYWORDS:
        if keyword in normalized:
            return {}  # Brak zmian - setup jest OK
    
    # Szukaj słów kluczowych i sumuj korekty
    corrections = {}
    
    for keyword, changes in COMMENT_KEYWORDS.items():
        if keyword in normalized:
            for setting, change in changes.items():
                corrections[setting] = corrections.get(setting, 0) + change
    
    return corrections


def adjust_for_driver_comment(base_setup, comment, confidence="medium"):
    """
    Korektuje setup na podstawie komentarza kierowcy.
    
    Args:
        base_setup: Bazowy setup (słownik z fw, rw, eng, bra, gear, susp)
        comment: Komentarz kierowcy (np. "Wings: I am missing a bit of grip...")
        confidence: Poziom pewności - wpływa na wielkość korekty
    
    Returns:
        Skorygowany setup (słownik)
    """
    corrections = interpret_driver_comment(comment)
    
    if not corrections:
        return base_setup.copy()  # Brak zmian
    
    # Wielkość korekty wg poziomu pewności
    # Niedoświadczony kierowca = mniejsze kroki (ostrożniej)
    confidence_multiplier = {
        "high": 1.0,      # Doświadczony kierowca - pełne korekty
        "medium": 0.8,   # Średni - 80% korekty
        "low": 0.5,      # Niedoświadczony - 50% korekty (ostrożniej)
    }
    
    multiplier = confidence_multiplier.get(confidence, 0.7)
    
    adjusted = base_setup.copy()
    
    for setting, change in corrections.items():
        if setting in adjusted:
            # Zaokrąglamy do liczb całkowitych
            new_value = int(adjusted[setting] + change * multiplier)
            # Ograniczamy do zakresu 0-999
            adjusted[setting] = max(0, min(999, new_value))
    
    return adjusted


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

FUEL_RATES = {
    "very_low": 1.45,
    "low": 1.30,
    "medium": 1.25,
    "high": 1.20,
    "very_high": 1.13
}

# Mapowanie nazw opon (internal -> display)
TYRE_NAMES = {
    "extra_soft": "Extra Soft",
    "soft": "Soft",
    "medium": "Medium",
    "hard": "Hard",
    "rain": "Rain"
}

TYRES_ORDER = ["extra_soft", "soft", "medium", "hard"]

# Bazowa żywotność opon (okrążenia przy 20°C, średnie zużycie toru)
TYRE_LIFE_BASE = {
    "extra_soft": 18,
    "soft": 25,
    "medium": 35,
    "hard": 50,
    "rain": 45
}

def select_best_compound(track_data, supplier_data, driver_data, race_temp, weather="dry"):
    """
    Wybiera optymalną mieszankę opon na podstawie danych toru, dostawcy i temperatury.
    Logika inspirowana GPRO Analyzer.
    """
    if weather == "wet":
        return "rain"

    # 1. Punkt wyjścia na podstawie temperatury
    # Każda mieszanka ma swój "idealny" zakres
    if race_temp < 13:
        compound = "extra_soft"
    elif race_temp < 23:
        compound = "soft"
    elif race_temp < 33:
        compound = "medium"
    else:
        compound = "hard"

    # 2. Korekta o zużycie toru
    track_wear = track_data.get("tyreWear", "Średnie").lower()

    # Przesuwamy o jeden stopień w górę (twardsze) jeśli tor mocno żre opony
    # lub w dół (miększe) jeśli tor jest łaskawy
    idx = TYRES_ORDER.index(compound)

    if "bardzo wysokie" in track_wear or "very high" in track_wear:
        idx = min(len(TYRES_ORDER) - 1, idx + 1)
    elif "wysokie" in track_wear or "high" in track_wear:
        # Jeśli temperatura jest na granicy, przesuń
        if (race_temp % 10) > 5:
            idx = min(len(TYRES_ORDER) - 1, idx + 1)
    elif "bardzo niskie" in track_wear or "very low" in track_wear:
        idx = max(0, idx - 1)
    elif "niskie" in track_wear or "low" in track_wear:
        if (race_temp % 10) < 5:
            idx = max(0, idx - 1)

    compound = TYRES_ORDER[idx]

    # 3. Korekta o agresywność kierowcy
    aggr = int(driver_data.get("aggressiveness", 0))
    if aggr > 80:
        # Bardzo agresywny kierowca = szybciej niszczy opony, może warto twardsze
        if idx < len(TYRES_ORDER) - 1 and (race_temp % 10) > 3:
            idx = min(len(TYRES_ORDER) - 1, idx + 1)

    return TYRES_ORDER[idx]

def load_track_data(track_id):
    """Wczytuje szczegółowe dane toru z cache."""
    if not track_id:
        return {}

    filepath = f"data/tracks/{track_id}.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
                return content.get("data", {})
        except:
            pass
    return {}


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
# WYKRYWANIE WYKONANYCH SESJI (DLA PROGRESJI WYŚCIGU)
# ============================================================

def get_completed_sessions_from_race(race_data):
    """
    Wykrywa które sesje zostały wykonane w danym wyścigu.
    Zwraca słownik: {session_name: {setup, feedback}}
    
    Mini-lekcja: Sesje w GPRO (polski): Trening 1-8, Kw1, Kw2, Wyścig
    """
    if not race_data:
        return {}
    
    setups = race_data.get("setups", [])
    completed = {}
    
    for setup in setups:
        session = setup.get("session", "")
        if not session:
            continue
            
        # Dekoduj encje HTML (np. Wy&#347;cig -> Wyścig)
        import html
        session = html.unescape(session)
        
        # Mapuj polskie nazwy na nasze klucze
        session_map = {
            "Trening 1": "P1",
            "Trening 2": "P2", 
            "Trening 3": "P3",
            "Trening 4": "P4",
            "Trening 5": "P5",
            "Trening 6": "P6",
            "Trening 7": "P7",
            "Trening 8": "P8",
            "Kw1": "Q1",
            "Kw2": "Q2",
            "Wyścig": "RACE"
        }
        
        key = session_map.get(session)
        if key:
            completed[key] = {
                "setup": {
                    "fw": normalize_int(setup.get("fw")),
                    "rw": normalize_int(setup.get("rw")),
                    "eng": normalize_int(setup.get("eng")),
                    "bra": normalize_int(setup.get("bra")),
                    "gear": normalize_int(setup.get("gear")),
                    "susp": normalize_int(setup.get("susp"))
                },
                "feedback": setup.get("feedback", ""),
                "tyres": setup.get("tyres", "")
            }
    
    return completed


def find_next_step(completed_sessions, sequence_order):
    """
    Znajduje następny niewykonany krok w kolejności P1->P2->...->RACE.
    
    Args:
        completed_sessions: dict z wykonanymi sesjami
        sequence_order: lista poprawna kroków ['P1', 'P2', ..., 'Q1', 'Q2', 'RACE']
    
    Returns:
        Nazwa następnego kroku (np. 'P1', 'Q1', 'RACE') lub None
    """
    for step in sequence_order:
        if step not in completed_sessions:
            return step
    
    # Wszystkie wykonane - wyścig zakończony
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

def calculate_fuel_strategy(history, track_name, total_laps, est_tyre_life_laps=None):
    """
    Oblicza strategię paliwową na podstawie historii pit stopów i żywotności opon.

    Mini-lekcja: Celem jest minimalizacja liczby pit stopów
    przy zachowaniu bezpiecznego zapasu paliwa i nie przekraczaniu zużycia opon.
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

        # Sprawdzamy czy opony wytrzymają taki stint
        tyres_ok = est_tyre_life_laps is None or laps_per_stint <= est_tyre_life_laps

        if fuel_per_stint <= 180 and tyres_ok:  # Limit baku i opon
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


def calculate_tyre_strategy(history, track_name, fuel_strategy, total_laps, selected_compound="medium", track_data=None):
    """
    Oblicza strategię oponową i bottleneck.
    """
    # 1. Próba estymacji z historii (najdokładniejsza)
    track_history = [h for h in history if h["track_name"] == track_name]
    tyre_life_estimates = []

    if track_history:
        for h in track_history:
            pits = h.get("pits", [])
            if pits and pits[0].get("tyre_condition") is not None and pits[0].get("lap"):
                wear_per_lap = (100 - pits[0]["tyre_condition"]) / pits[0]["lap"]
                if wear_per_lap > 0:
                    tyre_life_estimates.append(math.floor(90 / wear_per_lap))

    if tyre_life_estimates:
        est_tyre_life_laps = round(sum(tyre_life_estimates) / len(tyre_life_estimates))
        source = "historia toru"
    else:
        # 2. Jeśli brak historii toru, używamy bazowej żywotności wybranego compoundu
        # i korygujemy o zużycie toru
        base_life = TYRE_LIFE_BASE.get(selected_compound.lower().replace(" ", "_"), 30)

        # Korekta o zużycie toru
        track_wear = (track_data or {}).get("tyreWear", "Średnie").lower()
        wear_multiplier = 1.0
        if "bardzo wysokie" in track_wear or "very high" in track_wear: wear_multiplier = 0.6
        elif "wysokie" in track_wear or "high" in track_wear: wear_multiplier = 0.8
        elif "bardzo niskie" in track_wear or "very low" in track_wear: wear_multiplier = 1.4
        elif "niskie" in track_wear or "low" in track_wear: wear_multiplier = 1.2

        est_tyre_life_laps = round(base_life * wear_multiplier)
        source = f"baza ({selected_compound}) x {wear_multiplier:.1f} (zużycie toru)"

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




# ============================================================
# INFO O NASTĘPNYM WYŚCIGU
# ============================================================

def normalize_int(value):
    """Konwertuje wartość do int jeśli to możliwe. Obsługuje stringi i None."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        import re
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else None


def load_current_context():
    """Wczytuje aktywny kontekst sezonu/wyścigu zapisany przez fetcher."""
    if not os.path.exists(CURRENT_CONTEXT_FILE):
        return None

    try:
        with open(CURRENT_CONTEXT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [OSTRZEŻENIE] Nie udało się wczytać {CURRENT_CONTEXT_FILE}: {e}")
        return None

    if not isinstance(data, dict):
        return None

    season = normalize_int(data.get("season"))
    race = normalize_int(data.get("race"))
    track = data.get("track")
    if season is None or race is None or not track:
        return None

    return {
        "season": season,
        "race": race,
        "track": track,
        "track_id": data.get("track_id"),
        "total_laps": normalize_int(data.get("total_laps")) or 72
    }


def load_active_race_data(season, race):
    """Wczytuje dane obecnego wyścigu jeśli już istnieją (np. po treningach)."""
    filepath = f"data/races/S{season}R{race}.json"
    if not os.path.exists(filepath):
        # Sprawdź też latest.json czy to ten sam wyścig
        latest_path = "data/races/latest.json"
        if os.path.exists(latest_path):
            try:
                with open(latest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rd = data.get("race_data", {})
                    if normalize_int(rd.get("season")) == season and normalize_int(rd.get("race")) == race:
                        return data
            except:
                pass
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [OSTRZEŻENIE] Nie udało się wczytać aktywnego wyścigu: {e}")
        return None


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
                # Pobierz dane wyścigów - mogą być jako lista lub słownik
                calendar_data = calendar.get("data", [])

                # Jeśli data to słownik, spróbujmy znaleźć listę
                if isinstance(calendar_data, dict):
                    print(f"  [OSTRZEŻENIE] Kalendarz.data jest słownikiem zamiast listą. Próbuję znaleźć listę wyścigów...")
                    for key in ["races", "calendar", "events", "schedule", "items"]:
                        if key in calendar_data and isinstance(calendar_data[key], list):
                            calendar_data = calendar_data[key]
                            print(f"  Znaleziono listę w kluczu '{key}'")
                            break
                    else:
                        # Nie znaleziono listy - użyjemy fallback
                        print(f"  [OSTRZEŻENIE] Nie znaleziono listy wyścigów w kalendarzu. Używam fallback.")
                        calendar_data = []

                if isinstance(calendar_data, list):
                    # Szukamy następnego wyścigu (eventType="R" i idx = race + 1)
                    current_race_idx = race
                    for event in calendar_data:
                        if event.get("eventType") == "R":
                            event_idx = int(event.get("idx", 0))
                            if event_idx == current_race_idx + 1:
                                return {
                                    "season": season,
                                    "race": event_idx,
                                    "track": event.get("trackName"),
                                    "total_laps": 72  # Default, GPRO standard
                                }
                    # Jeśli nie znaleziono następnego, szukamy obecnego (isCurrentRace=1)
                    for event in calendar_data:
                        if event.get("isCurrentRace") == 1:
                            event_idx = int(event.get("idx", 0))
                            # Następny to idx + 1
                            for next_event in calendar_data:
                                if next_event.get("eventType") == "R" and int(next_event.get("idx", 0)) == event_idx + 1:
                                    return {
                                        "season": season,
                                        "race": int(next_event.get("idx", 0)),
                                        "track": next_event.get("trackName"),
                                        "total_laps": 72
                                    }
                else:
                    print(f"  [OSTRZEŻENIE] Kalendarz.data nie jest listą ani słownikiem (typ: {type(calendar_data).__name__})")
        except Exception as e:
            print(f"  [BŁĄD] Błąd wczytywania kalendarza: {e}")

    # Fallback: jeśli brak kalendarza, nie zgadujemy toru
    print(f"  [OSTRZEŻENIE] Brak danych kalendarza. Nie można określić następnego toru.")
    return None


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
    # Mini-lekcja: Najpierw sprawdzamy current_context.json - plik zapisany przez
    # fetcher który zawsze ma aktualny sezon z API (Office + Calendar).
    # Dopiero jeśli go brak, używamy starej logiki kalendarza jako fallback.
    print("\n2. Szukanie informacji o następnym wyścigu...")
    next_race = load_current_context()
    if next_race:
        print(f"   Źródło: current_context.json (S{next_race['season']}R{next_race['race']})")
    else:
        next_race = get_next_race_info()
        print(f"   Źródło: fallback z kalendarza")

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

    # Setup for Practice (same as base, with small temp adjustment)
    practice_temp = base["temp"] + 1
    setup_practice = adjust_for_temperature(base["setup"], base["temp"], practice_temp)
    setup_practice["temp"] = practice_temp

    # 5. Oblicz wstępną strategię paliwową
    print(f"\n5. Obliczanie wstępnej strategii paliwowej...")
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

    # 7. Oblicz strategię oponową (tymczasowa, zostanie zaktualizowana po wyborze opon)
    print(f"\n7. Obliczanie wstępnej strategii oponowej...")
    tyre_strategy = calculate_tyre_strategy(history, track_name, fuel_strategy, total_laps)
    print(f"   Żywotność opon: ~{tyre_strategy['est_tyre_life_laps']} okrążeń")
    print(f"   Okrążeń na baku: ~{tyre_strategy['laps_on_fuel']}")
    print(f"   Bottleneck: {tyre_strategy['bottleneck']}")

    # 8. Analiza obecnej progresji wyścigu
    print(f"\n8. Analiza obecnej progresji wyścigu...")
    active_data = load_active_race_data(season, race_num)
    completed_setups = []
    if active_data:
        completed_setups = active_data.get("race_data", {}).get("setups", [])
        print(f"   Znaleziono {len(completed_setups)} ukończonych sesji setupu.")

    # 9. Wybór opon (NOWA LOGIKA: takie same dla wszystkich sesji)
    print(f"\n9. Wybieranie opon na wyścig...")

    # Pobieramy dane pomocnicze z ostatniego wyścigu
    latest_race_raw = {}
    pattern = "data/races/latest.json"
    if os.path.exists(pattern):
        with open(pattern, "r", encoding="utf-8") as f:
            latest_race_raw = json.load(f)

    track_id = next_race.get("track_id")
    track_data = load_track_data(track_id)
    supplier_data = latest_race_raw.get("race_data", {}).get("tyre_supplier", {})
    driver_data = latest_race_raw.get("race_data", {}).get("driver", {})

    selected_compound = select_best_compound(track_data, supplier_data, driver_data, race_temp)
    selected_compound_name = TYRE_NAMES.get(selected_compound, selected_compound)

    print(f"   Wybrana mieszanka: {selected_compound_name} (dla wszystkich sesji)")

    # 10. Aktualizacja strategii oponowej o wybrany compound
    print(f"   Aktualizacja strategii oponowej dla {selected_compound_name}...")
    tyre_strategy = calculate_tyre_strategy(history, track_name, fuel_strategy, total_laps, selected_compound, track_data)

    # 11. Aktualizacja strategii paliwowej o żywotność opon
    print(f"   Aktualizacja strategii paliwowej o żywotność opon (~{tyre_strategy['est_tyre_life_laps']} okr)...")
    fuel_strategy = calculate_fuel_strategy(history, track_name, total_laps, tyre_strategy['est_tyre_life_laps'])

    # 12. Budowanie sekwencji sesji - TYLOKO jeden następny krok
    # ==================================================
    # Logika: P1->P2->P3->P4->P5->P6->P7->P8->Q1->Q2->Race
    # Znajdujemy pierwszą niewykonaną sesję w kolejności
    print(f"\n12. Budowanie sekwencji sesji...")

    # PobierzCompleted sesje z najnowszego wyścigu (jeśli istnieją)
    completed_sessions = {}
    if active_data:
        completed_sessions = get_completed_sessions_from_race(active_data.get("race_data", {}))
        print(f"   Znaleziono {len(completed_sessions)} ukończonych sesji z aktualnego wyścigu")

    # Kolejność sesji w wyścigu
    SESSION_ORDER = [
        "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
        "Q1", "Q2", "RACE"
    ]

    # Mapowanie naszych kluczy na polskie nazwy API GPRO
    SESSION_TO_API = {
        "P1": "Trening 1", "P2": "Trening 2", "P3": "Trening 3",
        "P4": "Trening 4", "P5": "Trening 5", "P6": "Trening 6",
        "P7": "Trening 7", "P8": "Trening 8",
        "Q1": "Kw1", "Q2": "Kw2", "RACE": "Wyścig"
    }

    # Znajdź następny krok
    next_step_name = find_next_step(completed_sessions, SESSION_ORDER)
    print(f"   Następny krok: {next_step_name}")

    # Inicjalizuj bazowy setup dla progression
    progression_setup = setup_practice.copy()
    last_feedback = ""
    correction_note = ""

    # Zbuduj pełną sekwencję (dla archiwum), ale zaznacz tylko jeden jako is_next
    sequence = []

    # Zbuduj mapęCompleted sesji z API (dla odczytu danych)
    api_session_map = {}
    if completed_setups:
        for s in completed_setups:
            raw_session = s.get("session", "")
            decoded_session = html.unescape(raw_session)
            api_session_map[decoded_session] = s

    # Użyj poprzedniego wyścigu do pobrania komentarza (jeśli brak w aktualnym)
    previous_race_comment = None
    if not completed_sessions and len(history) > 0:
        # Pobierz komentarz z poprzedniego wyścigu jako hint dla setupu
        prev = history[-1]
        # Szukamy setupu z komentarzem
        # (handled by adjust_for_driver_comment)

    # Generuj wszystkie kroki
    for step_key in SESSION_ORDER:
        is_completed = step_key in completed_sessions
        is_next = (step_key == next_step_name)

        # Konwertuj na nazwę wyświetlaną
        if step_key.startswith("P"):
            display_id = f"PRAKTYKA {step_key[1]}" if len(step_key) == 2 else "PRAKTYKA"
            display_type = "practice"
        elif step_key == "Q1":
            display_id = "KWALIFIKACJE 1"
            display_type = "q1"
        elif step_key == "Q2":
            display_id = "KWALIFIKACJE 2"
            display_type = "q2"
        else:
            display_id = "WYŚCIG"
            display_type = "race"

        # Pobierz setup zCompleted sesji (jeśli jest)
        completed_data = completed_sessions.get(step_key) or api_session_map.get(SESSION_TO_API.get(step_key))

        step_data = {
            "id": display_id,
            "type": display_type,
            "completed": is_completed,
            "is_next": is_next,
            "setup": None,
            "feedback": "",
            "tyres": selected_compound_name,
            "temp": practice_temp if step_key.startswith("P") else (q1_temp if step_key == "Q1" else (q2_temp if step_key == "Q2" else race_temp)),
            "note": "",
            "session_key": step_key
        }

        if is_completed and completed_data:
            # Dane z Completed sesji
            s = completed_data.get("setup", {})
            step_data["setup"] = s
            step_data["feedback"] = completed_data.get("feedback", "")
            step_data["note"] = "Ukończona sesja"

            # Zapamiętaj komentarz dla nastęnych korekcji
            if step_data["feedback"]:
                last_feedback = step_data["feedback"]
                correction_note = f"Setup skorygowany o: {step_data['feedback'][:80]}..."

        elif is_next:
            # TEN krok jest następnym - pokaż pełny setup
            step_data["setup"] = progression_setup.copy()
            step_data["note"] = correction_note if correction_note else "Sugerowany setup na podstawie poprzednich sesji"

            # Dla Race dodaj strategię paliwową
            if step_key == "RACE":
                step_data["fuel_strategy"] = fuel_strategy["recommended"]
        else:
            # Przyszłe kroki - bez setupu
            step_data["setup"] = None

        # Aktualizuj progression_setup na podstawie komentarza z tej sesji (dla następnego kroku)
        if is_completed and step_data["feedback"]:
            progression_setup = adjust_for_driver_comment(
                step_data["setup"] if step_data["setup"] else progression_setup,
                step_data["feedback"],
                base["confidence"]
            )

        sequence.append(step_data)

    # 13. Zbuduj predykcję
    prediction = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "next_race": {
            "track": track_name,
            "season": season,
            "race": race_num,
            "total_laps": total_laps,
            "track_id": track_id
        },
        "confidence": base["confidence"],
        "confidence_reason": base["source"],
        "driver_margin": {
            "MA": ma,
            "half_MA": half_ma,
            "note": f"Setup ±{half_ma} od optimum da satisfied (MA={ma}, TI={ti}, EXP={exp})"
        },
        "base": {
            "track": track_name,
            "setup": base["setup"],
            "temp": base["temp"]
        },
        "sequence": sequence,
        "fuel_strategy": fuel_strategy,
        "tyre_strategy": tyre_strategy,
        "tyre_info": {
            "supplier": "Pipirelli",
            "bottleneck": tyre_strategy["bottleneck"],
            "est_tyre_life_laps": tyre_strategy["est_tyre_life_laps"]
        },
        "notes": [
            f"Predykcja oparta na {len(history)} wyścigach w historii.",
            f"Pewność: {base['confidence']} - {base['source']}",
            f"Kierowca: {driver_name} (TI={ti}, EXP={exp})",
            f"Margines kierowcy: ±{half_ma} od optimum.",
            f"Opony: ~{tyre_strategy['est_tyre_life_laps']} okr, paliwo: ~{tyre_strategy['laps_on_fuel']} okr"
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