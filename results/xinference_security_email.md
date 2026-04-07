Subject: [SECURITY] Critical RCE via eval() in Xinference — Issue #4612 closed without fix

Dear Xinference Security Team,

I am writing to responsibly disclose a critical Remote Code Execution (RCE) vulnerability 
that remains present in the latest version of Xinference, despite being reported earlier.

## Summary
Issue #4612 (reported 2026-02-18) was closed as stale on 2026-03-21, but the underlying 
eval() calls that enable RCE were never replaced with safe alternatives.

## Affected Files
1. xinference/model/llm/tool_parsers/llama3_tool_parser.py:46
   data = eval(model_output, {}, {})
2. xinference/model/llm/utils.py:699
   data = eval(text, {}, {})

## Severity
CRITICAL — CVSS 9.8
An attacker who can influence LLM output can achieve remote code execution on the server.

## Why eval(x, {}, {}) is NOT safe
Python's eval() with empty globals/locals still exposes __builtins__, allowing full code 
execution via: eval("().__class__.__bases__[0].__subclasses__()", {}, {})

This bypass is well-documented and was confirmed by the original reporter.

## Proof of Concept
The following demonstrates that __builtins__ is accessible:
    result = eval("().__class__.__bases__[0].__subclasses__().__len__", {}, {})
    # Works! Returns the number of accessible subclasses.

## Timeline
- 2026-02-18: Issue #4612 reported on GitHub
- 2026-02-24: Maintainer replied "It's enabled already" (no code change was made)
- 2026-03-21: Issue closed as stale (no patch applied)
- 2026-04-06: Re-confirmed — eval() still present in latest main branch
- 2026-04-06: GitHub Issue #4769 opened as public notification

## Recommended Fix
Replace eval() with ast.literal_eval():

    import ast
    # UNSAFE:
    data = eval(model_output, {}, {})
    
    # SAFE:
    data = ast.literal_eval(model_output)

## About This Disclosure
This vulnerability was discovered during security research of AI/ML inference platforms.
I have also opened a public GitHub Issue (#4769) to ensure visibility, but am contacting 
you directly to provide full technical details and a recommended fix.

I believe in responsible disclosure and hope this information helps improve the security 
of Xinference for all users.

Best regards,
Rodion Horoshev
Independent Security Researcher
