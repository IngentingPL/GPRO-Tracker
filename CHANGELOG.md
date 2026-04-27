# GPRO Tracker - Changelog

## 2026-04-27

### ✨ Nowe funkcje

- **Endpoint Practice API** (`gpro_fetcher.py`)
  - Dodano `fetch_practice()` - pobiera dane z endpointu `/Practice` w trakcie tygodnia wyścigowego
  - Dodano `extract_practice_data()` - przetwarza dane praktyk do formatu pliku wyścigu
  - Dodano `fetch_current_week_data()` - nowa funkcja do pobierania danych praktyk
  - Dodano argument `--mode`: `post-race` (domyślnie) lub `current-week`

- **Zakładka "Następny wyścig"** (`predictor.py`)
  - Naprawiono wyświetlanie - teraz pokazuje TYLKO jeden następny krok z pełnym setupem
  - Dodano `get_completed_sessions_from_race()` - wykrywa wykonane sesje z pliku wyścigu
  - Dodano `find_next_step()` - wyznacza następny krok wg kolejności P1→P2→...→P8→Q1→Q2→Race
  - Ukończone sesje pokazują swój setup i feedback kierowcy
  - Przyszłe sesje mają `setup: null`

### 🔧 Naprawy błędów

- **Problem z praktykami** - predictor zawsze pokazywał P1
  - Przyczyna: brak danych o wykonanych sesjach w trakcie tygodnia
  - Rozwiązanie: dodano pobieranie z endpointu `/Practice` API GPRO

- **Dashboard HTML**
  - Usunięto duplikat górnego paska podsumowania

### 📖 Użycie

```bash
# Pobierz dane po wyścigu (standardowy tryb)
python gpro_fetcher.py

# Pobierz dane praktyk w trakcie tygodnia
python gpro_fetcher.py --mode current-week
```

### ✅ Weryfikacja (przypadki testowe)

| Przypadek | Wynik |
|-----------|-------|
| Brak sesji → P1 | ✓ OK |
| P1 ukończone → P2 | ✓ OK |
| P1-P8 ukończone → Q1 | ✓ OK |
| P1-P8+Q1 ukończone → Q2 | ✓ OK |

---

## Historia wersji

### Struktura projektu

```
GPRO-Tracker/
├── gpro_fetcher.py      # Pobieranie danych z GPRO API
├── predictor.py         # Generowanie predykcji setupów
├── generate_dashboard.py # Generowanie dashboardu HTML
├── index.html           # Dashboard (generowany)
├── data/
│   ├── races/         # Pliki wyścigów S*R*.json
│   ├── prediction.json # Predykcje setupów
│   ├── calendar.json  # Kalendarz sezonu
│   └── current_context.json # Bieżący kontekst
└── CHANGELOG.md       # Ten plik
```

### API GPRO (używane endpointy)

| Endpoint | Opis |
|---------|------|
| `Office` | Dane biura (sezon, wyścig) |
| `RaceAnalysis` | Pełna analiza wyścigu (po wyścigu) |
| `RaceSummary` | Wyniki wyścigu grupy |
| `DriProfile` | Profil kierowcy |
| `Standings` | Klasyfikacja sezonu |
| `Calendar` | Kalendarz sezonu |
| `UpdateCar` | Stan bolidu |
| `Practice` | Dane praktyk/Q1 (w trakcie tygodnia) |
| `TrackProfile` | Profil toru |

---

*Ostatnia aktualizacja: 2026-04-27*
