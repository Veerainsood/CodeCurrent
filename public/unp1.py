#!/usr/bin/env python3
import ast
import sys
import os

class CallVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.var_types = {}
        self.import_aliases = {}
        self.jython_classes = set()
        super().__init__()

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name
            self.import_aliases[asname] = name
            if name not in ('jpype', 'ctypes', 'cffi', 'subprocess', 'py4j'):
                self.var_types[asname] = 'cpp_extension'
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
            if '.' in module and alias.name and alias.name[0].isupper():
                self.jython_classes.add(asname)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                mod = call.func.value.id
                if mod in self.import_aliases and self.import_aliases[mod] == 'jpype' and call.func.attr == 'JClass':
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self.var_types[tgt.id] = 'java_class'

            if isinstance(call.func, ast.Name) and call.func.id in self.import_aliases and \
               self.import_aliases[call.func.id] == 'jpype.JClass':
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        self.var_types[tgt.id] = 'java_class'

            if isinstance(call.func, ast.Name):
                base = call.func.id
                if base in self.var_types and self.var_types[base] == 'java_class':
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self.var_types[tgt.id] = 'java_class'

            if isinstance(call.func, ast.Name) and call.func.id in self.import_aliases and \
               self.import_aliases[call.func.id].endswith('JavaGateway'):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        self.var_types[tgt.id] = 'py4j_gateway'

            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                base = call.func.value.id
                if base in self.var_types and self.var_types[base] == 'py4j_gateway' and call.func.attr == 'entry_point':
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self.var_types[tgt.id] = 'py4j_entry_point'

            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                if call.func.value.id == 'ctypes' and call.func.attr in ('CDLL', 'WinDLL'):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self.var_types[tgt.id] = 'ctypes_lib'

            if isinstance(call.func, ast.Name) and call.func.id in self.import_aliases and \
               self.import_aliases[call.func.id] == 'cffi.FFI':
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        self.var_types[tgt.id] = 'cffi_ffi'
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                if call.func.value.id == 'ffi' and call.func.attr == 'dlopen':
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self.var_types[tgt.id] = 'cffi_lib'

            if isinstance(call.func, ast.Name) and call.func.id in self.jython_classes:
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        self.var_types[tgt.id] = 'jython_class'

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) \
           and isinstance(node.func.value, ast.Name) \
           and node.func.value.id == 'subprocess' \
           and node.func.attr == 'run' \
           and node.args:
            first = node.args[0]
            if isinstance(first, ast.List) and first.elts:
                prog = first.elts[0]
                if isinstance(prog, ast.Constant) and isinstance(prog.value, str):
                    cmd = prog.value
                    kind = 'Java subprocess' if cmd.startswith('java') or '.jar' in cmd else 'C++ subprocess'
                    args = first.elts[1:]
                    self._report(kind, cmd, args, node.lineno)

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = node.func.value.id
            if base in self.var_types:
                kind = {
                    'java_class':       'JPype',
                    'py4j_entry_point': 'Py4J',
                    'jython_class':     'Jython',
                    'ctypes_lib':       'ctypes',
                    'cffi_lib':         'cffi',
                    'cpp_extension':    'C++ extension'
                }.get(self.var_types[base], None)
                if kind:
                    self._report(kind, node.func.attr, node.args, node.lineno)

        self.generic_visit(node)

    def _get_type(self, node):
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.Name):
            return 'variable'
        else:
            return node.__class__.__name__

    def _report(self, kind, func, args, lineno):
        types = [self._get_type(a) for a in args]
        source = self.filename

        # if func looks like a path or external program
        if func.endswith('.jar') or func.startswith('./') or '/' in func:
            target_file = func
        elif func.endswith('.py'):
            target_file = func
        else:
            target_file = source  # fallback to current file

        print(f"[{kind}] '{func}' called with {len(args)} args: {types} at line {lineno} from file: {target_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_calls.py <your_python_file.py>")
        sys.exit(1)
    fname = sys.argv[1]
    with open(fname, 'r') as f:
        src = f.read()
    tree = ast.parse(src, filename=fname)
    visitor = CallVisitor(fname)
    visitor.visit(tree)

if __name__ == '__main__':
    main()
