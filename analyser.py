import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama's local API endpoint

def extract_code_from_file(file_path, start, end):
    """Extracts code from a file between given start and end line numbers."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        return "".join(lines[start-1:end])  # Adjusting for zero-based index
    except FileNotFoundError:
        return None

def analyze_with_ollama(function_name, function_code):
    """Sends extracted function to DeepSeek-Coder via Ollama for analysis."""
    if not function_code:
        return f"Function {function_name} not found."
    
    payload = {
        "model": "deepseek-coder",
        "prompt": f"Analyze this function and explain its logic:\n{function_code}",
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    # Clip the response to the first 20 words
    response_clipped = ' '.join(response.text.split()[:20])
    return response_clipped

# Load JSON data
with open("file.json") as f:
    function_calls = json.load(f)["functions"]

# Extract and analyze each function
for call in function_calls:
    function_code = extract_code_from_file(call["path"],call["startLine"], call["endLine"])
    analysis = analyze_with_ollama(call["name"], function_code)
    
    print(f"\n### Analysis for {call['name']} ({call['language']}) ###")
    print(analysis)
