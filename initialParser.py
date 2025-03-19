import clang.cindex
import json
import os
import sys

# Global lists and hash map
functions = []
calls = {}
function_map = {}  # Maps function name -> function id

def get_function_parameters(node):
    """Extract function parameter count."""
    return {"count": len(list(node.get_arguments()))}

def first_pass(node, file_path):
    """Collect user-defined function declarations."""
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if node.location.file and node.location.file.name != file_path:
            return
        func_id = len(functions) + 1
        functions.append({"id": func_id, "name": node.spelling, "parameters": get_function_parameters(node)})
        function_map[node.spelling] = func_id
    for child in node.get_children():
        first_pass(child, file_path)

def second_pass(node):
    """Detect function calls."""
    if node.kind == clang.cindex.CursorKind.CALL_EXPR:
        caller = node.semantic_parent
        caller_id = function_map.get(caller.spelling, None) if caller and caller.kind == clang.cindex.CursorKind.FUNCTION_DECL else None
        callee_id = function_map.get(node.spelling, None)
        if caller_id and callee_id:
            calls.setdefault(caller_id, []).append(callee_id)
    for child in node.get_children():
        second_pass(child)

def generate_ast_json(file_path, output_file):
    """Parse the source file and generate JSON output."""
    index = clang.cindex.Index.create()
    tu = index.parse(file_path, args=['-std=c++17'])
    first_pass(tu.cursor, file_path)
    second_pass(tu.cursor)

    output = {"functions": functions, "calls": calls}
    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)
    print(f"AST JSON saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generator.py <file.cpp> <output.json>")
        sys.exit(1)

    # Manually set libclang path if needed
    clang.cindex.Config.set_library_file("/usr/lib/llvm-14/lib/libclang.so")

    generate_ast_json(sys.argv[1], sys.argv[2])
