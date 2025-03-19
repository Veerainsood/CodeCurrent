#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/CommandLine.h"

using namespace clang;
using namespace clang::tooling;

// ✅ Visitor to find function calls and definitions
class MyVisitor : public RecursiveASTVisitor<MyVisitor> {
public:
    bool VisitCallExpr(CallExpr *call) {
        if (const FunctionDecl *FD = call->getDirectCallee()) {
            llvm::outs() << "Function call: " << FD->getQualifiedNameAsString() << "\n";

            if (const CXXMethodDecl *MD = dyn_cast<CXXMethodDecl>(FD)) {
                llvm::outs() << " - Class: " << MD->getParent()->getQualifiedNameAsString() << "\n";
                if (MD->isVirtual()) {
                    llvm::outs() << " - Virtual: Yes\n";
                    if (MD->size_overridden_methods()) {
                        llvm::outs() << " - Overrides: ";
                        for (const auto *OM : MD->overridden_methods()) {
                            llvm::outs() << OM->getQualifiedNameAsString() << " ";
                        }
                        llvm::outs() << "\n";
                    }
                } else {
                    llvm::outs() << " - Virtual: No\n";
                }
            } else {
                llvm::outs() << " - Non-member function\n";
            }

            // Display parameter types
            llvm::outs() << " - Signature: (";
            for (unsigned i = 0; i < FD->getNumParams(); ++i) {
                if (i > 0) llvm::outs() << ", ";
                llvm::outs() << FD->getParamDecl(i)->getType().getAsString();
            }
            llvm::outs() << ")\n";
        }
        return true;
    }

    bool VisitFunctionDecl(FunctionDecl *FD) {
        if (FD->hasBody()) {
            llvm::outs() << "\nFunction definition: " << FD->getQualifiedNameAsString() << "\n";
            if (const CXXMethodDecl *MD = dyn_cast<CXXMethodDecl>(FD)) {
                llvm::outs() << " - Class: " << MD->getParent()->getQualifiedNameAsString() << "\n";
                if (MD->isVirtual()) {
                    llvm::outs() << " - Virtual: Yes\n";
                    if (MD->size_overridden_methods()) {
                        llvm::outs() << " - Overrides: ";
                        for (const auto *OM : MD->overridden_methods()) {
                            llvm::outs() << OM->getQualifiedNameAsString() << " ";
                        }
                        llvm::outs() << "\n";
                    }
                } else {
                    llvm::outs() << " - Virtual: No\n";
                }
            } else {
                llvm::outs() << " - Non-member function\n";
            }

            // Display parameter types
            llvm::outs() << " - Signature: (";
            for (unsigned i = 0; i < FD->getNumParams(); ++i) {
                if (i > 0) llvm::outs() << ", ";
                llvm::outs() << FD->getParamDecl(i)->getType().getAsString();
            }
            llvm::outs() << ")\n";
        }
        return true;
    }
};

// ✅ AST consumer that runs the visitor
class MyASTConsumer : public ASTConsumer {
public:
    void HandleTranslationUnit(ASTContext &Context) override {
        Visitor.TraverseDecl(Context.getTranslationUnitDecl());
    }
private:
    MyVisitor Visitor;
};

// ✅ Frontend action to create AST consumer
class MyFrontendAction : public ASTFrontendAction {
public:
    std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI, StringRef file) override {
        return std::make_unique<MyASTConsumer>();
    }
};

// ✅ Command line options
static llvm::cl::OptionCategory MyToolCategory("my-tool options");

int main(int argc, const char **argv) {
    // Updated to handle llvm::Expected<CommonOptionsParser>
    auto ExpectedParser = CommonOptionsParser::create(argc, argv, MyToolCategory);
    
    if (!ExpectedParser) {
        llvm::errs() << ExpectedParser.takeError();
        return 1;
    }
    
    // Unwrap the parser
    CommonOptionsParser &OptionsParser = *ExpectedParser;

    // Create ClangTool with compilation database and source file list
    ClangTool Tool(OptionsParser.getCompilations(), OptionsParser.getSourcePathList());

    // Run the tool using MyFrontendAction
    return Tool.run(newFrontendActionFactory<MyFrontendAction>().get());
}
