#!/usr/bin/env python3
import os
import subprocess
import json
from pathlib import Path

# Define paths for clarity (customize these as needed)
SRC_DIR = "/src"
AST_DIR = "/ast"
FINAL_JSON = "final_file.json"  # Destination for the aggregated JSON output

def process_file(file_path, aggregated_entries):
    """Process a single file through the parser scripts and update aggregated_entries list."""
    print(f"Parsing: {file_path}")

    # Call the first parser; if it fails, skip this file.
    result = subprocess.run(["python3", os.path.join(AST_DIR, "interlang_cpp_parser.py"), file_path])
    if result.returncode != 0:
        print(f"  Error: interlang_cpp_parser.py failed for {file_path}; skipping.")
        return

    # Call the second parser that relies on generated output files.
    result = subprocess.run(["python3", os.path.join(AST_DIR, "interlang_parser2Jsons.py"),
                            "/scr/output.json" ,"/ast/cpp_cross_lang_calls.json"])
    if result.returncode != 0:
        print(f"  Error: interlang_parser2Jsons.py failed for {file_path}; skipping.")
        return

    # Read the output file (assuming it contains a JSON array).
    caller_callee_file = os.path.join(AST_DIR, "caller_callee_pairs.json")
    try:
        with open(caller_callee_file, "r") as jf:
            data = json.load(jf)
            if isinstance(data, list) and data:
                # Add each element from the array to our aggregated entries.
                aggregated_entries.extend(data)
                print(f"  Added {len(data)} entries from {caller_callee_file}.")
            else:
                print(f"  No valid JSON array in {caller_callee_file}.")
    except Exception as e:
        print(f"  Error reading {caller_callee_file}: {e}")

def main():
    aggregated_entries = []  # Will hold all JSON entries

    # Walk through SRC_DIR and collect files with specified C/C++ extensions.
    valid_extensions = (".cpp", ".cc", ".cxx", ".C")
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(valid_extensions):
                file_path = os.path.join(root, file)
                process_file(file_path, aggregated_entries)

    # Write the aggregated entries to the final output JSON.
    try:
        with open(FINAL_JSON, "w") as outfile:
            json.dump(aggregated_entries, outfile, indent=2)
        print(f"\nFinal JSON written to {FINAL_JSON} with {len(aggregated_entries)} total entries.")
    except Exception as e:
        print(f"Error writing final JSON file: {e}")

if __name__ == "__main__":
    main()
