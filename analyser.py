import json
import requests

# URL for accessing Ollama's local inference server
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama's local API endpoint

def extract_code_from_file(file_path, start, end):
    """
    Extracts code lines from a source file between specified start and end lines.

    Args:
        file_path (str): Path to the source code file.
        start (int): Starting line number (1-based index).
        end (int): Ending line number (inclusive).

    Returns:
        str or None: Extracted code block as a string, or None if file not found.
    """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        return "".join(lines[start-1:end])  # Adjusting for zero-based index
    except FileNotFoundError:
        return None

def analyze_with_ollama(function_name, function_code):
    """
    Sends a code snippet to Ollama's DeepSeek model for analysis and returns a summarized response.

    Args:
        function_name (str): Name of the function being analyzed (used for error reporting).
        function_code (str): Source code of the function to analyze.

    Returns:
        str: Shortened analysis result clipped to the first 20 words.
    """
    if not function_code:
        return f"Function {function_name} not found."
    
    # Prepare the prompt payload for Ollama
    payload = {
        "model": "deepseek-coder",
        "prompt": f"Analyze this function and explain its logic:\n{function_code}",
        "stream": False
    }

    # Send POST request to Ollama's local API
    response = requests.post(OLLAMA_URL, json=payload)

    # Clip the response to the first 20 words for brevity
    response_clipped = ' '.join(response.text.split()[:20])
    return response_clipped

# Load JSON data containing function metadata
with open("file.json") as f:
    function_calls = json.load(f)["functions"]

# Iterate over each function definition in the JSON and analyze it
for call in function_calls:
    # Extract source code for the function based on file and line range
    function_code = extract_code_from_file(call["path"], call["startLine"], call["endLine"])
    
    # Send code to Ollama for analysis
    analysis = analyze_with_ollama(call["name"], function_code)
    
    # Print out the analysis result
    print(f"\n### Analysis for {call['name']} ({call['language']}) ###")
    print(analysis)
