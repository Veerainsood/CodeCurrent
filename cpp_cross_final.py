import re
import os
import argparse

# JNI signature mapping
SIG_MAP = {
    'Z': 'boolean', 'B': 'byte', 'C': 'char', 'S': 'short',
    'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double', 'V': 'void'
}


def infer_types(args):
    """
    Infer parameter types from a list of argument strings.
    Recognizes ints, floats, booleans, and defaults to string.
    """
    types = []
    for a in args:
        if re.fullmatch(r"\d+", a):  # Integer
            types.append('int')
        elif re.fullmatch(r"\d+\.\d*", a):  # Float
            types.append('float')
        elif a.lower() in ('true', 'false'):  # Boolean
            types.append('bool')
        else:
            types.append('string')  # Default to string
    return types


def parse_sig(sig):
    """
    Parses a JNI method signature string to extract parameter types.
    Example: "(ILjava/lang/String;)V" -> ['int', 'object']
    """
    types = []
    params = sig[sig.find('(')+1:sig.find(')')]
    i = 0
    while i < len(params):
        c = params[i]
        if c in SIG_MAP:
            types.append(SIG_MAP[c])  # Primitive type
            i += 1
        elif c == 'L':  # Object reference
            end = params.find(';', i)
            types.append('object')
            i = end + 1
        else:
            types.append('unknown')  # Unrecognized
            i += 1
    return types


def collect_calls_in_file(filepath):
    """
    Parse a C++ source file and extract inter-language function calls
    to Python or Java using multiple FFI mechanisms (Python/C API, pybind11, JNI, etc.).
    Returns a list of dicts describing each call.
    """
    calls = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    code = ''.join(lines)

    # Mappings for Python C API
    imports_map = {m.group(1): m.group(2)
                   for m in re.finditer(r"(\w+)\s*=\s*PyImport_ImportModule\(\s*\"([^\"]+)\"\s*\)", code)}
    funcs_map = {m.group(1): {'func': m.group(3), 'module_var': m.group(2)}
                 for m in re.finditer(r"(\w+)\s*=\s*PyObject_GetAttrString\(\s*(\w+)\s*,\s*\"([^\"]+)\"\s*\)", code)}
    args_map = {m.group(1): int(m.group(2))
                for m in re.finditer(r"(\w+)\s*=\s*PyTuple_New\(\s*(\d+)\s*\)", code)}

    # Mappings for pybind11 and Boost.Python
    py_import_map = {m.group(1): m.group(2)
                     for m in re.finditer(r"py::object\s+(\w+)\s*=\s*py::module::import\(\s*\"([^\"]+)\"\s*\)", code)}
    boost_import_map = {m.group(1): m.group(2)
                        for m in re.finditer(r"object\s+(\w+)\s*=\s*import\(\s*\"([^\"]+)\"\s*\)", code)}

    # Mappings for JNI
    class_map = {m.group(1): m.group(2)
                 for m in re.finditer(r"(\w+)\s*=\s*env->FindClass\(\s*\"([^\"]+)\"\s*\)", code)}
    mid_map = {m.group(1): {'method': m.group(2), 'sig': m.group(3)}
               for m in re.finditer(r"(\w+)\s*=\s*env->GetStaticMethodID\([^,]+,\s*\"([^\"]+)\"\s*,\s*\"([^\"]+)\"\s*\)", code)}

    # Identify SWIG block ranges by function headers
    swig_ranges = []
    for m in re.finditer(r"void\s+\w*swig\w*\s*\([^)]*\)\s*\{", code):
        start = code[:m.start()].count('\n') + 1
        end = code.find('}', m.end())
        end_line = code[:end].count('\n') + 1
        swig_ranges.append((start, end_line))

    # Parse each line for interop patterns
    for lineno, line in enumerate(lines, start=1):
        # C API
        for m in re.finditer(r"PyObject_CallObject\((\w+),\s*(\w+)\)", line):
            pf, pa = m.groups()
            entry = funcs_map.get(pf, {})
            fname = entry.get('func', 'unknown')
            count = args_map.get(pa)
            types = [pt.lower() for pt in re.findall(rf"PyTuple_SetItem\({pa},\s*\d+,\s*Py(\w+)_From", code)]
            mod_var = entry.get('module_var')
            module = imports_map.get(mod_var)
            file_called = module + '.py' if module else None
            calls.append({'kind': 'python_c_api', 'line': lineno,
                          'function': fname, 'num_params': count,
                          'param_types': types, 'file': file_called})

        # pybind11
        for m in re.finditer(r"(\w+)\.attr\(\s*\"([^\"]+)\"\s*\)\s*\(([^)]*)\)", line):
            var, fname, arg_str = m.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            module = py_import_map.get(var)
            file_called = module + '.py' if module else None
            calls.append({'kind': 'pybind11', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': file_called})

        # Boost.Python
        for m in re.finditer(r"(\w+)\.attr\(\s*\"([^\"]+)\"\s*\)\s*\(([^)]*)\)", line):
            var, fname, arg_str = m.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            module = boost_import_map.get(var)
            file_called = module + '.py' if module else None
            calls.append({'kind': 'boost_python', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': file_called})

        # SWIG
        for start, end in swig_ranges:
            if start <= lineno <= end:
                for m in re.finditer(r"(\w+)\s*\(([^)]*)\)", line):
                    fname, arg_str = m.groups()
                    args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
                    calls.append({'kind': 'swig', 'line': lineno,
                                  'function': fname, 'num_params': len(args),
                                  'param_types': infer_types(args), 'file': None})

        # Python subprocess
        for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*python3?[^\"]*)\"", line):
            cmd = m.group(1)
            m2 = re.search(r"(\w+)\.(\w+)\(([^)]*)\)", cmd)
            if not m2: continue
            mod, fname, arg_str = m2.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            calls.append({'kind': 'py_subprocess', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': mod + '.py'})

        # ZeroMQ-based Python
        for m in re.finditer(r"send\([^)]*?zmq::buffer\(\s*\"(\w+)\(([^)]*)\)\"", line):
            fname, arg_str = m.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            calls.append({'kind': 'zmq_python', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': None})

        # JNI
        for m in re.finditer(r"env->CallStatic\w+Method\(\s*(\w+)\s*,\s*(\w+)\)", line):
            cls_var, mid_var = m.groups()
            cls_name = class_map.get(cls_var)
            entry = mid_map.get(mid_var, {})
            fname = entry.get('method')
            sig = entry.get('sig')
            types = parse_sig(sig) if sig else []
            file_called = cls_name + '.java' if cls_name else None
            calls.append({'kind': 'jni', 'line': lineno,
                          'function': fname, 'num_params': len(types),
                          'param_types': types, 'file': file_called})

        # Java subprocess
        for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*java\s+\w+[^\"]*)\"", line):
            cmd = m.group(1)
            parts = cmd.split()
            if parts[0] != 'java': continue
            cls = parts[1]; args = parts[2:]
            calls.append({'kind': 'java_subproc', 'line': lineno,
                          'function': cls + '.main', 'num_params': len(args),
                          'param_types': infer_types(args), 'file': cls + '.java'})

        # REST API via curl command
        for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*curl[^\"]*)\"", line):
            cmd = m.group(1)
            m2 = re.search(r"curl\s+([^\s]+)\?([^\s]+)", cmd)
            if m2:
                path, query = m2.groups()
                fname = path.rstrip('/').split('/')[-1]
                vals = [p.split('=')[1] for p in query.split('&') if '=' in p]
                calls.append({'kind': 'rest', 'line': lineno,
                              'function': fname, 'num_params': len(vals),
                              'param_types': infer_types(vals), 'file': None})
        for m in re.finditer(r"curl_easy_setopt\([^,]+,\s*CURLOPT_URL\s*,\s*\"([^\"]+)\"", line):
            url = m.group(1)
            path = url.split('://')[-1].split('?')[0]
            fname = path.split('/')[-1]
            query = url.split('?')[1] if '?' in url else ''
            vals = [p.split('=')[1] for p in query.split('&') if '=' in p]
            calls.append({'kind': 'rest', 'line': lineno,
                          'function': fname, 'num_params': len(vals),
                          'param_types': infer_types(vals), 'file': None})

        # Java call over socket
        for m in re.finditer(r"send\(\s*sock\s*,\s*\"(\w+)\(([^)]*)\)\"", line):
            fname, arg_str = m.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            calls.append({'kind': 'socket_java', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': None})

        # gRPC call
        for m in re.finditer(r"stub->(\w+)\s*\(([^)]*)\)", line):
            fname, arg_str = m.groups()
            args = [a.strip() for a in arg_str.split(',') if a.strip()]
            calls.append({'kind': 'grpc', 'line': lineno,
                          'function': fname, 'num_params': len(args),
                          'param_types': infer_types(args), 'file': None})

    return calls


def main():
    """
    Entry point: iterates over provided files or directories and prints
    detected interop calls to Python/Java from C++.
    """
    print("C++ Interop Parser")
    parser = argparse.ArgumentParser(description='Parse C++ interop calls to Python/Java')
    # parser.add_argument('paths', nargs='+', help='Files or directories to scan')
    # args = parser.parse_args()
    paths = [
        './call_all.cpp'  # Can also be a directory
    ]

    for path in paths:
        files = ([path] if os.path.isfile(path)
                 else [os.path.join(dp, f) for dp, _, fs in os.walk(path)
                       for f in fs if f.endswith(('.cpp', '.cc', '.cxx', '.hpp', '.h'))])
        for fp in files:
            calls = collect_calls_in_file(fp)
            print(f"File: {fp}")
            for c in calls:
                print(f"  [{c['kind']}] Line {c['line']}: {c['function']}(" +
                      f"{c['num_params']} args, types={c['param_types']}) -> {c['file']}")

if __name__ == '__main__':
    main()
