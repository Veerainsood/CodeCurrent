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

CPP_EXTENSIONS = ('.cpp', '.cc', '.cxx', '.C')

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
    for dirpath, _, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith(CPP_EXTENSIONS):
                full_path = os.path.join(dirpath, filename)
                result = check_file_for_patterns(full_path)
                if result['python'] or result['java']:
                    matches.append((full_path, result))
    return matches

if __name__ == "__main__":
    results = scan_cpp_files()
    output_path = "external_calls.txt"

    if not results:
        print("✅ No external calls to Python or Java found.")
    else:
        print("⚠️ External calls detected:")
        with open(output_path, 'w') as f:
            for file, types in results:
                langs = []
                if types['python']:
                    langs.append('Python')
                if types['java']:
                    langs.append('Java')
                line = f"{file},{','.join(langs)}"
                print(f"- {line}")
                f.write(line + "\n")
        print(f"\n📁 File paths saved to: {output_path}")
