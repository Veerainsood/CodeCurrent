import json
import time
import requests
import subprocess
import sys
import os
import concurrent.futures
import shutil

def ensure_ollama_installed():
    if shutil.which("ollama") is None:
        print("❌ 'ollama' is not installed or not found in PATH.")
        if sys.platform.startswith("linux"):
            try:
                subprocess.check_call(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"])
            except subprocess.CalledProcessError:
                print("❌ Failed to install ollama via install.sh")
                print("➡️  Visit https://ollama.com to install it.")
                sys.exit(1)
        else:
            sys.exit(1)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tinyllama"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "cache.json")
FILE_JSON = os.path.join(BASE_DIR, "unique_functions_combined.json")

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
        for func in data:
            if func["id"] == target_id:
                return func
    return None

def extract_code_from_file(path, start, end, max_lines=40):
    
    try:
        with open(path, "r", encoding="utf-8") as f:
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
    code = code[:1000] # limit input chars
    prefix = {
        1: "Briefly explain this:",
        2: "Some improvement in:",
        3: "List code smells in the following function.Be specific and concise:\n",
        4: "List the mood of programmer in the following function.Be specific and concise:\n"
    }.get(task, "")
    return f"{prefix}\n{code}"

from functools import lru_cache

@lru_cache(maxsize=128)
def extract_code_from_file_cached(path, start, end):
    return extract_code_from_file(path, start, end)


def analyze_with_deepseek(code, task, timeout=20):
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


id = int(sys.argv[1])
task = int(sys.argv[2])

ensure_ollama_installed()

func = find_function_by_id(FILE_JSON, id)
if not func:
    print(f"❌ Function ID {id} not found.")
    sys.exit(1)

cache = load_cache()
key = f"{func['id']}-{task}"

if key in cache:
    result = cache[key]
    # log("Found in cache")
    print(result,flush=True)
else:
    # log(f"Came in else with path: {func['path']}")
    code = extract_code_from_file_cached(func["path"], func["startLine"], func["endLine"])
    result = analyze_with_deepseek(code, task)
    if '.' in result:
        result = result[:result.rfind('.') + 1]  # Include the period at the end
    cache[key] = result
    save_cache(cache)
    print(result,flush=True)