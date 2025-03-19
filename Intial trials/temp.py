import sys
import clang.cindex


def print_ast(node, indent=0):
    """Recursively prints the AST nodes with indentation."""
    print("  " * indent + f"{node.kind} - {node.spelling if node.spelling else ''}")
    for child in node.get_children():
        print_ast(child, indent + 1)

def generate_ast(filename):
    """Generates and prints AST for a given C++ source file."""
    index = clang.cindex.Index.create()
    translation_unit = index.parse(filename, args=['-std=c++17'])
    print_ast(translation_unit.cursor)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_ast.py <cpp_source_file>")
        sys.exit(1)
    generate_ast(sys.argv[1])
