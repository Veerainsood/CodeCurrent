
import re
import os
import argparse

# Mapping JNI signature codes to types
t_SIG_MAP = {
    'Z': 'boolean',
    'B': 'byte',
    'C': 'char',
    'S': 'short',
    'I': 'int',
    'J': 'long',
    'F': 'float',
    'D': 'double',
    'V': 'void'
}


def parse_python_c_api(code):
    # Map pFunc vars to Python function names
    func_map = {m.group(1): m.group(2)
                for m in re.finditer(r"(\w+)\s*=\s*PyObject_GetAttrString\(\s*\w+\s*,\s*\"([^\"]+)\"\s*\)", code)}
    # Map pArgs vars to tuple counts and types
    args_map = {}
    for m in re.finditer(r"(\w+)\s*=\s*PyTuple_New\(\s*(\d+)\s*\)", code):
        var, cnt = m.groups()
        args_map[var] = {'count': int(cnt), 'types': []}
    # Collect parameter types via PyTuple_SetItem
    for m in re.finditer(r"PyTuple_SetItem\(\s*(\w+)\s*,\s*\d+\s*,\s*Py(\w+)_From", code):
        var, ptype = m.groups()
        if var in args_map:
            args_map[var]['types'].append(ptype.lower())
    # Find calls
    calls = []
    for m in re.finditer(r"PyObject_CallObject\(\s*(\w+)\s*,\s*(\w+)\s*\)", code):
        pfunc, pargs = m.groups()
        fname = func_map.get(pfunc, 'unknown')
        arginfo = args_map.get(pargs, {'count': None, 'types': []})
        calls.append({
            'function': fname,
            'num_params': arginfo['count'],
            'param_types': arginfo['types']
        })
    return calls


def parse_pybind11(code):
    calls = []
    for m in re.finditer(r"\.attr\(\s*\"([^\"]+)\"\s*\)\s*\(([^)]*)\)", code):
        fname, arg_str = m.groups()
        args = [a.strip() for a in arg_str.split(',') if a.strip()]
        types = []
        for arg in args:
            if re.match(r"^\d+$", arg): types.append('int')
            elif re.match(r"^\d+\.\d*$", arg): types.append('float')
            elif re.match(r"^\".*\"$", arg): types.append('string')
            elif arg in ('true','false'): types.append('bool')
            else: types.append('unknown')
        calls.append({
            'function': fname,
            'num_params': len(args),
            'param_types': types
        })
    return calls


def parse_boost_python(code):
    # Map func vars to names
    func_vars = {m.group(1): m.group(2)
                 for m in re.finditer(r"object\s+(\w+)\s*=\s*\w+\.attr\(\s*\"([^\"]+)\"\s*\)", code)}
    calls = []
    for var, fname in func_vars.items():
        pattern = re.escape(var) + r"\s*\(([^)]*)\)"
        for m in re.finditer(pattern, code):
            arg_str = m.group(1)
            args = [a.strip() for a in arg_str.split(',') if a.strip()]
            types = []
            for arg in args:
                if re.match(r"^\d+$", arg): types.append('int')
                elif re.match(r"^\d+\.\d*$", arg): types.append('float')
                elif re.match(r"^\".*\"$", arg): types.append('string')
                elif arg in ('true','false'): types.append('bool')
                else: types.append('unknown')
            calls.append({
                'function': fname,
                'num_params': len(args),
                'param_types': types
            })
    return calls


def parse_swig(code):
    calls = []
    # Detect SWIG init
    if re.search(r'init\w+\s*\(', code):
        for m in re.finditer(r"\b([a-zA-Z_]\w*)\s*\(([^)]*)\)", code):
            fname, arg_str = m.groups()
            # skip common C/C++ calls
            if fname in ('if','for','while','switch','return','sizeof','new','delete',
                         'std::system','PyObject_CallObject','PyTuple_New','PyTuple_SetItem',
                         'PyObject_GetAttrString','object','py::module','env->CallStatic',
                         'sock.send','curl_easy_setopt','stub->'):
                continue
            args = [a.strip() for a in arg_str.split(',') if a.strip()]
            types = []
            for arg in args:
                if re.match(r"^\d+$", arg): types.append('int')
                elif re.match(r"^\d+\.\d*$", arg): types.append('float')
                elif re.match(r"^\".*\"$", arg): types.append('string')
                elif arg in ('true','false'): types.append('bool')
                else: types.append('unknown')
            calls.append({
                'function': fname,
                'num_params': len(args),
                'param_types': types
            })
    return calls


def parse_python_subprocess(code):
    calls = []
    for m in re.finditer(r'std::system\(\s*"([^"]*python3?[^\"]*)"', code):
        cmd = m.group(1)
        for m2 in re.finditer(r"(\w+)\.(\w+)\s*\(([^)]*)\)", cmd):
            mod, fname, arg_str = m2.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            types = []
            for arg in args:
                if re.match(r"^\d+$", arg): types.append('int')
                elif re.match(r"^\d+\.\d*$", arg): types.append('float')
                else: types.append('string')
            calls.append({
                'function': fname,
                'num_params': len(args),
                'param_types': types
            })
    return calls


def parse_jni(code):
    calls = []
    # Map mid vars to (fname, signature)
    mid_map = {}
    for m in re.finditer(r"(\w+)\s*=\s*env->GetStaticMethodID\(\s*\w+\s*,\s*\"([^\"]+)\"\s*,\s*\"([^\"]+)\"\s*\)", code):
        var, fname, sig = m.groups()
        mid_map[var] = {'fname': fname, 'sig': sig}

    def parse_sig(sig):
        params = sig[sig.find('(')+1:sig.find(')')]
        types = []
        i = 0
        while i < len(params):
            c = params[i]
            if c in t_SIG_MAP:
                types.append(t_SIG_MAP[c]); i += 1
            elif c == 'L':  # object reference
                semi = params.find(';', i)
                types.append('object'); i = semi + 1
            elif c == '[':  # array, skip
                i += 1
            else:
                types.append('unknown'); i += 1
        return types

    for m in re.finditer(r"env->CallStatic\w+Method\(\s*\w+\s*,\s*(\w+)\s*,\s*([^)]+)\)", code):
        mid_var, arg_str = m.groups()
        entry = mid_map.get(mid_var)
        if not entry: continue
        fname = entry['fname']
        param_types = parse_sig(entry['sig'])
        calls.append({
            'function': fname,
            'num_params': len(param_types),
            'param_types': param_types
        })
    return calls


def parse_java_subprocess(code):
    calls = []
    for m in re.finditer(r'std::system\(\s*"java\s+-cp\s+[^\"]+\s+(\w+)\s+([^\"]+)"', code):
        cls, arg_str = m.groups()
        fname = f"{cls}.main"
        args = arg_str.split()
        types = []
        for arg in args:
            if re.match(r"^\d+$", arg): types.append('int')
            elif re.match(r"^\d+\.\d*$", arg): types.append('float')
            else: types.append('string')
        calls.append({
            'function': fname,
            'num_params': len(args),
            'param_types': types
        })
    return calls


def parse_grpc(code):
    calls = []
    for m in re.finditer(r"stub->(\w+)\s*\(([^)]*)\)", code):
        fname, arg_str = m.groups()
        args = [a.strip() for a in arg_str.split(',') if a.strip()]
        calls.append({
            'function': fname,
            'num_params': len(args),
            'param_types': ['unknown'] * len(args)
        })
    return calls


def parse_rest(code):
    calls = []
    for m in re.finditer(r'curl_easy_setopt\([^,]+,\s*CURLOPT_URL\s*,\s*"([^"]+)"', code):
        url = m.group(1)
        path = url.split('://')[-1].split('?')[0]
        fname = path.split('/')[-1]
        query = url.split('?')[1] if '?' in url else ''
        params = [p for p in query.split('&') if p]
        types = []
        for p in params:
            k, v = p.split('=')
            if re.match(r"^\d+$", v): types.append('int')
            elif re.match(r"^\d+\.\d*$", v): types.append('float')
            else: types.append('string')
        calls.append({
            'function': fname,
            'num_params': len(params),
            'param_types': types
        })
    return calls


def collect_calls(code):
    return {
        'python_c_api': parse_python_c_api(code),
        'pybind11':       parse_pybind11(code),
        'boost_python':   parse_boost_python(code),
        'swig':           parse_swig(code),
        'py_subprocess':  parse_python_subprocess(code),
        'jni':            parse_jni(code),
        'java_subproc':   parse_java_subprocess(code),
        'grpc':           parse_grpc(code),
        'rest':           parse_rest(code)
    }


def main():
    print("C++ Interop Parser")
    parser = argparse.ArgumentParser(description='Parse C++ interop calls to Python/Java')
    # parser.add_argument('paths', nargs='+', help='Files or directories to scan')
    # args = parser.parse_args()
    paths = [
        './main.cpp'# This can also be a directory
    ]
    results = {}
    for path in paths:
        print(f"Scanning {path}...")
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for fname in files:
                    if fname.endswith(('.cpp', '.cc', '.cxx', '.hpp', '.h')):
                        fp = os.path.join(root, fname)
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                        results[fp] = collect_calls(code)
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            results[path] = collect_calls(code)

    # Print summary
    for fp, calls in results.items():
        print(f"File: {fp}")
        for kind, lst in calls.items():
            if not lst:
                continue
            print(f"  {kind}:")
            for c in lst:
                print(f"    Function: {c['function']}, Num Params: {c['num_params']}, Param Types: {c['param_types']}")
    return 0

main()
