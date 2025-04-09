
import re
import os
import argparse

# JNI signature mapping
SIG_MAP = {
    'Z': 'boolean', 'B': 'byte', 'C': 'char', 'S': 'short',
    'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double', 'V': 'void'
}

def infer_types(args):
    types = []
    for a in args:
        if re.fullmatch(r"\d+", a): types.append('int')
        elif re.fullmatch(r"\d+\.\d*", a): types.append('float')
        elif a.lower() in ('true','false'): types.append('bool')
        else: types.append('string')
    return types

# 1. Python/C API
def parse_python_c_api(code):
    funcs = {m.group(1): m.group(2)
             for m in re.finditer(r"(\w+)\s*=\s*PyObject_GetAttrString\([^,]+,\s*\"([^\"]+)\"", code)}
    args_map = {m.group(1): int(m.group(2))
                for m in re.finditer(r"(\w+)\s*=\s*PyTuple_New\((\d+)\)", code)}
    calls = []
    for m in re.finditer(r"PyObject_CallObject\((\w+),\s*(\w+)\)", code):
        pf, pa = m.groups()
        fname = funcs.get(pf, 'unknown')
        count = args_map.get(pa)
        # infer types via SetItem
        types = [pt.lower() for pt in re.findall(rf"PyTuple_SetItem\({pa},\s*\d+,\s*Py(\w+)_From", code)]
        calls.append({'function': fname, 'num_params': count, 'param_types': types})
    return calls

# 2. pybind11 and Boost.Python share same pattern
def parse_pybind_like(code):
    calls = []
    for m in re.finditer(r"\.attr\(\s*\"([^\"]+)\"\)\s*\(([^)]*)\)", code):
        fname, arg_str = m.groups()
        args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 3. SWIG: functions inside test_swig* blocks
def parse_swig(code):
    calls = []
    for block in re.finditer(r"void\s+\w*swig\w*\s*\([^)]*\)\s*\{([^}]+)\}", code, re.DOTALL):
        body = block.group(1)
        for m in re.finditer(r"(\w+)\s*\(([^)]*)\)", body):
            fname, arg_str = m.groups()
            args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
            calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 4. Python subprocess via system()
def parse_python_subprocess(code):
    calls = []
    for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*python3?[^\"]*)\"", code):
        cmd = m.group(1)
        m2 = re.search(r"(\w+)\.(\w+)\(([^)]*)\)", cmd)
        if not m2: continue
        _, fname, arg_str = m2.groups()
        args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 5. ZeroMQ Python messages
def parse_zmq_python(code):
    calls = []
    for m in re.finditer(r"send\([^)]*?zmq::buffer\(\s*\"(\w+)\(([^)]*)\)\"", code):
        fname, arg_str = m.groups()
        args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 6. JNI Invocation API
def parse_jni(code):
    mid_map = {}
    for m in re.finditer(r"(\w+)\s*=\s*env->GetStaticMethodID\([^,]+,\s*\"([^\"]+)\"\s*,\s*\"([^\"]+)\"", code):
        var, fname, sig = m.groups(); mid_map[var] = (fname, sig)
    calls = []
    for m in re.finditer(r"env->CallStatic\w+Method\([^,]+,\s*(\w+)(?:,\s*([^)]*))?\)", code):
        var, _ = m.groups()
        if var not in mid_map: continue
        fname, sig = mid_map[var]
        # parse signature
        params = sig[sig.find('(')+1:sig.find(')')]
        types = []
        i=0
        while i < len(params):
            c = params[i]
            if c in SIG_MAP: types.append(SIG_MAP[c]); i+=1
            elif c=='L': i = params.find(';', i)+1; types.append('object')
            else: types.append('unknown'); i+=1
        calls.append({'function': fname, 'num_params': len(types), 'param_types': types})
    return calls

# 7. Java subprocess via system()
def parse_java_subprocess(code):
    calls = []
    for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*java\s+\w+[^\"]*)\"", code):
        cmd = m.group(1)
        parts = cmd.split()
        if parts[0] != 'java': continue
        cls = parts[1]; args = parts[2:]
        fname = f"{cls}.main"
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 8. REST via curl command or libcurl
def parse_rest(code):
    calls = []
    # system("curl ...")
    for m in re.finditer(r"(?:std::)?system\(\s*\"([^\"]*curl[^\"]*)\"", code):
        cmd = m.group(1)
        m2 = re.search(r"curl\s+([^\s]+)\?([^\s]+)", cmd)
        if not m2: continue
        path, query = m2.groups()
        fname = path.rstrip('/').split('/')[-1]
        vals = [p.split('=')[1] for p in query.split('&') if '=' in p]
        calls.append({'function': fname, 'num_params': len(vals), 'param_types': infer_types(vals)})
    # libcurl
    for m in re.finditer(r"curl_easy_setopt\([^,]+,\s*CURLOPT_URL\s*,\s*\"([^\"]+)\"", code):
        url = m.group(1)
        path = url.split('://')[-1].split('?')[0]
        fname = path.split('/')[-1]
        query = url.split('?')[1] if '?' in url else ''
        vals = [p.split('=')[1] for p in query.split('&') if '=' in p]
        calls.append({'function': fname, 'num_params': len(vals), 'param_types': infer_types(vals)})
    return calls

# 9. Socket-based Java calls
def parse_socket_java(code):
    calls = []
    for m in re.finditer(r"send\(\s*sock\s*,\s*\"(\w+)\(([^)]*)\)\"", code):
        fname, arg_str = m.groups()
        args = [a.strip().strip('"\'"') for a in arg_str.split(',') if a.strip()]
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# 10. gRPC client calls
def parse_grpc(code):
    calls = []
    for m in re.finditer(r"stub->(\w+)\s*\(([^)]*)\)", code):
        fname, arg_str = m.groups()
        args = [a.strip() for a in arg_str.split(',') if a.strip()]
        calls.append({'function': fname, 'num_params': len(args), 'param_types': infer_types(args)})
    return calls

# Collect all
def collect_calls(code):
    return {
        'python_c_api':        parse_python_c_api(code),
        'pybind11':            parse_pybind_like(code),
        'boost_python':        parse_pybind_like(code),
        'swig':                parse_swig(code),
        'py_subprocess':       parse_python_subprocess(code),
        'zmq_python':          parse_zmq_python(code),
        'jni':                 parse_jni(code),
        'java_subproc':        parse_java_subprocess(code),
        'rest':                parse_rest(code),
        'socket_java':         parse_socket_java(code),
        'grpc':                parse_grpc(code)
    }

# Main
if __name__ == '__main__':
    print("C++ Interop Parser")
    parser = argparse.ArgumentParser(description='Parse C++ interop calls to Python/Java')
    # parser.add_argument('paths', nargs='+', help='Files or directories to scan')
    # args = parser.parse_args()
    paths = [
        './main.cpp'# This can also be a directory
    ]

    for path in paths:
        for fp in ([path] if os.path.isfile(path)
                   else [os.path.join(dp, f) for dp, _, fs in os.walk(path)
                         for f in fs if f.endswith(('.cpp','.cc','.cxx','.hpp','.h'))]):
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            calls = collect_calls(code)
            print(f"File: {fp}")
            for kind, lst in calls.items():
                if lst:
                    print(f"  {kind}:")
                    for c in lst:
                        print(f"    Function: {c['function']}, Num Params: {c['num_params']}, Param Types: {c['param_types']}")
