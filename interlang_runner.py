import os
import subprocess
import json
from pathlib import Path

# Define paths for clarity (customize these as needed)
SRC_DIR = "/src"                       # Root directory containing source files to parse
AST_DIR = "/ast"                       # Directory containing the parser scripts and intermediate output
FINAL_JSON = "final_file.json"         # Destination path for the aggregated JSON results

# Function: Process a single source file by calling two parser scripts sequentially.
def process_file(file_path, aggregated_entries):
    """Process a single file through the parser scripts and update aggregated_entries list."""
    print(f"Parsing: {file_path}")

    # Run the first parser (likely extracts function-level ASTs or metadata)
    result = subprocess.run(["python3", os.path.join(AST_DIR, "interlang_cpp_parser.py"), file_path])
    if result.returncode != 0:
        print(f"  Error: interlang_cpp_parser.py failed for {file_path}; skipping.")
        return

    # Run the second parser to transform extracted data into a unified format
    result = subprocess.run(["python3", os.path.join(AST_DIR, "interlang_parser2Jsons.py"),
                            "/scr/output.json", "/ast/cpp_cross_lang_calls.json"])
    if result.returncode != 0:
        print(f"  Error: interlang_parser2Jsons.py failed for {file_path}; skipping.")
        return

    # Read the output file containing caller-callee function mappings
    caller_callee_file = os.path.join(AST_DIR, "caller_callee_pairs.json")
    try:
        with open(caller_callee_file, "r") as jf:
            data = json.load(jf)
            if isinstance(data, list) and data:
                # Merge new entries into the master list
                aggregated_entries.extend(data)
                print(f"  Added {len(data)} entries from {caller_callee_file}.")
            else:
                print(f"  No valid JSON array in {caller_callee_file}.")
    except Exception as e:
        print(f"  Error reading {caller_callee_file}: {e}")

# Main driver function
def main():
    aggregated_entries = []  # Will hold all JSON entries from all source files

    # Recursively walk through the source directory and find C/C++ files
    valid_extensions = (".cpp", ".cc", ".cxx", ".C")
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(valid_extensions):
                file_path = os.path.join(root, file)
                process_file(file_path, aggregated_entries)

    # Write the final aggregated result to a single JSON file
    try:
        with open(FINAL_JSON, "w") as outfile:
            json.dump(aggregated_entries, outfile, indent=2)
        print(f"\nFinal JSON written to {FINAL_JSON} with {len(aggregated_entries)} total entries.")
    except Exception as e:
        print(f"Error writing final JSON file: {e}")

# Entry point
if __name__ == "__main__":
    main()