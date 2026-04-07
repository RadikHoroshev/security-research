# SafeTensors Security Vulnerability Analysis

**Date:** April 7, 2026
**Target:** SafeTensors format parser (Rust reference implementation, Python bindings, and third-party implementations)
**Bounty:** $4,000 on huntr.com

---

## Executive Summary

SafeTensors is a binary format for ML model weights designed as a safe alternative to pickle. The Rust reference implementation is remarkably well-engineered with strong validation. However, **third-party implementations** (C++, Go, fastsafetensors) and **consumer-side code** (Ollama, transformers, diffusers) contain exploitable vulnerabilities. The core Rust parser has already been audited by Trail of Bits (2023) and most obvious issues have been reported on huntr in late 2025/early 2026. The best remaining opportunities are in **third-party parsers** and **unreported consumer-side issues**.

---

## Previously Reported / Already Fixed Vulnerabilities (for reference)

### 1. Ollama: Safetensors Parser Unbounded Memory Allocation (CVE-2025-0315)
- **huntr:** `2edda9ac-69e3-47d8-a18a-b7b9d8458918` (reported Feb 2026, marked **duplicate**)
- **Root cause:** Ollama's SafeTensors parser allocated memory based on untrusted tensor metadata without bounds checking, causing OOM/DoS.
- **Status:** Patch miss from original CVE-2025-0315 fix. Multiple duplicate reports submitted.

### 2. Ollama: Missing Bounds Check on SafeTensors data_offsets
- **huntr:** `44cca936-cf10-4382-b7cc-e68e7b1be737` (reported Feb 2026, marked **duplicate**)
- **Root cause:** Crafted SafeTensors file with missing/short data_offsets causes index out-of-bounds panic.
- **Status:** Duplicate of the same class of vulnerability.

### 3. Ollama: OOM DoS via Unbounded Safetensors Allocation in imagegen Module
- **huntr:** `3bdc32cf-3403-4b3d-afb4-583befc1ed0e` (reported Mar 2026)
- **Root cause:** Same class of unbounded memory allocation in Ollama's imagegen SafeTensors parser.
- **Status:** Closed.

### 4. Ollama: Out-of-Range Slice Allocation Panic
- **huntr:** `003a5e49-5752-410c-85be-8683944267e7`
- **Root cause:** High-severity panic due to out-of-range slice allocation in Ollama's SafeTensors processing.
- **Status:** Closed.

### 5. Improper Safetensors Header-Length Validation (DoS)
- **huntr:** `d78afb51-3d3a-4a09-8ae6-66ff2f922f79` (reported Feb 2026)
- **Root cause:** Improper header-length validation allows remote DoS.
- **Status:** Closed.

### 6. Reversed data_offsets Integrity Bypass
- **huntr PoC:** `somebeast/huntr-poc-safetensors-04` on HuggingFace
- **Root cause:** Reversed data_offsets values accepted and propagated into malformed repacked output.
- **Status:** Reported.

---

## Trail of Bits Security Review Findings (March 2023)

The Trail of Bits audit of SafeTensors identified several issues, most of which have since been fixed in the Rust reference implementation:

- **TOB-SFTN-1:** Integer overflow in shape/dtype calculations -- **FIXED** (now uses `checked_mul`)
- **TOB-SFTN-2:** Metadata completeness validation -- **FIXED** (now validates `buffer_end + N_LEN + n == buffer_len`)
- **TOB-SFTN-3:** Non-consecutive tensor layout enforcement -- **FIXED** (validate checks contiguous offsets)
- The review noted that tensor **values** (NaN, +/-Inf) are not validated -- this is by design.

---

## Vulnerability Candidates for New Reporting

### VULN-1: Integer Overflow in safetensors-cpp `get_shape_size()` -- HIGH PRIORITY

**CVSS Estimate:** 7.5 (High) -- AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H

**Affected Component:** `syoyo/safetensors-cpp` -- `get_shape_size()` function
**File:** `safetensors.hh` (header-only C++ implementation)

**Root Cause:**
The `get_shape_size()` function multiplies tensor shape dimensions **without overflow checking**. A maliciously crafted shape (e.g., `[4194305, 4194305, 211106198978564]`) causes a `uint64` multiplication to wrap around to a small value (e.g., `4`). The parser allocates a tiny buffer (16 bytes) based on this wrapped value, but subsequent data consumers attempt to write millions of elements, triggering a **heap-buffer-overflow**.

**Contrast with Rust reference:**
The official Rust implementation uses `checked_mul` throughout `Metadata::validate()`:
```rust
let nelements: usize = info.shape.iter().copied()
    .try_fold(1usize, usize::checked_mul)
    .ok_or(SafeTensorError::ValidationOverflow)?;
```

**Attack Scenario:**
1. Attacker uploads a crafted `.safetensors` file to a model repository (HuggingFace, etc.)
2. Victim application uses safetensors-cpp to load the model
3. `get_shape_size()` overflows, returns a tiny value
4. Downstream code allocates a small buffer based on this value
5. Actual tensor data writes far exceed the buffer, causing heap-buffer-overflow
6. Potential for remote code execution via heap corruption (AddressSanitizer confirms the overflow)

**PoC Concept:**
```python
# Craft a SafeTensors file with overflow-causing shape
import json, struct

tensor_name = "overflow_tensor"
# Shape that will overflow uint64 when multiplied: 4194305 * 4194305 * 211106198978564
shape = [4194305, 4194305, 211106198978564]

header = json.dumps({
    tensor_name: {
        "dtype": "F32",
        "shape": shape,
        "data_offsets": [0, 16]  # Tiny offset range matching the overflowed value
    }
}).encode("utf-8")

# Pad to 8-byte alignment
padding = b" " * ((8 - len(header) % 8) % 8)
header_aligned = header + padding

file_content = struct.pack("<Q", len(header_aligned)) + header_aligned + b"\x00" * 16
```

**Novelty:** PoC exists on HuggingFace (`rez0/safetensors-cpp-integer-overflow-poc`) but **no CVE has been assigned** and **no huntr report found** for this specific third-party implementation. This is a strong candidate for reporting.

**Bounty Qualification Likelihood:** HIGH. This is a third-party implementation of the SafeTensors format with a demonstrable heap-buffer-overflow. While not the official Rust parser, safetensors-cpp is used by projects that depend on it.

---

### VULN-2: Go Implementation Missing `checkedMul` in `validate()` -- MEDIUM PRIORITY

**CVSS Estimate:** 5.3 (Medium) -- AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L

**Affected Component:** `nlpodyssey/safetensors` (Go implementation)
**File:** `metadata.go` -- `validate()` method

**Analysis:**
The Go implementation DOES include `checkedMul` in its `validate()` method, which was verified by examining the source. This means the Go implementation is protected against the integer overflow vulnerability that affects the C++ version.

**However**, a subtle difference exists: the Go implementation uses `uint64` for all offsets and sizes, while the Rust implementation uses `usize` for `TensorInfo.data_offsets`. On 32-bit platforms, `usize` is 32 bits, but the JSON header encodes offsets as arbitrary JSON numbers. The `serde` deserializer will parse them as `usize`, which on 32-bit platforms silently truncates values larger than 2^32.

**Attack Scenario (32-bit platforms only):**
1. Attacker crafts a SafeTensors file with `data_offsets` > 2^32
2. On 32-bit Rust platforms, `usize` truncation causes incorrect offset calculation
3. `Metadata::validate()` checks against the truncated values and may pass
4. Actual data access reads from wrong memory region

**Caveat:** The header size is capped at 100MB (`MAX_HEADER_SIZE`), which limits practical exploitation. However, the data region itself is NOT capped, and large models can legitimately exceed 4GB.

**Novelty:** UNREPORTED. The 32-bit truncation vector has not been publicly discussed.

**Bounty Qualification Likelihood:** MEDIUM. The 100MB header cap limits practical impact, and 32-bit platforms are increasingly rare for ML workloads. However, this is a genuine correctness bug that could lead to out-of-bounds reads in edge cases.

---

### VULN-3: JSON Key Collision via `__metadata__` Tensor Name -- LOW-MEDIUM PRIORITY

**CVSS Estimate:** 4.3 (Medium) -- AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N

**Affected Component:** Rust reference implementation -- `HashMetadata` deserialization
**File:** `tensor.rs` -- `HashMetadata` struct with `#[serde(flatten)]`

**Root Cause:**
The `HashMetadata` struct uses `#[serde(flatten)]` to merge tensor entries with the `__metadata__` field:
```rust
struct HashMetadata {
    #[serde(rename = "__metadata__")]
    metadata: Option<HashMap<String, String>>,
    #[serde(flatten)]
    tensors: HashMap<String, TensorInfo>,
}
```

If an attacker creates a tensor named `"__metadata__"`, the `#[serde(flatten)]` behavior with duplicate keys becomes ambiguous. While serde_json by default rejects duplicate keys for derived `Deserialize` implementations, the interaction between `#[serde(flatten)]` and explicit fields has known edge cases (see serde issue #2416).

**Attack Scenario:**
1. Attacker creates a SafeTensors file with a tensor named `"__metadata__"`
2. Deserialization behavior is undefined/implementation-dependent
3. Could result in metadata being overwritten or ignored
4. Downstream tools that read `__metadata__` for model provenance could be fooled

**Impact:** Low. At worst, metadata confusion. The tensor data itself is still validated. No code execution or memory corruption.

**Novelty:** UNREPORTED. This edge case has not been publicly discussed.

**Bounty Qualification Likelihood:** LOW-MEDIUM. The practical impact is limited to metadata confusion, and serde_json's default behavior likely rejects this. Worth investigating further with actual testing.

---

### VULN-4: Empty Tensor Name / Null Byte Injection -- MEDIUM PRIORITY

**CVSS Estimate:** 5.3 (Medium) -- AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N

**Affected Component:** All SafeTensors implementations -- no validation on tensor names
**File:** All implementations (Rust `tensor.rs`, Python bindings, Go, C++)

**Root Cause:**
The SafeTensors format specification does not explicitly restrict what characters can appear in tensor names. They are used as JSON object keys, so any valid JSON string is accepted. This includes:
- Empty string `""`
- Null bytes `\x00`
- Control characters
- Unicode homoglyphs
- Path-like strings (`"../../../etc/passwd"`)

**Attack Scenarios:**

**A. Empty tensor name:**
```json
{"": {"dtype": "F32", "shape": [2], "data_offsets": [0, 8]}}
```
This could cause issues in downstream code that assumes non-empty names (e.g., `transformers` logging, model diff tools).

**B. Null byte injection:**
```json
{"model.layers.0.\x00self_attn": {"dtype": "F32", "shape": [2], "data_offsets": [0, 8]}}
```
Null bytes in names could cause issues in C-string handling code or logging frameworks.

**C. Path traversal in tensor name (cosmetic):**
```json
{"../../../tmp/evil": {"dtype": "F32", "shape": [2], "data_offsets": [0, 8]}}
```
While the tensor name does NOT cause actual file system access (it's just a key in a HashMap), it could trick logging, visualization, or audit tools.

**Impact:** Low-to-medium. These are primarily integrity/correctness issues rather than exploitable vulnerabilities. However, specific downstream consumers could have bugs triggered by these edge cases.

**Novelty:** UNREPORTED. Tensor name validation has not been scrutinized.

**Bounty Qualification Likelihood:** LOW. These are format design choices rather than bugs. The format spec says "Duplicate keys are disallowed" but does not restrict character content. A strong case would need to demonstrate actual harm in a specific downstream consumer.

---

### VULN-5: Consumer-Side: `torch.frombuffer()` with Attacker-Controlled Data -- MEDIUM PRIORITY

**CVSS Estimate:** 6.5 (Medium) -- AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:H

**Affected Component:** `safetensors/torch.py` -- `_view2torch()` function
**File:** `bindings/python/py_src/safetensors/torch.py`, line ~100

**Root Cause:**
```python
def _view2torch(safeview) -> Dict[str, torch.Tensor]:
    result = {}
    for k, v in safeview:
        dtype = _getdtype(v["dtype"])
        arr = torch.frombuffer(v["data"], dtype=dtype).reshape(v["shape"])
```

`torch.frombuffer()` creates a tensor from raw bytes. If the dtype or shape from the SafeTensors header is crafted to create an extreme tensor, `torch.frombuffer().reshape()` could:
1. Attempt to allocate massive memory (DoS via OOM)
2. On some PyTorch versions, `frombuffer` has had its own vulnerabilities

**However**, the Rust parser validates that `e - s == size` (where size is computed from shape and dtype), so the byte buffer length always matches the claimed tensor size. This means `torch.frombuffer` receives correctly-sized data.

**The real risk is in the `reshape()` call:** If a tensor has shape `[9223372036854775807]` (near-max int64), the reshape itself could cause issues even if the underlying data is small, depending on PyTorch's implementation.

**Attack Scenario:**
1. Attacker crafts SafeTensors file with a tensor having extreme shape values but small data
2. Rust validation catches this via `e - s != size` check -- **THIS IS ALREADY PROTECTED**

**Conclusion:** The Rust validation prevents this attack on the core parser. However, if a consumer skips validation and directly uses `deserialize()` output, this could be an issue.

**Bounty Qualification Likelihood:** LOW for the core library. The Rust validation already prevents this.

---

### VULN-6: safetensors-cpp Missing `validate_data_offsets()` Implementation -- HIGH PRIORITY

**CVLS Estimate:** 7.5 (High) -- AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H

**Affected Component:** `syoyo/safetensors-cpp`
**File:** `safetensors.hh`

**Root Cause:**
The `validate_data_offsets()` function is **declared** but its implementation was not found in the source (it may be incomplete or missing). This means the C++ implementation may not validate that tensor byte ranges fall within the loaded memory buffer.

Compare with the Rust implementation which strictly validates:
```rust
if buffer_end + N_LEN + n != buffer_len {
    return Err(SafeTensorError::MetadataIncompleteBuffer);
}
```

And in `validate()`:
```rust
if e - s != size {
    return Err(SafeTensorError::TensorInvalidInfo);
}
```

If safetensors-cpp does not perform equivalent validation, a crafted file could cause:
- Out-of-bounds memory reads when accessing tensor data
- Potential information disclosure or crash

**Attack Scenario:**
1. Attacker creates SafeTensors file with `data_offsets` pointing beyond the actual data region
2. safetensors-cpp loads the file without validating offsets against file size
3. Tensor access reads arbitrary memory beyond the mapped file
4. Information disclosure or crash

**Novelty:** UNREPORTED as a CVE. Related to the already-reported Ollama issues but in the underlying C++ library itself.

**Bounty Qualification Likelihood:** HIGH. This is a missing security check in a widely-used third-party implementation. If `validate_data_offsets()` is indeed missing or incomplete, this is a clear vulnerability.

---

### VULN-7: serde_json Deeply Nested JSON in Header (DoS) -- LOW PRIORITY

**CVSS Estimate:** 3.7 (Low) -- AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:L

**Affected Component:** Rust reference implementation -- JSON deserialization
**File:** `tensor.rs` -- `serde_json::from_str(string)`

**Root Cause:**
The SafeTensors header is parsed via `serde_json::from_str()`. While serde_json has a built-in recursion depth limit (default 128), the SafeTensors code does not explicitly configure or tighten this limit.

However, the `HashMetadata` struct is flat (no nested structures except `__metadata__` which is `HashMap<String, String>`), so deeply nested JSON would simply fail to deserialize into the expected structure. The recursion limit in serde_json protects against stack overflow.

**The real concern:** The 100MB header limit means an attacker could send a 100MB header with millions of fake tensor entries, causing:
- High CPU usage during JSON parsing
- Memory allocation for the `HashMap<String, TensorInfo>`
- Potential slowdown of the deserialization path

**Mitigation already in place:**
- `MAX_HEADER_SIZE = 100_000_000` (100MB)
- `serde_json` recursion limit (default 128)
- The `MetadataIncompleteBuffer` check prevents processing incomplete files

**Bounty Qualification Likelihood:** LOW. The existing protections are adequate. 100MB of JSON parsing is expensive but not catastrophic.

---

## Novel Attack Surfaces Not Yet Reported

### Surface A: `fastsafetensors` Parallel Loading Race Conditions

The `fastsafetensors` library (arxiv:2505.23070) accelerates loading via parallel I/O and async mmap. Parallel tensor loading introduces potential race conditions:
- Concurrent mmap access to the same file region
- Partial reads during parallel deserialization
- GPU offloading race conditions

**Assessment:** Speculative. Requires access to fastsafetensors source code for detailed analysis.

### Surface B: Weight Manipulation (Backdoor Injection)

As documented in the "Banana Backdoor" research, SafeTensors prevents code execution but NOT weight manipulation. An attacker can:
1. Modify embedding weights to create trigger-based backdoors
2. Alter specific model weights to create targeted misbehavior
3. Poison models while maintaining format validity

**Assessment:** This is a supply-chain integrity issue, not a parser vulnerability. It's outside the scope of the SafeTensors format itself. However, a huntr report for a **model integrity verification mechanism** could be novel.

### Surface C: Conversion Script Pickle Deserialization

`bindings/python/convert.py` explicitly calls `torch.load()` on untrusted pickle files:
```python
loaded = torch.load(pt_filename, map_location="cpu")
```

The script warns the user but still performs the unsafe operation. If the conversion service (HuggingFace's automated bot) processes attacker-submitted models, this is a supply-chain attack vector.

**Assessment:** Already known and warned about. The HuggingFace conversion service was already scrutinized for this. Not novel.

---

## Summary and Recommendations

### Best Candidates for huntr Reporting (in priority order):

| # | Vulnerability | Target | Novelty | Bounty Likelihood |
|---|--------------|--------|---------|-------------------|
| 1 | Integer overflow in `get_shape_size()` | safetensors-cpp | HIGH | HIGH |
| 2 | Missing `validate_data_offsets()` | safetensors-cpp | HIGH | HIGH |
| 3 | 32-bit `usize` truncation of offsets | Rust core | MEDIUM | MEDIUM |
| 4 | Tensor name validation gaps | All implementations | MEDIUM | LOW-MEDIUM |
| 5 | `__metadata__` key collision | Rust serde | MEDIUM | LOW |

### What's Already Exhausted:
- All Ollama-specific SafeTensors vulnerabilities have been reported (multiple duplicates)
- The Trail of Bits findings have all been fixed in the Rust reference
- The core Rust parser's validation is thorough (checked arithmetic, bounds checks, header size limits)
- Header-length DoS has been reported

### Recommended Next Steps:
1. **Download safetensors-cpp** and verify whether `validate_data_offsets()` is implemented and whether `get_shape_size()` still lacks overflow checking
2. **Test the integer overflow PoC** against the latest safetensors-cpp to confirm exploitability
3. **File a huntr report** against safetensors-cpp (or whichever project uses it) for the integer overflow
4. **Investigate fastsafetensors** source code for race condition vulnerabilities
5. **Check if any downstream consumers** (not Ollama) of SafeTensors lack proper validation

---

## Key Source Files Referenced

| File | Repository | Purpose |
|------|-----------|---------|
| `safetensors/src/tensor.rs` | huggingface/safetensors | Core Rust parser: Metadata, validate(), deserialize |
| `safetensors/src/slice.rs` | huggingface/safetensors | Tensor slicing logic |
| `bindings/python/src/lib.rs` | huggingface/safetensors | Python bindings: safe_open, get_tensor |
| `bindings/python/py_src/safetensors/torch.py` | huggingface/safetensors | PyTorch integration: load_file, _view2torch |
| `bindings/python/convert.py` | huggingface/safetensors | Pickle-to-SafeTensors conversion |
| `safetensors.hh` | syoyo/safetensors-cpp | C++ header-only implementation |
| `safetensors.go` | nlpodyssey/safetensors | Go implementation |
| `metadata.go` | nlpodyssey/safetensors | Go metadata validation with checkedMul |
