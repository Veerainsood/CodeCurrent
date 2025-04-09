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
        "prompt": f"Analyze this function and explain in 10 words:\n{function_code}",
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        # Clip the response to the first 20 words
        response_json = response.json()
        
        # Get the response text and clip it to the first 20 words
        response_text = response_json.get("response", "")
        response_clipped = ' '.join(response_text.split()[:20])
        return response_clipped
    else:
        return f"Error: {response.status_code} - {response.text}"

# Load JSON data
with open("function_calls.json") as f:
    function_calls = json.load(f)["nodes"]

# Extract and analyze each function
for call in function_calls:
    function_code = extract_code_from_file(call["file"], call["start"], call["end"])
    analysis = analyze_with_ollama(call["function"], function_code)
    
    print(f"\n### Analysis for {call['function']} ({call['language']}) ###")
    print(analysis)
