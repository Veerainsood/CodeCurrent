import json
import os

def load_and_flatten(file):
    if os.path.getsize(file) == 0:
        print(f"Skipped empty file: {file}")
        return []
    with open(file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Skipped invalid JSON file: {file} — {e}")
            return []
        if isinstance(data, list):
            flat = []
            for item in data:
                if isinstance(item, list):
                    flat.extend(item)
                else:
                    flat.append(item)
            return flat
        return []

# Merge unique functions
input_files1 = [
    "unique_functions_cpp.json",
    "unique_functions_java.json",
    "unique_functions_python.json"
]

merged_functions = []
for file in input_files1:
    merged_functions.extend(load_and_flatten(file))

with open("unique_functions_combined.json", "w", encoding="utf-8") as f:
    json.dump(merged_functions, f, indent=4)

# Merge function calls
input_files2 = [
    "function_calls_cpp.json",
    "function_calls_java.json",
    "function_calls_python.json"
]

merged_calls = []
for file in input_files2:
    merged_calls.extend(load_and_flatten(file))

with open("function_calls_combined.json", "w", encoding="utf-8") as f:
    json.dump(merged_calls, f, indent=4)

print("Merged all JSON arrays correctly, skipping empty/invalid files.")
