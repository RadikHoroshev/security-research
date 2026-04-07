Xinference RCE via eval() — Vulnerability Check
=================================================
Repository: xorbitsai/inference (latest main, cloned 2026-04-06)

Status: VULNERABLE — eval() is still present in both locations.

Finding 1: xinference/model/llm/tool_parsers/llama3_tool_parser.py, line 46
  Code:  data = eval(model_output, {}, {})
  Context: Llama3ToolParser.extract_tool_calls() passes raw model_output
           (a string from the LLM response) directly into eval().
           Even with empty global/local dicts, Python eval() can execute
           arbitrary code via builtins (__import__, exec, etc.).

Finding 2: xinference/model/llm/utils.py, line 699
  Code:  data = eval(text, {}, {})
  Context: _eval_llama3_chat_arguments() passes text from
           c["choices"][0]["text"] (LLM completion output) directly
           into eval(). Same risk as above.

Impact: An attacker who can influence the LLM output (e.g. via prompt
        injection in tool-call scenarios) can achieve remote code execution
        on the Xinference server.

Recommendation: Replace eval() with json.loads() or ast.literal_eval().
