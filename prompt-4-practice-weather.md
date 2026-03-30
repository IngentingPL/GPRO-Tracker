Przeczytaj CLAUDE.md i predictor.py.

# Część 4/4: Rozbudowa predictora — Practice Plan, pogoda wet/dry, wing split

## Zmiany w predictor.py

### 1. Dodaj adjust_for_weather(setup, from_weather, to_weather)

Konwersja dry↔wet. Stałe z community:
```python
DRY_TO_WET = {"fw": +132, "rw": +132, "eng": -127, "bra": +55, "gear": -94, "susp": -141}
```
Jeśli Q1 dry i Q2 wet → dodaj DRY_TO_WET do setupu Q2 (oprócz korekty temperaturowej).
Jeśli Q1 wet i Q2 dry → dodaj odwrotne wartości.
Jeśli oba dry lub oba wet → nie koryguj.

### 2. Dodaj adjust_for_humidity(base_setup, base_hum, target_hum)

Wilgotność wpływa słabiej niż temperatura. Korekta proporcjonalna:
```python
for setting in TEMP_COEFFICIENTS:
    delta = TEMP_COEFFICIENTS[setting] * 0.1 * (target_hum - base_hum)
    # 0.1 = humidity ma ~10% wpływu temperatury
```

### 3. Dodaj practice_plan do prediction.json

Pole `practice_plan` z listą instrukcji per okrążenie:

```python
practice_plan = {
    "laps": [
        {"lap": 1, "action": "Użyj rekomendowanego setupu", "note": "Sprawdź czy satisfied"},
        {"lap": 2, "action": "Jeśli satisfied → zmień FW o +30", "note": "Porównaj czas z lap 1"},
        {"lap": 3, "action": "Jeśli lap2 wolniejszy → wróć do lap1 i zmień FW o -30", "note": "Szukamy kierunku"},
        {"lap": 4, "action": "Fine-tune najlepszy FW z krokiem ±15", "note": ""},
        {"lap": 5, "action": "Powtórz dla ENG lub SUSP", "note": "Drugie najważniejsze ustawienie"},
        {"lap": 6, "action": "Fine-tune ENG/SUSP", "note": ""},
        {"lap": 7, "action": "Testuj wing split: FW+20, RW-20 vs obecny", "note": "Suma FW+RW bez zmian"},
        {"lap": 8, "action": "Finalna weryfikacja najlepszego setupu", "note": "Ten setup idzie do Q1"},
    ],
    "priority_note": "FW/RW mają największy wpływ na czas. ENG i SUSP na drugim miejscu. BRA i GEAR zwykle trafiasz od razu.",
}
```

Jeśli predictor ma confidence "high" → plan skupia się na fine-tuningu (kroki ±15-30).
Jeśli confidence "low"/"very_low" → plan zaczyna od binary search (kroki ±128-256).

### 4. Dodaj tyre_strategy do prediction.json

Z historii pit stopów oblicz szacowaną żywotność opon:
```python
for each pit in history_of_this_track:
    tyre_life = pit["lap"] / (100 - pit["tyre_condition"]) * 100
# średnia = estimated total laps on one set
```

Dodaj pole:
```json
"tyre_strategy": {
    "est_tyre_life_laps": 25,
    "bottleneck": "fuel",
    "bottleneck_explanation": "Paliwo na ~18 okr, opony na ~25 okr → pit stopy wynikają z paliwa"
}
```

## Zmiany w generate_dashboard.py

Dodaj renderowanie practice_plan w zakładce "Następny wyścig":
- Lista kroków z numerem okrążenia i akcją
- Sekcja pod setupami, przed notatkami
- Użyj istniejącej klasy data-table lub prostej listy

Dodaj renderowanie tyre_strategy:
- "Opony: ~X okr · Bottleneck: PALIWO/OPONY"
- Pod strategią paliwową

## Zasady
- Nie zmieniaj istniejących funkcji w predictor.py — dodawaj nowe
- Komentarze po polsku z mini-lekcjami
- Zaokrąglaj do int, ogranicz 0-999
