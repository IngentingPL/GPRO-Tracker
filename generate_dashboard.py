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


# ============================================================
# GENEROWANIE HTML
# ============================================================

def generate_html(race_data, prediction_data, calendar_data):
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

    # Budujemy HTML
    html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPRO Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        /* ==========================================================
           GŁÓWNE ZMIENNE KOLORÓW
           Mini-lekcja: CSS custom properties (--nazwa) pozwalają
           zdefiniować kolory raz i używać ich wszędzie.
           Zmiana jednej zmiennej zmienia kolor w całym dashboardzie.
           ========================================================== */
        :root {{
            --bg-primary: #0a0e1a;
            --bg-card: #111827;
            --bg-card-hover: #1a2234;
            --bg-tab: #1e293b;
            --bg-tab-active: #2563eb;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-yellow: #eab308;
            --accent-orange: #f97316;
            --border-color: #1e293b;
            --font-display: 'Outfit', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        /* Reset i bazowe style */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: var(--font-display);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            /* Subtelna tekstura tła */
            background-image:
                radial-gradient(circle at 20% 50%, rgba(37, 99, 235, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(34, 197, 94, 0.02) 0%, transparent 50%);
        }}

        /* ==========================================================
           NAGŁÓWEK
           ========================================================== */
        .header {{
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .header h1 span {{
            color: var(--accent-blue);
        }}

        .header-info {{
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        /* ==========================================================
           KARTY PODSUMOWANIA (na górze dashboardu)
           ========================================================== */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            padding: 1.5rem 2rem;
        }}

        .summary-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            transition: background 0.2s;
        }}

        .summary-card:hover {{
            background: var(--bg-card-hover);
        }}

        .summary-card .label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .summary-card .value {{
            font-family: var(--font-mono);
            font-size: 1.5rem;
            font-weight: 700;
        }}

        .summary-card .sub {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}

        /* ==========================================================
           ZAKŁADKI (TABS)
           Mini-lekcja: Zakładki działają bez JS dzięki atrybutom
           data-tab. JS tylko przełącza klasy CSS "active".
           ========================================================== */
        .tabs {{
            display: flex;
            gap: 0.25rem;
            padding: 0 2rem;
            border-bottom: 1px solid var(--border-color);
            overflow-x: auto;
        }}

        .tab-btn {{
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 600;
            padding: 0.75rem 1.25rem;
            background: transparent;
            color: var(--text-muted);
            border: none;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .tab-btn:hover {{
            color: var(--text-primary);
        }}

        .tab-btn.active {{
            color: var(--accent-blue);
            border-bottom-color: var(--accent-blue);
        }}

        .tab-content {{
            display: none;
            padding: 1.5rem 2rem;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* ==========================================================
           TABELE
           ========================================================== */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}

        .data-table th {{
            text-align: left;
            padding: 0.75rem 1rem;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            background: var(--bg-primary);
        }}

        .data-table td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            font-family: var(--font-mono);
            font-size: 0.8rem;
        }}

        .data-table tr:hover td {{
            background: var(--bg-card-hover);
        }}

        /* Kolorowanie pozycji */
        .pos-1 {{ color: var(--accent-green); font-weight: 700; }}
        .pos-2 {{ color: var(--accent-blue); }}
        .pos-3 {{ color: var(--accent-orange); }}

        /* Kolorowanie wartości */
        .val-positive {{ color: var(--accent-green); }}
        .val-negative {{ color: var(--accent-red); }}

        /* ==========================================================
           SETUP GRID (per tor)
           ========================================================== */
        .setup-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }}

        .setup-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
        }}

        .setup-card h3 {{
            font-size: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .setup-card h3 .flag {{
            font-size: 1.2rem;
        }}

        .setup-values {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
        }}

        .setup-item {{
            text-align: center;
            padding: 0.5rem;
            background: var(--bg-tab);
            border-radius: 8px;
        }}

        .setup-item .setup-label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .setup-item .setup-val {{
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--accent-blue);
        }}

        .setup-meta {{
            margin-top: 0.75rem;
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* ==========================================================
           SEKCJA KIEROWCY
           ========================================================== */
        .driver-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 0.75rem;
        }}

        .stat-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }}

        .stat-item .stat-name {{
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .stat-item .stat-value {{
            font-family: var(--font-mono);
            font-size: 1.5rem;
            font-weight: 700;
        }}

        /* Kolory dla statystyk kierowcy */
        .stat-good {{ color: var(--accent-green); }}
        .stat-ok {{ color: var(--accent-yellow); }}
        .stat-bad {{ color: var(--accent-red); }}

        /* ==========================================================
           SEKCJA FINANSÓW
           ========================================================== */
        .finance-bar {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .finance-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem 1.5rem;
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
            margin-bottom: 1rem;
            color: var(--text-secondary);
        }}

        .empty-state code {{
            background: var(--bg-card);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 0.85rem;
        }}

        /* ==========================================================
           SEKCJA REKOMENDACJI (zakładka Następny wyścig)
           Mini-lekcja: BEM-like nazewnictwo (.rec-*) oddziela style
           rekomendacji od reszty dashboardu - łatwiej utrzymywać.
           ========================================================== */
        .rec-header {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .rec-header h2 {{
            font-size: 1.25rem;
            margin-bottom: 0.25rem;
        }}

        .rec-header .rec-subtitle {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .rec-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1rem;
        }}

        .rec-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
        }}

        .rec-card h3 {{
            font-size: 0.95rem;
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
            font-style: italic;
        }}

        .rec-card .rec-warn {{
            font-size: 0.8rem;
            color: var(--accent-yellow);
            margin-top: 0.5rem;
        }}

        .rec-card .rec-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.35rem 0;
            font-size: 0.85rem;
        }}

        .rec-card .rec-row .rec-label {{
            color: var(--text-secondary);
        }}

        .rec-disclaimer {{
            margin-top: 1.5rem;
            padding: 1rem 1.25rem;
            background: rgba(234, 179, 8, 0.08);
            border: 1px solid rgba(234, 179, 8, 0.2);
            border-radius: 10px;
            font-size: 0.8rem;
            color: var(--accent-yellow);
        }}

        /* ==========================================================
           Confidence Bar
           Mini-lekcja: Wizualny wskaźnik pewności predykcji.
           Zielony = wysoka pewność, czerwony = niska.
           ========================================================== */
        .confidence-bar {{
            height: 8px;
            border-radius: 4px;
            background: var(--bg-tab);
            overflow: hidden;
            margin: 0.5rem 0;
        }}

        .confidence-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}

        .confidence-fill.high {{
            background: var(--accent-green);
            width: 100%;
        }}

        .confidence-fill.medium {{
            background: var(--accent-yellow);
            width: 66%;
        }}

        .confidence-fill.low {{
            background: var(--accent-orange);
            width: 33%;
        }}

        .confidence-fill.very_low {{
            background: var(--accent-red);
            width: 10%;
        }}

        /* Session Card */
        .session-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        .session-card.practice {{ border-left: 3px solid var(--accent-yellow); }}
        .session-card.q1 {{ border-left: 3px solid var(--accent-green); }}
        .session-card.q2 {{ border-left: 3px solid var(--accent-blue); }}
        .session-card.race {{ border-left: 3px solid var(--accent-orange); }}

        .session-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .session-header h4 {{
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .session-badge {{
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            background: var(--bg-tab);
            color: var(--text-muted);
        }}

        .session-meta {{
            font-size: 0.7rem;
            color: var(--text-muted);
            display: flex;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}

        .session-meta span {{ display: flex; align-items: center; gap: 0.25rem; }}

        .session-setup {{
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }}

        .session-setup .setup-part {{
            background: var(--bg-tab);
            padding: 0.3rem 0.5rem;
            border-radius: 5px;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .session-setup .setup-part .label {{
            color: var(--text-muted);
            font-size: 0.6rem;
            text-transform: uppercase;
        }}

        .session-setup .setup-part .value {{
            color: var(--accent-blue);
            font-weight: 600;
        }}

        .session-note {{
            margin-top: 0.4rem;
            font-size: 0.7rem;
            color: var(--text-muted);
            font-style: italic;
        }}

        .fuel-stint-bar {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
            margin-top: 0.5rem;
            flex-wrap: wrap;
        }}

        .fuel-stint-bar .stint {{
            background: var(--bg-tab);
            padding: 0.25rem 0.4rem;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 0.7rem;
        }}

        .fuel-stint-bar .arrow {{
            color: var(--text-muted);
            font-size: 0.65rem;
        }}

        /* ==========================================================
           Setup Race Inline
           ========================================================== */
        .setup-race-inline {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            padding: 0.75rem;
            background: var(--bg-tab);
            border-radius: 8px;
        }}

        .setup-race-inline .setup-part {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .setup-race-inline .setup-part .setup-label {{
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .setup-race-inline .setup-part .setup-val {{
            font-weight: 700;
            color: var(--accent-blue);
        }}

        .setup-race-inline .separator {{
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        /* ==========================================================
           Adjustment Badge
           Mini-lekcja: Mały badge pokazujący korektę setupu
           względem wartości bazowej. Zielony = wzrost, czerwony = spadek.
           ========================================================== */
        .adjustment-badge {{
            font-size: 0.65rem;
            font-family: var(--font-mono);
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            background: var(--bg-tab);
            color: var(--text-secondary);
            display: block;
            margin-top: 0.1rem;
        }}

        .adjustment-badge.positive {{
            color: var(--accent-green);
            background: rgba(34, 197, 94, 0.1);
        }}

        .adjustment-badge.negative {{
            color: var(--accent-red);
            background: rgba(239, 68, 68, 0.1);
        }}

        /* ==========================================================
           Fuel Strategy
           Mini-lekcja: Wizualna reprezentacja strategii paliwowej
           z pit stopami.
           ========================================================== */
        .fuel-strategy {{
            margin-top: 0.75rem;
        }}

        .fuel-strategy .strategy-name {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .fuel-strategy .strategy-visual {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-family: var(--font-mono);
            font-size: 0.85rem;
        }}

        .fuel-strategy .strategy-visual .pit-stop {{
            background: var(--bg-tab);
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }}

        .fuel-strategy .strategy-visual .arrow {{
            color: var(--text-muted);
        }}

        .fuel-strategy .strategy-visual .finish {{
            background: var(--accent-blue);
            color: white;
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
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
            font-size: 0.8rem;
            color: var(--text-secondary);
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-color);
        }}

        .notes-list li:last-child {{
            border-bottom: none;
        }}

        /* ==========================================================
           RESPONSYWNOŚĆ
           ========================================================== */
        @media (max-width: 768px) {{
            .header {{ padding: 1rem; }}
            .summary-grid {{ padding: 1rem; }}
            .tabs {{ padding: 0 1rem; }}
            .tab-content {{ padding: 1rem; }}
            .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}

        /* Scrollbar stylizacja */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border-color); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

        /* ==========================================================
           PRAKTYKA - Binary Search Setup
           ========================================================== */
        .practice-header {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .practice-header h2 {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
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
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            background: var(--bg-tab);
            color: var(--text-muted);
            border: 2px solid var(--border-color);
        }}

        .timeline-step.active .timeline-dot {{
            background: var(--accent-blue);
            border-color: var(--accent-blue);
            color: white;
        }}

        .timeline-step.completed .timeline-dot {{
            background: var(--accent-green);
            border-color: var(--accent-green);
            color: white;
        }}

        .timeline-step.current .timeline-dot {{
            background: var(--accent-yellow);
            border-color: var(--accent-yellow);
            color: black;
            animation: pulse 1.5s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}

        .timeline-label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            text-align: center;
        }}

        .lap-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }}

        .lap-card.current {{
            border-color: var(--accent-yellow);
            box-shadow: 0 0 0 1px var(--accent-yellow);
        }}

        .lap-card.done {{
            opacity: 0.6;
        }}

        .lap-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .lap-header h3 {{
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .lap-badge {{
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-weight: 600;
        }}

        .lap-badge.next {{
            background: var(--accent-yellow);
            color: black;
        }}

        .lap-badge.done {{
            background: var(--accent-green);
            color: white;
        }}

        .lap-badge.pending {{
            background: var(--bg-tab);
            color: var(--text-muted);
        }}

        .lap-setup {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }}

        .setup-chip {{
            background: var(--bg-tab);
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .setup-chip .label {{
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .setup-chip .value {{
            font-family: var(--font-mono);
            font-weight: 700;
            color: var(--accent-blue);
            font-size: 0.95rem;
        }}

        .lap-instruction {{
            background: rgba(234, 179, 8, 0.1);
            border: 1px solid rgba(234, 179, 8, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .lap-instruction .instruction {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--accent-yellow);
            margin-bottom: 0.5rem;
        }}

        .lap-instruction .note {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .binary-search-visual {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: var(--bg-tab);
            border-radius: 8px;
        }}

        .search-range {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            text-align: center;
        }}

        .search-arrow {{
            text-align: center;
            color: var(--accent-yellow);
            font-size: 0.8rem;
        }}

        .session-summary {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            margin-top: 1.5rem;
        }}

        .session-summary h3 {{
            font-size: 1rem;
            margin-bottom: 1rem;
            color: var(--accent-green);
        }}

        .next-up {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: var(--bg-card);
            border: 1px solid var(--accent-blue);
            border-radius: 12px;
            margin-top: 1rem;
        }}

        .next-up .icon {{
            font-size: 1.5rem;
        }}

        .next-up .label {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .next-up .value {{
            font-weight: 600;
            color: var(--accent-blue);
        }}

        .driver-stats-mini {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin: 1rem 0;
            padding: 1rem;
            background: var(--bg-tab);
            border-radius: 8px;
        }}

        .driver-stat-mini {{
            text-align: center;
        }}

        .driver-stat-mini .label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .driver-stat-mini .value {{
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1.1rem;
        }}
    </style>
</head>
<body>

<!-- Nagłówek strony -->
<div class="header">
    <h1><span>GPRO</span> Tracker</h1>
    <div class="header-info" id="headerInfo">Ładowanie...</div>
</div>

<!-- Karty podsumowania -->
<div class="summary-grid" id="summaryGrid"></div>

<!-- Zakładki -->
<div class="tabs" id="tabsNav">
    <button class="tab-btn active" data-tab="nextrace">Następny wyścig</button>
    <button class="tab-btn" data-tab="practice">Praktyka</button>
    <button class="tab-btn" data-tab="results">Wyniki</button>
    <button class="tab-btn" data-tab="setups">Setupy</button>
    <button class="tab-btn" data-tab="fuel">Paliwo & Opony</button>
    <button class="tab-btn" data-tab="finances">Finanse</button>
    <button class="tab-btn" data-tab="driver">Kierowca</button>
</div>

<!-- Zawartość zakładek -->
<div class="tab-content active" id="tab-nextrace"></div>
<div class="tab-content" id="tab-practice"></div>
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
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
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


function getLatestRace() {{
    if (!RACE_DATA || RACE_DATA.length === 0) return null;
    return RACE_DATA[RACE_DATA.length - 1];
}}

function toInt(value) {{
    if (value === null || value === undefined || value === '') return null;
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}}

function normalizeTrackName(name) {{
    return String(name || '')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, ' ');
}}

function getCalendarEntries() {{
    if (!CALENDAR_DATA) return [];
    if (Array.isArray(CALENDAR_DATA)) return CALENDAR_DATA;
    if (Array.isArray(CALENDAR_DATA.data)) return CALENDAR_DATA.data;

    if (CALENDAR_DATA.data && typeof CALENDAR_DATA.data === 'object') {{
        for (const key of ['data', 'races', 'calendar', 'events', 'schedule']) {{
            if (Array.isArray(CALENDAR_DATA.data[key])) return CALENDAR_DATA.data[key];
        }}
    }}

    for (const key of ['races', 'calendar', 'events', 'schedule']) {{
        if (Array.isArray(CALENDAR_DATA[key])) return CALENDAR_DATA[key];
    }}

    return [];
}}

function getCalendarSeason() {{
    const directSeason = toInt(CALENDAR_DATA?.season)
        ?? toInt(CALENDAR_DATA?.selSeasonNb)
        ?? toInt(CALENDAR_DATA?.seasonNb);
    if (directSeason !== null) return directSeason;

    const entries = getCalendarEntries();
    for (const entry of entries) {{
        const season = toInt(entry?.season) ?? toInt(entry?.selSeasonNb) ?? toInt(entry?.seasonNb);
        if (season !== null) return season;
    }}

    return null;
}}

function normalizeCalendarRace(entry, index, fallbackSeason) {{
    return {{
        track: entry?.track || entry?.trackName || entry?.name || entry?.raceName || 'Nieznany tor',
        season: toInt(entry?.season) ?? toInt(entry?.selSeasonNb) ?? toInt(entry?.seasonNb) ?? fallbackSeason,
        race: toInt(entry?.race) ?? toInt(entry?.raceNb) ?? toInt(entry?.round) ?? toInt(entry?.number) ?? toInt(entry?.selRaceNb) ?? (index + 1),
        total_laps: toInt(entry?.total_laps) ?? toInt(entry?.totalLaps) ?? toInt(entry?.laps) ?? toInt(entry?.lapNb) ?? toInt(entry?.noOfLaps) ?? null
    }};
}}

function getCalendarNextRace() {{
    const entries = getCalendarEntries();
    if (!entries || entries.length === 0) return null;

    const fallbackSeason = getCalendarSeason();
    const normalized = entries
        .map((entry, index) => normalizeCalendarRace(entry, index, fallbackSeason))
        .filter(entry => entry.track || entry.race !== null)
        .sort((a, b) => (toInt(a.race) ?? 0) - (toInt(b.race) ?? 0));

    if (normalized.length === 0) return null;

    const latest = getLatestRace();
    const latestRaceData = latest?.race_data || {{}};
    const latestSeason = toInt(latestRaceData.season);
    const latestRace = toInt(latestRaceData.race);
    const calendarSeason = toInt(normalized[0].season) ?? fallbackSeason;

    if (latestSeason === null) return normalized[0];
    if (calendarSeason !== null && calendarSeason > latestSeason) return normalized[0];
    if (calendarSeason !== null && calendarSeason < latestSeason) return null;
    if (latestRace === null) return normalized[0];

    return normalized.find(entry => (toInt(entry.race) ?? 0) > latestRace) || null;
}}

function resolvePredictionContext(pred) {{
    const predictedRace = pred?.next_race || {{}};
    const calendarNextRace = getCalendarNextRace();

    if (!calendarNextRace) {{
        return {{ nextRace: predictedRace, isStale: false, staleReason: '' }};
    }}

    const predictedSeason = toInt(predictedRace.season);
    const predictedRaceNo = toInt(predictedRace.race);
    const calendarSeason = toInt(calendarNextRace.season);
    const calendarRaceNo = toInt(calendarNextRace.race);

    const sameSeasonRace = predictedSeason !== null
        && predictedRaceNo !== null
        && calendarSeason !== null
        && calendarRaceNo !== null
        && predictedSeason === calendarSeason
        && predictedRaceNo === calendarRaceNo;

    const sameTrack = normalizeTrackName(predictedRace.track) === normalizeTrackName(calendarNextRace.track);

    if (sameSeasonRace && (sameTrack || !predictedRace.track || !calendarNextRace.track)) {{
        return {{
            nextRace: {{ ...calendarNextRace, ...predictedRace }},
            isStale: false,
            staleReason: ''
        }};
    }}

    let staleReason = 'Prediction.json wskazuje inny wyścig niż aktualny kalendarz.';
    if (predictedRace.track || predictedSeason !== null || predictedRaceNo !== null) {{
        staleReason = `Prediction.json: ${{predictedRace.track || 'Nieznany tor'}} (S${{predictedSeason ?? '?'}} R${{predictedRaceNo ?? '?'}}) · ` +
            `Kalendarz: ${{calendarNextRace.track || 'Nieznany tor'}} (S${{calendarSeason ?? '?'}} R${{calendarRaceNo ?? '?'}})`;
    }}

    return {{
        nextRace: calendarNextRace,
        isStale: true,
        staleReason
    }};
}}

// ==========================================================
// RENDEROWANIE DASHBOARDU
// ==========================================================

function render() {{
    // Renderuj zakładkę "Następny wyścig" nawet bez danych wyścigowych
    // (może mieć kalendarz)
    renderNextRace();

    if (!RACE_DATA || RACE_DATA.length === 0) {{
        document.getElementById('summaryGrid').innerHTML = '';
        document.getElementById('tab-results').innerHTML = `
            <div class="empty-state">
                <h2>Brak danych</h2>
                <p>Uruchom fetcher po wyścigu, żeby zebrać dane:</p>
                <p style="margin-top:1rem"><code>python gpro_fetcher.py</code></p>
            </div>`;
        return;
    }}

    const latest = RACE_DATA[RACE_DATA.length - 1];
    const rd = latest.race_data || {{}};
    const drv = rd.driver || {{}};

    // Nagłówek
    document.getElementById('headerInfo').textContent =
        `Sezon ${{rd.season}} · Wyścig ${{rd.race}} · ${{rd.track}} · Dane: ${{RACE_DATA.length}} wyścigów`;

    // Karty podsumowania
    renderSummary(latest);

    // Zakładki
    renderNextRace();
    renderPractice();
    renderResults();
    renderSetups();
    renderFuel();
    renderFinances();
    renderDriver(latest);
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
            <div class="rec-card">
                <h2>${{nextRace.track || 'Następny wyścig'}}</h2>
                <div class="rec-subtitle">Sezon ${{nextRace.season || '?'}} · Wyścig ${{nextRace.race || '?'}}${{nextRace.total_laps ? ` · ${{nextRace.total_laps}} okrążeń` : ''}}</div>
                <div style="margin-top:1rem;padding:1rem;border-radius:12px;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.35);color:var(--text-primary)">
                    <strong>Wykryto nieaktualną predykcję.</strong>
                    <div style="margin-top:0.5rem;color:var(--text-secondary)">${{staleReason}}</div>
                    <div style="margin-top:0.75rem;color:var(--text-secondary)">Odśwież kalendarz i rekomendacje przed użyciem setupu:</div>
                    <div style="margin-top:0.75rem"><code>python predictor.py</code></div>
                </div>
            </div>`;
        return;
    }}

    // =============================================
    // 1. NAGŁÓWEK Z INFO O TORZE
    // =============================================
    html += `<div class="rec-header">`;
    html += `<h2>${{nextRace.track || 'Nieznany tor'}}</h2>`;
    html += `<span class="rec-subtitle">Sezon ${{nextRace.season || '?'}} · Wyścig ${{nextRace.race || '?'}} · ${{nextRace.total_laps || '?'}} okrążeń</span>`;

    // Confidence bar
    html += `<div class="confidence-bar">`;
    html += `<div class="confidence-fill ${{confidence}}"></div>`;
    html += `</div>`;
    html += `<div class="rec-subtitle">${{confidenceReason}}</div>`;
    html += `</div>`;

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
    // 3. STRATEGIA PALIWOWA (summary)
    // =============================================
    html += `<div class="rec-card"><h3>Setup Q2</h3>`;
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
    html += `<div class="setup-meta">Baza: ${{base.track || '?'}} (${{base.temp || '?'}}°C) → Prognoza: ${{q2.temp || '?'}}°C</div>`;
    html += `</div>`;

    html += `</div>`; // zamknięcie rec-grid

    // =============================================
    // 3. SETUP RACE (jedna linia)
    // =============================================
    html += `<div class="rec-card" style="margin-top:1rem"><h3>Setup Race</h3>`;
    const race = pred.setup_race || {{}};
    const raceParts = ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'];
    html += `<div class="setup-race-inline">`;
    raceParts.forEach((key, i) => {{
        if (i > 0) html += `<span class="separator">·</span>`;
        html += `<div class="setup-part">`;
        html += `<span class="setup-label">${{key.toUpperCase()}}</span>`;
        html += `<span class="setup-val">${{race[key] || 0}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    html += `<div class="setup-meta" style="margin-top:0.5rem">Temperatura: ${{race.temp || '?'}}°C</div>`;
    html += `</div>`;

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
    html += `<div class="rec-card" style="margin-top:1rem"><h3>Plan treningowy</h3>`;
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
        html += `<div class="rec-card" style="margin-top:1rem"><h3>Notatki</h3>`;
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
    
    let html = '';
    
    // Nagłówek
    html += `<div class="practice-header">`;
    html += `<h2>🏁 Praktyka - Binary Search Setup</h2>`;
    html += `<div class="track-info">\${{nextRace.track || 'Nieznany tor'}} · Sezon \${{nextRace.season || '?'}} · Wyścig \${{nextRace.race || '?'}}</div>`;
    html += `</div>`;
    
    // Driver stats mini
    const ma = driverMargin.MA || 0;
    const halfMa = driverMargin.half_MA || 0;
    html += `<div class="driver-stats-mini">`;
    html += `<div class="driver-stat-mini"><div class="label">Margines</div><div class="value" style="color:var(--accent-yellow)">\${{halfMa}}</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">MA</div><div class="value">\${{ma}}</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Temp</div><div class="value">\${{practiceTemp}}°C</div></div>`;
    html += `<div class="driver-stat-mini"><div class="label">Opony</div><div class="value">\${{pred.sessions?.practice?.tyres || 'medium'}}</div></div>`;
    html += `</div>`;
    
    // Timeline
    html += `<div class="practice-timeline">`;
    const steps = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'];
    const currentLap = 1; // Always start from lap 1
    steps.forEach((step, i) => {{
        const lapNum = i + 1;
        const isDone = lapNum < currentLap;
        const isCurrent = lapNum === currentLap;
        const statusClass = isDone ? 'completed' : (isCurrent ? 'current' : '');
    html += `<div class="timeline-step \${{statusClass}}">`;
    html += `<div class="timeline-dot">\${{lapNum}}</div>`;
    html += `<div class="timeline-label">\${{step}}</div>`;
        html += `</div>`;
    }});
    html += `</div>`;
    
    // Lap cards
    laps.forEach((lap, i) => {{
        const lapNum = lap.lap;
        const isDone = lapNum < currentLap;
        const isCurrent = lapNum === currentLap;
        
        // Calculate suggested setup based on binary search logic
        let suggestedSetup = {{...practiceSetup}};
        if (lapNum === 1) {{
            // First lap - use recommended setup
        }} else if (lapNum === 2) {{
            // After lap 1 feedback, try +halfMa if not satisfied
            suggestedSetup.fw = practiceSetup.fw + halfMa;
            suggestedSetup.rw = practiceSetup.rw + halfMa;
        }} else if (lapNum === 3) {{
            // Continue in direction from lap 2
            suggestedSetup.fw = practiceSetup.fw + halfMa + Math.floor(halfMa/2);
            suggestedSetup.rw = practiceSetup.rw + halfMa + Math.floor(halfMa/2);
        }} else if (lapNum === 4) {{
            // Change direction
            suggestedSetup.fw = practiceSetup.fw - halfMa;
            suggestedSetup.rw = practiceSetup.rw - halfMa;
        }} else {{
            // Narrow down binary search
            const offset = Math.floor(halfMa / (lapNum - 2));
            suggestedSetup.fw = practiceSetup.fw - halfMa + offset;
            suggestedSetup.rw = practiceSetup.rw - halfMa + offset;
        }}
        
        html += `<div class="lap-card \${{isCurrent ? 'current' : ''}} \${{isDone ? 'done' : ''}}">`;
        
        // Lap header
        html += `<h3>Lap \${{lapNum}}</h3>`;
        if (isDone) {{
            html += `<span class="lap-badge done">✓ Wykonane</span>`;
        }} else if (isCurrent) {{
            html += `<span class="lap-badge next">▶ Teraz</span>`;
        }} else {{
            html += `<span class="lap-badge pending">⏳ Dalej</span>`;
        }}
        html += `</div>`;
        
        // Setup chips
        html += `<div class="lap-setup">`;
        ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
            const val = suggestedSetup[key] || 0;
            html += `<div class="setup-chip">`;
            html += `<span class="label">\${{key.toUpperCase()}}</span>`;
            html += `<span class="value">\${{val}}</span>`;
            html += `</div>`;
        }});
        html += `</div>`;
        
        // Binary search visual
        if (!isDone) {{
            html += `<div class="binary-search-visual">`;
            if (lapNum === 1) {{
                html += `<div class="search-range">Start: \${{practiceSetup.fw - halfMa}} → \${{practiceSetup.fw + halfMa}}</div>`;
            }} else if (lapNum === 2) {{
                html += `<div class="search-arrow">Jeśli nie satisfied → FW +\${{halfMa}}</div>`;
            }} else if (lapNum === 4) {{
                html += `<div class="search-arrow">Jeśli gorszy → zmień kierunek</div>`;
            }} else {{
                html += `<div class="search-range">Zawężanie ±\${{Math.floor(halfMa / (lapNum - 2))}}</div>`;
            }}
            html += `</div>`;
        }}
        
        // Instruction
        if (!isDone) {{
            html += `<div class="lap-instruction">`;
            html += `<div class="instruction">\${{lap.action}}</div>`;
            html += `<div class="note">\${{lap.note}}</div>`;
            html += `</div>`;
        }}
        
        html += `</div>`;
    }});
    
    // Session summary - Q1 after practice
    html += `<div class="session-summary">`;
    html += `<h3>📊 Po praktyce → Q1 Setup</h3>`;
    const q1Setup = pred.sessions?.q1?.setup || pred.setup_q1 || {{}};
    html += `<div class="lap-setup">`;
    ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
        const val = q1Setup[key] || 0;
        html += `<div class="setup-chip">`;
        html += `<span class="label">\${{key.toUpperCase()}}</span>`;
        html += `<span class="value">\${{val}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    html += `<div class="next-up">`;
    html += `<span class="icon">🏎️</span>`;
    html += `<div><div class="label">Następna sesja</div><div class="value">Q1 - Soft tyres, \${{pred.sessions?.q1?.temp || 22}}°C</div></div>`;
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
        html += `<span class="label">\${{key.toUpperCase()}}</span>`;
        html += `<span class="value">\${{val}}</span>`;
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
        html += `<span class="label">\${{key.toUpperCase()}}</span>`;
        html += `<span class="value">\${{val}}</span>`;
        html += `</div>`;
    }});
    html += `</div>`;
    const fs = pred.sessions?.race?.fuel_strategy || {{}};
    html += `<div class="next-up">`;
    html += `<span class="icon">⛽</span>`;
    html += `<div><div class="label">Strategia paliwowa</div><div class="value">\${{fs.pits || 2}} pit stopy · \${{fs.total_fuel || 257}}L</div></div>`;
    html += `</div>`;
    html += `</div>`;
    
    container.innerHTML = html;
}}

function renderResults() {{
    if (RACE_DATA.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th><th>Q1</th><th>Q2</th><th>Pit</th>';
    html += '<th>Opony koniec</th><th>Paliwo koniec</th><th>Bilans</th>';
    html += '</tr></thead><tbody>';

    // Od najnowszego do najstarszego
    for (let i = RACE_DATA.length - 1; i >= 0; i--) {{
        const rd = RACE_DATA[i].race_data || {{}};
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

function renderSetups() {{
    if (RACE_DATA.length === 0) return;

    // Grupujemy setupy per tor
    const byTrack = {{}};
    RACE_DATA.forEach(race => {{
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
    if (RACE_DATA.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th><th>Start</th>';
    html += '<th>Pit 1</th><th>Pit 2</th><th>Pit 3</th><th>Pit 4</th>';
    html += '<th>Opony %</th><th>Paliwo L</th>';
    html += '</tr></thead><tbody>';

    for (let i = RACE_DATA.length - 1; i >= 0; i--) {{
        const rd = RACE_DATA[i].race_data || {{}};
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
    if (RACE_DATA.length === 0) return;

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>S/R</th><th>Tor</th>';
    html += '<th>Przychody</th><th>Koszty</th><th>Bilans</th><th>Saldo</th>';
    html += '</tr></thead><tbody>';

    for (let i = RACE_DATA.length - 1; i >= 0; i--) {{
        const rd = RACE_DATA[i].race_data || {{}};
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
        <h3 style="margin-top:2rem;margin-bottom:1rem">Dostawca opon: ${{ts.name}}</h3>
        <div class="driver-stats">
            <div class="stat-item"><div class="stat-name">Peak temp</div><div class="stat-value">${{ts.peak_temp || '-'}}°C</div></div>
            <div class="stat-item"><div class="stat-name">Dry perf</div><div class="stat-value">${{ts.dry_perf || '-'}}</div></div>
            <div class="stat-item"><div class="stat-name">Wet perf</div><div class="stat-value">${{ts.wet_perf || '-'}}</div></div>
            <div class="stat-item"><div class="stat-name">Durability</div><div class="stat-value">${{ts.durability || '-'}}</div></div>
            <div class="stat-item"><div class="stat-name">Warmup</div><div class="stat-value">${{ts.warmup || '-'}}</div></div>
        </div>`;
    }}

    document.getElementById('tab-driver').innerHTML = html;
}}

// Start!
render();
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

    # 2. Wygeneruj HTML
    print("\n2. Generowanie HTML...")
    html = generate_html(race_data, prediction_data, calendar_data)

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