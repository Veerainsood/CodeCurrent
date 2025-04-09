import clang.cindex
import json
import sys
import os

def get_callee_path(callee_cursor):
    if callee_cursor and callee_cursor.location.file:
        return os.path.abspath(callee_cursor.location.file.name)
    return None

def find_parent_class(node):
    while node:
        if node.kind in (clang.cindex.CursorKind.CLASS_DECL, clang.cindex.CursorKind.STRUCT_DECL):
            return node.spelling
        node = node.semantic_parent
    return None

def get_function_parameters(node):
    if node is None:
        return {"count": 0, "types": []}
    params = [arg.type.spelling for arg in node.get_arguments()]
    return {"count": len(params), "types": params}

def parse_function_calls(file_path):
    index = clang.cindex.Index.create()
    translation_unit = index.parse(
        file_path,
        args=['-x', 'c++', '-std=c++17']
    )

    function_calls = []

    def visit_node(node, parent_function=None, parent_node=None, parent_function_class=None, parent_chain=[]):
        current_chain = parent_chain + [node]

        # Track parent function context
        if node.kind in (clang.cindex.CursorKind.FUNCTION_DECL, clang.cindex.CursorKind.CXX_METHOD):
            parent_function = node.spelling
            parent_node = node
            parent_function_class = find_parent_class(node)

        if node.kind == clang.cindex.CursorKind.CALL_EXPR:
            function_name = node.spelling
            children = list(node.get_children())
            callee_cursor = node.referenced
            callee_path = get_callee_path(callee_cursor)

            is_foreign_call = function_name in (
                "PyObject_GetAttrString", "PyImport_Import", "PyObject_CallObject",
                "CallObjectMethod", "CallStaticObjectMethod"
            )

            target_language = "C++"
            if "PyObject" in function_name:
                target_language = "Python"
            elif "CallObject" in function_name:
                target_language = "Java"

            detected_function_name = children[1].spelling if is_foreign_call and len(children) > 1 else function_name
            parent_function_parameters = get_function_parameters(parent_node)

            def is_inside_chain(kinds):
                for n in current_chain:
                    if n.kind in kinds:
                        return True
                return False

            function_call = {
                "name": detected_function_name,
                "file": file_path,
                "caller_path": os.path.abspath(file_path),
                "language": target_language,
                "parameters": get_function_parameters(callee_cursor),
                "parentClass": find_parent_class(callee_cursor),
                "parentFunction": parent_function,
                "parentFunctionClass": parent_function_class,
                "parentFunctionParameters": parent_function_parameters,
                "callee_path": callee_path,
                "is_foreign_call": is_foreign_call,
                "isInsideIfElseOrSwitch": is_inside_chain({
                    clang.cindex.CursorKind.IF_STMT,
                    clang.cindex.CursorKind.SWITCH_STMT,
                    clang.cindex.CursorKind.CASE_STMT,
                    clang.cindex.CursorKind.DEFAULT_STMT,
                    clang.cindex.CursorKind.CONDITIONAL_OPERATOR
                }),
                "isInsideLoopOrEnvironment": is_inside_chain({
                    clang.cindex.CursorKind.FOR_STMT,
                    clang.cindex.CursorKind.WHILE_STMT,
                    clang.cindex.CursorKind.DO_STMT,
                    clang.cindex.CursorKind.CXX_FOR_RANGE_STMT
                }),
                "isDifferentLanguage": is_foreign_call,
                "isDifferentModule": False,  # Placeholder: could be enhanced
                "isInsideClass": is_inside_chain({
                    clang.cindex.CursorKind.CLASS_DECL,
                    clang.cindex.CursorKind.STRUCT_DECL
                }),
                "isInsideFunction": is_inside_chain({
                    clang.cindex.CursorKind.FUNCTION_DECL,
                    clang.cindex.CursorKind.CXX_METHOD,
                    clang.cindex.CursorKind.CONSTRUCTOR,
                    clang.cindex.CursorKind.DESTRUCTOR
                }),
            }

            if function_call["name"]:
                print(f"📌 Captured: {function_call['name']} in {function_call['parentFunction']} | Inside If/Switch? {function_call['isInsideIfElseOrSwitch']}")
                function_calls.append(function_call)

        # Recurse into children
        for child in node.get_children():
            visit_node(child, parent_function, parent_node, parent_function_class, current_chain)

    visit_node(translation_unit.cursor)
    return function_calls

def main():
    if len(sys.argv) != 2:
        print("Usage: python intralang_cpp_parser.py <input_cpp_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    function_calls = parse_function_calls(input_file)

    output_data = {"functions": function_calls}
    with open("parser_output.json", "w") as json_file:
        json.dump(output_data, json_file, indent=4)

    print("✅ Function calls extracted and saved to parser_output.json.")

if __name__ == "__main__":
    main()