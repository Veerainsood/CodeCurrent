import json
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/generate"
EXTERNAL_CALLS_FILE = "external_calls.txt"
NUM_THREADS = 4

CALL_PATTERNS = re.compile(r'(Py\w+|JNI\w+|Call\w+Method|GetMethodID|FindClass)')
FUNC_DEF_PATTERN = re.compile(r'(?:[\w:<>\*&\s]+)?\s+(\w+)\s*\(([^)]*)\)\s*{', re.MULTILINE)

def extract_relevant_functions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        blocks = []
        lines = code.splitlines()
        total_lines = len(lines)

        for match in FUNC_DEF_PATTERN.finditer(code):
            start_pos = match.start()
            start_line = code.count('\n', 0, start_pos)
            brace_count = 0
            found_start = False

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
                        blocks.append(block)
                    break
        return blocks
    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")
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

def analyze_code(code_blocks):
    prompt = format_prompt(code_blocks)
    payload = {
        "model": "deepseek-coder",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def dump_result(file_path, result, output_dir):
    file_name = os.path.basename(file_path).replace("/", "_")
    output_path = os.path.join(output_dir, f"{file_name}.out")
    with open(output_path, "w") as f:
        f.write(result)
    print(f"✅ Dumped → {output_path}")

def process_file(file_path, output_dir):
    print(f"🔍 Processing {file_path}...")
    code_blocks = extract_relevant_functions(file_path)
    if not code_blocks:
        dump_result(file_path, "No relevant functions found.", output_dir)
    else:
        result = analyze_code(code_blocks)
        dump_result(file_path, result, output_dir)

def load_files(path):
    try:
        with open(path, "r") as f:
            return [line.strip().split(",")[0] for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Missing external_calls.txt")
        return []

if __name__ == "__main__":
    files = load_files(EXTERNAL_CALLS_FILE)
    output_dir = "results_dumped"
    os.makedirs(output_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for file in files:
            executor.submit(process_file, file, output_dir)
