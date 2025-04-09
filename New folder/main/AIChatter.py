import json
import time
import requests
import subprocess
import sys
import os
import concurrent.futures
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tinyllama"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "cache.json")
FILE_JSON = os.path.join(BASE_DIR, "public", "file.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


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
    for _ in range(10):
        if is_ollama_running():
            return
        time.sleep(0.5) # give some time to start

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

def extract_code_from_file(path, start, end, max_lines=40):
    
    real_base = os.path.abspath(os.path.join(BASE_DIR, ".."))
    normalized_path = os.path.join(real_base, path.removeprefix("/src").lstrip("/"))
    log(f"{path} Extracting code from {normalized_path} lines {start}-{end}...")
    try:
        with open(normalized_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            lines = lines[start - 1:end]
            return "".join(lines[:max_lines])  # Limit lines
    except Exception:
        return None
def log(message):
    with open("AILog.txt", "a", encoding="utf-8") as log_file:
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        log_file.write(f"{timestamp} {message}\n")

def format_prompt_for_structure(code, task):
    code = code.strip()[:1000]  # limit input chars
    prefix = {
        1: "Briefly explain this:",
        2: "Some improvement in:",
        3: "Some code smell in:"
    }.get(task, "")
    return f"{prefix}\n{code}"

from functools import lru_cache

@lru_cache(maxsize=128)
def extract_code_from_file_cached(path, start, end):
    return extract_code_from_file(path, start, end)


def analyze_with_deepseek(code, task, timeout=10):
    prompt = format_prompt_for_structure(code, task)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 64,
            "temperature": 0.2,
            "top_k": 40,
            "top_p": 0.95
        }
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

code = extract_code_from_file_cached(func["path"], func["startLine"], func["endLine"])
cache = load_cache()
key = f"{func['id']}-{task}"

if key in cache:
    result = cache[key]
else:
    result = analyze_with_deepseek(code, task)
    cache[key] = result
    save_cache(cache)

print(result)