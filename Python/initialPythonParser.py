import os
import ast
import json
from collections import Counter

class PythonFunctionAnalyzer(ast.NodeVisitor):
    function_counter = 0  # Global counter for unique function IDs

    def __init__(self, file_path):
        self.file_path = file_path
        self.current_class = None
        self.current_function = None
        self.functions = []
        self.calls = []

    def visit_FunctionDef(self, node):
        """Extract function metadata."""
        PythonFunctionAnalyzer.function_counter += 1  # Increment global counter

        function_info = {
            "id": PythonFunctionAnalyzer.function_counter,  # Assign unique ID
            "name": node.name,
            "file": os.path.basename(self.file_path),
            "path": self.file_path,
            "language": "Python",
            "parameters": {
                "count": len(node.args.args),
                "types": ["unknown"] * len(node.args.args) 
            },
            "parentClass": self.current_class,
            "parentFunction": self.current_function if self.current_function else None
        }

        self.functions.append(function_info)

        previous_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        """Detect function calls and their surrounding context."""
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        else:
            return

        call_info = {
            "callerId": self._get_function_id(self.current_function),
            "calleeName": callee_name,
            "isInsideIfElseOrSwitch": self._is_inside(node, (ast.If, ast.Match)),
            "isInsideLoopOrEnvironment": self._is_inside(node, (ast.For, ast.While)),
            "isInsideClass": self.current_class is not None,
            "isInsideFunction": self.current_function is not None
        }

        self.calls.append(call_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Track class definitions."""
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class
    def _get_function_id(self, name):
        """Find function ID by name, avoiding None values."""
        if not name or name.strip() == "":
            return "UNKNOWN"

        # Ensure we correctly find the function by name and path
        for func in self.functions:
            if func["name"] == name and func["path"] == self.file_path:
                return func["id"]

        return "UNKNOWN"

    def _is_inside(self, node, types):
        """Check if a node is inside specific AST structures."""
        while node:
            if isinstance(node, types):
                return True
            node = getattr(node, "parent", None)
        return False

def analyze_python_files(directory):
    """Scan all Python files in a directory and generate function metadata & call relationships."""
    all_functions = []
    all_calls = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()

                try:
                    tree = ast.parse(code)
                    analyzer = PythonFunctionAnalyzer(file_path)

                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node

                    analyzer.visit(tree)

                    all_functions.extend(analyzer.functions)
                    all_calls.extend(analyzer.calls)

                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    # Resolve function call IDs
    for call in all_calls:
        for func in all_functions:
            if func["name"] == call["calleeName"]:
                call["calleeId"] = func["id"]
                break
        call.pop("calleeName", None)

    result = {
        "uniqueFunctions": all_functions,
        "functionCalls": all_calls
    }

    with open("function_analysis.json", "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4)

    print("JSON file 'function_analysis.json' generated.")

    # Analyze function metrics
    analyze_metrics(result)

def analyze_metrics(data):
    """Analyze function calls for insights."""
    call_counts = Counter(call["calleeId"] for call in data["functionCalls"] if "calleeId" in call)

    most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
    print("📌 Most Called Functions:")
    for func_id, count in most_called[:5]:  # Show top 5
        func_name = next((f["name"] for f in data["uniqueFunctions"] if f["id"] == func_id), "Unknown")
        print(f"{func_name} (ID: {func_id}) - {count} times")

    # Find unused functions
    called_ids = set(call_counts.keys())
    all_function_ids = {func["id"] for func in data["uniqueFunctions"]}
    unused = all_function_ids - called_ids
    print("\n🟢 Unused Functions:")
    for func in data["uniqueFunctions"]:
        if func["id"] in unused:
            print(f"{func['name']} (ID: {func['id']}) - Unused")

# Run the analysis
analyze_python_files("./tests/test_project")
