import re
import sys
import argparse
import os

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
        called_file = file_match.group(1) if file_match else source_file
        calls.append({'func': func, 'count': len(arg_list), 'types': types, 'line': line_num, 'file': called_file})
    return calls

def extract_calls(content, source_file):
    results = []
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        # 1. Jython/JEP: .eval("..."), .exec("...")
        for match in re.finditer(r"\.(eval|exec)\s*\(\s*\"([\s\S]*?)\"\s*\)", line):
            literal = match.group(2)
            calls = extract_calls_from_string_literal(literal, i, source_file)
            results.extend(calls)

        # 2. Direct method calls: obj.func(...)
        for match in re.finditer(r"\b(?:\w+(?:\.\w+)*)\.(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)
            args = match.group(2)
            if func in ('eval', 'exec'):
                continue
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({'func': func, 'count': len(arg_list), 'types': types, 'line': i, 'file': source_file})

        # 3. Static/global calls: func(...)
        for match in re.finditer(r"(?<!\.)\b(\w+)\s*\(([^)]*)\)", line):
            func = match.group(1)
            args = match.group(2)
            if func in ('if', 'for', 'while', 'switch', 'catch', 'new', 'return'):
                continue
            arg_list = [a.strip() for a in args.split(',')] if args.strip() else []
            types = [infer_type(a) for a in arg_list]
            results.append({'func': func, 'count': len(arg_list), 'types': types, 'line': i, 'file': source_file})
    return results

def main():
    print("C++ Interop Parser")
    parser = argparse.ArgumentParser(description='Parse C++ interop calls to Python/Java')
    # parser.add_argument('paths', nargs='+', help='Files or directories to scan')
    # args = parser.parse_args()
    paths = [
        './main.java'# This can also be a directory
    ]
    for filepath in paths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
            continue

        calls = extract_calls(content, os.path.basename(filepath))
        print(f"\nFile: {filepath}")
        if not calls:
            print("  No integration calls found.")
            continue

        seen = set()
        for c in calls:
            key = (c['func'], tuple(c['types']), c['count'], c['line'])
            if key in seen:
                continue
            seen.add(key)
            types_str = ', '.join(c['types']) if c['types'] else 'None'
            print(f"  Line {c['line']}: Function: {c['func']} | Count: {c['count']} | Types: {types_str} | From: {c['file']}")

main()