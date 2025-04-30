# Multi-language Functional Flow Visualization for Codebases

## Introduction

### Problem Statement

- Large codebases often span multiple programming languages(e.g., Python, Java, C++) making it difficult to understand the functional flow of the entire system.
- Understanding the functional call relationships across these languages is tedious and time-consuming.
- Developers struggle to visualize the flow of execution especially when
  - Functions are nested in classes or other functions.
  - Functions are defined in different files or modules.
  - Functions are defined in different languages.

### Objective

- To build a tool that can
  - Analyze a folder containing multiple programming languages.
  - Extract the definitions and calls of functions across these languages.
  - Show this data in an interactive visual graph format which is easy to understand.
  - Help developers explore the functions that are connected across codebase.

## Key Features

1. **Multi-language Support**: 
    - C++
    - Python
    - Java
2. **Functional Flow Extraction**: 
    - Identify all function definitions with clear metadata.
    - Track function calls, capture the context:
      - Inside conditionals(if, switch)
      - Inside loops(for, while)
      - cross-language or cross module
      - Nested in classes or other functions
3. **Interactive Visualization**: 
    - Uses `D3.js`  to render a force-directed graph.
    - Nodes = Functions, Edges = Calls between them
    - Clickable nodes to show metadata like function name, path, language and more.
4. **Standardized Output Format**: 
    - Outputs to a clean JSON format
      - `uniqueFunctions[]`: All distinct function metadata.
      - `functionCalls[]`: Links between functions + context.

## Methodology & Architecture

### 1. Generating JSON for C++ (Intra-language Calls)

- **Tool Used**: `clang`
- **Process**:
  - Parsed C++ files to extract function definitions.
  - Detected all intra-language function calls.
  - Captured function metadata (parameters, class nesting, file path).
  - Output the results into the `uniqueFunctions[]` and `functionCalls[]` JSON schema.

### 2. Generating JSON for Python (Intra-language Calls)

- **Tool Used**: Python `ast` module
- **Process**:
  - Walked the AST to find `FunctionDef`, `Call`, and nesting context.
  - Extracted function metadata and intra-language calls.
  - Structured the output in the common JSON format.

### 3. Generating JSON for Java (Intra-language Calls)
- **Tool Used**: `javalang` library
- **Process**:
  - Parsed Java files to extract class methods and call expressions.
  - Retrieved function nesting, class context, and parameters.
  - Serialized into the unified JSON format.

### 4. Generating JSON for Inter-language Calls

- **C++**
- **Goal**: Detect and record function calls made across C++ files of Python and Java functions.
- **Approach**:
  - Scanned known interop APIs.
  - Inferred links between caller and callee across language boundaries.

### 5. Frontend using D3.js

- Rendered nodes (functions) and edges (calls) with interactivity.
- Displayed metadata and DeepSeek summaries on node click.

### 6. Graph Generation from JSON

- Parsed and visualized the `uniqueFunctions[]` and `functionCalls[]` JSON.
- Used different colors, sizes, and shapes to indicate function type or origin.

### 7. Dockerized Environment

- Created Docker setup to encapsulate backend, frontend, and DeepSeek.
- Used `docker-compose` for seamless orchestration.

### 8. Integration of All Modules

- Unified JSON outputs from all parsers.
- Integrated data flow from backend to frontend.

### 13. Description, Code Smell and improvements Generation using LLM

- Generated concise summaries for each function using LLM.
- Identified code smells and suggested improvements.
- Shown as tooltips or detail cards in the UI.

### Format of JSON Output

1. **uniqueFunctions[]**
    Each function contains:

    ```json
    {
    "id": 1,
    "name": "functionName",
    "file": "filename.ext",
    "path": "/path/to/file",
    "language": "Python/C++/Java",
    "parameters": {
        "count": 2,
        "types": ["int", "str"]
    },
    "parentClass": "ClassName",
    "parentFunction": null
    }
    ```

2. **functionCalls[]**
Each function call captures:

    ```json
    {
    "callerId": 1,
    "calleeId": 2,
    "isInsideIfElseOrSwitch": true,
    "isInsideLoopOrEnvironment": false,
    "isDifferentLanguage": true,
    "isDifferentModule": false,
    "isInsideClass": true,
    "isInsideFunction": false
    }
    ```

## Technologies & Tools Used

| Purpose | Tool/Library |
|--------|--------------|
| Python Parsing | `Python ast` |
| C++ Parsing | `clang` |
| Java Parsing | `Javalang` |
| Function summary | `DeepSeek` |
| Visualization | D3.js (JavaScript) |
| Data Format | JSON |
| Deployment | Docker |

## Individual Contributions

1) **Ashish Raj**(CS22B055): Java JSON generation, Inter-language call detection for C++, Integrated and managed all json generation and management.

2) **Anuj Sharma**(CS22B007): Frontend development using D3.js, Visualization of function calls and metadata, Filter specific language and specific nodes(functions).

3) **Veerain**(CS22B049): C++ generator python implementation and generation, Code smell detection and improvement suggestions using LLM, Integration of all modules.

4) **Lavkush**(CS22B034): Resolved bugs in the Python parser,  Graph generation from JSON, Enhanced UI elements including the navigation bar.

5) **Kowshik**(CS22B015): Implemented Python function extraction,Developed  Function call detection in Python,Conducted Code Testing and bug fixes.

6) **Preet Bobde**(CS22B043): C++ JSON 2 generation, Set up Docker for environment, detection of inter-language function calls between JavaScript and Python.

## Release-2 Plan (Future Work)

- Improve accuracy of function call detection in current languages.
- Add inter-language call detection for Python and Java.
- Functionality Grouping & Layered Views
  - Keeping similar color for functions in the same module.
  - Use identical node shapes for functions written in the same programming language.
- Hotspot Analysis
  - Identify hotspots in the codebase where most function calls are concentrated.
  - Provide suggestions for optimization or refactoring.
- Refactoring Suggestions
  - Use AI to suggest 
    - Merging similar functions.
    - Remove unused functions.
- Metrics and Reporting
  - Show metrics like 
    - Number of functions per module.
    - Number of cross-language calls.
    - Function call depth.

## Conclusion

- This tool helps developers gain a clear understanding of the **functional flow** in multi-language projects.
- It goes beyond existing tools by providing **cross-language**, **control-aware**, and **visually intuitive** analysis.
- Integration of local DeepSeek for function summarization adds extra layer of insight.
