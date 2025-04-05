import os
import re

# Define patterns that indicate C++ calling Python or Java
PATTERNS = {
    'python': [
        r'#include\s*<Python\.h>',
        r'Py_Initialize\s*\(',
        r'PyRun_SimpleString\s*\(',
        r'PyObject_',
        r'Py_Finalize\s*\('
    ],
    'java': [
        r'#include\s*<jni\.h>',
        r'JNI_CreateJavaVM',
        r'JNIEnv\s*\*',
        r'jclass',
        r'Call\w+Method',
        r'FindClass\s*\(',
        r'GetMethodID\s*\('
    ]
}

def check_file_for_patterns(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            results = {
                'python': any(re.search(p, content) for p in PATTERNS['python']),
                'java': any(re.search(p, content) for p in PATTERNS['java']),
            }
            return results
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {'python': False, 'java': False}

def scan_cpp_files():
    matches = []

    for filename in os.listdir('.'):
        if filename.endswith('.cpp'):
            result = check_file_for_patterns(filename)
            if result['python'] or result['java']:
                matches.append((filename, result))
    
    return matches

if __name__ == "__main__":
    results = scan_cpp_files()
    if not results:
        print("✅ No external calls to Python or Java found.")
    else:
        print("⚠️ External calls detected:")
        for file, types in results:
            langs = []
            if types['python']:
                langs.append('Python')
            if types['java']:
                langs.append('Java')
            print(f"- {file}: {', '.join(langs)}")
