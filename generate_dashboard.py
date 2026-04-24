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
           SUMMARY CARDS
           ========================================================== */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1px;
            padding: 1px;
            background: var(--border-color);
            margin: 0 2rem 2rem 2rem;
        }}

        .summary-card {{
            background: var(--bg-primary);
            padding: 2rem;
            transition: background 0.3s;
            border-bottom: 1px solid var(--border-color);
        }}

        .summary-card:hover {{
            background: var(--bg-card);
        }}

        .summary-card .label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 1rem;
        }}

        .summary-card .value {{
            font-family: var(--font-display);
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            line-height: 1;
            color: var(--text-primary);
        }}

        .summary-card .value-small {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            line-height: 1;
        }}

        .summary-card .sub {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
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
            gap: 1px;
            background: #202020;
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
           SEKCJA KIEROWCY
           ========================================================== */
        .driver-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1px;
            background: #202020;
        }}

        .stat-item {{
            background: #000000;
            border: 1px solid #181818;
            padding: 1rem;
            text-align: center;
        }}

        .stat-item .stat-name {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.5rem;
        }}

        .stat-item .stat-value {{
            font-family: var(--font-mono);
            font-size: 1.5rem;
            font-weight: 700;
        }}

        /* Kolory dla statystyk kierowcy */
        .stat-good {{ color: #FFC000; }}
        .stat-ok {{ color: #FFCE3E; }}
        .stat-bad {{ color: var(--accent-red); }}

        /* ==========================================================
           SEKCJA FINANSÓW
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
            padding: 1.25rem 1.5rem;
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
           SEKCJA REKOMENDACJI (zakładka Następny wyścig)
           Mini-lekcja: BEM-like nazewnictwo (.rec-*) oddziela style
           rekomendacji od reszty dashboardu - łatwiej utrzymywać.
           ========================================================== */
        .rec-header {{
            background: #000000;
            border-bottom: 1px solid #202020;
            padding: 2rem 0;
            margin-bottom: 1.5rem;
        }}

        .rec-header h2 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .rec-header .rec-subtitle {{
            color: var(--text-muted);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
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
        }}

        .rec-card .rec-value {{
            font-family: var(--font-mono);
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent-blue);
        }}

        .rec-card .rec-note {{
            font-size: 0.75rem;
            color: var(--text-muted);
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
           PRAKTYKA - Binary Search Setup
           ========================================================== */
        .practice-header {{
            background: var(--bg-primary);
            border-bottom: 2px solid var(--accent-gold);
            padding: 3rem 0;
            margin-bottom: 2rem;
        }}

        .practice-header h2 {{
            font-size: 3rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            margin-bottom: 1rem;
            line-height: 1;
        }}

        .practice-header .track-info {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

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
            align-items: center;
            min-width: 80px;
        }}

        .timeline-dot {{
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 700;
            background: #181818;
            color: var(--text-muted);
            border: 1px solid #202020;
            font-family: var(--font-mono);
        }}

        .timeline-step.active .timeline-dot {{
            background: #FFC000;
            border-color: #FFC000;
            color: #000000;
        }}

        .timeline-step.completed .timeline-dot {{
            background: #917300;
            border-color: #917300;
            color: #000000;
        }}

        .timeline-step.current .timeline-dot {{
            background: #FFC000;
            border-color: #FFC000;
            color: #000000;
            animation: pulse 1.5s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .timeline-label {{
            font-size: 0.55rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .lap-card {{
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            margin-bottom: 1px;
            transition: background 0.3s;
        }}

        .lap-card:hover {{
            background: var(--bg-card);
        }}

        .lap-card.current {{
            border-color: #FFC000;
            border-left: 3px solid #FFC000;
        }}

        .lap-card.done {{
            opacity: 0.5;
        }}

        .lap-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .lap-header h3 {{
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        .lap-badge {{
            font-size: 0.6rem;
            padding: 0.2rem 0.5rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .lap-badge.next {{
            background: #FFC000;
            color: #000000;
        }}

        .lap-badge.done {{
            background: #917300;
            color: #000000;
        }}

        .lap-badge.pending {{
            background: #202020;
            color: var(--text-muted);
        }}

        .lap-setup {{
            display: flex;
            flex-wrap: wrap;
            gap: 1px;
            margin: 1rem 0;
            background: #202020;
        }}

        .setup-chip {{
            background: #181818;
            padding: 0.5rem 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        .setup-chip .label {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .setup-chip .value {{
            font-family: var(--font-mono);
            font-weight: 700;
            color: #FFC000;
            font-size: 0.95rem;
        }}

        .lap-instruction {{
            background: rgba(255, 192, 0, 0.06);
            border-left: 2px solid #FFC000;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .lap-instruction .instruction {{
            font-size: 0.85rem;
            font-weight: 700;
            color: #FFC000;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .lap-instruction .note {{
            font-size: 0.72rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .binary-search-visual {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: #181818;
            border-left: 2px solid #202020;
        }}

        .search-range {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--text-muted);
            text-align: center;
        }}

        .search-arrow {{
            text-align: center;
            color: #FFC000;
            font-size: 0.75rem;
        }}

        .session-summary {{
            background: #000000;
            border: 1px solid #202020;
            border-left: 3px solid #FFC000;
            padding: 1.25rem;
            margin-top: 1px;
        }}

        .session-summary h3 {{
            font-size: 0.7rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #FFC000;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        .next-up {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            background: #181818;
            border-left: 2px solid #FFC000;
            margin-top: 0.75rem;
        }}

        .next-up .icon {{
            font-size: 1.2rem;
        }}

        .next-up .label {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        .next-up .value {{
            font-weight: 700;
            color: #FFC000;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.82rem;
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
    <div class="header-info" id="headerInfo">Ładowanie...</div>
</div>

<!-- Karty podsumowania (Main) -->
<div id="mainSummaryContainer">
    <div class="summary-grid" id="summaryGrid"></div>
</div>

<!-- Zakładki -->
<div class="tabs" id="tabsNav">
    <button class="tab-btn active" data-tab="overview">Przegląd</button>
    <button class="tab-btn" data-tab="nextrace">Następny wyścig</button>
    <button class="tab-btn" data-tab="practice">Praktyka</button>
    <button class="tab-btn" data-tab="car">Bolid</button>
    <button class="tab-btn" data-tab="results">Wyniki</button>
    <button class="tab-btn" data-tab="setups">Setupy</button>
    <button class="tab-btn" data-tab="fuel">Paliwo & Opony</button>
    <button class="tab-btn" data-tab="finances">Finanse</button>
    <button class="tab-btn" data-tab="driver">Kierowca</button>
</div>

<!-- Zawartość zakładek -->
<div class="tab-content active" id="tab-overview"></div>
<div class="tab-content" id="tab-nextrace"></div>
<div class="tab-content" id="tab-practice"></div>
<div class="tab-content" id="tab-car"></div>
<div class="tab-content" id="tab-results"></div>
<div class="tab-content" id="tab-setups"></div>
<div class="tab-content" id="tab-fuel"></div>
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
document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        // Dezaktywuj wszystkie zakładki
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Aktywuj klikniętą
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.getElementById('tab-' + tabId).classList.add('active');

        // Hide main summary grid if Overview is selected
        const mainSummary = document.getElementById('mainSummaryContainer');
        if (['overview', 'nextrace', 'practice', 'car'].includes(tabId)) {{
            mainSummary.style.display = 'none';
        }} else {{
            mainSummary.style.display = 'block';
        }}
    }});
}});

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

function isPendingSeasonMode() {{
    const active = getCurrentContext();
    const latest = getLatestRace()?.race_data || {{}};
    const activeSeason = toInt(active?.season);
    const latestSeason = toInt(latest?.season);
    if (activeSeason === null) return false;
    if (latestSeason === null) return true;
    if (activeSeason > latestSeason) return true;
    return getDisplayedRaceData().length === 0;
}}

function renderSeasonEmptyState(tabId, title, activeContext, lastCompleted, description) {{
    const container = document.getElementById(tabId);
    if (!container) return;
    const lastText = lastCompleted ? `Ostatni ukończony wyścig: S${{lastCompleted.season || '?'}}R${{lastCompleted.race || '?'}} · ${{lastCompleted.track || 'Nieznany tor'}}.` : '';
    container.innerHTML = `
        <div class="empty-state">
            <h2>${{title}}</h2>
            <p>Aktywny sezon z API: <strong>S${{activeContext?.season || '?'}}R${{activeContext?.race || '?'}} · ${{activeContext?.track || 'Nieznany tor'}}</strong></p>
            <p style="margin-top:0.75rem">${{description}}</p>
            <p style="margin-top:0.75rem;color:var(--text-secondary)">${{lastText}}</p>
        </div>`;
}}

function renderPendingSeasonOverview(activeContext) {{
    const lastCompleted = getLatestRace()?.race_data || null;
    document.getElementById('headerInfo').textContent =
        `Sezon ${{activeContext?.season || '?'}} · Wyścig ${{activeContext?.race || '?'}} · ${{activeContext?.track || 'Nieznany tor'}} · Oczekiwanie na pierwszy wyścig sezonu`;

    const cards = [
        {{ label: 'Aktywny sezon', value: `S${{activeContext?.season || '?'}}R${{activeContext?.race || '?'}}`, sub: activeContext?.track || 'Nieznany tor' }},
        {{ label: 'Status', value: 'Nowy sezon', sub: 'Kontekst pobrany z Office + Calendar API' }},
        {{ label: 'Ostatni ukończony', value: lastCompleted ? `S${{lastCompleted.season || '?'}}R${{lastCompleted.race || '?'}}` : 'Brak', sub: lastCompleted?.track || 'Brak danych' }},
        {{ label: 'Rekomendacje', value: PREDICTION_DATA ? 'Gotowe' : 'Brak', sub: 'Sprawdź zakładkę Następny wyścig' }},
    ];

    document.getElementById('summaryGrid').innerHTML = cards.map(c => `
        <div class="summary-card">
            <div class="label">${{c.label}}</div>
            <div class="value">${{c.value}}</div>
            <div class="sub">${{c.sub}}</div>
        </div>`).join('');

    renderSeasonEmptyState('tab-results', 'Wyniki sezonu', activeContext, lastCompleted, 'Dane historyczne dla aktywnego sezonu pojawią się po ukończeniu pierwszego wyścigu.');
    renderSeasonEmptyState('tab-setups', 'Setupy sezonu', activeContext, lastCompleted, 'Setupy historyczne dla tego sezonu będą dostępne po zapisaniu pierwszego wyścigu przez fetcher.');
    renderSeasonEmptyState('tab-fuel', 'Paliwo sezonu', activeContext, lastCompleted, 'Strategie paliwowe dla aktywnego sezonu pojawią się po zakończeniu pierwszego wyścigu.');
    renderSeasonEmptyState('tab-finances', 'Finanse sezonu', activeContext, lastCompleted, 'Finanse sezonu będą widoczne po pierwszym zapisanym wyścigu.');
    renderSeasonEmptyState('tab-driver', 'Kierowca sezonu', activeContext, lastCompleted, 'Profil kierowcy w panelu historycznym będzie zasilony po zapisaniu wyścigu sezonu.');
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
                `Prediction.json: ${{predTrack || 'Nieznany tor'}} (S${{predSeason ?? '?'}} R${{predRace ?? '?'}}) · ` +
                `Aktualny: ${{ccTrack}} (S${{ccSeason}} R${{ccRace}})`;
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
    // Renderuj podstawowe zakładki
    renderOverview();
    renderNextRace();
    renderPractice();
    renderCar();

    const activeContext = getCurrentContext();
    const displayedData = getDisplayedRaceData();

    if ((!displayedData || displayedData.length === 0) && activeContext && isPendingSeasonMode()) {{
        renderPendingSeasonOverview(activeContext);
        return;
    }}

    if (!displayedData || displayedData.length === 0) {{
        document.getElementById('summaryGrid').innerHTML = '';
        document.getElementById('tab-results').innerHTML = `
            <div class="empty-state">
                <h2>Brak danych</h2>
                <p>Uruchom fetcher po wyścigu, żeby zebrać dane:</p>
                <p style="margin-top:1rem"><code>python gpro_fetcher.py</code></p>
            </div>`;
        return;
    }}

    const latest = displayedData[displayedData.length - 1];
    const rd = latest.race_data || {{}};

    // Nagłówek
    document.getElementById('headerInfo').textContent =
        `Sezon ${{rd.season}} · Wyścig ${{rd.race}} · ${{rd.track}} · Dane sezonu: ${{displayedData.length}} wyścigów`;

    // Karty podsumowania
    renderSummary(latest);

    // Pozostałe zakładki
    renderResults();
    renderSetups();
    renderFuel();
    renderFinances();
    renderDriver(latest);
}}

// ==========================================================
// ZAKŁADKA: PRZEGLĄD (Executive Summary)
// ==========================================================
function renderOverview() {{
    const container = document.getElementById('tab-overview');
    const latest = getLatestRace();
    const nextRace = getCalendarNextRace();
    const pred = PREDICTION_DATA;

    if (!latest && !nextRace) {{
        container.innerHTML = '<div class="empty-state"><h2>Brak danych do przeglądu</h2></div>';
        return;
    }}

    const rd = latest?.race_data || {{}};
    const dp = latest?.driver_profile || {{}};
    const cs = latest?.car_status || {{}};

    let html = '';

    // 1. Sekcja: Następny wyścig (Hero-like)
    if (nextRace) {{
        html += `
        <div class="rec-header" style="border-bottom: 2px solid var(--accent-gold); margin-bottom: 2rem;">
            <div class="rec-subtitle">NASTĘPNY WYŚCIG</div>
            <h2 style="font-size: 3.5rem; line-height: 1;">${{nextRace.track || 'Nieznany tor'}}</h2>
            <div class="rec-subtitle">Sezon ${{nextRace.season}} · Wyścig ${{nextRace.race}} · ${{nextRace.total_laps || 72}} OKRĄŻEŃ</div>
            ${{pred ? `<div style="margin-top: 1rem;"><span class="session-badge" style="background: var(--accent-gold); color: #000; font-weight: 700;">REKOMENDACJE GOTOWE</span></div>` : ''}}
        </div>`;
    }}

    // 2. Grid z kluczowymi informacjami
    html += `<div class="summary-grid" style="margin-left: 0; margin-right: 0;">`;

    // FINANSE
    const cash = dp.cash || rd.finances?.balance || 0;
    html += `
    <div class="summary-card">
        <div class="label">FINANSE</div>
        <div class="value" style="color: ${{cash >= 0 ? 'var(--accent-gold)' : 'var(--accent-red)'}}">
            ${{formatMoney(cash)}}
        </div>
        <div class="sub">SALDO KONTA</div>
        ${{rd.finances ? `<div class="rec-row" style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 0.5rem;"><span class="rec-label">Ostatni wyścig</span><span class="${{rd.finances.total >= 0 ? 'val-positive' : 'val-negative'}}">${{formatMoney(rd.finances.total)}}</span></div>` : ''}}
    </div>`;

    // KIEROWCA
    if (rd.driver || dp.driName) {{
        const drvName = dp.driName || rd.driver.name;
        const drvOA = dp.overall || rd.driver.OA;
        html += `
        <div class="summary-card">
            <div class="label">KIEROWCA</div>
            <div class="value-small">${{drvName}}</div>
            <div class="sub">OVERALL: ${{drvOA}}</div>
            <div class="rec-grid" style="grid-template-columns: 1fr 1fr; gap: 1px; margin-top: 1rem; background: var(--border-color); padding: 1px;">
                <div class="stat-item" style="background: var(--bg-primary);">
                    <div class="stat-name">Konc</div>
                    <div class="stat-value" style="font-size: 1.2rem;">${{dp.concentration || rd.driver.concentration}}</div>
                </div>
                <div class="stat-item" style="background: var(--bg-primary);">
                    <div class="stat-name">Talent</div>
                    <div class="stat-value" style="font-size: 1.2rem;">${{dp.talent || rd.driver.talent}}</div>
                </div>
            </div>
        </div>`;
    }}

    // BOLID (Stan ogólny)
    if (cs.lvlEngine || rd.car_parts) {{
        const parts = ['Chassis', 'Engine', 'FWing', 'RWing', 'Underbody', 'Sidepods', 'Cooling', 'Gear', 'Brakes', 'Susp', 'Electronics'];
        let totalWear = 0;
        let criticalParts = 0;

        parts.forEach(p => {{
            const wear = cs['usa' + p] || rd.car_parts?.[p.toLowerCase()]?.finish_wear || 0;
            totalWear += wear;
            if (wear > 70) criticalParts++;
        }});

        const avgWear = Math.round(totalWear / parts.length);

        html += `
        <div class="summary-card">
            <div class="label">BOLID</div>
            <div class="value" style="color: ${{criticalParts > 0 ? 'var(--accent-red)' : 'var(--text-primary)'}}">
                ${{avgWear}}%
            </div>
            <div class="sub">ŚREDNIE ZUŻYCIE</div>
            <div class="sub" style="margin-top: 0.5rem;">${{criticalParts > 0 ? `<span style="color: var(--accent-red)">⚠ ${{criticalParts}} CZĘŚCI WYMAGA UWAGI</span>` : 'STAN DOBRY'}}</div>
            <div style="margin-top: 1rem;">
                <button class="tab-btn" data-tab="car" style="padding: 0.5rem 1rem; border: 1px solid var(--accent-gold); font-size: 0.6rem; color: var(--accent-gold); height: auto; line-height: 1;">SZCZEGÓŁY BOLIDU &raquo;</button>
            </div>
        </div>`;
    }}

    html += `</div>`; // zamknięcie summary-grid

    container.innerHTML = html;

    // Re-attach listener for the button inside overview
    container.querySelector('[data-tab="car"]')?.addEventListener('click', () => {{
        document.querySelector('.tab-btn[data-tab="car"]').click();
    }});
}}

function renderSummary(latest) {{
    const rd = latest.race_data || {{}};
    const fin = rd.finances || {{}};

    const cards = [
        {{ label: 'Pozycja Q', value: `P${{rd.q1_pos || '?'}}`, sub: rd.q1_time || '' }},
        {{ label: 'Pozycja wyścigu', value: `—`, sub: 'Sprawdź zakładkę Wyniki' }},
        {{ label: 'Bilans', value: formatMoney(fin.balance), sub: `Wyścig: ${{formatMoney(fin.total)}}` }},
        {{ label: 'Kierowca', value: (rd.driver || {{}}).name || '?', sub: `OA: ${{(rd.driver || {{}}).OA || '?'}}` }},
    ];

    // Spróbuj znaleźć pozycję z race_summary
    const summary = latest.race_summary;
    if (summary && summary.results && summary.results.length > 0) {{
        // Szukamy naszego wyniku - porównujemy nazwę managera z driver_profile
        const dp = latest.driver_profile || {{}};
        const myName = dp.manName || dp.manager || '';
        let myResult = null;
        if (myName) {{
            myResult = summary.results.find(r => r.manager === myName);
        }}
        // Fallback: gracz z pozycją 1 lub gap 0.000s (lider nie ma luki)
        if (!myResult) {{
            myResult = summary.results.find(r => r.gap === '' || r.gap === '0.000s' || r.gap === '+0.000s');
        }}
        if (myResult) {{
            cards[1].value = `P${{myResult.position || '?'}}`;
            cards[1].sub = myResult.race_time || '';
        }}
    }}

    document.getElementById('summaryGrid').innerHTML = cards.map(c => `
        <div class="summary-card">
            <div class="label">${{c.label}}</div>
            <div class="value">${{c.value}}</div>
            <div class="sub">${{c.sub}}</div>
        </div>
    `).join('');
}}

// ==========================================================
// ZAKŁADKA: NASTĘPNY WYŚCIG (rekomendacje z predictor.py)
// Mini-lekcja: Ta funkcja używa danych z predictor.py aby
// pokazać dokładne rekomendacje setupu, paliwa i kierowcy.
// ==========================================================
function renderNextRace() {{
    const container = document.getElementById('tab-nextrace');

    // Jeśli mamy dane predykcji, używamy ich
    if (PREDICTION_DATA) {{
        renderPrediction(container);
        return;
    }}

    // Fallback: jeśli brak predykcji, pokaż komunikat
    container.innerHTML = `
        <div class="empty-state">
            <h2>Brak rekomendacji</h2>
            <p>Uruchom predictor.py żeby wygenerować rekomendacje:</p>
            <p style="margin-top:1rem"><code>python predictor.py</code></p>
        </div>`;
}}

function renderPrediction(container) {{
    const pred = PREDICTION_DATA;
    const predictionContext = resolvePredictionContext(pred);
    const nextRace = predictionContext.nextRace || pred.next_race || {{}};
    const isStalePrediction = predictionContext.isStale;
    const staleReason = predictionContext.staleReason || '';
    const confidence = pred.confidence || 'unknown';
    const confidenceReason = pred.confidence_reason || '';
    const driverMargin = pred.driver_margin || {{}};
    const base = pred.base || {{}};
    const fuelStrategy = pred.fuel_strategy || {{}};
    const tyreInfo = pred.tyres_info || {{}};
    const notes = pred.notes || [];
    const sessions = pred.sessions || {{}};

    let html = '';

    if (isStalePrediction) {{
        container.innerHTML = `
            <div class="rec-header">
                <h2>${{nextRace.track || 'Nieznany tor'}}</h2>
                <div class="rec-subtitle">Sezon ${{nextRace.season || '?'}} · Wyścig ${{nextRace.race || '?'}}${{nextRace.total_laps ? ` · ${{nextRace.total_laps}} okrążeń` : ''}}</div>
                <div class="lap-instruction" style="margin-top: 1rem;">
                    <div class="instruction">Wykryto nieaktualną predykcję</div>
                    <div class="note">${{staleReason}}</div>
                    <div class="note" style="margin-top: 0.5rem;">Uruchom <code>python predictor.py</code> aby odświeżyć.</div>
                </div>
            </div>`;
        return;
    }}

    // =============================================
    // 1. NAGŁÓWEK (Lamborghini Impact)
    // =============================================
    html += `
    <div class="rec-header" style="text-align: center; border-bottom: 2px solid var(--accent-gold); padding-bottom: 3rem;">
        <div class="rec-subtitle" style="font-size: 1rem; color: var(--accent-gold); margin-bottom: 1rem;">PLAN WYŚCIGOWY</div>
        <h2 style="font-size: 5rem; line-height: 0.9; margin-bottom: 1.5rem;">${{nextRace.track || 'Nieznany tor'}}</h2>
        <div class="rec-subtitle" style="font-size: 1.2rem; letter-spacing: 0.3em;">S${{nextRace.season}}R${{nextRace.race}} · ${{nextRace.total_laps || 72}} OKRĄŻEŃ</div>

        <div style="max-width: 600px; margin: 2rem auto 0 auto;">
            <div class="confidence-bar" style="height: 4px;">
                <div class="confidence-fill ${{confidence}}"></div>
            </div>
            <div class="rec-subtitle" style="margin-top: 0.5rem; font-size: 0.7rem;">PEWNOŚĆ: ${{confidence.toUpperCase()}} — ${{confidenceReason}}</div>
        </div>
    </div>`;

    // =============================================
    // 2. SESJE: Practice, Q1, Q2, Race
    // =============================================
    const sessionOrder = ['practice', 'q1', 'q2', 'race'];
    const sessionNames = {{ practice: 'Practice', q1: 'Q1', q2: 'Q2', race: 'Race' }};

    sessionOrder.forEach(sessionKey => {{
        const session = sessions[sessionKey] || {{}};
        if (!session.setup) return;

        const s = session.setup;
        const sessionName = sessionNames[sessionKey];

        html += `<div class="session-card ${{sessionKey}}">`;
        html += `<div class="session-header">`;
        html += `<h4>${{sessionName}}</h4>`;
        html += `<span class="session-badge">${{session.tyres || '?'}} tyres</span>`;
        html += `</div>`;

        html += `<div class="session-meta">`;
        html += `<span>🌡️ ${{session.temp || '?'}}°C</span>`;
        html += `<span>🌧️ ${{session.weather || 'dry'}}</span>`;
        if (session.fuel_start) {{
            html += `<span>⛽ ${{session.fuel_start}}L start</span>`;
        }}
        html += `</div>`;

        html += `<div class="session-setup">`;
        ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
            html += `<div class="setup-part"><span class="label">${{key.toUpperCase()}}</span> <span class="value">${{s[key] || 0}}</span></div>`;
        }});
        html += `</div>`;

        if (session.note) {{
            html += `<div class="session-note">${{session.note}}</div>`;
        }}

        // Fuel strategy for race
        if (sessionKey === 'race' && session.fuel_strategy) {{
            const fs = session.fuel_strategy;
            html += `<div class="fuel-stint-bar">`;
            (fs.stints || []).forEach((fuel, i) => {{
                if (i > 0) html += `<span class="arrow">→</span>`;
                html += `<span class="stint">${{fuel}}L</span>`;
            }});
            html += `<span class="arrow">→</span>`;
            html += `<span class="stint" style="background:var(--accent-blue)">META</span>`;
            html += `</div>`;
            html += `<div class="session-meta" style="margin-top:0.25rem"><span>⛽ ${{fs.pits || 0}} pit stops</span></div>`;
        }}

        html += `</div>`;
    }});

    // =============================================
    // 3. STRATEGIA PALIWOWA & SETUP SUMMARY
    // =============================================
    html += `<div class="rec-grid" style="margin-top: 1rem;">`;

    // SETUP Q2
    html += `<div class="rec-card"><h3>SETUP Q2</h3>`;
    html += `<div class="setup-values">`;
    const q2 = pred.setup_q2 || {{}};
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = q2[key] || 0;
        const baseVal = (base.setup || base)[key] || 0;
        const diff = val - baseVal;
        const diffClass = diff > 0 ? 'positive' : (diff < 0 ? 'negative' : '');
        const diffSign = diff > 0 ? '+' : '';
        html += `
        <div class="setup-item">
            <div class="setup-label">${{key.toUpperCase()}}</div>
            <div class="setup-val">${{val}}</div>
            <span class="adjustment-badge ${{diffClass}}">${{diffSign}}${{diff}}</span>
        </div>`;
    }});
    html += `</div>`;
    html += `<div class="setup-meta" style="margin-top: 1rem;">Baza: ${{base.track || '?'}} (${{base.temp || '?'}}°C) → Q2: ${{q2.temp || '?'}}°C</div>`;
    html += `</div>`;

    // SETUP RACE
    html += `<div class="rec-card"><h3>SETUP RACE</h3>`;
    html += `<div class="setup-values">`;
    const race = pred.setup_race || {{}};
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = race[key] || 0;
        const baseVal = (base.setup || base)[key] || 0;
        const diff = val - baseVal;
        const diffClass = diff > 0 ? 'positive' : (diff < 0 ? 'negative' : '');
        const diffSign = diff > 0 ? '+' : '';
        html += `
        <div class="setup-item">
            <div class="setup-label">${{key.toUpperCase()}}</div>
            <div class="setup-val" style="color: var(--accent-gold);">${{val}}</div>
            <span class="adjustment-badge ${{diffClass}}">${{diffSign}}${{diff}}</span>
        </div>`;
    }});
    html += `</div>`;
    html += `<div class="setup-meta" style="margin-top: 1rem;">Race Temp: ${{race.temp || '?'}}°C</div>`;
    html += `</div>`;

    html += `</div>`; // zamknięcie rec-grid

    html += `<div class="rec-grid" style="margin-top:1rem">`;

    // =============================================
    // 4. STRATEGIA PALIWOWA
    // =============================================
    html += `<div class="rec-card"><h3>Paliwo</h3>`;
    const fuelPerLap = fuelStrategy.fuel_per_lap || 0;
    const totalLaps = nextRace.total_laps || 72;
    const recommended = fuelStrategy.recommended || {{}};
    const alternative = fuelStrategy.alternative || {{}};

    html += `<div class="rec-row"><span class="rec-label">Zużycie</span><span class="rec-value">~${{fuelPerLap}} L/lap</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Okrążenia</span><span>${{totalLaps}}</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Pit stopy</span><span class="rec-value">${{recommended.pits || 0}}</span></div>`;

    // Rekomendowana strategia
    if (recommended.stints && recommended.stints.length > 0) {{
        html += `<div class="fuel-strategy">`;
        html += `<div class="strategy-name">Rekomendowana:</div>`;
        html += `<div class="strategy-visual">`;
        recommended.stints.forEach((fuel, i) => {{
            if (i > 0) html += `<span class="arrow">→</span>`;
            html += `<div class="pit-stop">${{fuel}}L</div>`;
        }});
        html += `<span class="arrow">→</span>`;
        html += `<div class="finish">META</div>`;
        html += `</div>`;
        html += `</div>`;
    }}

    // Alternatywna strategia
    if (alternative.stints && alternative.stints.length > 0 && alternative.pits !== recommended.pits) {{
        html += `<div class="fuel-strategy" style="margin-top:0.5rem">`;
        html += `<div class="strategy-name">Alternatywa (${{alternative.pits}} pitty):</div>`;
        html += `<div class="strategy-visual">`;
        alternative.stints.forEach((fuel, i) => {{
            if (i > 0) html += `<span class="arrow">→</span>`;
            html += `<div class="pit-stop">${{fuel}}L</div>`;
        }});
        html += `<span class="arrow">→</span>`;
        html += `<div class="finish">META</div>`;
        html += `</div>`;
        html += `</div>`;
    }}

    html += `</div>`;

    // =============================================
    // 4.5. STRATEGIA OPONOWA
    // =============================================
    html += `<div class="rec-card"><h3>Opony</h3>`;
    const tyreStrategy = pred.tyre_strategy || {{}};
    const estTyreLife = tyreStrategy.est_tyre_life_laps || 0;
    const lapsOnFuel = tyreStrategy.laps_on_fuel || 0;
    const bottleneck = tyreStrategy.bottleneck || 'unknown';
    const bottleneckExpl = tyreStrategy.bottleneck_explanation || '';

    html += `<div class="rec-row"><span class="rec-label">Żywotność</span><span class="rec-value">~${{estTyreLife}} okr</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Okrążeń na baku</span><span>~${{lapsOnFuel}}</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">Bottleneck</span><span class="rec-value">${{bottleneck.toUpperCase()}}</span></div>`;
    html += `<p style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-secondary)">${{bottleneckExpl}}</p>`;
    html += `</div>`;

    // =============================================
    // 5. MARGINES KIEROWCY
    // =============================================
    html += `<div class="rec-card"><h3>Kierowca</h3>`;
    const ma = driverMargin.MA || 0;
    const halfMa = driverMargin.half_MA || 0;
    const note = driverMargin.note || '';

    html += `<div class="rec-row"><span class="rec-label">Margines</span><span class="rec-value">±${{halfMa}} pkt</span></div>`;
    html += `<div class="rec-row"><span class="rec-label">MA</span><span>${{ma}}</span></div>`;
    html += `<p style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-secondary)">${{note}}</p>`;
    html += `</div>`;

    html += `</div>`; // zamknięcie rec-grid

    // =============================================
    // 6. PLAN TRENINGOWY
    // =============================================
    html += `<div class="rec-card" style="margin-top:1rem; border-left: 4px solid var(--accent-gold);"><h3>Plan treningowy</h3>`;
    const practicePlan = pred.practice_plan || {{}};
    const laps = practicePlan.laps || [];
    const priorityNote = practicePlan.priority_note || '';

    html += `<div class="notes-list">`;
    html += `<ul>`;
    laps.forEach(lap => {{
        html += `<li><strong>Lap ${{lap.lap}}:</strong> ${{lap.action}} <span style="color:var(--text-muted)">${{lap.note}}</span></li>`;
    }});
    html += `</ul>`;
    html += `</div>`;
    html += `<p style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-secondary)">${{priorityNote}}</p>`;
    html += `</div>`;

    // =============================================
    // 7. NOTATKI
    // =============================================
    if (notes && notes.length > 0) {{
        html += `<div class="rec-card" style="margin-top:1rem; background: var(--bg-card);"><h3>Notatki</h3>`;
        html += `<div class="notes-list">`;
        html += `<ul>`;
        notes.forEach(note => {{
            html += `<li>${{note}}</li>`;
        }});
        html += `</ul>`;
        html += `</div>`;
        html += `</div>`;
    }}

    container.innerHTML = html;
}}

// ==========================================================
// ZAKŁADKA: PRAKTYKA - Binary Search Setup
// Mini-lekcja: Pokazuje rekomendowany setup per lap praktyki
// zgodnie z binary search methodology z Calc.
// ==========================================================
function renderPractice() {{
    const container = document.getElementById('tab-practice');
    
    if (!PREDICTION_DATA) {{
        container.innerHTML = `
            <div class="empty-state">
                <h2>Brak danych predykcji</h2>
                <p>Uruchom predictor.py żeby wygenerować setup:</p>
                <p style="margin-top:1rem"><code>python predictor.py</code></p>
            </div>`;
        return;
    }}
    
    const pred = PREDICTION_DATA;
    const predictionContext = resolvePredictionContext(pred);
    if (predictionContext.isStale) {{
        const nextRace = predictionContext.nextRace || {{}};
        container.innerHTML = `
            <div class="empty-state">
                <h2>Practice map wymaga odświeżenia predykcji</h2>
                <p>${{predictionContext.staleReason}}</p>
                <p style="margin-top:1rem">Aktualny następny wyścig: <strong>${{nextRace.track || 'Nieznany tor'}}</strong> (Sezon ${{nextRace.season || '?'}}, Wyścig ${{nextRace.race || '?'}})</p>
                <p style="margin-top:1rem"><code>python predictor.py</code></p>
            </div>`;
        return;
    }}
    const nextRace = predictionContext.nextRace || pred.next_race || {{}};
    const driverMargin = pred.driver_margin || {{}};
    const practiceSetup = pred.sessions?.practice?.setup || pred.setup_practice || {{}};
    const practiceTemp = pred.sessions?.practice?.temp || pred.setup_practice?.temp || 20;
    const practicePlan = pred.practice_plan || {{}};
    const laps = practicePlan.laps || [];
    
    // Get laps completed and comments from localStorage
    let practiceState = {{ lapsCompleted: 0, comments: {{}} }};
    try {{
        const saved = localStorage.getItem('gpro_practice_state');
        if (saved) {{
            practiceState = JSON.parse(saved);
        }}
    }} catch (e) {{}}
    
    const lapsCompleted = practiceState.lapsCompleted || 0;
    const comments = practiceState.comments || {{}};
    const totalLaps = 8;
    const currentLap = lapsCompleted + 1;
    
    // Calculate current setup based on comments
    let currentSetup = {{...practiceSetup}};
    
    const commentCorrections = {{
        'grip': {{fw: +20, rw: +20}},
        'unstable': {{fw: +30, rw: +30}},
        'understeer': {{fw: +15}},
        'oversteer': {{rw: +15}},
        'too much front': {{fw: -20}},
        'too much rear': {{rw: -20}},
        'engine power': {{eng: +20}},
        'engine feels weak': {{eng: +25}},
        'rigid': {{susp: -20}},
        'too soft': {{susp: +20}},
        'not effective': {{bra: +20}},
        'top speed': {{gear: +15}},
    }};
    
    const satisfiedWords = ['satisfied', 'happy', 'perfect'];
    
    // Apply corrections from stored comments
    for (let lapNum = 1; lapNum <= lapsCompleted; lapNum++) {{
        const comment = comments[lapNum] || '';
        if (!comment) continue;
        const normalized = comment.toLowerCase();
        
        let isSatisfied = false;
        for (const word of satisfiedWords) {{
            if (normalized.includes(word)) {{ isSatisfied = true; break; }}
        }}
        if (isSatisfied) continue;
        
        for (const [keyword, corrections] of Object.entries(commentCorrections)) {{
            if (normalized.includes(keyword)) {{
                for (const [setting, change] of Object.entries(corrections)) {{
                    const multiplier = halfMa > 60 ? 1.0 : 0.7;
                    currentSetup[setting] = Math.max(0, Math.min(999, (currentSetup[setting] || 500) + Math.round(change * multiplier)));
                }}
            }}
        }}
    }}
    
    let html = '';
    
    // Nagłówek
    html += `<div class="practice-header">`;
    html += `<h2>Praktyka - Setup krokowy</h2>`;
    html += `<div class="track-info">${{nextRace.track || 'Nieznany tor'}} · Sezon ${{nextRace.season || '?'}} · Wyścig ${{nextRace.race || '?'}}</div>`;
    html += `</div>`;
    
    // Driver stats mini
    const ma = driverMargin.MA || 0;
    const halfMa = driverMargin.half_MA || 0;
    html += `<div class="driver-stats-mini">`;
    html += `<div class="driver-stat-mini"><div class="label">Okrążenie</div><div class="value" style="color:var(--accent-yellow)">${{currentLap}}/${{totalLaps}}</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Temp</div><div class="value">${{practiceTemp}}°C</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Opony</div><div class="value">${{pred.sessions?.practice?.tyres || 'medium'}}</div></div>`;
    html += `</div>`;
    
    // Show current lap comment if any
    if (lapsCompleted > 0 && comments[lapsCompleted]) {{
        const prevComment = comments[lapsCompleted];
        const normalized = prevComment.toLowerCase();
        const isSatisfied = satisfiedWords.some(w => normalized.includes(w));
        
        html += `<div class="lap-card current" style="margin-bottom:1rem">`;
        html += `<div class="lap-header">`;
        html += `<h3>Komentarz z okrążenia ${{lapsCompleted}}</h3>`;
        html += `<span class="lap-badge ${{isSatisfied ? 'done' : 'next'}}">${{isSatisfied ? '✓ Zadowolony' : '⚠ Wymaga korekty'}}</span>`;
        html += `</div>`;
        html += `<div class="lap-instruction">`;
        html += `<div class="instruction" style="font-size:0.9rem">${{prevComment}}</div>`;
        html += `</div>`;
        html += `</div>`;
    }}
    
    // Driver stats mini
    // (ma and halfMa already declared above)
    html += `<div class="driver-stats-mini">`;
    html += `<div class="driver-stat-mini"><div class="label">Margines</div><div class="value" style="color:var(--accent-yellow)">${{halfMa}}</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">MA</div><div class="value">${{ma}}</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Temp</div><div class="value">${{practiceTemp}}°C</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Opony</div><div class="value">${{pred.sessions?.practice?.tyres || 'medium'}}</div></div>`;
    html += `</div>`;
    
    // Timeline
    html += `<div class="practice-timeline">`;
    const steps = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'];
    // currentLap is already set above
    steps.forEach((step, i) => {{
        const lapNum = i + 1;
        const isDone = lapNum < currentLap;
        const isCurrent = lapNum === currentLap;
        const statusClass = isDone ? 'completed' : (isCurrent ? 'current' : '');
    html += `<div class="timeline-step ${{statusClass}}">`;
    html += `<div class="timeline-dot">${{lapNum}}</div>`;
    html += `<div class="timeline-label">${{step}}</div>`;
        html += `</div>`;
    }});
    html += `</div>`;
    
    // Lap cards
    laps.forEach((lap, i) => {{
        const lapNum = lap.lap;
        const isDone = lapNum < currentLap;
        const isCurrent = lapNum === currentLap;
        
        // Use currentSetup that has been adjusted based on comments
        let suggestedSetup = {{...currentSetup}};
        if (lapNum === 1) {{
            // First lap - use current setup (possibly adjusted by comments)
        }} else if (lapNum === 2) {{
            // After lap 1 feedback, try +halfMa if not satisfied
            suggestedSetup.fw = currentSetup.fw + halfMa;
            suggestedSetup.rw = currentSetup.rw + halfMa;
        }} else if (lapNum === 3) {{
            // Continue in direction from lap 2
            suggestedSetup.fw = currentSetup.fw + halfMa + Math.floor(halfMa/2);
            suggestedSetup.rw = currentSetup.rw + halfMa + Math.floor(halfMa/2);
        }} else if (lapNum === 4) {{
            // Change direction
            suggestedSetup.fw = currentSetup.fw - halfMa;
            suggestedSetup.rw = currentSetup.rw - halfMa;
        }} else {{
            // Narrow down binary search
            const offset = Math.floor(halfMa / (lapNum - 2));
            suggestedSetup.fw = currentSetup.fw - halfMa + offset;
            suggestedSetup.rw = currentSetup.rw - halfMa + offset;
        }}
        
        html += `<div class="lap-card ${{isCurrent ? 'current' : ''}} ${{isDone ? 'done' : ''}}">`;
        
        // Lap header
        html += `<div class="lap-header">`;
        html += `<h3>Lap ${{lapNum}}</h3>`;
        if (isDone) {{
            html += `<span class="lap-badge done">✓ Wykonane</span>`;
        }} else if (isCurrent) {{
            html += `<span class="lap-badge next">▶ Teraz</span>`;
        }} else {{
            html += `<span class="lap-badge pending">⏳ Dalej</span>`;
        }}
        html += `</div>`; // lap-header
        
        // Setup chips
        html += `<div class="lap-setup">`;
        ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
            const val = suggestedSetup[key] || 0;
            html += `<div class="setup-chip">`;
            html += `<span class="label">${{key.toUpperCase()}}</span>`;
            html += `<span class="value">${{val}}</span>`;
            html += `</div>`;
        }});
        html += `</div>`;
        
        // Binary search visual
        if (!isDone) {{
            html += `<div class="binary-search-visual">`;
            if (lapNum === 1) {{
                html += `<div class="search-range">Start: ${{practiceSetup.fw - halfMa}} → ${{practiceSetup.fw + halfMa}}</div>`;
            }} else if (lapNum === 2) {{
                html += `<div class="search-arrow">Jeśli nie satisfied → FW +${{halfMa}}</div>`;
            }} else if (lapNum === 4) {{
                html += `<div class="search-arrow">Jeśli gorszy → zmień kierunek</div>`;
            }} else {{
                html += `<div class="search-range">Zawężanie ±${{Math.floor(halfMa / (lapNum - 2))}}</div>`;
            }}
            html += `</div>`;
        }}
        
        // Instruction
        if (!isDone) {{
            html += `<div class="lap-instruction">`;
            html += `<div class="instruction">${{lap.action}}</div>`;
            html += `<div class="note">${{lap.note}}</div>`;
            html += `</div>`;
        }}
        
        html += `</div>`;
    }});
    
    // Test input for simulating lap completion
    if (currentLap <= totalLaps) {{
        html += `<div style="margin-top:1.5rem;padding:1rem;background:#181818;border:1px solid #333">`;
        html += `<div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.5rem">Wpisz komentarz kierowcy z gry po wykonaniu okrążenia:</div>`;
        html += `<input type="text" id="driverCommentInput" placeholder="np. Wings: I am missing a bit of grip" style="width:100%;padding:0.5rem;background:#000;color:#fff;border:1px solid #333;margin-bottom:0.5rem">`;
        html += `<button onclick="completeLap()" style="background:#FFC000;color:#000;padding:0.5rem 1rem;border:none;cursor:pointer;font-weight:700">Zapisz komentarz &raquo;</button>`;
        html += `</div>`;
    }}
    
    // Session summary - Q1 after practice
    html += `<div class="session-summary">`;
    html += `<h3>📊 Po praktyce → Q1 Setup</h3>`;
    const q1Setup = pred.sessions?.q1?.setup || pred.setup_q1 || {{}};
    html += `<div class="lap-setup">`;
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = q1Setup[key] || 0;
        html += `<div class="setup-chip">`;
        html += `<span class="label">${{key.toUpperCase()}}</span>`;
        html += `<span class="value">${{val}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    html += `<div class="next-up">`;
    html += `<span class="icon">🏎️</span>`;
    html += `<div><div class="label">Następna sesja</div><div class="value">Q1 - Soft tyres, ${{pred.sessions?.q1?.temp || 22}}°C</div></div>`;
    html += `</div>`;
    html += `</div>`;
    
    // Q2 and Race summary
    html += `<div class="session-summary">`;
    html += `<h3>📊 Po Q1 → Q2 Setup</h3>`;
    const q2Setup = pred.sessions?.q2?.setup || pred.setup_q2 || {{}};
    html += `<div class="lap-setup">`;
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = q2Setup[key] || 0;
        html += `<div class="setup-chip">`;
        html += `<span class="label">${{key.toUpperCase()}}</span>`;
        html += `<span class="value">${{val}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    html += `<div class="next-up">`;
    html += `<span class="icon">🎯</span>`;
    html += `<div><div class="label">Następna sesja</div><div class="value">Q2 - Soft tyres, push for time</div></div>`;
    html += `</div>`;
    html += `</div>`;
    
    html += `<div class="session-summary">`;
    html += `<h3>🏁 Wyścig Setup</h3>`;
    const raceSetup = pred.sessions?.race?.setup || pred.setup_race || {{}};
    html += `<div class="lap-setup">`;
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = raceSetup[key] || 0;
        html += `<div class="setup-chip">`;
        html += `<span class="label">${{key.toUpperCase()}}</span>`;
        html += `<span class="value">${{val}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    const fs = pred.sessions?.race?.fuel_strategy || {{}};
    html += `<div class="next-up">`;
    html += `<span class="icon">⛽</span>`;
    html += `<div><div class="label">Strategia paliwowa</div><div class="value">${{fs.pits || 2}} pit stopy · ${{fs.total_fuel || 257}}L</div></div>`;
    html += `</div>`;
    html += `</div>`;
    
    container.innerHTML = html;
}}

// Funkcja do symulacji ukończenia okrążenia
function completeLap() {{
    const input = document.getElementById('driverCommentInput');
    const comment = input.value.trim();
    
    if (!comment) {{
        alert('Wpisz komentarz kierowcy!');
        return;
    }}
    
    let practiceState = {{ lapsCompleted: 0, comments: {{}} }};
    try {{
        const saved = localStorage.getItem('gpro_practice_state');
        if (saved) {{
            practiceState = JSON.parse(saved);
        }}
    }} catch (e) {{}}
    
    const nextLap = practiceState.lapsCompleted + 1;
    practiceState.comments[nextLap] = comment;
    practiceState.lapsCompleted = nextLap;
    
    localStorage.setItem('gpro_practice_state', JSON.stringify(practiceState));
    
    renderPractice();
}}

function renderResults() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th><th>Q1</th><th>Q2</th><th>Pit</th>';
    html += '<th>Opony koniec</th><th>Paliwo koniec</th><th>Bilans</th>';
    html += '</tr></thead><tbody>';

    // Od najnowszego do najstarszego
    for (let i = displayedData.length - 1; i >= 0; i--) {{
        const rd = displayedData[i].race_data || {{}};
        const fin = rd.finances || {{}};
        const pits = rd.pits || [];

        html += `<tr>`;
        html += `<td>S${{rd.season}}R${{rd.race}}</td>`;
        html += `<td style="font-family:var(--font-display)">${{rd.track || '?'}}</td>`;
        html += `<td class="${{posClass(rd.q1_pos)}}">P${{rd.q1_pos || '?'}}</td>`;
        html += `<td class="${{posClass(rd.q2_pos)}}">P${{rd.q2_pos || '?'}}</td>`;
        html += `<td>${{pits.length}}</td>`;
        html += `<td>${{rd.finish_tyres != null ? rd.finish_tyres + '%' : '-'}}</td>`;
        html += `<td>${{rd.finish_fuel != null ? rd.finish_fuel + 'L' : '-'}}</td>`;
        html += `<td class="${{(fin.total || 0) >= 0 ? 'val-positive' : 'val-negative'}}">${{formatMoney(fin.total)}}</td>`;
        html += `</tr>`;
    }}

    html += '</tbody></table>';
    document.getElementById('tab-results').innerHTML = html;
}}

// ==========================================================
// ZAKŁADKA: BOLID (Car & Parts Upgrade Planning)
// ==========================================================
function renderCar() {{
    const container = document.getElementById('tab-car');
    const latest = getLatestRace();
    if (!latest) return;

    const cs = latest.car_status || {{}};
    const rd = latest.race_data || {{}};

    const parts = [
        {{ key: 'Chassis', label: 'Chassis', options: cs.chassisOptions }},
        {{ key: 'Engine', label: 'Silnik', options: cs.engineOptions }},
        {{ key: 'FWing', label: 'Przednie skrzydło', options: cs.fWingOptions }},
        {{ key: 'RWing', label: 'Tylne skrzydło', options: cs.rWingOptions }},
        {{ key: 'Underbody', label: 'Podłoga', options: cs.underbodyOptions }},
        {{ key: 'Sidepods', label: 'Sekcje boczne', options: cs.sidepodsOptions }},
        {{ key: 'Cooling', label: 'Chłodzenie', options: cs.coolingOptions }},
        {{ key: 'Gear', label: 'Skrzynia biegów', options: cs.gearOptions }},
        {{ key: 'Brakes', label: 'Hamulce', options: cs.brakesOptions }},
        {{ key: 'Susp', label: 'Zawieszenie', options: cs.suspOptions }},
        {{ key: 'Electronics', label: 'Elektronika', options: cs.electronicsOptions }},
    ];

    let html = `
    <div class="practice-header">
        <h2>Stan Bolidu i Planowanie</h2>
        <div class="track-info">Poziomy części i zużycie po ostatnim wyścigu</div>
    </div>

    <div class="summary-grid" style="grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); margin-left: 0; margin-right: 0;">`;

    parts.forEach(p => {{
        const lvl = cs['lvl' + p.key] || 0;
        const wear = cs['usa' + p.key] || 0;
        const health = 100 - wear;
        const color = wear > 85 ? 'var(--accent-red)' : (wear > 70 ? 'var(--accent-gold)' : 'var(--accent-cyan)');

        // GPRO Analyzer-like logic: Estimate wear after next race
        // Try to get average wear per lap from history
        let wearPerLap = 0.3; // Default fallback
        const trackRaces = RACE_DATA.filter(r => r.race_data?.track === rd.track);
        const sourceRaces = trackRaces.length > 0 ? trackRaces : RACE_DATA.slice(-3);

        if (sourceRaces.length > 0) {{
            let totalWPL = 0;
            let count = 0;
            sourceRaces.forEach(r => {{
                const partData = r.race_data?.car_parts?.[p.key.toLowerCase()] || r.race_data?.car_parts?.[p.key];
                const laps = r.race_summary?.results?.[0]?.laps || 70;
                if (partData && partData.finish_wear !== undefined && partData.start_wear !== undefined) {{
                    totalWPL += (partData.finish_wear - partData.start_wear) / laps;
                    count++;
                }}
            }});
            if (count > 0) wearPerLap = totalWPL / count;
        }}

        const nextLaps = getCalendarNextRace()?.total_laps || 72;
        const estRaceWear = Math.round(wearPerLap * nextLaps);
        const estWear = wear + estRaceWear;
        const needsUpgrade = estWear > 85;

        html += `
        <div class="summary-card" style="border-left: 4px solid ${{color}};">
            <div class="session-header">
                <h4 style="color: #fff;">${{p.label}}</h4>
                <span class="session-badge">Lvl ${{lvl}}</span>
            </div>
            <div class="value" style="font-size: 1.5rem; color: ${{color}};">${{wear}}% <span style="font-size: 0.7rem; color: var(--text-muted);">ZUŻYCIA</span></div>

            <div style="height: 4px; background: #333; margin: 1rem 0; position: relative;">
                <div style="height: 100%; width: ${{health}}%; background: ${{color}}; transition: width 1s ease-out;"></div>
            </div>

            <div class="rec-note">
                EST. PO NAST. WYŚCIGU: <span style="color: ${{needsUpgrade ? 'var(--accent-red)' : '#fff'}}">${{estWear}}%</span>
            </div>

            ${{needsUpgrade ? `
            <div class="lap-instruction" style="margin-top: 1rem; padding: 0.5rem;">
                <div class="instruction" style="font-size: 0.7rem; color: var(--accent-red);">⚠ WYMAGANA WYMIANA</div>
            </div>` : ''}}

            <div style="margin-top: 1rem;">
                <select style="width: 100%; background: #000; color: var(--text-muted); border: 1px solid var(--border-color); padding: 0.4rem; font-size: 0.6rem; font-family: var(--font-mono);">
                    <option>ZOBACZ OPCJE WYMIANY...</option>
                    ${{(p.options || []).map(o => `<option>${{o.text}}</option>`).join('')}}
                </select>
            </div>
        </div>`;
    }});

    html += `</div>`;
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

    let html = '<div class="setup-grid">';

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
                ${{entries.length > 1 ? ' · ' + entries.length + ' wyścigi na tym torze' : ''}}
            </div>
        </div>`;
    }});

    html += '</div>';
    document.getElementById('tab-setups').innerHTML = html;
}}

function renderFuel() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th><th>Start</th>';
    html += '<th>Pit 1</th><th>Pit 2</th><th>Pit 3</th><th>Pit 4</th>';
    html += '<th>Opony %</th><th>Paliwo L</th>';
    html += '</tr></thead><tbody>';

    for (let i = displayedData.length - 1; i >= 0; i--) {{
        const rd = displayedData[i].race_data || {{}};
        const pits = rd.pits || [];

        html += `<tr>`;
        html += `<td>S${{rd.season}}R${{rd.race}}</td>`;
        html += `<td style="font-family:var(--font-display)">${{rd.track || '?'}}</td>`;
        html += `<td>${{rd.start_fuel || '-'}}L</td>`;

        // Pit stopy (max 4 kolumn)
        for (let p = 0; p < 4; p++) {{
            if (pits[p]) {{
                html += `<td>Lap ${{pits[p].lap}} · ${{pits[p].tyre_condition || '?'}}% · ${{pits[p].refilled_to || '?'}}L</td>`;
            }} else {{
                html += `<td>-</td>`;
            }}
        }}

        html += `<td>${{rd.finish_tyres != null ? rd.finish_tyres + '%' : '-'}}</td>`;
        html += `<td>${{rd.finish_fuel != null ? rd.finish_fuel + 'L' : '-'}}</td>`;
        html += `</tr>`;
    }}

    html += '</tbody></table>';
    document.getElementById('tab-fuel').innerHTML = html;
}}

function renderFinances() {{
    const displayedData = getDisplayedRaceData();
    if (displayedData.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th>';
    html += '<th>Przychody</th><th>Koszty</th><th>Bilans</th><th>Saldo</th>';
    html += '</tr></thead><tbody>';

    for (let i = displayedData.length - 1; i >= 0; i--) {{
        const rd = displayedData[i].race_data || {{}};
        const fin = rd.finances || {{}};
        const txs = fin.transactions || [];

        const income = txs.filter(t => t.amount > 0).reduce((s, t) => s + t.amount, 0);
        const costs = txs.filter(t => t.amount < 0).reduce((s, t) => s + t.amount, 0);

        html += `<tr>`;
        html += `<td>S${{rd.season}}R${{rd.race}}</td>`;
        html += `<td style="font-family:var(--font-display)">${{rd.track || '?'}}</td>`;
        html += `<td class="val-positive">${{formatMoney(income)}}</td>`;
        html += `<td class="val-negative">${{formatMoney(costs)}}</td>`;
        html += `<td class="${{(fin.total || 0) >= 0 ? 'val-positive' : 'val-negative'}}">${{formatMoney(fin.total)}}</td>`;
        html += `<td>${{formatMoney(fin.balance)}}</td>`;
        html += `</tr>`;
    }}

    html += '</tbody></table>';
    document.getElementById('tab-finances').innerHTML = html;
}}

function renderDriver(latest) {{
    const rd = latest.race_data || {{}};
    const drv = rd.driver || {{}};

    if (!drv.name) {{
        document.getElementById('tab-driver').innerHTML =
            '<div class="empty-state"><h2>Brak danych kierowcy</h2></div>';
        return;
    }}

    const stats = [
        {{ name: 'concentration', label: 'Koncentracja', value: drv.concentration }},
        {{ name: 'talent', label: 'Talent', value: drv.talent }},
        {{ name: 'aggressiveness', label: 'Agresja', value: drv.aggressiveness }},
        {{ name: 'experience', label: 'Doświadczenie', value: drv.experience }},
        {{ name: 'technical_insight', label: 'Wgl. Techniczny', value: drv.technical_insight }},
        {{ name: 'stamina', label: 'Stamina', value: drv.stamina }},
        {{ name: 'charisma', label: 'Charyzma', value: drv.charisma }},
        {{ name: 'motivation', label: 'Motywacja', value: drv.motivation }},
    ];

    let html = `<h2 style="margin-bottom:1rem">${{drv.name}} <span style="color:var(--text-muted);font-weight:300">OA: ${{drv.OA}}</span></h2>`;
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
        <h3 style="margin-top:3rem;margin-bottom:1.5rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--accent-gold);">Dostawca opon: ${{ts.name}}</h3>
        <div class="driver-stats">
            <div class="stat-item" style="border-bottom: 2px solid var(--accent-gold);"><div class="stat-name">Peak temp</div><div class="stat-value">${{ts.peak_temp || '-'}}°C</div></div>
            <div class="stat-item" style="border-bottom: 2px solid var(--accent-gold);"><div class="stat-name">Dry perf</div><div class="stat-value">${{ts.dry_perf || '-'}}</div></div>
            <div class="stat-item" style="border-bottom: 2px solid var(--accent-gold);"><div class="stat-name">Wet perf</div><div class="stat-value">${{ts.wet_perf || '-'}}</div></div>
            <div class="stat-item" style="border-bottom: 2px solid var(--accent-gold);"><div class="stat-name">Durability</div><div class="stat-value">${{ts.durability || '-'}}</div></div>
            <div class="stat-item" style="border-bottom: 2px solid var(--accent-gold);"><div class="stat-name">Warmup</div><div class="stat-value">${{ts.warmup || '-'}}</div></div>
        </div>`;
    }}

    document.getElementById('tab-driver').innerHTML = html;
}}

// Start!
window.onload = () => {{
    render();

    // Initial visibility state based on active tab
    const activeBtn = document.querySelector('.tab-btn.active');
    if (activeBtn) {{
        const tabId = activeBtn.dataset.tab;
        const mainSummary = document.getElementById('mainSummaryContainer');
        if (['overview', 'nextrace', 'practice', 'car'].includes(tabId)) {{
            mainSummary.style.display = 'none';
        }}
    }}
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