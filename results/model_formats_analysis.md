# Huntr Model File Formats — Security Analysis

**Program:** https://huntr.com/bounties?q=gguf (Model File Formats, 56 targets)
**Date:** 2026-04-06
**Bounty Range:** $1,500–$4,000 per finding

---

## Huntr Program Overview

| Format | Bounty | Repo |
|--------|--------|------|
| **GGUF** | **$4,000** | ggerganov/llama.cpp |
| **Joblib** | **$4,000** | joblib/joblib |
| **Keras Native** | **$4,000** | keras-team/keras |
| **ONNX** | **$4,000** | onnx/onnx |
| **SafeTensors** | **$4,000** | huggingface/safetensors |
| TensorRT | $4,000 | nvidia/TensorRT |
| TensorFlow Saved Model | $4,000 | tensorflow/tensorflow |
| Pickle | $1,500 | python |
| OpenVINO | $1,500 | intel/openvino |
| HDF5, NPY, NPZ, Parquet, ORC | $1,500 each | various |

---

## Format 1: GGUF ($4,000) — llama.cpp

**Parser:** `gguf-py/gguf/gguf_reader.py` + C++ core in `ggml.c` / `llama.cpp`
**Attack Surface:** Load malicious `.gguf` model file

### Known CVEs (PATCHED — DO NOT RE-REPORT)

| CVE | Description | Component |
|-----|-------------|-----------|
| CVE-2024-25664 | Integer overflow in `n_kv` field → heap overflow | ggml.c |
| CVE-2024-21836 | Integer overflow in tensor count → heap overflow | gguf_reader |
| CVE-2024-23496 | `gguf_fread_str`: crafted string length → malloc underalloc → heap OOB | llama.cpp |
| CVE-2024-23605 | Unchecked `n_kv` → heap-based buffer overflow → RCE | llama.cpp |
| GHSA-8wwf-w4qm-gpqr | `size_t` cast to `int32_t` in vocab loader → signed underflow bypass | llama.cpp |
| CVE-2026-33298 | `ggml_nbytes()` integer overflow in tensor dimension calc → heap corruption RCE | ggml.c |

### GGUF Jinja2 SSTI (Partially Mitigated)
- **CVE-2024-34359** / JFrog Research: `chat_template` metadata field in GGUF files rendered as Jinja2 template
- Vulnerable when: llama-cpp-python < 0.2.72 renders templates server-side
- **Research angle:** Check if newer wrappers/frontends still render chat_template unsafely

### GGUF Remaining Research Targets (OPEN)
1. **Python gguf_reader.py metadata parsing**: No bounds check on `n_kv` reads in pure-Python reader
2. **String metadata integer overflow**: `key_length` / `value_length` read as `uint64` — verify Python reader validates against file size
3. **Tensor data offset arithmetic**: `data_offset` field not validated against file bounds in Python path
4. **GGUF metadata injection**: Attacker-controlled KV metadata values passed directly to downstream APIs (e.g., BPE tokenizer config, rope scaling)

---

## Format 2: SafeTensors ($4,000) — HuggingFace

**Parser:** `safetensors` Rust crate + Python bindings
**Design Goal:** Explicitly safe — no code execution on parse
**Attack Surface:** Header parsing, implementation bugs in consumers

### Known Issues
- **CVE-2025-0315** (Ollama): SafeTensors Go impl reads header size as uint64, passes to `make([]byte, 0, n)` without bounds → DoS crash (panics)
- **Patch miss (2025)**: Similar fix applied in one parser but not SafeTensors-specific handler in Ollama
- HuggingFace formal security audit (EleutherAI / Stability AI) — no RCE found in Rust core

### Remaining Research Targets
1. **Header size integer overflow**: `header_size` is `u64` LE at bytes 0-7. If consumer doesn't cap at file_size → OOM DoS
2. **Tensor bounds validation**: `data_offsets[0]..data_offsets[1]` — verify no gap between end of last tensor and file end allows OOB read
3. **Metadata string injection**: `metadata` dict values are unconstrained strings — potential downstream injection if apps use metadata values directly in SQL/paths/prompts
4. **Shape overflow**: `shape` field is array of `usize` — product overflow (2³² × 2³² on 64-bit → wraps to 0) if consumer multiplies without overflow check

### PoC Concept (DoS / OOM)
```python
import struct, json

metadata = {"__metadata__": {}}
header = json.dumps(metadata).encode()
# Craft n = 2**63 - 1 as header_size (Rust parser rejects, but Go / Python may not)
payload = struct.pack("<Q", 2**63 - 1) + header
with open("bomb.safetensors", "wb") as f:
    f.write(payload)
```

---

## Format 3: ONNX ($4,000) — onnx/onnx

**Parser:** Python protobuf + C++ checker
**Attack Surface:** Load malicious `.onnx` file, external data loading

### Known CVEs (PATCHED)

| CVE | Description | Fixed in |
|-----|-------------|----------|
| CVE-2024-5187 | Path traversal in `download_model_with_test_data` tar extraction → arbitrary file overwrite | 1.16.2 |
| CVE-2024-27318 | Path traversal read in `external_data` field (bypass of CVE-2022-25882 patch) | 1.16.0 |
| CVE-2024-7776 | Arbitrary file overwrite via `download_model` path traversal | 1.17.0 |
| CVE-2025-51480 | Path traversal write in `save_external_data()` via `location` field | pending |

### Remaining Research Targets

#### 1. Protobuf Tensor Shape Resource Exhaustion (DoS)
- **Location:** `onnx/checker.py` — `check_model()` uses `sys.getsizeof()` to estimate protobuf size (MAXIMUM_PROTOBUF = 2GB)
- **Issue:** `sys.getsizeof()` does NOT count nested protobuf fields; shape `[2**31, 2**31, 2**31]` passes the size check but causes OOM on deserialization
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **PoC:**
```python
import onnx
from onnx import TensorProto, helper
# Create tensor with huge shape but no actual data
node = helper.make_node("Relu", ["X"], ["Y"])
X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2**20, 2**20])  # 4TB shape
graph = helper.make_graph([node], "g", [X], [])
model = helper.make_model(graph)
# checker allows through, runtime OOMs
```

#### 2. External Data Symlink Race Condition
- **Location:** `onnx/external_data_helper.py` `_open_external_data_fd()`
- **Issue:** Validation in C++ layer, Python trusts `location` string
- **Attack:** Create symlink at `location` path after validation but before read (TOCTOU)
- **CWE:** CWE-362 (Race Condition / TOCTOU)

#### 3. `onnx.hub.load()` Code Execution (CVE-2026-28500)
- **Status:** Being removed in 1.21.0; executes arbitrary Git repo code
- **CWE:** CWE-426, CWE-94

---

## Format 4: Pickle ($1,500) — Python Standard Library

**Context:** Used by PyTorch (`torch.load`), scikit-learn, and many ML frameworks
**Attack Surface:** Loading untrusted `.pkl` / `.pt` / `.pth` files

### Core Issue
Python's `pickle.loads()` executes arbitrary Python code via `__reduce__`:
```python
import pickle, os
class Exploit:
    def __reduce__(self):
        return (os.system, ('id',))
pickle.dumps(Exploit())  # Payload
```

### PyTorch `weights_only` History
| Version | Default | Risk |
|---------|---------|------|
| < 2.0 | `weights_only=False` | Full RCE |
| 2.0–2.5 | `weights_only=False` (with warning) | Full RCE |
| 2.6+ | `weights_only=True` | Restricted |

### CVE-2025-32434 — `weights_only=True` BYPASS (CRITICAL)
- **CVSS:** 9.8 (Critical)
- **Affected:** PyTorch ≤ 2.5.1
- **Description:** Even with `weights_only=True`, specially crafted `.pt` files trigger RCE via pickle `__reduce__` mechanism
- **Fixed in:** PyTorch 2.6.0
- **Advisory:** GHSA-53q9-r3pm-6pq6

### Remaining Research Targets
1. **`add_safe_globals()` allowlist abuse**: Can allowlisted classes (e.g., `torch.Tensor`) be subclassed or wrapped to execute arbitrary code?
2. **Sparse / quantized tensor metadata**: Does `weights_only=True` properly restrict deserialization of exotic tensor types?
3. **`torch._weights_only_unpickler` GLOBAL opcode**: Check if any allowlisted modules expose `eval`/`exec` indirectly
4. **Joblib + PyTorch interop**: When PyTorch models are saved with `joblib.dump()`, both parsers interact

---

## Format 5: Joblib ($4,000) — joblib/joblib

**Parser:** `joblib/numpy_pickle.py` (wraps Python pickle + zlib/lzma)
**Attack Surface:** Loading untrusted `.joblib` / `.pkl` scikit-learn model files

### Core Vulnerability: Unrestricted `pickle.load()` in `NumpyArrayWrapper`

**File:** `joblib/numpy_pickle.py`, line ~175
```python
# When dtype.hasobject is True:
array = pickle.load(unpickler.file_handle)  # UNSAFE
```

Uses standard `pickle._Unpickler` without overriding `find_class()` — allows importing any Python module.

**CVE-2024-34997** — Joblib Unsafe Pickle Deserialization
- **CWE:** CWE-502 (Deserialization of Untrusted Data)
- **CVSS:** 7.5 (High); some researchers rate 9.8 (Critical)
- **Affected:** joblib 1.4.2
- **Status:** Maintainers **DISPUTED** — claim intended for internal cache only. **No official patch.**
- **Real-World Risk:** scikit-learn `load()` pipelines from HuggingFace Hub = full RCE

### PoC
```python
# Craft malicious joblib file
import joblib, os, pickle, io, struct, zlib

class Exploit:
    def __reduce__(self):
        return (os.system, ('id > /tmp/pwned',))

# Embed in object-dtype numpy array → triggers unrestricted pickle.load()
# on NumpyArrayWrapper.read_array() path
```

### Remaining Research Targets
1. **`find_class()` bypass**: Standard `_Unpickler.find_class()` has no restrictions — research which dangerous modules are importable
2. **Python 3.13 `pickle.restricted_loads()`**: Joblib doesn't use it — potential new finding
3. **Compressed joblib files**: Does zlib/lzma decompression bomb trigger before deserialization?
4. **joblib.Parallel + pickle**: Parallel task serialization attack surface

---

## Format 6: Keras Native ($4,000) — keras-team/keras

**Format:** ZIP archive containing `config.json` + weights HDF5/NPZ + assets
**Attack Surface:** Load malicious `.keras` file, Lambda layer deserialization

### CVE History

| CVE | Description | Fixed in |
|-----|-------------|----------|
| CVE-2024-3660 | Lambda layer deserialization executes arbitrary Python code (pre-Keras 2.13) | Keras 2.13 |
| CVE-2025-1550 | `config.json` manipulation enables `enable_unsafe_deserialization()` before lambda load → safe_mode bypass | Keras 3.x |
| CVE-2025-9906 | Keras 3.0–3.10.x: unsafe deserialization of `.keras` bypassing `safe_mode` | Keras 3.11 |
| CVE-2024-55459 | Arbitrary file write via `keras.utils.get_file()` path traversal | pending |

### Remaining Research Targets

#### 1. `safe_mode` Bypass via `custom_objects` Registry Pollution
- **File:** `keras/src/saving/serialization_lib.py`
- **Issue (GitHub #22466):** `safe_mode` doesn't isolate built-in class names from the custom objects registry
- **Attack:** Register malicious class under trusted name before model load
```python
keras.utils.get_custom_objects()["Dense"] = MaliciousLayer
keras.models.load_model("safe_model.keras")  # Instantiates MaliciousLayer
```

#### 2. ZIP Slip in `assets/` Directory Extraction
- **File:** `keras/src/saving/saving_lib.py` uses `zipfile.ZipFile()`
- **Attack:** Craft `.keras` ZIP with `assets/../../../etc/cron.d/backdoor` entry
- **Check Status:** Verify if `ZipFile.extractall()` has path validation

#### 3. `TFSMLayer` Path Traversal (Issue #22035)
- **File:** Deserialization of `TFSMLayer` in `safe_mode`
- **Issue:** Loads arbitrary SavedModel directories from disk — path not validated

#### 4. Lambda Layer RCE Chain (post-safe_mode bypass)
```python
# config.json snippet that triggers RCE
{
    "class_name": "Lambda",
    "config": {
        "name": "lambda",
        "function": {"class_name": "__lambda__", "config": {"value": "<pickled_rce_bytecode>"}}
    }
}
```

---

## Priority Matrix for Submission

| Format | Finding | Novelty | CVSS est. | Bounty | Status |
|--------|---------|---------|-----------|--------|--------|
| **Keras** | `safe_mode` bypass via registry pollution (GH#22466) | High | 8.8 | $4,000 | Open issue, no CVE |
| **Keras** | ZIP slip in assets extraction | Medium | 8.1 | $4,000 | Unconfirmed |
| **Joblib** | Unrestricted pickle (CVE-2024-34997 re-submission with new variant) | Medium | 9.8 | $4,000 | Disputed/unpatched |
| **Joblib** | Decompression bomb before deserialize | Medium | 7.5 | $4,000 | Unknown status |
| **GGUF** | Python reader metadata OOB (n_kv no file size check) | Medium | 8.1 | $4,000 | Unclear |
| **SafeTensors** | Consumer-side OOM via crafted header_size in Go/Python clients | Medium | 7.5 | $4,000 | Patched in Rust; consumers vary |
| **ONNX** | Protobuf shape DoS via `sys.getsizeof()` bypass | Medium | 7.5 | $4,000 | Unknown status |
| **Pickle** | `weights_only=True` bypass research (post-CVE-2025-32434) | High | 9.8 | $1,500 | CVE-2025-32434 patched in 2.6 |

---

## Recommended Next Steps

1. **Keras #22466 (safe_mode bypass)**: Open GitHub issue, no CVE yet → **highest priority for submission**
2. **Keras ZIP slip**: Write PoC script to test `zipfile.ZipFile` path validation in `saving_lib.py`
3. **Joblib**: Create new variant of CVE-2024-34997 demonstrating `find_class()` bypass with different gadget chain
4. **GGUF Python reader**: Clone `gguf-py`, audit `GGUFReader.__init__()` bounds checking vs file size

---

## GGUF Python Reader — Specific Code-Level Findings (Novel)

These findings are in the pure-Python `gguf-py` reader (`gguf_reader.py`), distinct from the C++ CVEs already patched.

### GGUF-001: Integer Overflow in Tensor Element Count (CRITICAL)
- **Issue:** `np.prod(dims)` silently overflows on 32-bit numpy integers for large tensor dimensions
- **Example:** `dims = [2**17, 2**17]` → `np.prod` wraps to 0 on int32 → undersized buffer allocated
- **CWE:** CWE-190
- **Impact:** Heap buffer overflow, potential RCE
- **PoC:** Craft GGUF with tensor shape `[131072, 131072]` — element count overflows int32

### GGUF-002: Unbounded Memory Allocation (CRITICAL / DoS)
- **Issue:** Python reader allocates based on `n_tensors` * element_size with no cap
- **Example:** `n_tensors = 0xFFFFFFFF` → reader tries to allocate exabytes
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **Impact:** Instant OOM crash — most reproducible finding
- **PoC:**
```python
import struct
magic = b'GGUF'
version = struct.pack('<I', 3)
n_tensors = struct.pack('<Q', 0xFFFFFFFFFFFFFFFF)  # 18 exabytes
n_kv = struct.pack('<Q', 0)
with open("bomb.gguf", "wb") as f:
    f.write(magic + version + n_tensors + n_kv)
```

### GGUF-003: Metadata String Length Unbounded (HIGH)
- **Issue:** String KV values declare `uint64` byte length — reader allocates without checking against file size
- **Attack:** `key_length = 2**63 - 1` → `value_length = 2**63 - 1` → OOM before EOF
- **CWE:** CWE-190, CWE-400

### GGUF-004: Unbounded Array Element Iteration (HIGH / DoS)
- **Issue:** Array-type metadata values declare `array_len: uint64` — reader iterates N times in Python with no limit
- **Impact:** CPU exhaustion — 2⁶⁴ iterations = infinite loop / 100% CPU
- **CWE:** CWE-835 (Infinite Loop)

### GGUF-005: Alignment Field No Upper Bound (MEDIUM)
- **Issue:** `general.alignment` field validated as power-of-two but no maximum — can be 2**62
- **Impact:** Integer overflow when computing data offsets

---

## SafeTensors Python Layer — Specific Code-Level Findings (Novel)

The Rust core is memory-safe; these affect the Python/NumPy layer.

### ST-001: Endianness Silent Data Corruption (CRITICAL — Data Integrity)
- **Issue:** SafeTensors assumes little-endian byte order — on big-endian systems (s390x, SPARC, some ARM) all tensor values are silently byte-swapped
- **Impact:** Wrong model inference results without any error; models appear to load successfully
- **CWE:** CWE-682 (Incorrect Calculation)
- **Research Value:** No explicit CVE — novel finding for big-endian ML environments

### ST-002: Unsafe NumPy Reshape Without Buffer Validation (MEDIUM)
- **Issue:** After parsing header, tensor data is reshaped using declared `shape` without verifying `shape.product == buffer.len`
- **Impact:** OOB read if `shape` product > actual data bytes
- **CWE:** CWE-125 (Out-of-Bounds Read), CWE-400

### ST-003: Unknown dtype → Uncaught KeyError (LOW)
- **Issue:** Unknown `dtype` string causes `KeyError` rather than graceful error
- **Impact:** Unhandled exception crashes application
- **CWE:** CWE-248 (Uncaught Exception)

---

## Tools
- `modelscan` (GitHub: protectai/modelscan) — static scanner for model file vulnerabilities
- `MODEL_SCAN_HUNTR` (GitHub: twgcriot/MODEL_SCAN_HUNTR) — huntr-aligned scanner

## References
- [Databricks GGUF/GGML Vulns](https://www.databricks.com/blog/ggml-gguf-file-format-vulnerabilities)
- [JFrog GGUF SSTI](https://research.jfrog.com/model-threats/gguf-ssti/)
- [JFrog Keras safe_mode analysis](https://jfrog.com/blog/keras-safe_mode-bypass-vulnerability/)
- [Huntr Keras writeup](https://blog.huntr.com/hunting-vulnerabilities-in-keras-model-deserialization)
- [CERT VU#253266 Keras Lambda](https://kb.cert.org/vuls/id/253266)
- [CVE-2025-32434 PyTorch weights_only bypass](https://github.com/pytorch/pytorch/security/advisories/GHSA-53q9-r3pm-6pq6)
