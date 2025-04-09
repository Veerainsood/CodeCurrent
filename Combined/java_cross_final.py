import re
import sys
import os
import json

def infer_type(arg):
    arg = arg.strip()
    if re.match(r'^["\'].*["\']$', arg):
        return 'String'
    if re.match(r'^\d+$', arg):
        return 'int'
    if re.match(r'^\d+\.\d*$', arg):
        return 'double'
    if arg in ('true', 'false'):
        return 'boolean'
    if arg == 'null':
        return 'null'
    return 'Unknown'

def extract_calls_from_string_literal(literal, line_num, source_file):
    calls = []
    for match in re.finditer(r'(\w+)\s*\(([^)]*)\)', literal):
        func = match.group(1)
        args = match.group(2)
        arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
        types = [infer_type(a) for a in arg_list]
        file_match = re.search(r'(\w+\.py|\.cpp|\.so|\.dll)', literal)
        called_file = file_match.group(1) if file_match else None
        calls.append({
            "function_name": func,
            "called_inside_java_function": None,  # Filled later
            "arguments": types,
            "java_file_path": source_file,
            "language": guess_language(file_match.group(1)) if file_match else "unknown",
            "callee_file_path": called_file
        })
    return calls

def extract_calls(content, source_file):
    results = []
    lines = content.splitlines()
    java_functions = get_java_function_ranges(lines)

    for i, line in enumerate(lines, start=1):
        enclosing_func = find_enclosing_function(i, java_functions)

        # 1. Jython/JEP eval/exec
        for match in re.finditer(r"\.(eval|exec)\s*\(\s*\"([\s\S]*?)\"\s*\)", line):
            literal = match.group(2)
            embedded_calls = extract_calls_from_string_literal(literal, i, source_file)
            for call in embedded_calls:
                call["called_inside_java_function"] = enclosing_func
                call["language"] = "python"
            results.extend(embedded_calls)

        # 2. obj.func(...) — method calls
        for match in re.finditer(r"\b(?:\w+(?:\.\w+)*)\.(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)
            args = match.group(2)
            if func in ('eval', 'exec'):
                continue
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({
                "function_name": func,
                "called_inside_java_function": enclosing_func,
                "arguments": types,
                "java_file_path": source_file,
                "language": "unknown",
                "callee_file_path": None
            })

        # 3. static/global calls
        for match in re.finditer(r"(?<!\.)\b(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)
            if func in ('if', 'for', 'while', 'switch', 'catch', 'new', 'return'):
                continue
            args = match.group(2)
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({
                "function_name": func,
                "called_inside_java_function": enclosing_func,
                "arguments": types,
                "java_file_path": source_file,
                "language": "unknown",
                "callee_file_path": None
            })
    return results

def get_java_function_ranges(lines):
    functions = []
    pattern = re.compile(r'\b(?:public|private|protected)?\s+(?:static\s+)?\w+\s+(\w+)\s*\(.*?\)\s*\{')
    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            name = match.group(1)
            start = i + 1
            brace_level = 1
            for j in range(i + 1, len(lines)):
                brace_level += lines[j].count('{')
                brace_level -= lines[j].count('}')
                if brace_level == 0:
                    functions.append((name, start, j + 1))
                    break
    return functions

def find_enclosing_function(line_number, functions):
    for name, start, end in functions:
        if start <= line_number <= end:
            return name
    return "global"

def guess_language(path):
    if path:
        if path.endswith('.py'): return "python"
        if path.endswith('.cpp') or path.endswith('.so') or path.endswith('.dll'): return "cpp"
    return "unknown"

def main():
    input_path = "main.java"  # Change as needed
    output_path = "java_cross_lang_calls.json"

    if not os.path.isfile(input_path):
        print(f"❌ File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    calls = extract_calls(content, os.path.basename(input_path))
    with open(output_path, "w") as f:
        json.dump(calls, f, indent=2)
    print(f"✅ JSON written to {output_path} with {len(calls)} calls.")

if __name__ == "__main__":
    main()

