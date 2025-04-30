import re
import sys
import os
import json

# Function: Infer the type of an argument based on its pattern.
def infer_type(arg):
    arg = arg.strip()
    if re.match(r'^["\'].*["\']$', arg):  # String literals
        return 'String'
    if re.match(r'^\d+$', arg):  # Integer values
        return 'int'
    if re.match(r'^\d+\.\d*$', arg):  # Floating-point numbers
        return 'double'
    if arg in ('true', 'false'):  # Boolean values
        return 'boolean'
    if arg == 'null':  # Null value
        return 'null'
    return 'Unknown'  # Default case for unknown types

# Function: Extract function calls from string literals embedded in eval/exec statements.
def extract_calls_from_string_literal(literal, line_num, source_file):
    calls = []
    # Match function calls in the literal
    for match in re.finditer(r'(\w+)\s*\(([^)]*)\)', literal):
        func = match.group(1)  # Function name
        args = match.group(2)  # Arguments to the function
        # Process the arguments to infer their types
        arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
        types = [infer_type(a) for a in arg_list]
        # Search for any referenced file in the string literal
        file_match = re.search(r'(\w+\.py|\.cpp|\.so|\.dll)', literal)
        called_file = file_match.group(1) if file_match else None
        # Append the extracted function call data to the calls list
        calls.append({
            "function_name": func,
            "called_inside_java_function": None,  # To be filled later
            "arguments": types,
            "java_file_path": source_file,
            "language": guess_language(file_match.group(1)) if file_match else "unknown",
            "callee_file_path": called_file
        })
    return calls

# Function: Extract function calls from the Java source content.
def extract_calls(content, source_file):
    results = []  # This will hold all the extracted function calls
    lines = content.splitlines()  # Split content into lines
    java_functions = get_java_function_ranges(lines)  # Get function ranges for Java methods

    for i, line in enumerate(lines, start=1):
        enclosing_func = find_enclosing_function(i, java_functions)  # Find the enclosing function name for the current line

        # 1. Handling Jython/JEP eval/exec cases
        for match in re.finditer(r"\.(eval|exec)\s*\(\s*\"([\s\S]*?)\"\s*\)", line):
            literal = match.group(2)  # The string literal passed to eval/exec
            embedded_calls = extract_calls_from_string_literal(literal, i, source_file)
            for call in embedded_calls:
                call["called_inside_java_function"] = enclosing_func  # Mark as called inside a Java function
                call["language"] = "python"  # Mark language as Python
            results.extend(embedded_calls)

        # 2. Handling method calls (obj.func(...))
        for match in re.finditer(r"\b(?:\w+(?:\.\w+)*)\.(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)  # Function name
            args = match.group(2)  # Arguments
            if func in ('eval', 'exec'):  # Skip eval/exec calls to avoid redundancy
                continue
            # Process the arguments to infer their types
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({
                "function_name": func,
                "called_inside_java_function": enclosing_func,
                "arguments": types,
                "java_file_path": source_file,
                "language": "unknown",  # Unknown language for method calls
                "callee_file_path": None
            })

        # 3. Handling static/global function calls
        for match in re.finditer(r"(?<!\.)\b(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)  # Function name
            if func in ('if', 'for', 'while', 'switch', 'catch', 'new', 'return'):  # Skip control flow and return statements
                continue
            args = match.group(2)  # Arguments
            # Process the arguments to infer their types
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({
                "function_name": func,
                "called_inside_java_function": enclosing_func,
                "arguments": types,
                "java_file_path": source_file,
                "language": "unknown",  # Unknown language for static/global calls
                "callee_file_path": None
            })
    return results

# Function: Get the ranges of Java functions in the source code.
def get_java_function_ranges(lines):
    functions = []
    pattern = re.compile(r'\b(?:public|private|protected)?\s+(?:static\s+)?\w+\s+(\w+)\s*\(.*?\)\s*\{')  # Regex to match function definitions
    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            name = match.group(1)  # Function name
            start = i + 1  # Start line of the function body
            brace_level = 1  # Brace level to track function body
            for j in range(i + 1, len(lines)):
                brace_level += lines[j].count('{')
                brace_level -= lines[j].count('}')
                if brace_level == 0:
                    functions.append((name, start, j + 1))  # Add function details when the body is closed
                    break
    return functions

# Function: Find the enclosing function for a given line of code.
def find_enclosing_function(line_number, functions):
    for name, start, end in functions:
        if start <= line_number <= end:  # Check if the line number is within the function's range
            return name
    return "global"  # If no enclosing function is found, return "global"

# Function: Guess the programming language based on the file extension.
def guess_language(path):
    if path:
        if path.endswith('.py'): return "python"  # Python file
        if path.endswith('.cpp') or path.endswith('.so') or path.endswith('.dll'): return "cpp"  # C++/compiled file
    return "unknown"  # Default case for unknown language

# Main function: Entry point to parse the Java source file and write results to a JSON file.
def main():
    input_path = "main.java"  # Change as needed
    output_path = "java_cross_lang_calls.json"

    if not os.path.isfile(input_path):  # Check if the input file exists
        print(f"❌ File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()  # Read the content of the Java source file

    calls = extract_calls(content, os.path.basename(input_path))  # Extract function calls
    with open(output_path, "w") as f:
        json.dump(calls, f, indent=2)  # Write the extracted calls to the JSON output file
    print(f"✅ JSON written to {output_path} with {len(calls)} calls.")

# Entry point
if __name__ == "__main__":
    main()
