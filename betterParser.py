import clang.cindex
import json
import os

# Global lists and hash map
unique_functions = []
function_calls = []
function_map = {}  # Maps function name -> function id

def get_function_parameters(node):
    """Extract function parameter types and count."""
    params = [arg.type.spelling for arg in node.get_arguments()]
    return {"count": len(params), "types": params}

def find_parent(node):
    """Return the immediate parent class and parent function (if any)."""
    parent_class = None
    parent_function = None
    parent = node.semantic_parent
    while parent:
        if parent.kind == clang.cindex.CursorKind.CLASS_DECL:
            parent_class = parent.spelling
        if parent.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            parent_function = parent.spelling
        parent = parent.semantic_parent  # Traverse upwards
    return parent_class, parent_function

def first_pass(node, file_path):
    """
    First pass: Traverse the AST and collect user-defined function declarations.
    Uses file_path to filter out functions not defined in the current file.
    """
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        # Ignore functions not in the target file (i.e. system headers)
        if node.location.file and node.location.file.name != file_path:
            return

        parent_class, parent_function = find_parent(node)
        func_info = {
            "id": len(unique_functions) + 1,
            "name": node.spelling,
            "file": os.path.basename(file_path),
            "path": os.path.abspath(file_path),
            "language": "C++",
            "parameters": get_function_parameters(node),
            "parentClass": parent_class,
            "parentFunction": parent_function
        }
        unique_functions.append(func_info)
        function_map[node.spelling] = func_info["id"]

    # Recurse into children
    for child in node.get_children():
        first_pass(child, file_path)

def is_inside_structure(node, kinds):
    """Check if a node is inside any of the given kinds."""
    parent = node.semantic_parent
    while parent:
        if parent.kind in kinds:
            return True
        parent = parent.semantic_parent
    return False

def second_pass(node):
    """
    Second pass: Traverse the AST to detect function call expressions.
    For each call, check if caller and callee exist in the hash (user-defined).
    """
    if node.kind == clang.cindex.CursorKind.CALL_EXPR:
        caller = node.semantic_parent
        caller_id = function_map.get(caller.spelling, None) if caller and caller.kind == clang.cindex.CursorKind.FUNCTION_DECL else None
        callee_id = function_map.get(node.spelling, None)  # Lookup callee

        # Determine context flags
        is_inside_if_else_or_switch = is_inside_structure(node, {clang.cindex.CursorKind.IF_STMT, clang.cindex.CursorKind.SWITCH_STMT})
        is_inside_loop_or_environment = is_inside_structure(node, {clang.cindex.CursorKind.FOR_STMT, clang.cindex.CursorKind.WHILE_STMT, clang.cindex.CursorKind.DO_STMT})
        
        in_class = in_func = False
        if caller and caller.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            parent_class, parent_function = find_parent(caller)
            in_class = parent_class is not None
            in_func = parent_function is not None

        call_info = {
            "callerId": caller_id,  
            "calleeId": callee_id,  
            "isInsideIfElseOrSwitch": is_inside_if_else_or_switch,
            "isInsideLoopOrEnvironment": is_inside_loop_or_environment,
            "isDifferentLanguage": False,  # Assuming same language for now
            "isDifferentModule": False,    # Assuming single module
            "isInsideClass": in_class,
            "isInsideFunction": in_func
        }
        function_calls.append(call_info)

    # Recurse into children
    for child in node.get_children():
        second_pass(child)

def find_libclang():
    """Automatically find and set the correct libclang path."""
    possible_paths = [
        "/usr/lib/llvm-11/lib/libclang.so",
        "/usr/lib/llvm-12/lib/libclang.so",
        "/usr/lib/llvm-13/lib/libclang.so",
        "/usr/lib/llvm-14/lib/libclang.so",
        "/usr/lib/llvm-15/lib/libclang.so",
        "/usr/lib/libclang.so"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            clang.cindex.Config.set_library_file(path)
            return
    print("Error: libclang.so not found. Please install LLVM/Clang.")
    exit(1)

def generate_ast_json(file_path, output_file):
    """
    Parse the source file using clang, run both passes,
    and then output the JSON with unique functions and function calls.
    """
    index = clang.cindex.Index.create()
    translation_unit = index.parse(file_path, args=['-std=c++17'])
    if not translation_unit:
        print("Error: Failed to parse the C++ file.")
        return

    # First pass: collect functions
    first_pass(translation_unit.cursor, file_path)
    # Second pass: collect call relationships
    second_pass(translation_unit.cursor)

    output_data = {"uniqueFunctions": unique_functions, "functionCalls": function_calls}
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"AST JSON saved to: {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 generator.py <file.cpp> <output.json>")
        sys.exit(1)

    # Find and set the correct libclang path
    find_libclang()
    
    generate_ast_json(sys.argv[1], sys.argv[2])
