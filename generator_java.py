import javalang
import json
import os
import sys

# Global data
id_counter_file = "./id_counter.txt"
function_map = {}
current_id = 1
unique_functions = []

def read_id_counter():
    global current_id
    if os.path.exists(id_counter_file):
        with open(id_counter_file, "r") as f:
            try:
                current_id = int(f.read().strip())
            except:
                current_id = 1
    else:
        current_id = 1

def write_id_counter():
    with open(id_counter_file, "w") as f:
        f.write(str(current_id))

def get_parameters(declaration):
    param_types = []

    for param in declaration.parameters:
        type_name = param.type.name

        # Handle generics like List<String>
        if hasattr(param.type, 'arguments') and param.type.arguments:
            generics = ','.join(
                arg.type.name for arg in param.type.arguments
                if hasattr(arg, 'type') and arg.type
            )
            type_name += f"<{generics}>"

        # Handle arrays
        if hasattr(param.type, 'dimensions') and param.type.dimensions:
            type_name += "[]" * len(param.type.dimensions)

        # Handle varargs
        if param.varargs:
            type_name += "..."

        param_types.append(type_name)

    return {"types": param_types , "count": len(param_types)}

def get_return_type(declaration):
    if isinstance(declaration, javalang.tree.ConstructorDeclaration):
        return None  # Constructors don't have return types

    if declaration.return_type is None:
        return "void"  # Explicitly return "void" for void methods

    type_name = declaration.return_type.name

    # Handle generics
    if hasattr(declaration.return_type, 'arguments') and declaration.return_type.arguments:
        generics = ','.join(
            arg.type.name for arg in declaration.return_type.arguments
            if hasattr(arg, 'type') and arg.type
        )
        type_name += f"<{generics}>"

    # Handle arrays
    if hasattr(declaration.return_type, 'dimensions') and declaration.return_type.dimensions:
        type_name += "[]" * len(declaration.return_type.dimensions)

    return type_name

def extract_methods(node, parent_class=None):
    global current_id

    if isinstance(node, javalang.tree.ClassDeclaration):
        parent_class = node.name

    if isinstance(node, (javalang.tree.MethodDeclaration, javalang.tree.ConstructorDeclaration)):
        func_info = {
            "id": current_id,
            "name": node.name,
            "file": current_file_name,
            "path": current_file_path,
            "language": "Java",
            "parameters": get_parameters(node),
            "returnType": get_return_type(node),
            "parentClass": parent_class,
            "parentFunction": None,
            "startLine": node.position.line if node.position else None,
            "endLine": None
        }
        unique_functions.append(func_info)
        function_map[node.name] = current_id
        current_id += 1

    for child in node.children:
        if isinstance(child, list):
            for item in child:
                if hasattr(item, 'children'):
                    extract_methods(item, parent_class)
        elif hasattr(child, 'children'):
            extract_methods(child, parent_class)

def parse_java_file(file_path):
    global current_file_name, current_file_path
    current_file_name = os.path.basename(file_path)
    current_file_path = os.path.abspath(file_path)

    with open(file_path, 'r') as file:
        code = file.read()

    try:
        tree = javalang.parse.parse(code)
    except javalang.parser.JavaSyntaxError as e:
        print(f"Syntax error in Java file: {e}")
        return

    extract_methods(tree)

def generate_ast_json(file_path, output_file):
    if not os.path.isfile(file_path):
        print(f"Error: File not found - {file_path}")
        sys.exit(1)

    parse_java_file(file_path)

    with open(output_file, "w") as f:
        json.dump(unique_functions, f, indent=4)
    print(f"AST JSON saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generator_java.py <file.java> <output.json>")
        sys.exit(1)

    read_id_counter()
    generate_ast_json(sys.argv[1], sys.argv[2])
    write_id_counter()