def parse_ast(node, file_path):
    """ Recursively traverse the AST to extract user-defined functions & calls """
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if node.location.file and node.location.file.name != file_path:
            return  # Ignore functions from system headers

        # Extract function details
        parent_class, parent_function = find_parent(node)
        function_info = {
            "id": len(unique_functions) + 1,
            "name": node.spelling,
            "file": os.path.basename(file_path),
            "path": os.path.abspath(file_path),
            "language": "C++",
            "parameters": get_function_parameters(node),
            "parentClass": parent_class,
            "parentFunction": parent_function
        }
        unique_functions.append(function_info)

    if node.kind == clang.cindex.CursorKind.CALL_EXPR:
        # Identify function calls and relationships
        caller = node.semantic_parent
        if caller and caller.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            caller_name = caller.spelling
            callee_name = node.spelling

            caller_id = next((f["id"] for f in unique_functions if f["name"] == caller_name), None)
            callee_id = next((f["id"] for f in unique_functions if f["name"] == callee_name), None)

            if caller_id and callee_id:
                call_info = {
                    "callerId": caller_id,
                    "calleeId": callee_id,
                    "isInsideIfElseOrSwitch": any(
                        parent.kind in [clang.cindex.CursorKind.IF_STMT, clang.cindex.CursorKind.SWITCH_STMT]
                        for parent in node.get_ancestors()
                    ),
                    "isInsideLoopOrEnvironment": any(
                        parent.kind in [clang.cindex.CursorKind.FOR_STMT, clang.cindex.CursorKind.WHILE_STMT, clang.cindex.CursorKind.DO_STMT]
                        for parent in node.get_ancestors()
                    ),
                    "isDifferentLanguage": False,  # Currently only parsing C++
                    "isDifferentModule": False,  # Assuming one module for now
                    "isInsideClass": find_parent(caller)[0] is not None,
                    "isInsideFunction": find_parent(caller)[1] is not None
                }
                function_calls.append(call_info)

    # Recursively process child nodes
    for child in node.get_children():
        parse_ast(child, file_path)
