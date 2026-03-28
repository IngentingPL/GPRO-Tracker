# CLAUDE.md - Instrukcje dla Claude Code

## O projekcie

GPRO Tracker — automatyczny tracker danych z gry GPRO (Grand Prix Racing Online).
Pobiera dane wyścigowe przez oficjalne API i generuje statyczny dashboard HTML na GitHub Pages.

## Architektura

1. `gpro_fetcher.py` — pobiera dane z GPRO API, zapisuje JSON do `data/races/`
2. `generate_dashboard.py` — czyta JSONy, generuje `index.html` z osadzonymi danymi
3. GitHub Actions workflow uruchamia oba skrypty po wyścigach (wt/pt)

## Ważne zasady

- **Zero zewnętrznych bibliotek w Pythonie** — używamy tylko stdlib (urllib, json, os, glob)
- **Zero zewnętrznych bibliotek w JS** — czysty HTML/CSS/JS, dane osadzone w HTML
- **Komentarze po polsku** — w CSS i Python
- **Mini-lekcje** — krótkie wyjaśnienia dla początkujących w komentarzach
- **Struktura jak ScrapFEks** — statyczna strona, GitHub Pages, GitHub Actions

## Konwencje kodu

- Nazwy zmiennych i funkcji: angielskie (snake_case w Python, camelCase w JS)
- Komentarze: polskie
- CSS: custom properties w :root, zmienne --bg-*, --text-*, --accent-*
- Pliki danych: `data/races/S{sezon}R{wyścig}.json`

## API GPRO

- Bazowy URL: `https://gpro.net`
- Auth: Bearer token w nagłówku Authorization
- Endpointy: `/{lang}/backend/api/v2/{endpoint}`
- Specyfikacja: `gpro-public-api.yml` (OpenAPI 3.0)
- Limit: ~100 zapytań (pole `apiRequestsRemaining` w odpowiedzi)

## Kluczowe endpointy

- `RaceAnalysis` — setupy, pit stopy, paliwo, opony, pogoda, finanse, stan auta
- `RaceSummary` — wyniki wyścigu całej grupy
- `DriProfile` — profil kierowcy
- `Standings` — klasyfikacja sezonu
- `Calendar` — kalendarz torów
- `UpdateCar` — stan bolidu
- `AvailDrivers` — rynek kierowców (z filtrami)

## Testowanie

```bash
export GPRO_TOKEN="token_testowy"
python gpro_fetcher.py
python generate_dashboard.py
# Otwórz index.html w przeglądarce
```

## Planowane rozszerzenia

- Wykres zużycia paliwa per tor (l/km)
- Porównanie kierowców z rynku
- Predykcja setupu na podstawie historii toru
- Filtrowanie wyników po sezonie
