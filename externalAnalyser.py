import json
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
OLLAMA_URL = "http://localhost:11434/api/generate"  # Local LLM inference API
EXTERNAL_CALLS_FILE = "external_calls.txt"          # Input file list
NUM_THREADS = 4                                      # Thread count for parallel execution

# Regex pattern to detect foreign function interface (FFI) and interop-related keywords
CALL_PATTERNS = re.compile(r'(Py\w+|JNI\w+|Call\w+Method|GetMethodID|FindClass)')

# Regex pattern to detect C++-style function definitions
FUNC_DEF_PATTERN = re.compile(r'(?:[\w:<>\*&\s]+)?\s+(\w+)\s*\(([^)]*)\)\s*{', re.MULTILINE)

# Function: Extract C++ functions from a file that likely contain external/FFI calls
def extract_relevant_functions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        blocks = []  # Store function blocks that match criteria
        lines = code.splitlines()
        total_lines = len(lines)

        for match in FUNC_DEF_PATTERN.finditer(code):
            start_pos = match.start()
            start_line = code.count('\n', 0, start_pos)
            brace_count = 0
            found_start = False

            # Extract function body using brace matching
            for i in range(start_line, total_lines):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
                if not found_start and '{' in lines[i]:
                    found_start = True
                    start = i
                if found_start and brace_count == 0:
                    end = i
                    block = "\n".join(lines[start:end+1])
                    # Retain functions that have external call patterns
                    if CALL_PATTERNS.search(block):
                        blocks.append(block)
                    break
        return blocks
    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")
        return []

# Function: Format the extracted function blocks into a prompt for the LLM
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

# Function: Send the prompt to the LLM and get the result
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

# Function: Process a single file — extract functions, analyze via LLM, return result
def process_file(file_path):
    print(f"🔍 {file_path}")
    code_blocks = extract_relevant_functions(file_path)
    if not code_blocks:
        return (file_path, "No relevant functions found.")
    
    result = analyze_code(code_blocks)
    return (file_path, result)

# Function: Load list of source file paths from external_calls.txt
def load_files(path):
    try:
        with open(path, "r") as f:
            return [line.strip().split(",")[0] for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Missing external_calls.txt")
        return []

# Entry point of the script
if __name__ == "__main__":
    files = load_files(EXTERNAL_CALLS_FILE)
    results_dir = "results_light"
    os.makedirs(results_dir, exist_ok=True)

    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(process_file, f) for f in files]
        for future in as_completed(futures):
            file_path, result = future.result()
            file_name = os.path.basename(file_path).replace("/", "_")
            result_path = os.path.join(results_dir, f"{file_name}.out")

            # Save the result of analysis to output file
            with open(result_path, "w") as f:
                f.write(result)
            
            print(f"✅ Result saved for {file_path} → {result_path}")
