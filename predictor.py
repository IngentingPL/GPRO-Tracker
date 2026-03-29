import json
import os

# Constants
TEMP_COEFFICIENTS = {"low": 0.9, "high": 1.1}
DRY_TO_WET_CONVERSION = {"dry": 1.0, "wet": 0.5}
DOWNFORCE_START = 1.0
FUEL_RATES = {"default": 1.2}

# Load historical race data

def load_history(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Find the base setup configuration

def find_base_setup(setups, weather):
    # Logic to find base setup according to weather conditions
    return setups.get(weather, setups['default'])

# Adjust fuel calculations based on temperature

def adjust_for_temperature(base_fuel, temperature):
    if temperature < 20:
        return base_fuel * TEMP_COEFFICIENTS["low"]
    else:
        return base_fuel * TEMP_COEFFICIENTS["high"]

# Calculate the fuel strategy for the race

def calculate_fuel_strategy(setup, temperature):
    base_fuel = setup['fuel']
    return adjust_for_temperature(base_fuel, temperature)

# Calculate driver margin based on setups and performance

def calculate_driver_margin(setup, weather):
    # Logic to calculate driver margin
    return setup['performance'] * DRY_TO_WET_CONVERSION.get(weather, 1.0)

# Generate the final prediction

def generate_prediction():
    race_data = load_history('data/races/S*R*.json')
    predictions = []
    for race in race_data:
        setups = race['setups']
        weather = race['weather']
        base_setup = find_base_setup(setups, weather)
        fuel_strategy = calculate_fuel_strategy(base_setup, race['temperature'])
        margin = calculate_driver_margin(base_setup, weather)
        prediction = {
            'race': race['id'],
            'fuel_strategy': fuel_strategy,
            'margin': margin,
        }
        predictions.append(prediction)
    # Save predictions to JSON file
    with open('data/prediction.json', 'w') as pred_file:
        json.dump(predictions, pred_file, ensure_ascii=False, indent=4)

# Polish Documentation:
# Funkcja load_history umożliwia załadowanie danych historycznych z pliku.
# Funkcja find_base_setup wyszukuje odpowiednie ustawienia auta w zależności od warunków pogodowych.
# Funkcja adjust_for_temperature modyfikuje ilość paliwa na podstawie temperatury.
# Funkcja calculate_fuel_strategy oblicza strategię paliwową.
# Funkcja calculate_driver_margin oblicza margines kierowcy w zależności od ustawień i warunków.
# Funkcja generate_prediction generuje prognozy na podstawie danych wyścigów.