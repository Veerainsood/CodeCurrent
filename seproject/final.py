import os
import ast
import json
from collections import Counter, defaultdict

class PythonFunctionAnalyzer(ast.NodeVisitor):
    function_counter = 0

    def __init__(self, file_path, alias_map):
        self.file_path = file_path
        self.alias_map = alias_map  # {"alias": "module"}
        self.current_class = None
        self.current_function = None
        self.functions = []
        self.calls = []

    def visit_FunctionDef(self, node):
        PythonFunctionAnalyzer.function_counter += 1

        function_info = {
            "id": PythonFunctionAnalyzer.function_counter,
            "name": node.name,
            "file": os.path.basename(self.file_path),
            "path": self.file_path,
            "language": "Python",
            "parameters": {
                "count": len([arg for arg in node.args.args if arg.arg not in ("self", "cls")]),
                "types": ["unknown"] * len([arg for arg in node.args.args if arg.arg not in ("self", "cls")])
            },
            "parentClass": self.current_class,
            "parentFunction": self.current_function,
            "startLine": node.lineno,
            "endLine": getattr(node, "end_lineno", None)
        }

        self.functions.append(function_info)

        prev_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_ImportFrom(self, node):
        # from a import MyClass as Alias
        module = node.module
        for alias in node.names:
            self.alias_map[alias.asname or alias.name] = module

    def visit_Import(self, node):
        # import a as b
        for alias in node.names:
            self.alias_map[alias.asname or alias.name] = alias.name

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
            callee_class = None
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
            callee_class = self._get_called_class_name(node.func)
        else:
            return

        caller_param_count = next(
            (f["parameters"]["count"] for f in self.functions 
             if f["name"] == self.current_function and f["parentClass"] == self.current_class and f["path"] == self.file_path),
            None
        )

        call_info = {
            "callerId": self._get_function_id(name=self.current_function, parent_class=self.current_class, param_count=caller_param_count),
            "calleeName": callee_name,
            "calleeClass": callee_class,
            "isInsideIfElseOrSwitch": self._is_inside(node, (ast.If, ast.Match)),
            "isInsideLoopOrEnvironment": self._is_inside(node, (ast.For, ast.While)),
            "isInsideClass": self.current_class is not None,
            "isInsideFunction": self.current_function is not None,
            "argCount": len(node.args),
            "callerClass": self.current_class,
            "callerFunction": self.current_function
        }

        self.calls.append(call_info)
        self.generic_visit(node)

    def _get_called_class_name(self, attr_node):
        if isinstance(attr_node.value, ast.Call):
            if isinstance(attr_node.value.func, ast.Name):
                return attr_node.value.func.id
        elif isinstance(attr_node.value, ast.Name):
            return attr_node.value.id
        return None

    def _get_function_id(self, name, parent_class=None, param_count=None):
        for func in self.functions:
            if (
                func["name"] == name and
                func["path"] == self.file_path and
                (parent_class is None or func["parentClass"] == parent_class) and
                (param_count is None or func["parameters"]["count"] == param_count)
            ):
                return func["id"]
        return "UNKNOWN"

    def _is_inside(self, node, types):
        while node:
            if isinstance(node, types):
                return True
            node = getattr(node, "parent", None)
        return False

def analyze_python_files(root_dir):
    all_functions = []
    all_calls = []
    file_to_aliases = {}
    parsed_trees = {}

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node
                    alias_map = {}
                    alias_visitor = PythonFunctionAnalyzer(file_path, alias_map)
                    alias_visitor.visit(tree)
                    file_to_aliases[file_path] = alias_map
                    parsed_trees[file_path] = (tree, alias_map)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    for file_path, (tree, alias_map) in parsed_trees.items():
        analyzer = PythonFunctionAnalyzer(file_path, alias_map)
        analyzer.visit(tree)
        all_functions.extend(analyzer.functions)
        all_calls.extend(analyzer.calls)

    for call in all_calls:
        callee_name = call.get("calleeName")
        callee_class = call.get("calleeClass")
        arg_count = call.get("argCount")
        matched = False

        for func in all_functions:
            if (
                func["name"] == callee_name and
                func["parameters"]["count"] == arg_count and
                func.get("parentClass") == callee_class
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
        call.pop("calleeClass", None)

    result = {
        "uniqueFunctions": all_functions,
        "functionCalls": all_calls
    }

    with open("function_analysis_test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print("Generated JSON: function_analysis_test.json")
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

if __name__ == "__main__":
    analyze_python_files("./new")
