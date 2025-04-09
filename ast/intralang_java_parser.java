import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.github.javaparser.resolution.declarations.ResolvedConstructorDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;
import com.github.javaparser.symbolsolver.javaparsermodel.JavaParserFacade;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.FileWriter;
import java.util.*;

public class intralang_java_parser {

    static class FunctionCallInfo {
        String name;
        String file;
        String caller_path;
        String language = "Java";
        Map<String, Object> parameters;
        String parentClass;
        String parentFunction;
        String parentFunctionClass;
        Map<String, Object> parentFunctionParameters;
        String callee_path;
        String parentFunctionReturnType;
        String calleeReturnType;

        // New metadata flags
        boolean is_foreign_call = false;
        boolean isInsideIfElseOrSwitch = false;
        boolean isInsideLoopOrEnvironment = false;
        boolean isDifferentLanguage = false;
        boolean isDifferentModule = false;
        boolean isInsideClass = false;
        boolean isInsideFunction = true;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.out.println("Usage: java intralang_java_parser <input_java_file>");
            return;
        }

        String filePath = args[0];
        File file = new File(filePath);
        if (!file.exists()) {
            System.out.println("File not found: " + filePath);
            return;
        }

        // Setup symbol solver
        CombinedTypeSolver typeSolver = new CombinedTypeSolver();
        typeSolver.add(new ReflectionTypeSolver());
        File sourceRoot = file.getParentFile() != null ? file.getParentFile() : new File(".");
        typeSolver.add(new JavaParserTypeSolver(sourceRoot));
        JavaParserFacade javaParserFacade = JavaParserFacade.get(typeSolver);

        CompilationUnit cu = StaticJavaParser.parse(file);
        List<FunctionCallInfo> calls = new ArrayList<>();

        cu.accept(new VoidVisitorAdapter<Void>() {
            @Override
            public void visit(MethodCallExpr mce, Void arg) {
                super.visit(mce, arg);

                FunctionCallInfo callInfo = new FunctionCallInfo();
                callInfo.name = mce.getNameAsString();
                callInfo.file = file.getName();
                callInfo.caller_path = file.getAbsolutePath();

                Optional<MethodDeclaration> enclosingMethod = mce.findAncestor(MethodDeclaration.class);
                Optional<ClassOrInterfaceDeclaration> enclosingClass = mce.findAncestor(ClassOrInterfaceDeclaration.class);

                // Return types and names
                if (enclosingMethod.isPresent()) {
                    MethodDeclaration methodDecl = enclosingMethod.get();
                    callInfo.parentFunction = methodDecl.getNameAsString();
                    callInfo.parentFunctionReturnType = methodDecl.isConstructorDeclaration() ? null : methodDecl.getType().toString();
                }

                callInfo.parentFunctionClass = enclosingClass.map(ClassOrInterfaceDeclaration::getNameAsString).orElse(null);

                // Parent parameters
                List<String> paramTypes = enclosingMethod.map(m -> {
                    List<String> params = new ArrayList<>();
                    for (Parameter p : m.getParameters()) {
                        params.add(p.getType().toString());
                    }
                    return params;
                }).orElse(Collections.emptyList());

                Map<String, Object> parentParams = new HashMap<>();
                parentParams.put("count", paramTypes.size());
                parentParams.put("types", paramTypes);
                callInfo.parentFunctionParameters = parentParams;

                // Call parameters (arguments count)
                Map<String, Object> callParams = new HashMap<>();
                callParams.put("count", mce.getArguments().size());
                callParams.put("types", Collections.emptyList());
                callInfo.parameters = callParams;

                // Metadata flags
                callInfo.isInsideClass = enclosingClass.isPresent();
                callInfo.isInsideFunction = enclosingMethod.isPresent();
                callInfo.isInsideIfElseOrSwitch = isInsideIfSwitch(mce);
                callInfo.isInsideLoopOrEnvironment = isInsideLoop(mce);
                // Dummy flags, can be made meaningful with further logic
                callInfo.is_foreign_call = false;
                callInfo.isDifferentLanguage = false;
                callInfo.isDifferentModule = false;

                // Callee info
                try {
                    ResolvedMethodDeclaration resolvedMethod = javaParserFacade.solve(mce).getCorrespondingDeclaration();
                    callInfo.parentClass = resolvedMethod.declaringType().getQualifiedName();

                    if (resolvedMethod instanceof ResolvedConstructorDeclaration) {
                        callInfo.calleeReturnType = null;
                    } else {
                        String fullName = resolvedMethod.getReturnType().describe();
                        String simpleName = fullName.replaceAll(".*\\.", "");
                        callInfo.calleeReturnType = simpleName;
                    }

                    Optional<CompilationUnit> declCU = resolvedMethod.toAst().flatMap(md -> md.findCompilationUnit());
                    if (declCU.isPresent()) {
                        declCU.get().getStorage().ifPresent(storage -> {
                            callInfo.callee_path = storage.getPath().toAbsolutePath().toString();
                        });
                    } else {
                        callInfo.callee_path = "Unknown";
                    }
                } catch (Exception e) {
                    callInfo.parentClass = "Unresolved";
                    callInfo.callee_path = "Unresolved";
                    callInfo.calleeReturnType = null;
                }

                calls.add(callInfo);
                System.out.println("📌 Captured: " + callInfo.name + " in " + callInfo.parentFunction);
            }
        }, null);

        // Write to JSON
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        try (FileWriter writer = new FileWriter("parser_output.json")) {
            Map<String, Object> output = new HashMap<>();
            output.put("functions", calls);
            gson.toJson(output, writer);
        }

        System.out.println("✅ Function calls extracted and saved to parser_output.json.");
    }

    private static boolean isInsideIfSwitch(Node node) {
        return node.findAncestor(IfStmt.class).isPresent() ||
               node.findAncestor(SwitchStmt.class).isPresent();
    }

    private static boolean isInsideLoop(Node node) {
        return node.findAncestor(ForStmt.class).isPresent() ||
               node.findAncestor(WhileStmt.class).isPresent() ||
               node.findAncestor(DoStmt.class).isPresent() ||
               node.findAncestor(ForEachStmt.class).isPresent();
    }
}
