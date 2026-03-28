#!/usr/bin/env python3
"""
GPRO Dashboard Generator
=========================
Czyta pliki JSON z danymi wyścigowymi i generuje statyczną stronę HTML.
Strona jest hostowana na GitHub Pages - zero backendu, czyste HTML/CSS/JS.

Mini-lekcja: To jest wzorzec "Static Site Generator" (SSG).
Zamiast serwera generującego stronę na żądanie, generujemy HTML raz
i udostępniamy gotowy plik. GitHub Pages idealnie się do tego nadaje.
"""

import json
import os
import glob
from datetime import datetime


DATA_DIR = "data/races"
CALENDAR_FILE = "data/calendar.json"
OUTPUT_FILE = "index.html"


def load_all_races():
    """
    Wczytuje wszystkie pliki JSON z danymi wyścigowymi.
    Zwraca listę posortowaną chronologicznie (najnowsze na końcu).

    Mini-lekcja: glob.glob() znajduje pliki pasujące do wzorca.
    'S*R*.json' znaczy: litera S, cokolwiek, litera R, cokolwiek, .json.
    To jak wyrażenie regularne, ale prostsze - idealne do plików.
    """
    races = []
    for filepath in glob.glob(os.path.join(DATA_DIR, "S*R*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                races.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Pominięto {filepath}: {e}")

    # Sortujemy po sezonie i numerze wyścigu
    def sort_key(r):
        rd = r.get("race_data", {})
        try:
            return (int(rd.get("season", "0")), int(rd.get("race", "0")))
        except (ValueError, TypeError):
            return (0, 0)

    races.sort(key=sort_key)
    return races


def load_calendar():
    """
    Wczytuje plik kalendarza (data/calendar.json).

    Mini-lekcja: Kalendarz jest osobnym plikiem, bo to dane współdzielone
    między wyścigami - nie chcemy ich kopiować do każdego pliku wyścigowego.
    Jeśli plik nie istnieje, zwracamy pusty słownik.
    """
    if not os.path.exists(CALENDAR_FILE):
        print("  Brak pliku kalendarza (data/calendar.json)")
        return {}

    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Błąd odczytu kalendarza: {e}")
        return {}


def generate_html(races):
    """
    Generuje kompletny plik HTML z dashboardem.
    Dane wyścigowe są osadzone bezpośrednio w JS jako zmienna -
    dzięki temu strona działa offline bez żadnego serwera.
    """

    # Przygotowujemy dane do osadzenia w JS
    js_data = json.dumps(races, ensure_ascii=False)

    # Ładujemy i osadzamy kalendarz osobno
    calendar = load_calendar()
    js_calendar = json.dumps(calendar, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
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
    <button class="tab-btn" data-tab="results">Wyniki</button>
    <button class="tab-btn" data-tab="setups">Setupy</button>
    <button class="tab-btn" data-tab="fuel">Paliwo & Opony</button>
    <button class="tab-btn" data-tab="finances">Finanse</button>
    <button class="tab-btn" data-tab="driver">Kierowca</button>
</div>

<!-- Zawartość zakładek -->
<div class="tab-content active" id="tab-nextrace"></div>
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
const RACE_DATA = {js_data};

// Dane kalendarza (pobrane z osobnego pliku data/calendar.json)
const CALENDAR_DATA = {js_calendar};

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
// ZAKŁADKA: NASTĘPNY WYŚCIG (rekomendacje)
// Mini-lekcja: Ta funkcja analizuje dane historyczne i generuje
// sugestie na następny wyścig. To NIE są pewne prognozy -
// każdy wyścig zależy od wielu czynników (pogoda, rywal, RNG).
// ==========================================================
function renderNextRace() {{
    const container = document.getElementById('tab-nextrace');

    // --- Szukamy następnego wyścigu w kalendarzu ---
    // Kalendarz z API zwraca listę torów z numerami wyścigów
    const calData = (CALENDAR_DATA && CALENDAR_DATA.data) || {{}};
    const calendarRaces = calData.races || calData.calendar || [];

    // Ustalamy numer następnego wyścigu na podstawie ostatniego w danych
    let nextRaceNum = null;
    let nextTrackName = null;
    let nextTrackCountry = null;
    let currentSeason = null;

    if (RACE_DATA.length > 0) {{
        const lastRd = RACE_DATA[RACE_DATA.length - 1].race_data || {{}};
        currentSeason = lastRd.season;
        nextRaceNum = (parseInt(lastRd.race) || 0) + 1;
    }}

    // Szukamy toru w kalendarzu po numerze wyścigu
    if (Array.isArray(calendarRaces) && nextRaceNum) {{
        const nextEntry = calendarRaces.find(c =>
            parseInt(c.raceNb || c.race || c.number) === nextRaceNum
        );
        if (nextEntry) {{
            nextTrackName = nextEntry.trackName || nextEntry.track || nextEntry.name || null;
            nextTrackCountry = nextEntry.trackCountry || nextEntry.country || '';
        }}
    }}

    // Fallback: jeśli nie znaleźliśmy w kalendarzu, pokaż ogólny komunikat
    if (!nextTrackName && !nextRaceNum) {{
        container.innerHTML = `
            <div class="empty-state">
                <h2>Brak danych</h2>
                <p>Potrzebuję danych z co najmniej jednego wyścigu i kalendarza.</p>
                <p style="margin-top:1rem"><code>python gpro_fetcher.py</code></p>
            </div>`;
        return;
    }}

    // --- Szukamy historii na tym torze ---
    const trackHistory = [];
    if (nextTrackName) {{
        RACE_DATA.forEach(race => {{
            const rd = race.race_data || {{}};
            // Porównujemy po nazwie toru (ignorujemy wielkość liter)
            if (rd.track && rd.track.toLowerCase() === nextTrackName.toLowerCase()) {{
                trackHistory.push(rd);
            }}
        }});
    }}

    const hasHistory = trackHistory.length > 0;

    // =============================================
    // 1. INFO O TORZE
    // =============================================
    let html = `<div class="rec-header">`;
    html += `<h2>${{nextTrackName || 'Wyścig #' + nextRaceNum}}</h2>`;
    if (nextTrackCountry) {{
        html += `<span class="rec-subtitle">${{nextTrackCountry}}</span>`;
    }}
    if (currentSeason) {{
        html += `<span class="rec-subtitle"> · Sezon ${{currentSeason}}, Wyścig ${{nextRaceNum}}</span>`;
    }}
    if (hasHistory) {{
        html += `<p class="rec-subtitle" style="margin-top:0.5rem">Mamy dane z ${{trackHistory.length}} wyścig${{trackHistory.length === 1 ? 'u' : 'ów'}} na tym torze</p>`;
    }} else {{
        html += `<p class="rec-subtitle" style="margin-top:0.5rem;color:var(--accent-yellow)">Brak historii na tym torze</p>`;
    }}
    html += `</div>`;

    html += `<div class="rec-grid">`;

    // =============================================
    // 2. REKOMENDOWANY SETUP
    // =============================================
    html += `<div class="rec-card"><h3>Setup</h3>`;

    if (hasHistory) {{
        // Bierzemy ostatni wyścig na tym torze
        const lastTrack = trackHistory[trackHistory.length - 1];
        const raceSetup = (lastTrack.setups || []).find(s =>
            s.session && s.session.toLowerCase().includes('race')
        ) || (lastTrack.setups || [])[0];

        if (raceSetup) {{
            html += `<div class="setup-values">`;
            ['fw', 'rw', 'eng', 'bra', 'gear', 'susp'].forEach(key => {{
                html += `
                <div class="setup-item">
                    <div class="setup-label">${{key.toUpperCase()}}</div>
                    <div class="setup-val">${{raceSetup[key] || '-'}}</div>
                </div>`;
            }});
            html += `</div>`;

            // Warunki pogodowe z tamtego wyścigu
            const w = lastTrack.weather || {{}};
            const q1w = w.q1 || {{}};
            html += `<div class="setup-meta">Ostatnio użyty: S${{lastTrack.season}}R${{lastTrack.race}} · ${{q1w.temp || '?'}}°C · ${{q1w.humidity || '?'}}% wilg. · ${{q1w.condition || '?'}}</div>`;

            // Jeśli mamy wiele wyścigów, pokażmy różnice
            if (trackHistory.length > 1) {{
                html += `<div class="rec-note">Masz ${{trackHistory.length}} wyścigów na tym torze - sprawdź zakładkę Setupy dla porównania</div>`;
            }}
        }} else {{
            html += `<p>Brak danych setupu z tego toru.</p>`;
        }}
    }} else {{
        html += `<p class="rec-warn">Brak historii - użyj metody binary search (start od 512)</p>`;
        html += `<div class="rec-note">Metoda binary search: ustaw każdy parametr na 512, potem dziel zakres na pół w zależności od Q1 vs Q2.</div>`;
    }}

    html += `<div class="rec-note">Setup zależy od pogody i temperatury - sprawdź prognozę przed wyścigiem</div>`;
    html += `</div>`;

    // =============================================
    // 3. REKOMENDACJA PALIWOWA
    // =============================================
    html += `<div class="rec-card"><h3>Paliwo</h3>`;

    // Obliczamy średnie zużycie paliwa na okrążenie
    let fuelPerLap = null;
    let fuelSource = '';

    // Próbujemy z historii tego toru
    if (hasHistory) {{
        const fuelData = [];
        trackHistory.forEach(rd => {{
            const startFuel = rd.start_fuel;
            const pits = rd.pits || [];
            if (startFuel && pits.length > 0 && pits[0].lap) {{
                // Zużycie = paliwo startowe - paliwo na pierwszym picie / ilość okrążeń
                const fuelAtPit = pits[0].fuel_left;
                if (fuelAtPit != null) {{
                    const consumption = (startFuel - fuelAtPit) / pits[0].lap;
                    if (consumption > 0 && consumption < 20) {{ // sanity check
                        fuelData.push(consumption);
                    }}
                }}
            }}
        }});
        if (fuelData.length > 0) {{
            fuelPerLap = fuelData.reduce((a, b) => a + b, 0) / fuelData.length;
            fuelSource = `z ${{fuelData.length}} wyścig${{fuelData.length === 1 ? 'u' : 'ów'}} na tym torze`;
        }}
    }}

    // Fallback: średnia ze WSZYSTKICH wyścigów
    if (fuelPerLap === null) {{
        const allFuelData = [];
        RACE_DATA.forEach(race => {{
            const rd = race.race_data || {{}};
            const startFuel = rd.start_fuel;
            const pits = rd.pits || [];
            if (startFuel && pits.length > 0 && pits[0].lap) {{
                const fuelAtPit = pits[0].fuel_left;
                if (fuelAtPit != null) {{
                    const consumption = (startFuel - fuelAtPit) / pits[0].lap;
                    if (consumption > 0 && consumption < 20) {{
                        allFuelData.push(consumption);
                    }}
                }}
            }}
        }});
        if (allFuelData.length > 0) {{
            fuelPerLap = allFuelData.reduce((a, b) => a + b, 0) / allFuelData.length;
            fuelSource = `średnia z ${{allFuelData.length}} wyścigów (brak danych z tego toru)`;
        }}
    }}

    if (fuelPerLap !== null) {{
        html += `<div class="rec-row"><span class="rec-label">Szacowane zużycie</span><span class="rec-value">${{fuelPerLap.toFixed(2)}} L/lap</span></div>`;
        html += `<div class="rec-row"><span class="rec-label">Źródło</span><span>${{fuelSource}}</span></div>`;

        // Sugerowana strategia pit stopów
        // Zakładamy zbiornik 180L i ~70 okrążeń (standardowe wartości)
        // Obliczamy ile okrążeń na pełnym baku
        const maxFuel = 180;
        const lapsPerTank = Math.floor(maxFuel / fuelPerLap);

        html += `<div class="rec-row" style="margin-top:0.5rem"><span class="rec-label">Okrążeń na pełnym baku</span><span class="rec-value">~${{lapsPerTank}}</span></div>`;

        // Pokaż historię pit stopów z tego toru
        if (hasHistory) {{
            html += `<div style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-muted)">Historia pit stopów na tym torze:</div>`;
            trackHistory.forEach(rd => {{
                const pits = rd.pits || [];
                const pitLaps = pits.map(p => 'Lap ' + p.lap + ' (' + (p.refilled_to || '?') + 'L)').join(', ');
                html += `<div class="rec-row"><span class="rec-label">S${{rd.season}}R${{rd.race}}</span><span>${{rd.start_fuel}}L start · ${{pitLaps || 'brak pit'}}</span></div>`;
            }});
        }}
    }} else {{
        html += `<p class="rec-warn">Za mało danych do oszacowania zużycia paliwa</p>`;
    }}

    html += `<div class="rec-note">Wartości orientacyjne - rzeczywiste zużycie zależy od setupu, pogody i stylu jazdy</div>`;
    html += `</div>`;

    // =============================================
    // 4. REKOMENDACJA OPONOWA
    // =============================================
    html += `<div class="rec-card"><h3>Opony</h3>`;

    // Dane dostawcy opon z ostatniego wyścigu
    if (RACE_DATA.length > 0) {{
        const lastRace = RACE_DATA[RACE_DATA.length - 1].race_data || {{}};
        const ts = lastRace.tyre_supplier || {{}};

        if (ts.name) {{
            html += `<div class="rec-row"><span class="rec-label">Dostawca</span><span class="rec-value">${{ts.name}}</span></div>`;
            html += `<div class="rec-row"><span class="rec-label">Peak temp</span><span>${{ts.peak_temp || '?'}}°C</span></div>`;
            html += `<div class="rec-row"><span class="rec-label">Durability</span><span>${{ts.durability || '?'}}</span></div>`;
            html += `<div class="rec-row"><span class="rec-label">Dry perf</span><span>${{ts.dry_perf || '?'}}</span></div>`;
            html += `<div class="rec-row"><span class="rec-label">Wet perf</span><span>${{ts.wet_perf || '?'}}</span></div>`;
        }}
    }}

    // Historia zużycia opon na tym torze
    if (hasHistory) {{
        html += `<div style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-muted)">Zużycie opon na tym torze:</div>`;

        const tyreLapEstimates = [];
        trackHistory.forEach(rd => {{
            const pits = rd.pits || [];
            // Obliczamy ile okrążeń opony wytrzymały do pierwszego pitu
            if (pits.length > 0 && pits[0].tyre_condition != null && pits[0].lap) {{
                const tyreAtPit = pits[0].tyre_condition;
                // Zużycie % na okrążenie: (100 - stan_przy_picie) / okrążenia
                const wearPerLap = (100 - tyreAtPit) / pits[0].lap;
                // Szacujemy ile okrążeń do ~10% (minimalny bezpieczny stan)
                if (wearPerLap > 0) {{
                    const estimatedLaps = Math.floor(90 / wearPerLap);
                    tyreLapEstimates.push(estimatedLaps);
                }}
                html += `<div class="rec-row"><span class="rec-label">S${{rd.season}}R${{rd.race}}</span><span>Pit na lap ${{pits[0].lap}} · ${{tyreAtPit}}% opon</span></div>`;
            }}
        }});

        if (tyreLapEstimates.length > 0) {{
            const avgTyreLaps = Math.round(tyreLapEstimates.reduce((a, b) => a + b, 0) / tyreLapEstimates.length);
            html += `<div class="rec-row" style="margin-top:0.5rem"><span class="rec-label">Szacowana wytrzymałość</span><span class="rec-value">~${{avgTyreLaps}} okrążeń</span></div>`;
        }}
    }} else {{
        // Fallback: ogólna estymacja ze wszystkich wyścigów
        const allTyreLaps = [];
        RACE_DATA.forEach(race => {{
            const rd = race.race_data || {{}};
            const pits = rd.pits || [];
            if (pits.length > 0 && pits[0].tyre_condition != null && pits[0].lap) {{
                const wearPerLap = (100 - pits[0].tyre_condition) / pits[0].lap;
                if (wearPerLap > 0) {{
                    allTyreLaps.push(Math.floor(90 / wearPerLap));
                }}
            }}
        }});
        if (allTyreLaps.length > 0) {{
            const avg = Math.round(allTyreLaps.reduce((a, b) => a + b, 0) / allTyreLaps.length);
            html += `<div class="rec-row"><span class="rec-label">Śr. wytrzymałość (wszystkie tory)</span><span class="rec-value">~${{avg}} okrążeń</span></div>`;
        }}
    }}

    html += `<div class="rec-note">Wytrzymałość opon zależy od toru, temperatury i peak temp dostawcy</div>`;
    html += `</div>`;

    // =============================================
    // 5. RYZYKO
    // =============================================
    html += `<div class="rec-card"><h3>Ryzyko</h3>`;
    html += `<div class="rec-row"><span class="rec-label">Zalecane ryzyko</span><span class="rec-value">0</span></div>`;
    html += `<p style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-secondary)">Rookie - nie używaj ryzyka. Ryzyko zwiększa szansę na awarię i błędy kierowcy. Na poziomie Rookie zysk jest minimalny, a straty mogą być duże.</p>`;
    html += `</div>`;

    html += `</div>`; // zamknięcie rec-grid

    // Disclaimer
    html += `<div class="rec-disclaimer">Wszystkie rekomendacje to szacunki oparte na danych historycznych. Rzeczywiste warunki wyścigu (pogoda, temperatura, zmiany w bolidzie) mogą znacząco wpłynąć na wyniki. Zawsze weryfikuj sugestie przed wyścigiem.</div>`;

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
</html>"""

    return html


def main():
    print("=" * 60)
    print("GPRO Dashboard Generator")
    print("=" * 60)

    races = load_all_races()
    print(f"  Załadowano {len(races)} wyścigów")

    html = generate_html(races)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Wygenerowano: {OUTPUT_FILE}")
    print(f"  Rozmiar: {len(html) // 1024} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
