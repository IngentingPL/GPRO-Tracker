import json

class PredictionEngine:
    def __init__(self, race_history):
        self.race_history = race_history
        self.temperature_adjustments = {}
        self.fuel_strategy = {}
        self.driver_margins = {}

    def load_race_history(self, file_path):
        with open(file_path, 'r') as file:
            self.race_history = json.load(file)
    
    def calculate_temperature_adjustments(self):
        # Example logic for temperature adjustments
        for race in self.race_history:
            temperature = race['temperature']
            adjustment = temperature / 100  # Dummy calculation
            self.temperature_adjustments[race['race_id']] = adjustment

    def calculate_fuel_strategy(self):
        # Example logic for fuel strategy
        for race in self.race_history:
            fuel_used = race['fuel_used']
            fuel_strategy = fuel_used * 0.95  # Dummy calculation
            self.fuel_strategy[race['race_id']] = fuel_strategy
    
    def calculate_driver_margins(self):
        # Example logic for driver margins
        for race in self.race_history:
            margin = race['margin']
            self.driver_margins[race['race_id']] = margin

    def output_predictions(self, output_path):
        predictions = {
            'temperature_adjustments': self.temperature_adjustments,
            'fuel_strategy': self.fuel_strategy,
            'driver_margins': self.driver_margins
        }
        with open(output_path, 'w') as output_file:
            json.dump(predictions, output_file, indent=4)

# Example usage
if __name__ == '__main__':
    engine = PredictionEngine([])
    engine.load_race_history('data/race_history.json')  # Path to race history
    engine.calculate_temperature_adjustments()
    engine.calculate_fuel_strategy()
    engine.calculate_driver_margins()
    engine.output_predictions('data/prediction.json')
