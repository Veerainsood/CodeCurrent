import json
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/generate"
EXTERNAL_CALLS_FILE = "external_calls.txt"
NUM_THREADS = 16  # Adjust based on your CPU

# Patterns to detect external calls
CALL_PATTERNS = re.compile(r'(Py\w+|JNI\w+|Call\w+Method|GetMethodID|FindClass)')

# Function pattern: crude but works for most C++ signatures
FUNC_DEF_PATTERN = re.compile(r'(?:[\w:<>\*&\s]+)?\s+(\w+)\s*\(([^)]*)\)\s*{', re.MULTILINE)

def extract_relevant_functions(file_path):
    """Extracts functions containing external calls only."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        relevant_blocks = []
        lines = code.splitlines()
        total_lines = len(lines)

        # Find all function blocks
        for match in FUNC_DEF_PATTERN.finditer(code):
            start_pos = match.start()
            start_line = code.count('\n', 0, start_pos)
            brace_count = 0
            found_start = False

            # Track function body using braces
            for i in range(start_line, total_lines):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
                if not found_start and '{' in lines[i]:
                    found_start = True
                    start = i
                if found_start and brace_count == 0:
                    end = i
                    block = "\n".join(lines[start:end+1])
                    if CALL_PATTERNS.search(block):
                        relevant_blocks.append(block)
                    break

        return relevant_blocks

    except Exception as e:
        print(f"❌ Failed to parse {file_path}: {e}")
        return []

def format_prompt(code_blocks):
    joined_code = '\n\n'.join(code_blocks)
    return (
        "Analyze the following C++ functions and extract function call relationships in this JSON format:\n\n"
        "{\n"
        '  "functionCalls": [\n'
        "    {\n"
        '      "callerId": 1,\n'
        '      "calleeId": 2,\n'
        '      "isInsideIfElseOrSwitch": true,\n'
        '      "isInsideLoopOrEnvironment": false,\n'
        '      "isDifferentLanguage": true,\n'
        '      "isDifferentModule": false,\n'
        '      "isInsideClass": true,\n'
        '      "isInsideFunction": false\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Code:\n```cpp\n{joined_code}\n```"
    )

def analyze_code(file_path, code_blocks):
    prompt = format_prompt(code_blocks)
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
            return {"error": "Invalid JSON", "raw": response.text}
    except Exception as e:
        return {"error": str(e)}

def process_file(file_path):
    print(f"🔍 Analyzing: {file_path}")
    code_blocks = extract_relevant_functions(file_path)
    if code_blocks:
        result = analyze_code(file_path, code_blocks)
        return (file_path, result)
    else:
        print(f"⚠️ No relevant code found in {file_path}")
        return (file_path, {"note": "No relevant blocks found"})

def load_external_call_files(path):
    try:
        with open(path, "r") as f:
            return [line.strip().split(",")[0] for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return []

if __name__ == "__main__":
    files = load_external_call_files(EXTERNAL_CALLS_FILE)
    results = {}

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(process_file, file_path) for file_path in files]
        for future in as_completed(futures):
            file_path, result = future.result()
            results[file_path] = result

    with open("deepseek_structured_output.json", "w") as out_file:
        json.dump(results, out_file, indent=2)

    print("\n✅ Done! Output saved to deepseek_structured_output.json")
