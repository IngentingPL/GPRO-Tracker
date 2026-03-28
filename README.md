# 🏎️ GPRO Tracker

Automatyczny tracker danych wyścigowych z [GPRO (Grand Prix Racing Online)](https://gpro.net).

Pobiera dane po każdym wyścigu przez GPRO API i generuje statyczny dashboard na GitHub Pages.

## Funkcje

- **Setupy per tor** — historia setupów z pogodą i warunkami
- **Paliwo & Opony** — zużycie per wyścig, pit stopy, strategia
- **Wyniki** — pozycje kwalifikacji i wyścigu
- **Finanse** — przychody, koszty, bilans per wyścig
- **Kierowca** — profil z kolorowaniem statystyk (wg porad bvk)

## Konfiguracja

### 1. Wygeneruj token API

1. Zaloguj się na [app.gpro.net](https://app.gpro.net)
2. Menu → Miscellaneous → API access
3. Skopiuj istniejący token lub wygeneruj nowy

### 2. Dodaj token jako GitHub Secret

1. W swoim repozytorium: Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `GPRO_TOKEN`
4. Value: twój token API

### 3. Włącz GitHub Pages

1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`, folder: `/ (root)`

### 4. Gotowe!

Workflow automatycznie pobiera dane po każdym wyścigu (wt/pt o 20:30 CET).
Możesz też uruchomić ręcznie: Actions → Fetch GPRO Data & Deploy → Run workflow.

## Ręczne uruchomienie

```bash
# Ustaw token
export GPRO_TOKEN="twój_token"

# Pobierz dane
python gpro_fetcher.py

# Wygeneruj dashboard
python generate_dashboard.py
```

## Struktura projektu

```
gpro-tracker/
├── gpro_fetcher.py          # Pobiera dane z GPRO API
├── generate_dashboard.py    # Generuje HTML dashboard
├── index.html               # Wygenerowany dashboard
├── data/
│   └── races/
│       ├── S109R15.json     # Dane per wyścig
│       ├── S109R16.json
│       └── latest.json      # Zawsze ostatni wyścig
├── .github/
│   └── workflows/
│       └── fetch.yml        # GitHub Actions automatyzacja
├── CLAUDE.md                # Instrukcje dla Claude Code
└── README.md
```

## Wymagania

- Python 3.8+ (brak dodatkowych bibliotek!)
- Konto GPRO z tokenem API

## Notatki

- API ma limit zapytań — skrypt jest oszczędny (~7 zapytań per wyścig)
- Dane są zapisywane jako JSON — łatwe do analizy w przyszłości
- Dashboard działa offline — dane są osadzone w HTML
