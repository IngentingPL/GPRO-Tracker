#!/usr/bin/env python3
"""
GPRO Dashboard Generator
=========================
Generuje statyczny dashboard HTML z osadzonymi danymi.
Czyta dane wyścigowe z data/races/ i predykcję z data/prediction.json.

Mini-lekcja: To jest generator stron statycznych.
Zamiast serwera backendowego, osadzamy dane bezpośrednio w HTML
jako zmienne JavaScript. Dzięki temu strona działa natychmiast
bez zapytań HTTP - idealne dla GitHub Pages.
"""

import json
import os
import glob
import re
from datetime import datetime


# ============================================================
# KONFIGURACJA
# ============================================================

# Folder na dane wyścigowe
DATA_DIR = "data/races"

# Plik z predykcją setupu
PREDICTION_FILE = "data/prediction.json"

# Plik kalendarza
CALENDAR_FILE = "data/calendar.json"

# Plik z aktywnym kontekstem sezonu/wyścigu
CURRENT_CONTEXT_FILE = "data/current_context.json"

# Plik wyjściowy
OUTPUT_FILE = "index.html"


# ============================================================
# WCZYTYWANIE DANYCH
# ============================================================

def load_race_data():
    """
    Wczytuje wszystkie pliki data/races/S*R*.json.

    Mini-lekcja: Pattern "data aggregation" - zbieramy dane
    z wielu źródeł do jednej struktury. Dzięki temu dashboard
    pokazuje historię wszystkich wyścigów w jednym miejscu.
    """
    race_data = []

    if not os.path.exists(DATA_DIR):
        print(f"[OSTRZEŻENIE] Folder {DATA_DIR} nie istnieje.")
        return race_data

    # Szukamy plików z wyścigami (S*R*.json)
    pattern = os.path.join(DATA_DIR, "S*R*.json")
    race_files = glob.glob(pattern)

    def sort_key(filepath):
        filename = os.path.basename(filepath)
        match = re.match(r"S(\d+)R(\d+)\.json$", filename)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0, filename)

    race_files = sorted(race_files, key=sort_key)

    print(f"  Znaleziono {len(race_files)} plików z wyścigami.")

    for filepath in race_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                race_data.append(data)
        except Exception as e:
            print(f"  [BŁĄD] Błąd wczytywania {filepath}: {e}")
            continue

    return race_data


def load_prediction():
    """
    Wczytuje dane predykcji z predictor.py.

    Mini-lekcja: Predykcja to rekomendacje setupu na podstawie
    historii. Jeśli plik nie istnieje, zwracamy None - dashboard
    pokaże fallback message.
    """
    if not os.path.exists(PREDICTION_FILE):
        print(f"  Plik {PREDICTION_FILE} nie istnieje.")
        return None

    try:
        with open(PREDICTION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [BŁĄD] Błąd wczytywania {PREDICTION_FILE}: {e}")
        return None


def load_calendar():
    """
    Wczytuje dane kalendarza.

    Mini-lekcja: Kalendarz zawiera listę torów w sezonie.
    Używamy go do pokazania informacji o następnym wyścigu.
    """
    if not os.path.exists(CALENDAR_FILE):
        print(f"  Plik {CALENDAR_FILE} nie istnieje.")
        return None

    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [BŁĄD] Błąd wczytywania {CALENDAR_FILE}: {e}")
        return None

def load_current_context():
    """
    Wczytuje aktywny kontekst sezonu/wyścigu zapisany przez fetcher.
    """
    if not os.path.exists(CURRENT_CONTEXT_FILE):
        print(f"  Plik {CURRENT_CONTEXT_FILE} nie istnieje.")
        return None

    try:
        with open(CURRENT_CONTEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [BŁĄD] Błąd wczytywania {CURRENT_CONTEXT_FILE}: {e}")
        return None


# ============================================================
# GENEROWANIE HTML
# ============================================================

def generate_html(race_data, prediction_data, calendar_data, current_context_data):
    """
    Generuje kompletny dashboard HTML z osadzonymi danymi.

    Mini-lekcja: Template stringi w Pythonie pozwalają łatwo
    budować HTML. Osadzamy dane JSON bezpośrednio jako zmienne
    JavaScript - to wzorzec "data embedding".
    """
    # Osadzamy dane jako zmienne JavaScript
    race_data_js = json.dumps(race_data, ensure_ascii=False)
    prediction_data_js = json.dumps(prediction_data, ensure_ascii=False) if prediction_data else "null"
    calendar_data_js = json.dumps(calendar_data, ensure_ascii=False) if calendar_data else "null"
    current_context_js = json.dumps(current_context_data, ensure_ascii=False) if current_context_data else "null"

    # Budujemy HTML
    html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPRO Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;600&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        /* ==========================================================
           LAMBORGHINI DESIGN SYSTEM
           Inspiracja: lamborghini.com — czarne powierzchnie, złoto,
           zero border-radius, uppercase typography.
           Mini-lekcja: CSS custom properties (--nazwa) pozwalają
           zdefiniować kolory raz i używać ich wszędzie.
           Zmiana jednej zmiennej zmienia kolor w całym dashboardzie.
           ========================================================== */
        :root {{
            /* Surfaces — darkness layering */
            --bg-primary: #000000;       /* Absolute Black */
            --bg-card: #181818;          /* Dark Iron */
            --bg-elevated: #202020;      /* Charcoal */
            --bg-tab-active: #FFC000;    /* Lamborghini Gold */

            /* Text */
            --text-primary: #FFFFFF;     /* Pure White */
            --text-secondary: #F5F5F5;   /* Smoke */
            --text-muted: #7D7D7D;       /* Ash */
            --text-gold: #FFC000;        /* Lamborghini Gold */

            /* Accent */
            --accent-gold: #FFC000;      /* Lamborghini Gold */
            --accent-gold-dark: #917300; /* Dark Gold */
            --accent-red: #ef4444;       /* Error/Loss Red */
            --accent-cyan: #29ABE2;      /* Cyan Pulse */

            /* Borders */
            --border-color: #202020;     /* Charcoal Border */

            /* Fonts */
            --font-display: 'Barlow Condensed', 'Barlow', sans-serif;
            --font-mono: 'Share Tech Mono', monospace;
        }}

        /* Reset and base styles */
        * {{ margin: 0; padding: 0; box-sizing: border-box; border-radius: 0 !important; }}

        body {{
            font-family: var(--font-display);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            letter-spacing: 0.02em;
            line-height: 1.5;
        }}

        /* ==========================================================
           HEADER — floats in darkness
           ========================================================== */
        .header {{
            padding: 2rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            background: var(--bg-primary);
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            line-height: 0.92;
        }}

        .header h1 span {{
            color: var(--accent-gold);
        }}

        .header-info {{
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

/* ==========================================================
            SUMMARY CARDS (Main Summary) — ujednolicony styl setup-card
            ========================================================== */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1px;
            padding: 1px;
            background: #202020;
            margin: 0;
            border-bottom: 1px solid #202020;
        }}

        .summary-card {{
            background: #000000;
            padding: 1.5rem 2rem;
            transition: background 0.3s;
            position: relative;
            overflow: hidden;
        }}

        .summary-card::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: transparent;
            transition: background 0.3s;
        }}

        .summary-card:hover {{
            background: #101010;
        }}

        .summary-card:hover::before {{
            background: #FFC000;
        }}

        .summary-card .label {{
            font-size: 0.65rem;
            color: #7D7D7D;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            margin-bottom: 0.5rem;
        }}

        .summary-card .value {{
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            line-height: 1;
            color: #FFC000;
        }}

        .summary-card .value-small {{
            font-family: var(--font-display);
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            line-height: 1;
            color: #FFC000;
        }}

        .summary-card .sub {{
            font-size: 0.75rem;
            color: #7D7D7D;
            margin-top: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        /* ==========================================================
           ZAKŁADKI (TABS) — złota aktywna linia
           Mini-lekcja: Zakładki działają bez JS dzięki atrybutom
           data-tab. JS tylko przełącza klasy CSS "active".
           ========================================================== */
        .tabs {{
            display: flex;
            gap: 0;
            padding: 0 2rem;
            border-bottom: 1px solid #202020;
            overflow-x: auto;
        }}

        .tab-btn {{
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 600;
            padding: 1.25rem 2rem;
            background: transparent;
            color: var(--text-muted);
            border: none;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
            white-space: nowrap;
            text-transform: uppercase;
            letter-spacing: 0.15em;
        }}

        .tab-btn:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }}

        .tab-btn.active {{
            color: var(--accent-gold);
            border-bottom-color: var(--accent-gold);
        }}

        .tab-content {{
            display: none;
            padding: 1.5rem 2rem;
        }}

        .tab-content.active {{
            display: block;
        }}

        .tab-content.active .data-grid {{
            display: grid !important;
        }}

        /* ==========================================================
           TABELE — ostre krawędzie, złote akcenty
           ========================================================== */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
        }}

        .data-table th {{
            text-align: left;
            padding: 1rem 1.5rem;
            color: var(--text-muted);
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            background: var(--bg-primary);
        }}

        .data-table td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #181818;
            font-family: var(--font-mono);
            font-size: 0.8rem;
        }}

        .data-table tr:hover td {{
            background: #181818;
        }}

        /* Kolorowanie pozycji */
        .pos-1 {{ color: #FFC000; font-weight: 700; }}
        .pos-2 {{ color: #FFCE3E; }}
        .pos-3 {{ color: #7D7D7D; }}

        /* Kolorowanie wartości */
        .val-positive {{ color: #FFC000; }}
        .val-negative {{ color: var(--accent-red); }}

        /* ==========================================================
           SETUP GRID (per tor)
           ========================================================== */
        .setup-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 24px;
        }}

        .setup-card {{
            background: #000000;
            padding: 1.5rem;
        }}

        .setup-card h3 {{
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #FFFFFF;
        }}

        .setup-values {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1px;
            background: #202020;
        }}

        .setup-item {{
            text-align: center;
            padding: 0.75rem 0.5rem;
            background: #181818;
        }}

        .setup-item .setup-label {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.35rem;
        }}

        .setup-item .setup-val {{
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1.1rem;
            color: #FFC000;
        }}

        .setup-meta {{
            margin-top: 0.75rem;
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

/* ==========================================================
            SEKCJA KIEROWCY — ujednolicony styl setup-card
            ========================================================== */
        .driver-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1px;
            background: #202020;
        }}

        .stat-item {{
            background: #000000;
            padding: 1rem;
            text-align: center;
        }}

        .stat-item .stat-name {{
            font-size: 0.6rem;
            color: #7D7D7D;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.5rem;
        }}

        .stat-item .stat-value {{
            font-family: var(--font-mono);
            font-size: 1.5rem;
            font-weight: 700;
            color: #FFC000;
        }}

        /* Kolory dla statystyk kierowcy */
        .stat-good {{ color: #FFC000; }}
        .stat-ok {{ color: #FFCE3E; }}
        .stat-bad {{ color: var(--accent-red); }}

/* ==========================================================
            SEKCJA FINANSÓW — ujednolicony styl setup-card
            ========================================================== */
        .finance-bar {{
            display: flex;
            gap: 1px;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            background: #202020;
        }}

        .finance-card {{
            background: #000000;
            padding: 1.5rem;
        }}
            flex: 1;
            min-width: 180px;
        }}

        /* ==========================================================
           PUSTA STRONA (brak danych)
           ========================================================== */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }}

        .empty-state h2 {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #FFFFFF;
        }}

        .empty-state code {{
            background: #202020;
            padding: 0.25rem 0.75rem;
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: #FFC000;
        }}

        /* ==========================================================
           HERO SECTION - Ujednolicony nagłówek dla wszystkich zakładek
           ========================================================== */
        .hero-section {{
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
            padding: 3rem 0;
            margin-bottom: 2rem;
            text-align: left;
        }}

        .hero-section .hero-subtitle {{
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.3em;
            margin-bottom: 0.5rem;
            display: block;
        }}

        .hero-section h2 {{
            font-size: 4rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            line-height: 0.9;
            margin-bottom: 1rem;
        }}

        .hero-section .hero-meta {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }}

        .hero-section .hero-meta span {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .hero-section .hero-badge {{
            display: inline-block;
            background: var(--accent-gold);
            color: #000;
            padding: 0.25rem 0.75rem;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            margin-top: 1rem;
            text-transform: uppercase;
        }}

        .rec-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1px;
            background: #202020;
            margin-bottom: 1px;
        }}

        .rec-card {{
            background: #000000;
            padding: 1.5rem;
        }}

        .rec-card h3 {{
            font-size: 0.65rem;
            font-weight: 700;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .rec-card .rec-value {{
            font-family: var(--font-mono);
            font-size: 1.1rem;
            font-weight: 700;
            color: #FFC000;
        }}

        .rec-card .rec-note {{
            font-size: 0.75rem;
            color: #7D7D7D;
            margin-top: 0.75rem;
        }}

        .rec-card .rec-warn {{
            font-size: 0.75rem;
            color: #FFC000;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .rec-card .rec-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            font-size: 0.82rem;
            border-bottom: 1px solid #181818;
        }}

        .rec-card .rec-row .rec-label {{
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.65rem;
            letter-spacing: 0.08em;
        }}

        .rec-disclaimer {{
            margin-top: 1.5rem;
            padding: 1rem 1.25rem;
            background: rgba(255, 192, 0, 0.06);
            border-left: 2px solid #FFC000;
            font-size: 0.75rem;
            color: #FFC000;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        /* ==========================================================
           Confidence Bar — złoto dla high, ciemniejsze dla low
           Mini-lekcja: Wizualny wskaźnik pewności predykcji.
           ========================================================== */
        .confidence-bar {{
            height: 2px;
            background: #202020;
            overflow: hidden;
            margin: 0.75rem 0;
        }}

        .confidence-fill {{
            height: 100%;
            transition: width 0.3s;
        }}

        .confidence-fill.high {{
            background: #FFC000;
            width: 100%;
        }}

        .confidence-fill.medium {{
            background: #FFCE3E;
            width: 66%;
        }}

        .confidence-fill.low {{
            background: #917300;
            width: 33%;
        }}

        .confidence-fill.very_low {{
            background: var(--accent-red);
            width: 10%;
        }}

        /* Session Card — złota linia po lewej */
        .session-card {{
            background: #000000;
            border: 1px solid #202020;
            padding: 1.25rem;
            margin-bottom: 1px;
        }}
        .session-card.practice {{ border-left: 3px solid #7D7D7D; }}
        .session-card.q1 {{ border-left: 3px solid #FFCE3E; }}
        .session-card.q2 {{ border-left: 3px solid #FFC000; }}
        .session-card.race {{ border-left: 3px solid #FFC000; }}

        .session-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .session-header h4 {{
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.14em;
        }}

        .session-badge {{
            font-size: 0.6rem;
            padding: 0.2rem 0.5rem;
            background: #202020;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .session-meta {{
            font-size: 0.65rem;
            color: var(--text-muted);
            display: flex;
            gap: 1rem;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .session-meta span {{ display: flex; align-items: center; gap: 0.25rem; }}

        .session-setup {{
            display: flex;
            gap: 1px;
            flex-wrap: wrap;
            background: #202020;
        }}

        .session-setup .setup-part {{
            background: #181818;
            padding: 0.4rem 0.6rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .session-setup .setup-part .label {{
            color: var(--text-muted);
            font-size: 0.55rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .session-setup .setup-part .value {{
            color: #FFC000;
            font-weight: 600;
        }}

        .session-note {{
            margin-top: 0.5rem;
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .fuel-stint-bar {{
            display: flex;
            align-items: center;
            gap: 0;
            margin-top: 0.75rem;
            flex-wrap: wrap;
            background: #202020;
        }}

        .fuel-stint-bar .stint {{
            background: #181818;
            padding: 0.3rem 0.6rem;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            border-right: 1px solid #202020;
        }}

        .fuel-stint-bar .arrow {{
            color: #FFC000;
            font-size: 0.65rem;
            padding: 0 0.25rem;
        }}

        /* ==========================================================
           Setup Race Inline
           ========================================================== */
        .setup-race-inline {{
            display: flex;
            flex-wrap: wrap;
            gap: 1px;
            align-items: stretch;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            background: #202020;
        }}

        .setup-race-inline .setup-part {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.6rem 0.75rem;
            background: #181818;
        }}

        .setup-race-inline .setup-part .setup-label {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .setup-race-inline .setup-part .setup-val {{
            font-weight: 700;
            color: #FFC000;
        }}

        .setup-race-inline .separator {{
            display: none;
        }}

        /* ==========================================================
           Adjustment Badge — złoto dla wzrostu, czerwony dla spadku
           Mini-lekcja: Mały badge pokazujący korektę setupu
           względem wartości bazowej.
           ========================================================== */
        .adjustment-badge {{
            font-size: 0.6rem;
            font-family: var(--font-mono);
            padding: 0.1rem 0.3rem;
            background: #181818;
            color: var(--text-muted);
            display: block;
            margin-top: 0.15rem;
        }}

        .adjustment-badge.positive {{
            color: #FFC000;
            background: rgba(255, 192, 0, 0.08);
        }}

        .adjustment-badge.negative {{
            color: var(--accent-red);
            background: rgba(239, 68, 68, 0.08);
        }}

        /* ==========================================================
           Fuel Strategy — ostre prostokąty, złota meta
           Mini-lekcja: Wizualna reprezentacja strategii paliwowej.
           ========================================================== */
        .fuel-strategy {{
            margin-top: 0.75rem;
        }}

        .fuel-strategy .strategy-name {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.5rem;
        }}

        .fuel-strategy .strategy-visual {{
            display: flex;
            align-items: stretch;
            gap: 1px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            background: #202020;
        }}

        .fuel-strategy .strategy-visual .pit-stop {{
            background: #181818;
            padding: 0.4rem 0.75rem;
        }}

        .fuel-strategy .strategy-visual .arrow {{
            color: #FFC000;
            display: flex;
            align-items: center;
            padding: 0 0.25rem;
            background: #000000;
        }}

        .fuel-strategy .strategy-visual .finish {{
            background: #FFC000;
            color: #000000;
            padding: 0.4rem 0.75rem;
            font-weight: 700;
        }}

        /* ==========================================================
           Notes List
           Mini-lekcja: Lista notatek z predykcji.
           ========================================================== */
        .notes-list {{
            margin-top: 1rem;
        }}

        .notes-list ul {{
            list-style: none;
            padding: 0;
        }}

        .notes-list li {{
            font-size: 0.75rem;
            color: var(--text-muted);
            padding: 0.5rem 0;
            border-bottom: 1px solid #181818;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .notes-list li:last-child {{
            border-bottom: none;
        }}

        /* ==========================================================
           RESPONSYWNOŚĆ
           ========================================================== */
        @media (max-width: 768px) {{
            .header {{ padding: 1rem; }}
            .summary-grid {{ margin: 1rem; }}
            .tabs {{ padding: 0 1rem; }}
            .tab-content {{ padding: 1rem; }}
        }}

        /* Scrollbar — minimalistyczny, czarny */
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: #000000; }}
        ::-webkit-scrollbar-thumb {{ background: #202020; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #7D7D7D; }}

/* ==========================================================
            MODERN SEQUENTIAL UI — ujednolicony styl setup-card
            ========================================================== */
        .step-container {{
            VISUAL DATA CARDS (Zastępują tabele)
            ========================================================== */
        .data-grid {{
            display: grid !important;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 2rem;
            width: 100%;
        }}

        .data-card {{
            background: #000000;
            padding: 1.5rem;
            border: 1px solid #202020;
            transition: background 0.3s;
        }}

        .data-card:hover {{
            background: #101010;
        }}

        .data-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid #202020;
            padding-bottom: 0.75rem;
        }}

        .data-card-header h3 {{
            font-size: 1.1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .data-card-header .tag {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: #7D7D7D;
        }}

        .data-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #181818;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .data-row:last-child {{ border-bottom: none; }}

        .data-row .label {{ color: #7D7D7D; font-size: 0.7rem; }}
        .data-row .value {{ font-family: var(--font-mono); font-weight: 700; color: #FFC000; }}

        .progress-container {{
            height: 4px;
            background: #202020;
            margin-top: 0.5rem;
            position: relative;
        }}

        .progress-bar {{
            height: 100%;
            background: var(--accent-gold);
        }}

        /* Klasy pomocnicze dla typografii */
        .text-uppercase {{ text-transform: uppercase; }}
        .letter-spacing-lg {{ letter-spacing: 0.2em; }}

        .practice-timeline {{
            display: flex;
            gap: 0.5rem;
            margin: 1rem 0;
            overflow-x: auto;
            padding-bottom: 0.5rem;
        }}

        .timeline-step {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-top: 2rem;
        }}

        .step-card {{
            background: var(--bg-card);
            border-left: 4px solid #333;
            padding: 1.5rem;
            transition: all 0.3s;
        }}

        .step-card.completed {{
            border-left-color: #917300;
            opacity: 0.8;
        }}

        .step-card.next {{
            border-left-color: var(--accent-gold);
            background: #101010;
            box-shadow: 0 0 30px rgba(255, 192, 0, 0.05);
            transform: scale(1.01);
        }}

        .step-card.future {{
            border-left-color: #202020;
            opacity: 0.4;
        }}

        .step-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .step-title {{
            font-size: 1.2rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .step-status {{
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            background: #222;
            color: #777;
            text-transform: uppercase;
        }}

        .step-card.next .step-status {{
            background: var(--accent-gold);
            color: #000;
        }}

        .step-card.completed .step-status {{
            background: #917300;
            color: #000;
        }}

        .setup-display {{
            display: flex;
            flex-wrap: wrap;
            gap: 1px;
            background: #222;
            margin: 1rem 0;
        }}

        .setup-box {{
            flex: 1;
            min-width: 80px;
            background: #000;
            padding: 0.75rem;
            text-align: center;
        }}

        .setup-box .label {{
            font-size: 0.55rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .setup-box .value {{
            font-family: var(--font-mono);
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent-gold);
        }}

        .feedback-box {{
            background: rgba(255, 255, 255, 0.03);
            padding: 1rem;
            font-size: 0.85rem;
            color: #bbb;
            border-left: 2px solid #444;
            margin-top: 0.5rem;
        }}

        .feedback-box span {{
            color: var(--accent-gold);
            font-weight: 700;
            margin-right: 0.5rem;
        }}

        .deploy-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--accent-gold);
            color: #000;
            padding: 1rem 2rem;
            text-decoration: none;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 2rem;
            transition: transform 0.2s;
        }}

        .deploy-btn:hover {{
            transform: translateY(-2px);
            background: #ffcf33;
        }}


        .driver-stats-mini {{
            display: flex;
            gap: 1px;
            flex-wrap: wrap;
            margin: 1rem 0;
            background: #202020;
        }}

        .driver-stat-mini {{
            text-align: center;
            padding: 0.75rem 1rem;
            background: #000000;
        }}

        .driver-stat-mini .label {{
            font-size: 0.55rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.25rem;
        }}

        .driver-stat-mini .value {{
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1rem;
        }}
    </style>
</head>
<body>

<!-- Nagłówek strony -->
<div class="header">
    <h1><span>GPRO</span> Tracker</h1>
    <div class="header-info" id="headerInfo">Loading...</div>
</div>

<!-- Zakładki -->
<div class="tabs" id="tabsNav">
    <button class="tab-btn active" data-tab="overview">Overview</button>
    <button class="tab-btn" data-tab="nextrace">Next Race</button>
    <button class="tab-btn" data-tab="standings">Standings</button>
    <button class="tab-btn" data-tab="results">Results</button>
    <button class="tab-btn" data-tab="setups">Setups</button>
    <button class="tab-btn" data-tab="finances">Finances</button>
    <button class="tab-btn" data-tab="driver">Driver</button>
</div>

<!-- Zawartość zakładek -->
<div class="tab-content active" id="tab-overview"></div>
<div class="tab-content" id="tab-nextrace"></div>
<div class="tab-content" id="tab-standings"></div>
<div class="tab-content" id="tab-results"></div>
<div class="tab-content" id="tab-setups"></div>
<div class="tab-content" id="tab-finances"></div>
<div class="tab-content" id="tab-driver"></div>

<script>
// ==========================================================
// DANE WYŚCIGOWE
// Mini-lekcja: Dane są osadzone bezpośrednio w HTML jako
// zmienna JavaScript. Dzięki temu strona nie potrzebuje
// serwera ani dodatkowych zapytań HTTP - działa natychmiast.
// ==========================================================
const RACE_DATA = {race_data_js};

// Dane predykcji setupu (z predictor.py)
const PREDICTION_DATA = {prediction_data_js};

// Dane kalendarza (pobrane z osobnego pliku data/calendar.json)
const CALENDAR_DATA = {calendar_data_js};

// Aktywny kontekst sezonu/wyścigu (Office + Calendar)
const CURRENT_CONTEXT_DATA = {current_context_js};

// ==========================================================
// OBSŁUGA ZAKŁADEK
// ==========================================================
function setupTabs() {{
    // Event delegation - obsłuży wszystkie przyciski .tab-btn teraz i w przyszłości
    document.addEventListener('click', (e) => {{
        const btn = e.target.closest('.tab-btn');
        if (!btn || !btn.dataset.tab) return;

        const tabId = btn.dataset.tab;
        const targetContent = document.getElementById('tab-' + tabId);
        if (!targetContent) return;

        // Dezaktywuj wszystkie przyciski i treści
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Aktywuj klikniętą zakładkę (znajdź główny przycisk w nawigacji)
        const navBtn = document.querySelector(`.tabs .tab-btn[data-tab="${{tabId}}"]`);
        if (navBtn) navBtn.classList.add('active');
        else btn.classList.add('active');

        // Pokaż treść wybranej zakładki
        targetContent.classList.add('active');
    }});
}}

// ==========================================================
// FUNKCJE POMOCNICZE
// ==========================================================

// Formatuje kwotę pieniężną (np. 9041500 -> "$9,041,500")
function formatMoney(amount) {{
    if (amount == null) return '-';
    const prefix = amount < 0 ? '-$' : '$';
    return prefix + Math.abs(amount).toLocaleString('en-US');
}}

// Zwraca klasę CSS dla pozycji wyścigu
function posClass(pos) {{
    if (pos === 1 || pos === '1' || pos === '1.') return 'pos-1';
    if (pos === 2 || pos === '2' || pos === '2.') return 'pos-2';
    if (pos === 3 || pos === '3' || pos === '3.') return 'pos-3';
    return '';
}}

// Zwraca klasę CSS dla wartości statystyki kierowcy
function statClass(name, value) {{
    const v = parseInt(value);
    if (isNaN(v)) return '';
    // Wyższe = lepsze (oprócz agresji i charyzmy)
    if (name === 'aggressiveness' || name === 'charisma') {{
        if (v <= 30) return 'stat-good';
        if (v <= 80) return 'stat-ok';
        return 'stat-bad';
    }}
    if (name === 'concentration' || name === 'stamina') {{
        if (v >= 150) return 'stat-good';
        if (v >= 80) return 'stat-ok';
        return 'stat-bad';
    }}
    return '';
}}


function toInt(value) {{
    if (value === null || value === undefined || value === '') return null;
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}}

function getLatestRace() {{
    if (!RACE_DATA || RACE_DATA.length === 0) return null;
    return RACE_DATA[RACE_DATA.length - 1];
}}

// Znajduje pierwszy wyścig od końca z danymi kierowcy (driver_profile, standings)
// Używane przez renderOverview() żeby pokazać statystyki nawet gdy ostatni plik jest pusty
function getRaceWithProfileData() {{
    if (!RACE_DATA || RACE_DATA.length === 0) return null;
    // Szukaj od końca - ostatni wyścig z danymi
    for (let i = RACE_DATA.length - 1; i >= 0; i--) {{
        const race = RACE_DATA[i];
        if (race?.driver_profile && Object.keys(race.driver_profile).length > 0) {{
            return race;
        }}
    }}
    return RACE_DATA[RACE_DATA.length - 1]; // Fallback do ostatniego
}}

// Znajduje wyścig z danymi klasyfikacji (standings)
function getRaceWithStandingsData() {{
    if (!RACE_DATA || RACE_DATA.length === 0) return null;
    for (let i = RACE_DATA.length - 1; i >= 0; i--) {{
        const race = RACE_DATA[i];
        if (race?.standings?.managers && race.standings.managers.length > 0) {{
            return race;
        }}
    }}
    return RACE_DATA[RACE_DATA.length - 1];
}}

function getCurrentContext() {{
    const current = CURRENT_CONTEXT_DATA || null;
    const predicted = PREDICTION_DATA?.next_race || null;
    const latest = getLatestRace()?.race_data || null;

    if (current && toInt(current.season) !== null) return current;
    if (predicted && toInt(predicted.season) !== null) return predicted;
    if (latest && toInt(latest.season) !== null) return latest;
    return null;
}}

function getDisplayedRaceData() {{
    if (!RACE_DATA || RACE_DATA.length === 0) return [];
    const active = getCurrentContext();
    const activeSeason = toInt(active?.season);
    if (activeSeason === null) return RACE_DATA;
    return RACE_DATA.filter(item => toInt(item?.race_data?.season) === activeSeason);
}}

function normalizeTrackName(name) {{
    return String(name || '')
        .trim()
        .toLowerCase()
        .replace(/\\s+/g, ' ');
}}

function isTransferMarketName(name) {{
    const normalized = normalizeTrackName(name);
    return normalized.includes('rynek transferowy') ||
           normalized.includes('transfer market');
}}

function getCalendarEntries() {{
    if (!CALENDAR_DATA) return [];

    const payload = Array.isArray(CALENDAR_DATA)
        ? {{ data: CALENDAR_DATA }}
        : CALENDAR_DATA;

    const rootData = payload?.data;

    if (Array.isArray(rootData)) return rootData;

    if (rootData && typeof rootData === 'object') {{
        for (const key of ['races', 'calendar', 'events', 'schedule', 'items', 'data']) {{
            if (Array.isArray(rootData[key])) return rootData[key];
        }}
    }}

    for (const key of ['races', 'calendar', 'events', 'schedule', 'items']) {{
        if (Array.isArray(payload?.[key])) return payload[key];
    }}

    return [];
}}

function getCalendarSeason() {{
    const direct =
        toInt(CALENDAR_DATA?.season) ??
        toInt(CALENDAR_DATA?.selSeasonNb) ??
        toInt(CALENDAR_DATA?.seasonNb);

    if (direct !== null) return direct;

    for (const entry of getCalendarEntries()) {{
        const season =
            toInt(entry?.season) ??
            toInt(entry?.selSeasonNb) ??
            toInt(entry?.seasonNb);

        if (season !== null) return season;
    }}

    return null;
}}

function normalizeCalendarRace(entry, index, fallbackSeason) {{
    const eventType = String(entry?.eventType || '').trim().toUpperCase();
    const track = entry?.track || entry?.trackName || entry?.name || entry?.raceName || 'Nieznany tor';

    return {{
        eventType,
        track,
        season:
            toInt(entry?.season) ??
            toInt(entry?.selSeasonNb) ??
            toInt(entry?.seasonNb) ??
            fallbackSeason,
        race:
            toInt(entry?.race) ??
            toInt(entry?.raceNb) ??
            toInt(entry?.round) ??
            toInt(entry?.number) ??
            toInt(entry?.idx) ??
            toInt(entry?.selRaceNb) ??
            (index + 1),
        total_laps:
            toInt(entry?.total_laps) ??
            toInt(entry?.totalLaps) ??
            toInt(entry?.laps) ??
            toInt(entry?.lapNb) ??
            toInt(entry?.noOfLaps) ??
            null,
        isCurrent:
            toInt(entry?.isCurrentRace) === 1 ||
            entry?.current === true ||
            entry?.upcoming === true
    }};
}}

// Pomocnicza: parsuj polską datę z kalendarza (np. "Kwi 10, 2026")
function parsePolishDate(dateStr) {{
    if (!dateStr) return null;
    
    const months = {{
        'sty': 0, 'lut': 1, 'mar': 2, 'kwi': 3, 'maj': 4, 'cze': 5,
        'lip': 6, 'sie': 7, 'wrz': 8, 'paź': 9, 'lis': 10, 'gru': 11
    }};
    
    // Usuń polskie znaki i normalizuj
    const normalized = dateStr.toLowerCase()
        .replace('ą', 'a').replace('ę', 'e')
        .replace('ó', 'o').replace('ń', 'n')
        .replace('ś', 's').replace('ź', 'z')
        .replace('ż', 'z').replace('ł', 'l');
    
    // Format: "Kwi 10, 2026" lub "Apr 10, 2026"
    const match = normalized.match(/([a-z]+)\\s+(\\d+),?\\s*(\\d{{4}})/);
    if (!match) return null;
    
    const monthName = match[1];
    const day = parseInt(match[2]);
    const year = parseInt(match[3]);
    
    const month = months[monthName];
    if (month === undefined) return null;
    
    return new Date(year, month, day);
}}

function getCalendarNextRace() {{
    // PRIORYTET: Użyj current_context.json jeśli jest dostępny - ma aktualne dane z Office API
    // To jest najbardziej wiarygodne źródło (pobrane z API)
    if (CURRENT_CONTEXT_DATA) {{
        const cc = CURRENT_CONTEXT_DATA;
        const ccSeason = toInt(cc.season);
        const ccRace = toInt(cc.race);
        const ccTrack = cc.track;
        
        if (ccSeason !== null && ccRace !== null && ccTrack) {{
            return {{
                season: ccSeason,
                race: ccRace,
                track: ccTrack,
                total_laps: cc.total_laps || 72
            }};
        }}
    }}

    // Fallback: użyj kalendarza jeśli current_context niedostępny
    const entries = getCalendarEntries();
    if (!entries || entries.length === 0) return null;

    const fallbackSeason = getCalendarSeason();
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const normalized = entries
        .map((entry, index) => normalizeCalendarRace(entry, index, fallbackSeason))
        .filter(entry => entry.eventType === '' || entry.eventType === 'R')
        .filter(entry => !isTransferMarketName(entry.track))
        .filter(entry => entry.race !== null)
        .sort((a, b) =>
            ((toInt(a.season) ?? 0) - (toInt(b.season) ?? 0)) ||
            ((toInt(a.race) ?? 0) - (toInt(b.race) ?? 0))
        );

    if (normalized.length === 0) return null;

    // Znajdź najbliższy przyszły wyścig (data > dzisiejsza data)
    const racesWithDates = entries
        .map((entry, idx) => {{
            const raceInfo = normalizeCalendarRace(entry, idx, fallbackSeason);
            const dateStr = entry?.dateEvent || entry?.eventDate || entry?.date || null;
            const parsedDate = parsePolishDate(dateStr);
            return {{ ...raceInfo, dateStr, parsedDate }};
        }})
        .filter(r => r.eventType === '' || r.eventType === 'R')
        .filter(r => !isTransferMarketName(r.track))
        .filter(r => r.race !== null);

    let nextFutureRace = null;
    for (const race of racesWithDates) {{
        if (race.parsedDate && race.parsedDate > today) {{
            if (!nextFutureRace || race.parsedDate < nextFutureRace.parsedDate) {{
                nextFutureRace = race;
            }}
        }}
    }}

    if (nextFutureRace) return nextFutureRace;

    // Fallback: szukaj isCurrentRace
    const explicitCurrent = normalized.find(entry => entry.isCurrent);
    if (explicitCurrent) return explicitCurrent;

    // Fallback: szukaj wyścigu po sezonie/race z getCurrentContext
    const active = getCurrentContext();
    const activeSeason = toInt(active?.season);
    const activeRace = toInt(active?.race);
    if (activeSeason !== null && activeRace !== null) {{
        const exact = normalized.find(entry =>
            toInt(entry.season) === activeSeason &&
            toInt(entry.race) === activeRace
        );
        if (exact) return exact;
    }}

    // Fallback: szukaj następnego wyścigu po ostatnim zapisanym
    const latest = getLatestRace()?.race_data || {{}};
    const latestSeason = toInt(latest?.season);
    const latestRace = toInt(latest?.race);

    for (const entry of normalized) {{
        const season = toInt(entry.season);
        const race = toInt(entry.race);
        if (latestSeason === null) return entry;
        if (season > latestSeason) return entry;
        if (season === latestSeason && latestRace !== null && race > latestRace) return entry;
    }}

    return normalized[0] || null;
}}

function resolvePredictionContext(pred) {{
    // Simple approach: compare prediction.json with current_context (most reliable source)
    const predictedRace = pred?.next_race || {{}};
    
    // Use current_context if available, otherwise fall back to prediction
    let nextRace;
    let isStale = false;
    let staleReason = '';
    
    if (CURRENT_CONTEXT_DATA) {{
        const cc = CURRENT_CONTEXT_DATA;
        const ccSeason = toInt(cc.season);
        const ccRace = toInt(cc.race);
        const ccTrack = cc.track;
        
        const predSeason = toInt(predictedRace.season);
        const predRace = toInt(predictedRace.race);
        const predTrack = predictedRace.track || '';
        const ccTrackNorm = normalizeTrackName(ccTrack);
        
        // Sprawdź czy predykcja pasuje do current_context
        // Porównujemy season/race ORAZ track (jeśli pred ma track)
        const trackMatches = !predTrack || normalizeTrackName(predTrack) === ccTrackNorm;
        const matches = predSeason === ccSeason && predRace === ccRace && trackMatches;
        
        if (matches) {{
            // Predykcja jest aktualna - użyj jej
            nextRace = {{ ...predictedRace, total_laps: cc.total_laps || 72 }};
            isStale = false;
        }} else {{
            // Predykcja nieaktualna - użyj current_context ale zachowaj setup z predykcji
            nextRace = {{
                season: ccSeason,
                race: ccRace,
                track: ccTrack,
                total_laps: cc.total_laps || 72
            }};
            isStale = true;
            staleReason = 
                `Prediction.json: ${{predTrack || 'Unknown track'}} (S${{predSeason ?? '?'}} R${{predRace ?? '?'}}) · ` +
                `Current: ${{ccTrack}} (S${{ccSeason}} R${{ccRace}})`;
        }}
    }} else {{
        // Brak current_context - użyj predykcji bezpośrednio
        nextRace = predictedRace;
        isStale = false;
    }}

    return {{ nextRace, isStale, staleReason }};
}}

// ==========================================================
// RENDEROWANIE DASHBOARDU
// ==========================================================

function render() {{
    const displayedData = getDisplayedRaceData();
    const activeContext = getCurrentContext();

    if (!displayedData || displayedData.length === 0) {{
        document.getElementById('tab-results').innerHTML = `
            <div class="empty-state">
                <h2>No data available</h2>
                <p>Run fetcher after a race to collect data:</p>
                <p style="margin-top:1rem"><code>python gpro_fetcher.py</code></p>
            </div>`;
        return;
    }}

    const latest = displayedData[displayedData.length - 1];
    const rd = latest.race_data || {{}};

    // Nagłówek
    document.getElementById('headerInfo').textContent =
        `Season ${{rd.season}} · Race ${{rd.race}} · ${{rd.track}} · Season data: ${{displayedData.length}} races`;

    // Renderuj wszystkie zakładki
    renderOverview();
    renderNextRace();
    renderStandings();
    renderResults();
    renderSetups();
    renderFinances();
    renderDriver(latest);
}}

// ==========================================================
// ZAKŁADKA: PRZEGLĄD (Executive Summary)
// ==========================================================
function renderOverview() {{
    const container = document.getElementById('tab-overview');
    if (!container) return;
    container.innerHTML = ''; // Wyczyść stare napisy

    const latest = getLatestRace();
    const nextRace = getCalendarNextRace();
    const pred = PREDICTION_DATA;

    if (!latest && !nextRace) {{
        container.innerHTML = '<div class="empty-state"><h2>No data for overview</h2></div>';
        return;
    }}

    const rd = latest?.race_data || {{}};
    // Użyj wyścigu z danymi kierowcy dla statystyk
    const raceWithProfile = getRaceWithProfileData();
    const raceWithStandings = getRaceWithStandingsData();
    const dp = raceWithProfile?.driver_profile || latest?.driver_profile || {{}};
    const cs = raceWithProfile?.car_status || latest?.car_status || {{}};
    // Użyj standings z wyścigu który je ma
    const standingsData = raceWithStandings?.standings || latest?.standings || null;

    let html = '';

    // Pobierz aktualny kontekst dla nagłówka (sezon, wyścig, tor)
    const ctx = getCurrentContext();
    const seasonLabel = ctx?.season ? "SEZON " + ctx.season : '';
    const raceLabel = ctx?.race ? "R" + ctx.race : '';
    const trackLabel = ctx?.track || '';

    // 1. Sekcja: Nagłówek Przeglądu (Hero)
    html += `
    <div class="hero-section">
        <span class="hero-subtitle">${{seasonLabel}} · ${{raceLabel}}</span>
        <h2>${{trackLabel || 'SEASON OVERVIEW'}}</h2>
        <div class="hero-meta">
            <span>🏎️ YOUR GPRO CAREER STATUS</span>
        </div>
    </div>`;

    // 2. Grid z kluczowymi informacjami
    html += `<div class="summary-grid" style="margin-left: 0; margin-right: 0;">`;

    // NASTĘPNY WYŚCIG (Karta zamiast Hero, aby uniknąć duplikatu)
    if (nextRace) {{
        html += `
        <div class="hero-section">
            <span class="hero-subtitle">NEXT RACE</span>
            <h2>${{nextRace.track || 'Unknown track'}}</h2>
            <div class="hero-meta">
                <span>📅 SEASON ${{nextRace.season}} R${{nextRace.race}}</span>
                <span>🏁 ${{nextRace.total_laps || 72}} LAPS</span>
            </div>
            ${{pred ? `<div><span class="hero-badge">RECOMMENDATIONS READY</span></div>` : ''}}
        </div>`;
    }}

    // FINANSE - użyj danych z wyścigu z profilem (pełne dane)
    const rdProfile = raceWithProfile?.race_data || latest?.race_data || {{}};
    const finances = rdProfile?.finances || {{}};
    const cash = dp.cash || finances?.balance || rdProfile?.finances?.balance || 0;
    html += `
    <div class="summary-card">
        <div class="label">FINANCES</div>
        <div class="value" style="color: ${{cash >= 0 ? 'var(--accent-gold)' : 'var(--accent-red)'}}">
            ${{formatMoney(cash)}}
        </div>
        <div class="sub">ACCOUNT BALANCE</div>
        ${{finances && finances.total !== undefined ? `<div class="rec-row" style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 0.5rem;"><span class="rec-label">Last race</span><span class="${{finances.total >= 0 ? 'val-positive' : 'val-negative'}}">${{formatMoney(finances.total)}}</span></div>` : ''}}
    </div>`;

    // KIEROWCA
    if (rd.driver || dp.driName) {{
        const drvName = dp.driName || rd.driver?.name;
        const drvOA = dp.overall || rd.driver?.OA;
        // Pobierz overall z driver_profile (jeśli istnieje w profilu)
        const drvOAFromProfile = dp.overallRating || dp.ti || null;
        const finalOA = drvOAFromProfile || drvOA || '';

        // Kariera
        const cWins = dp.wins || 0;
        const cPodiums = dp.podiums || 0;
        const cPoles = dp.poles || 0;

        // Sezon
        let sWins = 0, sPodiums = 0, sPoles = 0;
        const myName = dp.manName || dp.manager || dp.owner?.name || '';

        // Spróbuj pobrać statystyki sezonu z tabeli ligowej (najbardziej wiarygodne źródło dla pozycji)
        const myStanding = standingsData?.managers?.find(m => m.name === myName);
        if (myStanding && myStanding.results) {{
            myStanding.results.forEach(r => {{
                const pos = toInt(r.pos);
                if (pos === 1) sWins++;
                if (pos >= 1 && pos <= 3) sPodiums++;

                const qPos = toInt(r.grid);
                if (qPos === 1) sPoles++;
            }});
        }} else {{
            // Fallback do danych wyścigowych jeśli brak tabeli
            const displayedData = getDisplayedRaceData();
            displayedData.forEach(d => {{
                const summary = d.race_summary;
                let myResult = summary?.results?.find(r => r.manager === myName);
                if (!myResult) myResult = summary?.results?.find(r => r.gap === '' || r.gap === '0.000s' || r.gap === '+0.000s');

                const pos = toInt(myResult?.position);
                if (pos === 1) sWins++;
                if (pos >= 1 && pos <= 3) sPodiums++;

                const qPos = toInt(d.race_data?.q1_pos);
                if (qPos === 1) sPoles++;
            }});
        }}

        html += `
        <div class="summary-card">
            <div class="label">DRIVER</div>
            <div class="value-small">${{drvName}}</div>
            <div class="sub">OVERALL: ${{finalOA}}</div>

            <div class="rec-grid" style="grid-template-columns: 1fr 1fr 1fr; gap: 1px; margin-top: 1rem; background: var(--border-color); padding: 1px;">
                <div class="stat-item" style="background: var(--bg-primary); padding: 0.5rem;">
                    <div class="stat-name">WINS</div>
                    <div class="stat-value" style="font-size: 1rem; color: var(--accent-gold);">${{cWins}}</div>
                    <div class="sub" style="font-size: 0.6rem;">S: ${{sWins}}</div>
                </div>
                <div class="stat-item" style="background: var(--bg-primary); padding: 0.5rem;">
                    <div class="stat-name">PODIUM</div>
                    <div class="stat-value" style="font-size: 1rem; color: var(--accent-gold);">${{cPodiums}}</div>
                    <div class="sub" style="font-size: 0.6rem;">S: ${{sPodiums}}</div>
                </div>
                <div class="stat-item" style="background: var(--bg-primary); padding: 0.5rem;">
                    <div class="stat-name">POLES</div>
                    <div class="stat-value" style="font-size: 1rem; color: var(--accent-gold);">${{cPoles}}</div>
                    <div class="sub" style="font-size: 0.6rem;">S: ${{sPoles}}</div>
                </div>
            </div>
        </div>`;
    }}

    // TABELA LIGOWA (League Table)
    const standings = standingsData?.managers || [];
    if (standings.length > 0) {{
        const myName = dp.manName || dp.manager || dp.owner?.name || '';
        const myIndex = standings.findIndex(m => m.name === myName);

        // Wybierz kilka osób obok
        let startIndex = Math.max(0, myIndex - 1);
        let endIndex = Math.min(standings.length, startIndex + 3);
        if (endIndex === standings.length) startIndex = Math.max(0, endIndex - 3);

        const miniStandings = standings.slice(startIndex, endIndex);

        html += `
        <div class="summary-card">
            <div class="label">LEAGUE TABLE</div>
            <div style="margin-top: 1rem;">
                <table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.75rem;">
                    ${{miniStandings.map(m => `
                        <tr style="${{m.name === myName ? 'color: var(--accent-gold); font-weight: 700;' : 'color: var(--text-secondary);'}}">
                            <td style="padding: 0.25rem 0;">P${{m.pos}}</td>
                            <td style="padding: 0.25rem 0; text-transform: uppercase;">${{m.name.split(' ')[0]}}</td>
                            <td style="padding: 0.25rem 0; text-align: right;">${{m.pts}} PTS</td>
                        </tr>
                    `).join('')}}
                </table>
            </div>
            <div style="margin-top: 1rem;">
                <button class="tab-btn" data-tab="standings" style="padding: 0.5rem 1rem; border: 1px solid var(--accent-gold); font-size: 0.6rem; color: var(--accent-gold); height: auto; line-height: 1;">FULL STANDINGS &raquo;</button>
            </div>
        </div>`;
    }}

    html += `</div>`; // zamknięcie summary-grid

    container.innerHTML = html;

    // Re-attach listener for the button inside overview
    container.querySelector('[data-tab="standings"]')?.addEventListener('click', () => {{
        document.querySelector('.tab-btn[data-tab="standings"]').click();
    }});
}}

// ==========================================================
// ZAKŁADKA: NASTĘPNY WYŚCIG (rekomendacje z predictor.py)
// Mini-lekcja: Ta funkcja używa danych z predictor.py aby
// pokazać dokładne rekomendacje setupu, paliwa i kierowcy.
// ==========================================================
function renderNextRace() {{
    const container = document.getElementById('tab-nextrace');
    if (!container) return;
    container.innerHTML = ''; // WYCZYŚĆ STARE NAPISY (NASTĘPNE WYDARZENIA ITD.)

    // Jeśli mamy dane predykcji, używamy ich
    if (PREDICTION_DATA) {{
        renderPrediction(container);
        return;
    }}

    // Fallback: jeśli brak predykcji, pokaż komunikat
    container.innerHTML = `
        <div class="empty-state">
            <h2>No recommendations</h2>
            <p>Run predictor.py to generate recommendations:</p>
            <p style="margin-top:1rem"><code>python predictor.py</code></p>
        </div>`;
}}

function renderPrediction(container) {{
    const pred = PREDICTION_DATA;
    const predictionContext = resolvePredictionContext(pred);
    const nextRace = predictionContext.nextRace || pred.next_race || {{}};
    const sequence = pred.sequence || [];
    const confidence = pred.confidence || 'unknown';
    const confidenceReason = pred.confidence_reason || '';
    const fuelStrategy = pred.fuel_strategy || {{}};
    const tyreStrategy = pred.tyre_strategy || {{}};
    const notes = pred.notes || [];

    let html = '';

    // =============================================
    // 1. NAGŁÓWEK
    // =============================================
    html += `
    <div class="hero-section" style="text-align: center;">
        <span class="hero-subtitle">RACE PLAN</span>
        <h2>${{nextRace.track || 'Unknown track'}}</h2>
        <div class="hero-meta" style="justify-content: center;">
            <span>📅 SEASON ${{nextRace.season}} R${{nextRace.race}}</span>
            <span>🏁 ${{nextRace.total_laps || 72}} LAPS</span>
        </div>

        <div style="max-width: 600px; margin: 2.5rem auto 0 auto;">
            <div class="confidence-bar" style="height: 4px;">
                <div class="confidence-fill ${{confidence}}"></div>
            </div>
            <div class="hero-subtitle" style="margin-top: 0.5rem; font-size: 0.7rem;">CONFIDENCE: ${{confidence.toUpperCase()}} — ${{confidenceReason}}</div>
        </div>

        <div id="deployBtnContainer"></div>
    </div>`;

    // =============================================
    // 2. SEKWENCJA ZDARZEŃ
    // =============================================
    html += `<div class="step-container">`;

    sequence.forEach(step => {{
        const isCompleted = step.completed;
        const isNext = step.is_next;
        const statusClass = isCompleted ? 'completed' : (isNext ? 'next' : 'future');
        const statusLabel = isCompleted ? 'COMPLETED' : (isNext ? 'YOUR NEXT STEP' : 'FUTURE');

        html += `<div class="step-card ${{statusClass}}">`;
        html += `<div class="step-header">`;
        html += `<div class="step-title">${{step.id}}</div>`;
        html += `<div class="step-status">${{statusLabel}}</div>`;
        html += `</div>`;

        html += `<div class="session-meta">`;
        html += `<span>🌡️ ${{step.temp || '?'}}°C</span>`;
        html += `<span>🛞 ${{step.tyres || '?'}}</span>`;
        if (step.id === 'Race' && step.fuel_strategy) {{
             html += `<span>⛽ ${{step.fuel_strategy.pits}} PIT STOPS</span>`;
        }}
        html += `</div>`;

        if (step.setup) {{
            html += `<div class="setup-display">`;
            ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(k => {{
                html += `<div class="setup-box"><div class="label">${{k.toUpperCase()}}</div><div class="value">${{step.setup[k] || '-'}}</div></div>`;
            }});
            html += `</div>`;
        }} else {{
            html += `<div style="padding: 2rem; text-align: center; color: #444; font-size: 0.8rem; border: 1px dashed #222; margin: 1rem 0;">PARAMETERS WILL BE GENERATED AFTER COMPLETING PREVIOUS STEP</div>`;
        }}

        if (step.feedback) {{
            html += `<div class="feedback-box"><span>FEEDBACK:</span> ${{step.feedback}}</div>`;
        }}

        if (step.note) {{
            html += `<div class="session-note" style="margin-top: 1rem; color: var(--accent-gold); font-weight: 700;">${{step.note}}</div>`;
        }}

        if (step.id === 'Race' && step.fuel_strategy) {{
            const fs = step.fuel_strategy;
            html += `<div class="fuel-stint-bar" style="margin-top: 1.5rem;">`;
            (fs.stints || []).forEach((fuel, i) => {{
                if (i > 0) html += `<span class="arrow">→</span>`;
                html += `<span class="stint">${{fuel}}L</span>`;
            }});
            html += `<span class="arrow">→</span>`;
            html += `<span class="stint" style="background:var(--accent-blue)">META</span>`;
            html += `</div>`;
        }}

        html += `</div>`;
    }});

    html += `</div>`;

    // =============================================
    // 3. PODSUMOWANIE STRATEGII
    // =============================================
    html += `<div class="rec-grid" style="margin-top: 2rem;">`;

// Paliwo
    html += `<div class="rec-card"><h3>FUEL STRATEGY</h3>`;
    html += `<div class="rec-row"><span class="rec-label">Consumption</span><span class="rec-value">~${{fuelStrategy.fuel_per_lap || 0}} L/lap</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Pit stops</span><span class="rec-value">${{fuelStrategy.recommended?.pits || 0}}</span></div>`;
    html += `</div>`;

    // Opony
    html += `<div class="rec-card"><h3>TYRE STRATEGY</h3>`;
    html += `<div class="rec-row"><span class="rec-label">Life</span><span class="rec-value">~${{ tyreStrategy.est_tyre_life_laps || 0}} laps</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Bottleneck</span><span class="rec-value">${{( tyreStrategy.bottleneck || '').toUpperCase()}}</span></div>`;
    html += `</div>`;

    // Opony
    html += `<div class="rec-card"><h3>STRATEGIA OPONOWA</h3>`;
    html += `<div class="rec-row"><span class="rec-label">Żywotność</span><span class="rec-value">~${{tyreStrategy.est_tyre_life_laps || 0}} okr</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Bottleneck</span><span class="rec-value">${{(tyreStrategy.bottleneck || '').toUpperCase()}}</span></div>`;
    html += `</div>`;

    html += `</div>`;

    // =============================================
    // 4. NOTATKI
    // =============================================
    if (notes && notes.length > 0) {{
        html += `<div class="rec-card" style="margin-top:1rem; background: var(--bg-card);"><h3>Tips</h3>`;
        html += `<div class="notes-list"><ul>`;
        notes.forEach(note => {{ html += `<li>${{note}}</li>`; }});
        html += `</ul></div></div>`;
    }}

    container.innerHTML = html;
}}

function renderResults() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    // Znajdź najlepszą pozycję gracza w sezonie - z standings
    const positions = displayedData.map(d => {{
        const standings = d.standings || {{}};
        const managers = standings.managers || [];
        const dp = d.driver_profile || {{}};
        const myName = dp.manName || dp.manager || dp.owner?.name || '';
        const myManager = managers.find(m => m.name === myName);
        if (myManager && myManager.results && myManager.results.length > 0) {{
            // Pobierz ostatni wynik (najnowszy wyścig)
            const lastResult = myManager.results[myManager.results.length - 1];
            return toInt(lastResult?.pos);
        }}
        return null;
    }}).filter(p => p !== null);

    const bestPos = positions.length > 0 ? Math.min(...positions) : '?';

    let html = `
    <div class="hero-section">
        <span class="hero-subtitle">RACE HISTORY</span>
        <h2>SEASON RESULTS</h2>
        <div class="hero-meta">
            <span>🏁 ${{displayedData.length}} RACES</span>
            <span>🏆 BEST: P${{bestPos}}</span>
        </div>
    </div>
    <div class="setup-grid">`;

    // Od najnowszego do najstarszego
    for (let i = displayedData.length - 1; i >= 0; i--) {{
        const rd = displayedData[i].race_data || {{}};
        const fin = rd.finances || {{}};
        const pits = rd.pits || [];
        const standings = displayedData[i].standings || {{}};
        const managers = standings.managers || [];
        const dp = displayedData[i].driver_profile || {{}};
        const myName = dp.manName || dp.manager || dp.owner?.name || '';
        const myManager = managers.find(m => m.name === myName);
        const myResult = (myManager && myManager.results && myManager.results.length > 0)
            ? myManager.results[myManager.results.length - 1]
            : {{}};

        // Buduj sekcję pit stopów
        let pitsHtml = '';
        pits.forEach((pit, idx) => {{
            pitsHtml += `
            <div class="data-row" style="background: rgba(255,192,0,0.03);">
                <span class="label">PIT ${{idx + 1}} (LAP ${{pit.lap}})</span>
                <span class="value">${{pit.tyre_condition}}% 🛞 / ${{pit.refilled_to}}L ⛽</span>
            </div>`;
        }});

        html += `
        <div class="setup-card">
            <h3>${{rd.track || '?'}} <span style="color: var(--text-muted); font-weight: 400;">· ${{rd.country || ''}}</span></h3>
            <div class="tag" style="margin-bottom: 1rem;">S${{rd.season}}R${{rd.race}}</div>

            <!-- Sekcja Wyniki -->
            <div class="data-row">
                <span class="label">RACE POSITION</span>
                <span class="value ${{posClass(myResult.position)}}">P${{myResult.position || '-'}}</span>
            </div>
            <div class="data-row">
                <span class="label">QUALIFYING (Q1 / Q2)</span>
                <span class="value">P${{rd.q1_pos || '-'}} / P${{rd.q2_pos || '-'}}</span>
            </div>
            <div class="data-row">
                <span class="label">TIME</span>
                <span class="value">${{myResult.gap || '-'}}</span>
            </div>
            <div class="data-row">
                <span class="label">POINTS</span>
                <span class="value">${{myResult.points || '-'}}</span>
            </div>

            <!-- Sekcja Paliwo & Opony -->
            <div class="data-row" style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
                <span class="label" style="color: var(--accent-gold);">FUEL & TYRES</span>
                <span class="value"></span>
            </div>
            <div class="data-row">
                <span class="label">START FUEL</span>
                <span class="value">${{rd.start_fuel || '-'}} L</span>
            </div>
            ${{pitsHtml}}
            <div class="data-row">
                <span class="label">FINISH FUEL</span>
                <span class="value">${{rd.finish_fuel || 0}} L</span>
            </div>
            <div class="data-row">
                <span class="label">TYRE TYPE</span>
                <span class="value">${{rd.tyres || (rd.setups && rd.setups[0] && rd.setups[0].tyres) || '-'}}</span>
            </div>

            <div class="progress-container" style="margin-top: 0.75rem;">
                <div class="progress-bar" style="width: ${{rd.finish_tyres || 0}}%; background: ${{rd.finish_tyres < 20 ? 'var(--accent-red)' : 'var(--accent-gold)'}}"></div>
            </div>
            <div class="data-row" style="border: none; padding-top: 0.25rem;">
                <span class="label">TYRE WEAR</span>
                <span class="value">${{rd.finish_tyres || 0}}%</span>
            </div>

            <!-- Stopka: sezon, temperatura, wilgotność -->
            <div class="setup-meta">
                SEASON ${{rd.season || '-'}} · TEMP: ${{rd.weather && rd.weather.q1 && rd.weather.q1.temp ? rd.weather.q1.temp + '°C' : (rd.weather && rd.weather.race && rd.weather.race.temp_range ? rd.weather.race.temp_range[0] + '°C' : '-')}} · HUMIDITY: ${{rd.weather && rd.weather.q1 && rd.weather.q1.humidity ? rd.weather.q1.humidity + '%' : (rd.weather && rd.weather.race && rd.weather.race.humidity_range ? rd.weather.race.humidity_range[0] + '%' : '-')}}
            </div>
        </div>`;
    }}

    html += '</div>';
    document.getElementById('tab-results').innerHTML = html;
}}

// ==========================================================
// ZAKŁADKA: TABELA LIGOWA (Standings)
// ==========================================================
function renderStandings() {{
    const container = document.getElementById('tab-standings');
    const latest = getLatestRace();
    if (!latest || !latest.standings) {{
        container.innerHTML = '<div class="empty-state"><h2>No standings data</h2></div>';
        return;
    }}

    const s = latest.standings;
    const managers = s.managers || [];
    const dp = latest.driver_profile || {{}};
    const myName = dp.manName || dp.manager || dp.owner?.name || '';

    let html = `
    <div class="hero-section">
        <span class="hero-subtitle">MANAGER RANKING</span>
        <h2>${{s.group || 'LEAGUE STANDINGS'}}</h2>
        <div class="hero-meta">
            <span>📊 SEASON ${{getCurrentContext()?.season || '?'}}</span>
            <span>👥 ${{managers.length}} PARTICIPANTS</span>
        </div>
    </div>

    <div class="data-card" style="padding: 0; overflow-x: auto;">
        <table class="data-table">
            <thead>
                <tr>
                    <th>POS</th>
                    <th>MANAGER</th>
                    <th>TYRES</th>
                    <th>PTS</th>
                    <th>RESULTS (1-17)</th>
                </tr>
            </thead>
            <tbody>`;

    managers.forEach(m => {{
        const isMe = m.name === myName;
        html += `
            <tr style="${{isMe ? 'background: rgba(255,192,0,0.05);' : ''}}">
                <td class="${{posClass(m.pos)}}">${{m.pos}}</td>
                <td style="${{isMe ? 'color: var(--accent-gold); font-weight: 700;' : ''}}">${{m.name}}</td>
                <td>${{m.tyre}}</td>
                <td style="font-weight: 700;">${{m.pts}}</td>
                <td>
                    <div style="display: flex; gap: 4px;">
                    ${{(m.results || []).map(r => `
                        <div style="
                            width: 18px;
                            height: 18px;
                            font-size: 0.6rem;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background: ${{ r.pos === '-' ? '#111' : (toInt(r.pos) <= 3 ? 'var(--accent-gold)' : (toInt(r.pos) <= 10 ? '#444' : '#222')) }};
                            color: ${{ toInt(r.pos) <= 3 ? '#000' : '#888' }};
                            font-weight: ${{ toInt(r.pos) <= 10 ? '700' : '400' }};
                            border: 1px solid #1a1a1a;
                        ">
                            ${{r.pos === '-' ? '' : r.pos}}
                        </div>
                    `).join('')}}
                    </div>
                </td>
            </tr>`;
    }});

    html += `
            </tbody>
        </table>
    </div>`;

    container.innerHTML = html;
}}

function renderSetups() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    // Grupujemy setupy per tor
    const byTrack = {{}};
    displayedData.forEach(race => {{
        const rd = race.race_data || {{}};
        const track = rd.track || 'Unknown';
        if (!byTrack[track]) byTrack[track] = [];

        // Szukamy setupu wyścigowego (Race)
        const raceSetup = (rd.setups || []).find(s =>
            s.session && s.session.toLowerCase().includes('race')
        ) || (rd.setups || [])[0];

        if (raceSetup) {{
            byTrack[track].push({{
                season: rd.season,
                race: rd.race,
                setup: raceSetup,
                weather: rd.weather || {{}},
                q1_time: rd.q1_time
            }});
        }}
    }});

    let html = `
    <div class="hero-section">
        <span class="hero-subtitle">SETUP ARCHIVE</span>
        <h2>RACE SETUPS</h2>
        <div class="hero-meta">
            <span>🔧 ${{Object.keys(byTrack).length}} UNIQUE TRACKS</span>
        </div>
    </div>
    <div class="setup-grid">`;

    Object.entries(byTrack).sort().forEach(([track, entries]) => {{
        const latest = entries[entries.length - 1];
        const s = latest.setup;
        const w = latest.weather;
        const q1w = w.q1 || {{}};

        html += `
        <div class="setup-card">
            <h3>${{track}}</h3>
            <div class="setup-values">
                <div class="setup-item">
                    <div class="setup-label">FW</div>
                    <div class="setup-val">${{s.fw || '-'}}</div>
                </div>
                <div class="setup-item">
                    <div class="setup-label">RW</div>
                    <div class="setup-val">${{s.rw || '-'}}</div>
                </div>
                <div class="setup-item">
                    <div class="setup-label">ENG</div>
                    <div class="setup-val">${{s.eng || '-'}}</div>
                </div>
                <div class="setup-item">
                    <div class="setup-label">BRA</div>
                    <div class="setup-val">${{s.bra || '-'}}</div>
                </div>
                <div class="setup-item">
                    <div class="setup-label">GEAR</div>
                    <div class="setup-val">${{s.gear || '-'}}</div>
                </div>
                <div class="setup-item">
                    <div class="setup-label">SUSP</div>
                    <div class="setup-val">${{s.susp || '-'}}</div>
                </div>
            </div>
            <div class="setup-meta">
                S${{latest.season}}R${{latest.race}} · ${{q1w.temp || '?'}}°C · ${{q1w.humidity || '?'}}%
                ${{entries.length > 1 ? ' · ' + entries.length + ' RACES AT THIS TRACK' : ''}}
            </div>
        </div>`;
    }});

    html += '</div>';
    document.getElementById('tab-setups').innerHTML = html;
}}

function renderFinances() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    const latestFin = displayedData[displayedData.length - 1]?.race_data?.finances || {{}};

    let html = `
    <div class="hero-section">
        <span class="hero-subtitle">BUDGET CONTROL</span>
        <h2>SEASON FINANCES</h2>
        <div class="hero-meta">
            <span>💰 BALANCE: <b class="${{latestFin.balance >= 0 ? 'val-positive' : 'val-negative'}}">${{formatMoney(latestFin.balance)}}</b></span>
            <span>📈 AVG PROFIT: ${{formatMoney(Math.round(displayedData.reduce((acc, d) => acc + (d.race_data?.finances?.total || 0), 0) / displayedData.length))}}</span>
        </div>
    </div>
    <div class="data-grid">`;

    for (let i = displayedData.length - 1; i >= 0; i--) {{
        const rd = displayedData[i].race_data || {{}};
        const fin = rd.finances || {{}};
        const txs = fin.transactions || [];

        const income = txs.filter(t => t.amount > 0).reduce((s, t) => s + t.amount, 0);
        const costs = txs.filter(t => t.amount < 0).reduce((s, t) => s + t.amount, 0);

        html += `
        <div class="data-card">
            <div class="data-card-header">
                <h3>${{rd.track || '?'}}</h3>
                <div class="tag">S${{rd.season}}R${{rd.race}}</div>
            </div>

            <div class="data-row">
                <span class="label">INCOME</span>
                <span class="value val-positive">${{formatMoney(income)}}</span>
            </div>
            <div class="data-row">
                <span class="label">COSTS</span>
                <span class="value val-negative">${{formatMoney(costs)}}</span>
            </div>
            <div class="data-row" style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
                <span class="label">RACE RESULT</span>
                <span class="value ${{fin.total >= 0 ? 'val-positive' : 'val-negative'}}" style="font-size: 1.2rem;">${{formatMoney(fin.total)}}</span>
            </div>
            <div class="data-row">
                <span class="label">BALANCE AFTER ROUND</span>
                <span class="value">${{formatMoney(fin.balance)}}</span>
            </div>
        </div>`;
    }}

    html += '</div>';
    document.getElementById('tab-finances').innerHTML = html;
}}

function renderDriver(latest) {{
    const raceWithProfile = getRaceWithProfileData();
    const rd = latest.race_data || {{}};
    const drv = raceWithProfile?.race_data?.driver || rd.driver || {{}};
    const dp = raceWithProfile?.driver_profile || latest.driver_profile || {{}};
    const driverAge = dp.age || drv.age || null;

    if (!drv.name && !dp.driName) {{
        document.getElementById('tab-driver').innerHTML =
            '<div class="empty-state"><h2>No driver data</h2></div>';
        return;
    }}

const stats = [
        {{ name: 'concentration', label: 'CONCENTRATION', value: drv.concentration }},
        {{ name: 'talent', label: 'TALENT', value: drv.talent }},
        {{ name: 'aggressiveness', label: 'AGGRESSION', value: drv.aggressiveness }},
        {{ name: 'experience', label: 'EXPERIENCE', value: drv.experience }},
        {{ name: 'technical_insight', label: 'TECHNICAL', value: drv.technical_insight }},
        {{ name: 'stamina', label: 'STAMINA', value: drv.stamina }},
        {{ name: 'charisma', label: 'CHARISMA', value: drv.charisma }},
        {{ name: 'motivation', label: 'MOTIVATION', value: drv.motivation }},
    ];

    let html = `
    <div class="hero-section">
        <span class="hero-subtitle">DRIVER PROFILE</span>
        <h2>${{drv.name || dp.driName || '?'}}</h2>
        <div class="hero-meta">
            <span>⭐ OVERALL: ${{drv.OA || dp.overall || '?'}}</span>
            <span>🎂 AGE: ${{driverAge !== null ? driverAge : '?'}}</span>
        </div>
    </div>`;

    html += '<div class="driver-stats">';
    stats.forEach(s => {{
        html += `
        <div class="stat-item">
            <div class="stat-name">${{s.label}}</div>
            <div class="stat-value ${{statClass(s.name, s.value)}}">${{s.value || '-'}}</div>
        </div>`;
    }});

    html += '</div>';

    // Dostawca opon
    const ts = rd.tyre_supplier || {{}};
    if (ts.name) {{
        html += `
        <div class="hero-section" style="margin-top: 4rem; padding: 2rem 0;">
            <span class="hero-subtitle">TECHNICAL PARTNER</span>
            <h2 style="font-size: 2.5rem;">${{ts.name}}</h2>
        </div>
        <div class="driver-stats">
            <div class="stat-item" style="border-top: 2px solid var(--accent-gold);"><div class="stat-name">PEAK TEMP</div><div class="stat-value">${{ts.peak_temp || '-'}}°C</div></div>
            <div class="stat-item" style="border-top: 2px solid var(--accent-gold);"><div class="stat-name">DRY PERF</div><div class="stat-value">${{ts.dry_perf || '-'}}</div></div>
            <div class="stat-item" style="border-top: 2px solid var(--accent-gold);"><div class="stat-name">WET PERF</div><div class="stat-value">${{ts.wet_perf || '-'}}</div></div>
            <div class="stat-item" style="border-top: 2px solid var(--accent-gold);"><div class="stat-name">DURABILITY</div><div class="stat-value">${{ts.durability || '-'}}</div></div>
            <div class="stat-item" style="border-top: 2px solid var(--accent-gold);"><div class="stat-name">WARMUP</div><div class="stat-value">${{ts.warmup || '-'}}</div></div>
        </div>`;
    }}

    document.getElementById('tab-driver').innerHTML = html;
}}

// Funkcja generująca link do GitHub Actions
function renderDeployButton() {{
    const container = document.getElementById('deployBtnContainer');
    if (!container) return;

    // Próba wykrycia repozytorium z URL (format: https://username.github.io/repo/)
    const pathParts = window.location.pathname.split('/').filter(p => p);
    let repoUrl = 'https://github.com/';

    if (window.location.hostname.includes('github.io')) {{
        const user = window.location.hostname.split('.')[0];
        const repo = pathParts[0] || '';
        repoUrl += `${{user}}/${{repo}}`;
    }} else {{
        // Fallback dla lokalnego developmentu
        repoUrl += 'user/repo';
    }}

    repoUrl += '/actions/workflows/fetch.yml';

    container.innerHTML = `
        <a href="${{repoUrl}}" target="_blank" class="deploy-btn">
            <span>🚀 FETCH GPRO DATA & DEPLOY</span>
        </a>`;
}}

// Start!
setupTabs();
render();

window.onload = () => {{
    setupTabs();
    render();
    renderDeployButton();
}};
</script>
</body>
</html>'''

    return html


# ============================================================
# GŁÓWNA LOGIKA SKRYPTU
# ============================================================

def generate_dashboard():
    """
    Główna funkcja generująca dashboard.

    Mini-lekcja: To jest entry point skryptu.
    Kolejność jest ważna:
    1. Wczytaj dane
    2. Wygeneruj HTML
    3. Zapisz plik
    """
    print("=" * 60)
    print("GPRO Dashboard Generator")
    print("=" * 60)

    # 1. Wczytaj dane
    print("\n1. Wczytywanie danych...")
    race_data = load_race_data()
    prediction_data = load_prediction()
    calendar_data = load_calendar()
    current_context_data = load_current_context()

    # 2. Wygeneruj HTML
    print("\n2. Generowanie HTML...")
    html = generate_html(race_data, prediction_data, calendar_data, current_context_data)

    # 3. Zapisz plik
    print(f"\n3. Zapisywanie do {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n" + "=" * 60)
    print("Gotowe!")
    print(f"Dashboard zapisany do: {OUTPUT_FILE}")
    print(f"  - Dane wyścigowe: {len(race_data)} plików")
    print(f"  - Predykcja: {'Tak' if prediction_data else 'Nie (uruchom predictor.py)'}")
    print(f"  - Kalendarz: {'Tak' if calendar_data else 'Nie'}")
    print("=" * 60)


if __name__ == "__main__":
    generate_dashboard()
