import json

# Load JSON file
with open("parser_output.json") as f:
    data = json.load(f)

# Filter objects where callee_path ends with .cc
filtered = [item for item in data if isinstance(item, dict) and item.get("callee_path", "").endswith(".cc")]

# Print results
print(json.dumps(filtered, indent=2))

