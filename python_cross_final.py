#!/usr/bin/env python3
import ast
import sys
import json

class CallVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        # Stack to keep track of function definitions (AST nodes)
        self.func_stack = []
        self.calls = []
        self.var_types = {}         # mapping variable -> interop type
        self.import_aliases = {}    # mapping alias -> full module name
        self.jython_classes = set()
        super().__init__()

    def visit_FunctionDef(self, node):
        self.func_stack.append(node)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name
            self.import_aliases[asname] = name
            # Only mark known interop modules.
            if name in ('jpype', 'ctypes', 'cffi', 'py4j'):
                self.var_types[asname] = name  # use module name as type
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            asname = alias.asname or alias.name
            fullname = f"{module}.{alias.name}" if module else alias.name
            self.import_aliases[asname] = fullname
            if module == 'jpype' and alias.name == 'JClass':
                self.import_aliases[asname] = 'jpype.JClass'
            if module == 'py4j.java_gateway' and alias.name == 'JavaGateway':
                self.import_aliases[asname] = 'py4j.java_gateway.JavaGateway'
            if module == 'cffi' and alias.name == 'FFI':
                self.import_aliases[asname] = 'cffi.FFI'
            # For Jython-style, mark classes (imported from a dotted module) with a leading uppercase.
            if '.' in module and alias.name and alias.name[0].isupper():
                self.jython_classes.add(asname)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            call = node.value
            tgt_ids = [tgt.id for tgt in node.targets if isinstance(tgt, ast.Name)]
            # JPype via module: var = jpype.JClass('...')
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                base = call.func.value.id
                if base in self.import_aliases and self.import_aliases[base] == 'jpype' and call.func.attr == 'JClass':
                    for tid in tgt_ids:
                        self.var_types[tid] = 'java_class'
            # JPype via direct import
            if isinstance(call.func, ast.Name) and call.func.id in self.import_aliases:
                full = self.import_aliases[call.func.id]
                if full == 'jpype.JClass':
                    for tid in tgt_ids:
                        self.var_types[tid] = 'java_class'
                elif full.endswith('JavaGateway'):
                    for tid in tgt_ids:
                        self.var_types[tid] = 'py4j_gateway'
                elif full == 'cffi.FFI':
                    for tid in tgt_ids:
                        self.var_types[tid] = 'cffi_ffi'
            # Process attribute calls on already typed objects
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                base = call.func.value.id
                attr = call.func.attr
                if base in self.var_types:
                    if self.var_types[base] == 'py4j_gateway' and attr == 'entry_point':
                        for tid in tgt_ids:
                            self.var_types[tid] = 'py4j_entry_point'
                    if self.var_types[base] == 'cffi_ffi' and attr == 'dlopen':
                        for tid in tgt_ids:
                            self.var_types[tid] = 'cffi_lib'
                # ctypes handling:
                if base == 'ctypes' and attr in ('CDLL', 'WinDLL'):
                    for tid in tgt_ids:
                        self.var_types[tid] = 'ctypes_lib'
            # Jython style:
            if isinstance(call.func, ast.Name) and call.func.id in self.jython_classes:
                for tid in tgt_ids:
                    self.var_types[tid] = 'jython_class'
            # Propagate java_class type if a java class is instantiated.
            if isinstance(call.func, ast.Name) and call.func.id in self.var_types:
                if self.var_types[call.func.id] == 'java_class':
                    for tid in tgt_ids:
                        self.var_types[tid] = 'java_class'
        self.generic_visit(node)

    def visit_Call(self, node):
        # Handle subprocess.run calls explicitly.
        if (isinstance(node.func, ast.Attribute) and 
            isinstance(node.func.value, ast.Name) and 
            node.func.value.id == 'subprocess' and 
            node.func.attr == 'run' and node.args):
            first = node.args[0]
            if isinstance(first, ast.List) and first.elts:
                prog = first.elts[0]
                if isinstance(prog, ast.Constant) and isinstance(prog.value, str):
                    cmd = prog.value
                    lang = 'java' if cmd.startswith('java') or '.jar' in cmd else 'cpp'
                    self._report(lang, cmd, first.elts[1:], node)
        # Only report calls on objects with an interop type.
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = node.func.value.id
            if base in self.var_types:
                lang = {
                    'java_class':       'java',
                    'py4j_gateway':     'java',
                    'py4j_entry_point': 'java',
                    'jython_class':     'java',
                    'ctypes':           'cpp',
                    'cffi':             'cpp',
                    'ctypes_lib':       'cpp',
                    'cffi_lib':         'cpp'
                }.get(self.var_types.get(base))
                if lang:
                    self._report(lang, node.func.attr, node.args, node)
        self.generic_visit(node)

    def _get_type(self, node):
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.Name):
            return 'variable'
        return node.__class__.__name__

    def _report(self, language, callee, args, call_node):
        # Determine caller from the function stack. If empty, then it's global.
        if self.func_stack:
            caller_node = self.func_stack[-1]
            caller_function = caller_node.name
            caller_args = [arg.arg for arg in caller_node.args.args]
            caller_args_count = len(caller_args)
        else:
            caller_function = "global"
            caller_args = []
            caller_args_count = 0

        # Use _get_type to get the type for each argument in the call.
        callee_args = [self._get_type(a) for a in args]
        callee_args_count = len(callee_args)

        start_line = call_node.lineno
        end_line = getattr(call_node, "end_lineno", start_line)

        self.calls.append({
            "caller_function": caller_function,
            "caller_arguments": caller_args,
            "caller_arguments_count": caller_args_count,
            "callee_name": callee,
            "callee_arguments": callee_args,
            "callee_arguments_count": callee_args_count,
            "caller_path": self.filename,
            "language": language,
            "target_file_path": None,
            "start_line": start_line,
            "end_line": end_line
        })

def main():
    if len(sys.argv) != 2:
        print("Usage: python detect_interop_calls.py <your_python_file.py>")
        sys.exit(1)
    fname = sys.argv[1]
    with open(fname, "r") as f:
        src = f.read()
    tree = ast.parse(src, filename=fname)
    visitor = CallVisitor(fname)
    visitor.visit(tree)
    with open("interlang_calls.json", "w") as f:
        json.dump(visitor.calls, f, indent=2)
    print(f"✅ JSON written to interlang_calls.json with {len(visitor.calls)} calls.")

if __name__ == "__main__":
    main()
