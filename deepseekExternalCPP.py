import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"  # Adjust if needed
EXTERNAL_CALLS_FILE = "external_calls.txt"


def extract_code_from_file(file_path):
    """Reads the full content of the given file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Could not read {file_path}: {e}")
        return None


def format_prompt_for_structure(code):
    """Formats the prompt to ask DeepSeek-Coder for structured function call metadata."""
    return f"""
You are a code analysis AI. Given this C++ code snippet, extract inter-function call relationships and return a JSON of the following structure:

{{
  "functionCalls": [
    {{
      "callerId": 1,
      "calleeId": 2,
      "isInsideIfElseOrSwitch": true,
      "isInsideLoopOrEnvironment": false,
      "isDifferentLanguage": true,
      "isDifferentModule": false,
      "isInsideClass": true,
      "isInsideFunction": false
    }}
  ]
}}

Assign unique IDs to caller/callee. Only output valid JSON. Code:
```cpp
{code}
```"""


def analyze_with_deepseek(file_path, code):
    """Sends code to DeepSeek-Coder via Ollama and returns JSON result."""
    prompt = format_prompt_for_structure(code)

    payload = {
        "model": "deepseek-coder",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            print(f"⚠️ Could not decode JSON from response for {file_path}")
            return {"error": "Invalid JSON", "raw": response.text}
    except requests.RequestException as e:
        print(f"❌ Request failed for {file_path}: {e}")
        return {"error": str(e)}


def load_external_call_files(path):
    """Loads file paths from external_calls.txt"""
    try:
        with open(path, "r") as f:
            return [line.strip().split(",")[0] for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return []


if __name__ == "__main__":
    files = load_external_call_files(EXTERNAL_CALLS_FILE)

    results = {}
    for file_path in files:
        print(f"\n🔍 Analyzing: {file_path}")
        code = extract_code_from_file(file_path)
        if code:
            result = analyze_with_deepseek(file_path, code)
            results[file_path] = result

    # Save everything to a JSON
    with open("deepseek_structured_output.json", "w") as out_file:
        json.dump(results, out_file, indent=2)

    print("\n✅ Analysis complete. Output saved to deepseek_structured_output.json")
