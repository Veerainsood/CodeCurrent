#!/usr/bin/env python3
import os
import argparse
from clang import cindex

# Adjust to point exactly at the DLL:
cindex.Config.set_library_file(
    r"C:\Program Files\LLVM\bin\libclang.dll"
)

# Now you can safely create the Index
index = cindex.Index.create()

#--- CONFIGURE: if libclang isn't found, you may need to point this to your libclang.so/dylib
# cindex.Config.set_library_file("/usr/lib/llvm-12/lib/libclang.so")

def find_cpp_files(root_dir):
    exts = ('.cpp', '.cc', '.cxx', '.c++', '.C')
    for dirpath, _, fnames in os.walk(root_dir):
        for fn in fnames:
            if fn.endswith(exts):
                yield os.path.join(dirpath, fn)

def is_user_function(callee, project_root):
    """Return True if this function declaration lives under your project."""
    loc = callee.location
    if not loc.file:
        return False
    # normalize paths
    fpath = os.path.abspath(loc.file.name)
    return os.path.commonpath([fpath, project_root]) == project_root

def collect_calls(tu, project_root):
    """
    Walk the AST of this translation unit,
    find all CALL_EXPRs, filter to user-defined funcs,
    and yield (name, [param types]).
    """
    for cursor in tu.cursor.walk_preorder():
        # free functions, member calls, constructors, etc.
        if cursor.kind.is_call_expr():
            callee = cursor.referenced
            if callee and callee.kind.is_function_decl() and is_user_function(callee, project_root):
                name = callee.spelling
                # declared parameters of the function
                param_types = [p.type.spelling for p in callee.get_arguments()]
                yield name, param_types

def main():
    p = argparse.ArgumentParser(
        description="Extract all calls to user-defined functions in a C++ project")
    p.add_argument("project_dir",
                   help="Path to your C++ project root")
    p.add_argument("--clang-args", nargs="*", default=[],
                   help="Extra flags to pass to libclang (e.g. -Iinclude)")
    args = p.parse_args()

    project_root = os.path.abspath(args.project_dir)
    # always at least set C++17
    clang_args = ["-std=c++17", f"-I{project_root}"] + args.clang_args

    index = cindex.Index.create()
    seen = set()  # to dedupe identical signatures

    for cpp_file in find_cpp_files(project_root):
        try:
            tu = index.parse(cpp_file, args=clang_args)
        except Exception as e:
            print(f"⚠️  Failed to parse {cpp_file}: {e}")
            continue

        for name, params in collect_calls(tu, project_root):
            sig = (name, tuple(params))
            if sig not in seen:
                seen.add(sig)
                print(f"{name} — {len(params)} param(s): {', '.join(params) or 'void'}")

if __name__ == "__main__":
    main()
