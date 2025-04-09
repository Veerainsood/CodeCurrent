import os
import ast
import json
from collections import Counter

class PythonFunctionAnalyzer(ast.NodeVisitor):
    function_counter = 0

    def __init__(self, file_path):
        self.file_path = file_path
        self.module = os.path.splitext(os.path.basename(file_path))[0]
        self.current_class = None
        self.current_function = None
        self.functions = []
        self.calls = []

    def visit_FunctionDef(self, node):
        PythonFunctionAnalyzer.function_counter += 1

        param_names = [arg.arg for arg in node.args.args if arg.arg not in ("self", "cls")]
        param_count = len(param_names)

        function_info = {
            "id": PythonFunctionAnalyzer.function_counter,
            "name": node.name,
            "file": os.path.basename(self.file_path),
            "path": self.file_path,
            "language": "Python",
            "module": self.module,
            "parameters": {
                "count": param_count,
                "types": ["unknown"] * param_count
            },
            "parentClass": self.current_class,
            "parentFunction": self.current_function if self.current_function else None,
            "startLine": node.lineno,
            "endLine": getattr(node, "end_lineno", None)
        }

        self.functions.append(function_info)

        previous_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        else:
            return

        call_info = {
            "callerId": self._get_function_id(name=self.current_function, parent_class=self.current_class),
            "calleeName": callee_name,
            "module": self.module,
            "isInsideIfElseOrSwitch": self._is_inside(node, (ast.If, ast.Match)),
            "isInsideLoopOrEnvironment": self._is_inside(node, (ast.For, ast.While)),
            "isInsideClass": self.current_class is not None,
            "isInsideFunction": self.current_function is not None,
            "argCount": len(node.args),
            "callerClass": self.current_class,
            "callerFunction": self.current_function,
        }

        self.calls.append(call_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class

    def _get_function_id(self, name, parent_class=None):
        for func in self.functions:
            if (
                func["name"] == name and
                func["parentClass"] == parent_class and
                func["path"] == self.file_path
            ):
                return func["id"]
        return "UNKNOWN"

    def _is_inside(self, node, types):
        while node:
            if isinstance(node, types):
                return True
            node = getattr(node, "parent", None)
        return False


def analyze_python_files(directory):
    all_functions = []
    all_calls = []

    # First pass: gather all function definitions
    analyzers = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    tree = ast.parse(code)
                    analyzer = PythonFunctionAnalyzer(file_path)

                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node

                    analyzer.visit(tree)
                    analyzers.append(analyzer)
                    all_functions.extend(analyzer.functions)

                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    # Second pass: resolve all calls using gathered functions
    for analyzer in analyzers:
        for call in analyzer.calls:
            callee_name = call["calleeName"]
            arg_count = call["argCount"]
            caller_class = call["callerClass"]
            matched = False

            # Try exact match: name + class + args
            for func in all_functions:
                if (
                    func["name"] == callee_name and
                    func["parameters"]["count"] == arg_count and
                    func.get("parentClass") == caller_class
                ):
                    call["calleeId"] = func["id"]
                    matched = True
                    break

            if not matched:
                for func in all_functions:
                    if func["name"] == callee_name and func["parameters"]["count"] == arg_count:
                        call["calleeId"] = func["id"]
                        matched = True
                        break

            if not matched:
                for func in all_functions:
                    if func["name"] == callee_name:
                        call["calleeId"] = func["id"]
                        matched = True
                        break

            call.pop("calleeName", None)
            all_calls.append(call)

    result = {
        "uniqueFunctions": all_functions,
        "functionCalls": all_calls
    }

    with open("function_analysis_crossfile.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print("Saved: function_analysis_crossfile.json")
    analyze_metrics(result)


def analyze_metrics(data):
    call_counts = Counter(call["calleeId"] for call in data["functionCalls"] if "calleeId" in call)

    most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
    print("Most Called Functions:")
    for func_id, count in most_called[:5]:
        func_name = next((f["name"] for f in data["uniqueFunctions"] if f["id"] == func_id), "Unknown")
        print(f"{func_name} (ID: {func_id}) - {count} times")

    called_ids = set(call_counts.keys())
    all_function_ids = {func["id"] for func in data["uniqueFunctions"]}
    unused = all_function_ids - called_ids
    print("\nUnused Functions:")
    for func in data["uniqueFunctions"]:
        if func["id"] in unused:
            print(f"{func['name']} (ID: {func['id']}) - Unused")

# Entry point
analyze_python_files("./new")
