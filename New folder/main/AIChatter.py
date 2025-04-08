import json
import requests
import subprocess
import sys
import os
import concurrent.futures
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-coder"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_JSON = os.path.join(BASE_DIR, "public", "file.json")

def is_ollama_running():
    try:
        response = requests.get("http://localhost:11434")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def is_model_available():
    try:
        output = subprocess.check_output(["ollama", "list"]).decode()
        return MODEL_NAME in output
    except Exception:
        return False

def start_ollama():
    # print("🟡 Starting ollama serve...")  
    subprocess.Popen(["ollama", "serve"])
    import time
    time.sleep(3)  # give some time to start

def pull_model():
    # print(f"📦 Pulling model {MODEL_NAME}...")
    subprocess.call(["ollama", "pull", MODEL_NAME])

def find_function_by_id(file_path, target_id):
    # print(f"🔍 Searching for function ID {target_id} in {file_path}...")
    with open(file_path, "r") as f:
        data = json.load(f)
    for group in data:
        for func in group:
            if func["id"] == target_id:
                return func
    return None

def extract_code_from_file(path, start, end):
    # BASE_DIR is .../New folder/main
    real_base = os.path.abspath(os.path.join(BASE_DIR, ".."))  # Points to "New folder"
    normalized_path = os.path.join(real_base, path.removeprefix("/src").lstrip("/"))
    # print(normalized_path)

    try:
        with open(normalized_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[start - 1:end])
    except Exception as e:
        # print(f"❌ Error reading file {normalized_path}: {e}")
        return None

def format_prompt_for_structure(code, task):
    if task == 1:
        return f"Explain what the following code does:\n\n{code} give very short ans"
    elif task == 2:
        return f"Suggest improvements for the following code:\n\n{code} give very short an"
    elif task == 3:
        return f"Identify potential code smells in the following code:\n\n{code} give very short an"
    return code



def analyze_with_deepseek(code, task, timeout=10):
    prompt = format_prompt_for_structure(code, task)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    def make_request():
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return json.loads(response.text)["response"]

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_request)
            return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        print(f"⚠️ Ollama response timed out after {timeout} seconds.")
        return "⚠️ Response timed out. Try again."
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ Invalid response format")
        return None


if not is_ollama_running():
    start_ollama()

if not is_model_available():
    pull_model()

# try:
#     id = int(input("Enter function ID: "))
#     task = int(input("Enter task (1=Description, 2=Improvements, 3=Code smells): "))
# except ValueError:
#     print("❌ Invalid input.")
#     sys.exit(1)

id = int(sys.argv[1])
task = int(sys.argv[2])

func = find_function_by_id(FILE_JSON, id)
if not func:
    print(f"❌ Function ID {id} not found.")
    sys.exit(1)

code = extract_code_from_file(func["path"], func["startLine"], func["endLine"])
result = analyze_with_deepseek(code, task)
print(result)  # send result back to Node.js