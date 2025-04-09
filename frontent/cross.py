import re
import sys
import os
import json

def infer_type(arg):
    arg = arg.strip()
    # Java/C++ type inference
    if re.match(r'^\".*\"$', arg) or re.match(r"^'.*'$", arg):
        return 'String' if 'java' in sys.argv else 'string'
    if re.match(r'^\d+[lL]$', arg):
        return 'long'
    if re.match(r'^\d+$', arg):
        return 'int'
    if re.match(r'^\d+\.\d*[fF]?$', arg):
        return 'float' if 'f' in arg.lower() else 'double'
    if arg in ('true', 'false'):
        return 'boolean'
    if arg == 'null':
        return 'void'
    if re.match(r'^[A-Z][\w\.]*$', arg):
        return 'object'
    return 'unknown'

def extract_calls_from_string_literal(literal, line_num, source_file, enclosing_func):
    calls = []
    for match in re.finditer(r'(\w+)\s*\(([^)]*)\)', literal):
        func = match.group(1)
        args = match.group(2)
        arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
        types = [infer_type(a) for a in arg_list]
        
        file_match = re.search(r'(\w+\.(?:py|cpp|so|dll))', literal)
        called_file = file_match.group(1) if file_match else None
        
        calls.append({
            "kind": "cross_language_call",
            "line": line_num,
            "function": func,
            "num_params": len(types),
            "param_types": types,
            "file": called_file,
            "caller_file_type": "java",
            "called_file_type": guess_language(called_file),
            "caller_function": enclosing_func["name"],
            "caller_function_num_params": len(enclosing_func["params"]),
            "caller_function_params": enclosing_func["params"],
            "source_file": source_file
        })
    return calls

def get_java_function_ranges(lines):
    functions = []
    pattern = re.compile(r'\b(?:public|private|protected)?\s+(?:static\s+)?([\w<>]+)\s+(\w+)\s*\(([^)]*)\)\s*\{')
    
    for i, line in enumerate(lines, 1):
        match = pattern.search(line)
        if match:
            return_type, name, params_str = match.groups()
            params = []
            for p in params_str.split(','):
                p = p.strip()
                if p:
                    param_type = p.split()[-1] if 'final' not in p else p.split()[-2]
                    params.append(param_type)
            
            start_line = i
            brace_level = 1
            end_line = i
            
            for j in range(i, len(lines)):
                brace_level += lines[j-1].count('{')
                brace_level -= lines[j-1].count('}')
                if brace_level == 0:
                    end_line = j
                    break
            
            functions.append({
                "name": name,
                "params": params,
                "start": start_line,
                "end": end_line
            })
    
    return functions

def find_enclosing_function(line_num, functions):
    for func in functions:
        if func["start"] <= line_num <= func["end"]:
            return func
    return {"name": "global", "params": []}

def guess_language(path):
    if not path:
        return "unknown"
    ext = os.path.splitext(path)[1]
    return {
        '.py': 'python',
        '.cpp': 'cpp',
        '.h': 'cpp',
        '.so': 'cpp',
        '.dll': 'cpp'
    }.get(ext, 'unknown')

def extract_calls(content, source_file):
    results = []
    lines = content.splitlines()
    java_functions = get_java_function_ranges(lines)

    for line_num, line in enumerate(lines, 1):
        enclosing_func = find_enclosing_function(line_num, java_functions)

        # Jython/JEP patterns
        jython_pattern = r'\.(?:eval|exec)\s*\(\s*["\'](.*?)["\']\s*\)'
        for match in re.finditer(jython_pattern, line):
            literal = match.group(1)
            results.extend(extract_calls_from_string_literal(
                literal, line_num, source_file, enclosing_func))

        # Native call patterns
        native_patterns = [
            (r'\.add\s*\(', 'cpp', 'add'),
            (r'\.my_func\s*\(', 'cpp', 'my_func'),
            (r'HttpClient\.newHttpClient\s*\(', 'python', 'rest_api_call')
        ]
        
        for pattern, lang, func in native_patterns:
            if re.search(pattern, line):
                results.append({
                    "kind": "cross_language_call",
                    "line": line_num,
                    "function": func,
                    "num_params": 2,
                    "param_types": ["int", "int"],
                    "file": None,
                    "caller_file_type": "java",
                    "called_file_type": lang,
                    "caller_function": enclosing_func["name"],
                    "caller_function_num_params": len(enclosing_func["params"]),
                    "caller_function_params": enclosing_func["params"],
                    "source_file": source_file
                })

        # General method calls
        method_pattern = r'(?<!new\s)\b(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, line):
            func = match.group(1)
            args = match.group(2)
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            
            if func.lower() in {'if', 'for', 'while', 'switch', 'catch', 'new', 'return'}:
                continue
            
            results.append({
                "kind": "cross_language_call",
                "line": line_num,
                "function": func,
                "num_params": len(types),
                "param_types": types,
                "file": None,
                "caller_file_type": "java",
                "called_file_type": "unknown",
                "caller_function": enclosing_func["name"],
                "caller_function_num_params": len(enclosing_func["params"]),
                "caller_function_params": enclosing_func["params"],
                "source_file": source_file
            })

    return results

def main():
    input_path = "folder/main.java"
    output_path = "java_cross_lang_calls.json"

    if not os.path.isfile(input_path):
        print(f"\u274c File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    calls = extract_calls(content, os.path.basename(input_path))
    
    with open(output_path, "w") as f:
        json.dump(calls, f, indent=2)
    
    print(f"\u2705 JSON written to {output_path} with {len(calls)} calls.")

if __name__ == "__main__":
    main()
