import os
import ast
import json
from collections import Counter

ID_COUNTER_FILE = "./id_counter.txt"

def load_id_counter():
    if os.path.exists(ID_COUNTER_FILE):
        with open(ID_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_id_counter(counter):
    with open(ID_COUNTER_FILE, "w") as f:
        f.write(str(counter))

class PythonFunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path, counter_start):
        self.file_path = file_path
        self.current_class = None
        self.current_function = None
        self.functions = []
        self.calls = []
        self.counter = counter_start

    def visit_FunctionDef(self, node):
        self.counter += 1

        function_info = {
            "id": self.counter,
            "name": node.name,
            "file": os.path.basename(self.file_path),
            "path": self.file_path[2:] if self.file_path.startswith("./") else self.file_path,
            "language": "Python",
            "parameters": {
                "count": len([arg for arg in node.args.args if arg.arg not in ("self", "cls")]),
                "types": ["unknown"] * len([arg for arg in node.args.args if arg.arg not in ("self", "cls")])
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
            "caller_Id": self._get_function_id(name=self.current_function, parent_class=self.current_class, param_count=caller_param_count),
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

    def visit_ClassDef(self, node):
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class

    def _get_function_id(self, name, parent_class=None, param_count=None):
        if not name or name.strip() == "":
            return "UNKNOWN"

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

def analyze_python_files(directory):
    all_functions = []
    all_calls = []

    counter = load_id_counter()

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()

                try:
                    tree = ast.parse(code)
                    analyzer = PythonFunctionAnalyzer(file_path, counter)

                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node

                    analyzer.visit(tree)

                    all_functions.extend(analyzer.functions)
                    all_calls.extend(analyzer.calls)

                    counter = analyzer.counter

                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    # Update each call with callee_Id by matching against known functions.
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
                call["callee_Id"] = func["id"]
                matched = True
                break

        if not matched:
            for func in all_functions:
                if (
                    func["name"] == callee_name and
                    func["parameters"]["count"] == arg_count
                ):
                    call["callee_Id"] = func["id"]
                    matched = True
                    break

        if not matched:
            for func in all_functions:
                if func["name"] == callee_name:
                    call["callee_Id"] = func["id"]
                    matched = True
                    break

        call.pop("calleeName", None)
        call.pop("calleeClass", None)

    with open("unique_functions_python.json", "w", encoding="utf-8") as f:
        json.dump(all_functions, f, indent=4)

    # Keep only calls with both caller_Id and callee_Id defined and not "UNKNOWN"
    final_calls = [
        call for call in all_calls 
        if call.get("caller_Id") is not None and 
           call.get("callee_Id") is not None and 
           str(call.get("caller_Id")) != "UNKNOWN" and 
           str(call.get("callee_Id")) != "UNKNOWN"
    ]

    with open("function_calls_python.json", "w", encoding="utf-8") as f:
        json.dump(final_calls, f, indent=4)

    save_id_counter(counter)
    print("Generated 'unique_functions_java.json' and 'function_calls_python.json'.")
    analyze_metrics(all_functions, all_calls)

def analyze_metrics(all_functions, all_calls):
    call_counts = Counter(call["callee_Id"] for call in all_calls if "callee_Id" in call)

    most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
    print("Most Called Functions:")
    for func_id, count in most_called[:5]:
        func_name = next((f["name"] for f in all_functions if f["id"] == func_id), "Unknown")
        print(f"{func_name} (ID: {func_id}) - {count} times")

    called_ids = set(call_counts.keys())
    all_function_ids = {func["id"] for func in all_functions}
    unused = all_function_ids - called_ids
    print("\nUnused Functions:")
    for func in all_functions:
        if func["id"] in unused:
            print(f"{func['name']} (ID: {func['id']}) - Unused")

if __name__ == "__main__":
    analyze_python_files(".")
    save_id_counter(1)
    

