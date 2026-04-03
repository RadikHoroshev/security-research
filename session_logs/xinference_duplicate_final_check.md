# Xinference Security Duplicate Check: RCE in Tool Parsing

## Definitive Answer
**YES**, a critical Remote Code Execution (RCE) vulnerability related to `eval()` and `llama3_tool_parser.py` has been explicitly identified and reported.

## Key Findings
- **Vulnerability**: Remote Code Execution (RCE) via Python Code Injection.
- **Root Cause**: Unsafe use of `eval(model_output, {}, {})` on model-generated strings in several tool parsers.
- **Primary Reference**: [GitHub Issue #4612](https://github.com/xorbitsai/inference/issues/4612) - "Security: eval() on model output in tool parsers creates RCE risk".
- **Date Reported**: February 18, 2026.
- **Reporter**: nasircsms.

## Affected Components
1.  **`xinference/model/llm/tool_parsers/llama3_tool_parser.py`**: Uses `eval()` to parse model output for Llama 3 tool calls.
2.  **`xinference/model/llm/utils.py`**: Function `_eval_llama3_chat_arguments()` uses `eval()`.
3.  **`xinference/thirdparty/deepseek_vl2/serve/app_modules/utils.py`**: Uses `eval()` on extracted content.
4.  **`xinference/model/image/ocr/deepseek_ocr.py`**: Uses `eval()` on coordinate strings.

## Mitigation Status
- **Initial Flaw**: The developers used `eval(text, {}, {})`, believing it was a secure sandbox.
- **Bypass**: Security researchers confirmed this is bypassable via Python class hierarchy traversal (e.g., `().__class__.__bases__[0].__subclasses__()`) to reach the `os` module.
- **Remediation**: Recommended switch to `json.loads()` or `ast.literal_eval()`.

## Other Related CVEs
- **CVE-2025-3622**: Deserialization vulnerability in `xinference/thirdparty/cosyvoice/cli/model.py`.
- **CVE-2025-45424**: Unauthenticated access to Web GUI (Fixed in v1.4.0).

## Conclusion
Submitting a report for RCE via `eval()` in `llama3_tool_parser.py` or similar components would be a **duplicate** of Issue #4612. Any new report should focus on completely different components or demonstrate a bypass for the `ast.literal_eval()` fixes if they have been implemented.
