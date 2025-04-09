import json

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def make_key(obj):
    """Create a matching key from output.json or parentFunctionParameters"""
    return (
        obj.get("name"),
        # obj.get("file"),
        obj.get("path"),
        obj.get("language"),
        tuple(obj.get("parameters", {}).get("types", [])),
        obj.get("parameters", {}).get("count"),
        obj.get("parentClass"),
        obj.get("returnType")
    )

# Step 1: Load and map output.json
output_data = load_json("output.json")
function_map = {}

for func in output_data:
    key = make_key(func)
    function_map[key] = func["id"]

# Step 2: Load parser_output.json and enrich with parentFunctionId
parser_data = load_json("parser_output.json")["functions"]

# Assume `parser_data`, `function_map`, and `make_key()` are already defined
matched_calls = []

for item in parser_data:
    # Build callee key
    callee_path = {
        "name": item.get("name"),
        # "file": item.get("file"),
        "path": item.get("callee_path"),
        "language": item.get("language"),
        "parameters": item.get("parameters", {}),
        "parentClass": item.get("parentClass"),
        "returnType": item.get("calleeReturnType")
    }
    callee_key = make_key(callee_path)
    callee_id = function_map.get(callee_key)

    # Build caller key
    caller_path = {
        "name": item.get("parentFunction"),
        # "file": item.get("file"),
        "path": item.get("caller_path"),
        "language": item.get("language"),
        "parameters": item.get("parentFunctionParameters", {}),
        "parentClass": item.get("parentFunctionClass"),
        "returnType": item.get("parentFunctionReturnType")
    }
    caller_key = make_key(caller_path)
    caller_id = function_map.get(caller_key)

    # If both IDs are found, record the relationship
    
    if caller_id is not None and callee_id is not None:
        matched_calls.append({
            "caller_id": caller_id,
            "callee_id": callee_id,
            "is_foreign_call": item.get("is_foreign_call"),
            "isInsideIfElseOrSwitch": item.get("is_foreign_call"),
            "isInsideLoopOrEnvironment": item.get("isInsideLoopOrEnvironment"),
            "isDifferentLanguage": item.get("isDifferentLanguage"),
            "isDifferentModule": item.get("isDifferentModule"),
            "isInsideClass": item.get("isInsideClass"),
            "isInsideFunction": item.get("isInsideFunction"),
        })

# Save to a new JSON file
with open("caller_callee_pairs.json", "w") as f:
    json.dump(matched_calls, f, indent=4)
