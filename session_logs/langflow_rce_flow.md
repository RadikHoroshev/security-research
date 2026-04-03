# Langflow RCE Flow Analysis (CustomComponent)

## Chain of Execution
1.  **HTTP Entry Point**: `POST /api/v1/custom_component` (in `src/backend/base/langflow/api/v1/endpoints.py`).
    - Receives a JSON body with a `code` field containing Python source code.
2.  **Building Template**: Calls `build_custom_component_template(component, user_id=user.id)`.
3.  **Running Build Config**: Calls `run_build_config(custom_component, user_id=user_id)` (in `src/lfx/src/lfx/custom/utils.py`).
4.  **Evaluating Code**: Calls `eval_custom_component_code(custom_component._code)` (in `src/lfx/src/lfx/custom/eval.py`).
5.  **Dynamic Class Creation**: Calls `validate.create_class(code, class_name)` (in `src/lfx/src/lfx/custom/validate.py`).
6.  **Global Scope Preparation**: `prepare_global_scope(module)` (in `src/lfx/src/lfx/custom/validate.py`) iterates over AST nodes and uses `importlib.import_module()` to load any modules requested in the code (e.g., `import os`).
7.  **Execution (Sink)**: `exec(compiled_class, exec_globals, exec_locals)` (inside `build_class_constructor` in `validate.py`) executes the compiled class definition in the prepared global context.

## Vulnerability Assessment
- **Arbitrary Code Execution**: **YES**. The system is designed to execute user-provided Python code to define custom components.
- **Sandboxing**: **NONE**. The code is executed using standard `exec()` within the same process as the Langflow backend.
- **Module Restriction**: **NONE**. The `prepare_global_scope` function explicitly supports importing arbitrary modules via `importlib`.
- **Impact**: An attacker can send a request to `/api/v1/custom_component` with code that imports `os` or `subprocess` and executes arbitrary system commands (e.g., `os.system("id")`).

## Conclusion
The custom component mechanism in Langflow provides a direct path to Remote Code Execution (RCE) by design. While this is a "feature" for developers, it represents a critical security risk if the instance is exposed without strict authentication (which was often disabled by default in older versions or via `LANGFLOW_AUTO_LOGIN`).
