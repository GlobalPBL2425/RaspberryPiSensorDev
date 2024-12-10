import json

# Load JSON from file
def load_json(json_file):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {json_file}.")
    return None

json_file = "default.json"
# Load and process the JSON
sensors = load_json(json_file)
print(sensors[1]['thresholds'])