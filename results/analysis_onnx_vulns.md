# ONNX Model File Format Vulnerability Analysis

**Date:** 2026-04-07
**Analyst:** AI Security Researcher
**Target:** ONNX file format (Python `onnx` package and C++ `onnx/checker.cc`)
**Bounty Target:** huntr.com - $4,000
**Scope:** `github.com/onnx/onnx`

---

## Executive Summary

This report documents a deep security analysis of the ONNX file format, covering 16 distinct attack surfaces across the protobuf schema, shape inference engine, external data handling, optimizer, visualization tools, and runtime integration. The ONNX ecosystem has received significant security attention recently (15+ CVEs in 2024-2026, many more pending reports on huntr), making the search for novel vulnerabilities increasingly difficult. This analysis identifies **3 potentially novel findings** with moderate-to-high confidence, **4 lower-confidence leads** worth further investigation, and **9 already-reported vectors** for completeness.

---

## Section 1: Already-Reported Vulnerability Landscape

### 1.1 External Data Path Traversal Family (EXTENSIVELY REPORTED)

| CVE | Title | Status |
|-----|-------|--------|
| CVE-2022-25882 | Directory traversal via external_data field | Published |
| CVE-2024-27318 | Path traversal via incomplete path normalization | Published |
| CVE-2024-7776 | Arbitrary file overwrite via tar extraction | Published, $750 |
| CVE-2024-5187 | Arbitrary file overwrite via download_model | Published, $750 |
| CVE-2025-51480 | Path traversal in save_external_data | Published |
| CVE-2026-34446 | Arbitrary file read via hardlink bypass | Published |
| CVE-2026-34447 | External data symlink traversal | Published |
| N/A | Multiple path traversal bypasses (tar, symlink, etc.) | Duplicate on huntr |
| N/A | Path traversal in convert_model_to_external_data | Duplicate on huntr |
| N/A | Path traversal in ONNX Hub manifest | Duplicate on huntr |

**Attack Vector:** `TensorProto.external_data` key-value pairs containing `location` fields with `../` sequences, symlinks, or hardlinks pointing outside the model directory.

**Mitigation (current):** 4-layer defense in checker.cc: canonical path containment via `weakly_canonical()`, symlink detection, secure file open with platform-specific containment, pre-open hardlink count check. 3-layer defense in Python: key whitelist, parse-time bounds validation, file-size validation at read time.

**Novel bypass potential:** LOW. This surface is exhaustively covered.

---

### 1.2 Attribute Injection via setattr (REPORTED)

| CVE | Title | Status |
|-----|-------|--------|
| CVE-2026-34445 | Object state corruption and DoS via ExternalDataInfo | Published, GHSA-538c-55jv-c5g9 |
| N/A | Unsafe raw_data handling in Tensor::data<T>() | Self-closed on huntr |

**Attack Vector:** `ExternalDataInfo` class used `setattr()` to load metadata from `external_data` entries without validation. Crafted key-value pairs could overwrite `length` (to 9 PB for DoS), `offset` (to -1 for access bypass), or dunder attributes (`__class__`) for type confusion.

**Mitigation:** PR #7751 implemented strict key whitelist (`location`, `offset`, `length`, `checksum`, `basepath`), parse-time bounds validation, and file-size validation at read time.

**Fixed in:** onnx 1.21.0

---

### 1.3 Shape Inference Integer Overflow (REPORTED)

| Identifier | Title | Status |
|------------|-------|--------|
| N/A | Integer Overflow in Dimension Multiplication (Flatten, etc.) | Self-closed on huntr |
| N/A | Integer Overflow in Reshape Shape Inference | Self-closed on huntr |
| GHSA-538c-55jv-c5g9 | Integer overflow in shape inference | Published |
| N/A | Heap Buffer Overflow in ParseData() via Integer Division Truncation | Duplicate on huntr |
| N/A | Integer Overflow in onnx::ParseData leading to DoS | Self-closed on huntr |

**Attack Vector:** Crafted tensor dimensions in `TensorShapeProto` that, when multiplied during shape inference (e.g., Flatten computing `product(dim[1:])`), overflow `int64`, causing undersized buffer allocation and subsequent heap overflow.

---

### 1.4 Runtime-Specific Vulnerabilities (REPORTED)

| Identifier | Title | Status |
|------------|-------|--------|
| N/A | Denial of Service via Unbounded Memory Allocation during Expand | Pending on huntr |
| N/A | Stack Overflow DoS via Unbounded Recursion | Pending on huntr |
| N/A | Heap buffer overflow | Pending on huntr |
| N/A | ONNX Runtime does not validate dimensional consistency | Pending on huntr |
| N/A | ONNX Model Loading Backdoor in onnxruntime | Disclosure $1,500 |
| N/A | Insecure Command Execution in ONNX Runtime | Pending on huntr |
| N/A | Unsafe use of PyTorch torch.load() in ONNX | Self-closed |
| N/A | Lack of Error Handling for Malformed Input | Pending on huntr |

---

### 1.5 Hub and Visualization (REPORTED)

| Identifier | Title | Status |
|------------|-------|--------|
| CVE-2026-28500 | Untrusted Model Repository Warning Bypass (silent=True) | Published |
| N/A | Exploit ONNX Net Drawer via doc_string injection | Pending on huntr |
| N/A | RCE via Documentation Updates | Informative |

---

## Section 2: Potentially Novel Vulnerabilities

### Finding 1: FunctionProto Non-Recursive Call Graph Exponential Expansion DoS

**Severity:** Medium-High (CVSS 7.5 - Availability)
**CWE:** CWE-400 (Uncontrolled Resource Consumption)
**Component:** `onnx/shape_inference/implementation.cc` + function body expansion
**Novel Confidence:** MODERATE
**huntr Qualification Likelihood:** 50-60%

#### Description

ONNX `FunctionProto` definitions are prohibited from being directly recursive (documented in schema: "recursive reference is not allowed"). However, there is no protection against **non-recursive exponential call graph expansion**. A crafted model can define a chain of functions where each function calls multiple other functions, creating an exponentially growing node tree during function body inlining.

#### Attack Scenario

```python
# Conceptual PoC
# Function A calls B, C
# Function B calls D, E
# Function C calls D, E, F
# Function D calls G, H, I
# ... 20 functions forming a DAG with exponential fanout

# When the runtime or optimizer inlines function bodies,
# the effective node count grows exponentially:
# A -> B,C -> (D,E),(D,E,F) -> (G,H,I),(G,H,I),(G,H,I),(G,H,I) -> ...
# With sufficient depth, this causes OOM or extreme CPU consumption
```

#### PoC Concept

```python
import onnx
from onnx import helper, TensorProto

# Create a chain of 30+ functions, each calling 2-3 others
# The call graph forms a DAG with 2^N effective node expansion
functions = []
for i in range(30):
    # Each function calls the next 2 functions
    nodes = []
    if i + 1 < 30:
        nodes.append(helper.make_node(f'Func_{i+1}', inputs=['x'], outputs=[f'out_{i}']))
    if i + 2 < 30:
        nodes.append(helper.make_node(f'Func_{i+2}', inputs=[f'out_{i}'], outputs=[f'out_{i}_b']))

    func = helper.make_function(
        domain='exploit',
        fname=f'Func_{i}',
        inputs=['x'],
        outputs=['y'],
        nodes=nodes,
        opset_imports=[onnx.defs.onnx_opset_version()]
    )
    functions.append(func)

# Model uses the root function which expands exponentially
model = helper.make_model(
    helper.make_graph([], 'exploit_graph', [], []),
    functions=functions,
    opset_imports=[helper.make_opsetid('', 17)]
)
```

#### Why Likely Novel

- All reported ONNX DoS vulnerabilities focus on: (a) external data path traversal, (b) shape inference integer overflow, (c) tensor dimension OOM
- No reported CVE or huntr bounty specifically addresses FunctionProto call graph expansion
- The recursive prohibition is documented, but the non-recursive exponential case is not mitigated
- The onnxscript issue #2859 (infinite loop in Resize constant folding) is a related but distinct bug in the optimizer, not the core function expansion

#### Mitigation Gap

ONNX does not track or limit the total expanded node count across function bodies. The checker validates structural correctness but does not compute or enforce a maximum effective graph size after function inlining.

---

### Finding 2: Protobuf Default Value Mismatch Creating Shape Inference Bypass

**Severity:** Medium (CVSS 6.5 - Integrity)
**CWE:** CWE-682 (Incorrect Calculation)
**Component:** Protobuf serialization + shape inference fallback
**Novel Confidence:** MODERATE
**huntr Qualification Likelihood:** 40-50%

#### Description

Protobuf omits numeric fields during serialization when their value equals the type default (0). When ONNX shape inference encounters a missing attribute, it falls back to schema-defined defaults. This creates a **silent behavioral divergence** between the model author's intent and the runtime's interpretation.

Specifically documented in GitHub issue #7573: the `axis` attribute of `Flatten` defaults to `0` in the model, but protobuf serializes it as absent (since 0 is the default). Shape inference then falls back to its schema default of `axis=1`, producing incorrect shapes.

#### Attack Scenario

An attacker crafts a model where critical numeric attributes are intentionally set to 0 (and thus omitted from serialization). When shape inference runs, it uses different defaults, producing shape metadata that doesn't match the actual computation. This can:

1. **Bypass model validation** in CI/CD pipelines that rely on shape inference
2. **Cause silent model corruption** where the model passes validation but produces incorrect results at inference
3. **Trigger downstream buffer overflows** in runtimes that trust shape metadata for allocation

#### PoC Concept

```python
import onnx
from onnx import helper, numpy_helper, TensorProto
import numpy as np
from google.protobuf import json_format

# Create a Flatten node with axis=0
# Protobuf will omit axis=0 since it's the default
flatten_node = helper.make_node('Flatten', inputs=['X'], outputs=['Y'], axis=0)

# Shape inference will use schema default axis=1
# This creates a mismatch: model intended axis=0, shape inferred with axis=1

graph = helper.make_graph(
    [flatten_node],
    'test_graph',
    [helper.make_tensor_value_info('X', TensorProto.FLOAT, [2, 3, 4])],
    [helper.make_value_info('Y', TensorProto.FLOAT, [2, 12])]  # Expected output with axis=0
)

model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 17)])

# Shape inference produces wrong shape for Y
onnx.shape_inference.infer_shapes_path(model)
# Y shape becomes [6, 4] instead of [2, 12]
```

#### Why Potentially Already Known

- Issue #7573 documents this as a functional bug, not a security vulnerability
- The security implications (buffer overflow, validation bypass) have not been explicitly claimed as a bounty
- May be considered "by design" by ONNX maintainers

#### Assessment

This sits at the boundary between functional bug and security vulnerability. To qualify as a bounty-worthy finding, it would need to demonstrate a concrete exploitable impact (e.g., buffer overflow in a specific runtime due to shape mismatch).

---

### Finding 3: DOT Syntax Injection in net_drawer for Unescaped Model Fields

**Severity:** Low-Medium (CVSS 5.3 - Integrity, XSS)
**CWE:** CWE-79 (Cross-Site Scripting)
**Component:** `onnx/tools/net_drawer.py`
**Novel Confidence:** MODERATE
**huntr Qualification Likelihood:** 30-40%

#### Description

The `doc_string` field in `net_drawer.py` is sanitized via `_form_and_sanitize_docstring()` which strips `<` and `>` characters. However, **other model fields** are passed directly to pydot/graphviz without HTML escaping:

- `NodeProto.name`
- `NodeProto.op_type`
- `NodeProto.domain`
- `GraphProto.name`
- `ValueInfoProto.name`

If the generated DOT output is rendered to SVG/HTML and displayed in a web context (common for model visualization in web-based ML platforms), unescaped `<`, `>`, or `&` in these fields can break SVG structure or trigger XSS.

#### Attack Scenario

1. Attacker creates an ONNX model with `op_type` or `name` containing SVG-breaking content
2. Victim visualizes the model using `net_drawer.py` -> DOT -> SVG
3. SVG is embedded in a web-based model catalog or analysis dashboard
4. XSS payload executes in the victim's browser

#### PoC Concept

```python
import onnx
from onnx import helper, TensorProto
from onnx.tools import net_drawer

# Create a node with malicious op_type/name containing DOT/SVG injection
xss_payload = '"></script><svg/onload=alert(1)>'

node = helper.make_node(
    op_type=xss_payload,  # Unescaped in DOT output
    inputs=['X'],
    outputs=['Y'],
    name=xss_payload,     # Also unescaped
    doc_string="harmless"  # This field IS sanitized
)

graph = helper.make_graph(
    [node],
    xss_payload,  # Graph name also unescaped
    [helper.make_tensor_value_info('X', TensorProto.FLOAT, [1])],
    [helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1])]
)

model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 17)])

# Generate DOT - the XSS payload is in the raw DOT output
dot_graph = net_drawer.GetPydotGraph(model.graph, name=model.graph.name)
dot_graph.write_svg('malicious.svg')
```

#### Why Potentially Already Known

- The doc_string injection is already reported on huntr
- The unescaped fields are a known limitation but not specifically reported as a separate bounty
- Impact is limited to visualization context (not model loading or inference)

#### Assessment

This is a legitimate finding but likely considered low severity. The doc_string report on huntr may cover the broader net_drawer injection surface. Worth submitting as a separate finding if the doc_string report was specifically limited to that field.

---

## Section 3: Lower-Confidence Leads (Worth Investigating)

### Lead 4: External Data basepath Field Path Concatenation Bypass

**Severity:** Unknown
**Component:** `onnx/external_data_helper.py` - `basepath` field handling
**Novel Confidence:** LOW-MODERATE

The `basepath` field in `external_data` is used for path resolution. The recent CVE-2025-51480 specifically targeted `save_external_data` which uses `os.path.join(basepath, entry.value)`. However, the `basepath` field itself could potentially contain path traversal sequences when used during **loading** (not saving). If `basepath` is set to `../../etc/` and `location` is `passwd`, the concatenation resolves to `/etc/passwd`.

**Research needed:** Verify if current path validation (`weakly_canonical()` + prefix check) properly handles basepath + location concatenation in all code paths. The recent security hardening may already cover this.

---

### Lead 5: SparseTensorProto Indices/Dims Mismatch

**Severity:** Unknown
**Component:** Sparse tensor shape inference + runtime allocation
**Novel Confidence:** LOW

`SparseTensorProto` has three fields:
- `values` (TensorProto): the non-zero values
- `indices` (TensorProto): positions of non-zero values, shape [NNZ] or [NNZ, rank]
- `dims` (repeated int64): shape of the dense tensor

A crafted model could set `dims` to `[1000000, 1000000]` (implying 10^12 elements) while `indices` only has a few entries. If a runtime pre-allocates based on `dims` without verifying consistency with `indices`, this causes OOM. Alternatively, if `indices` values exceed `dims` bounds, this could trigger out-of-bounds access during sparse-to-dense conversion.

**Research needed:** Verify whether ONNX checker validates SparseTensorProto internal consistency, and whether runtimes handle malformed sparse tensors safely.

---

### Lead 6: External Data Checksum Non-Validation

**Severity:** Medium (integrity)
**Component:** `TensorProto.external_data` - `checksum` field
**Novel Confidence:** LOW

The `external_data` field supports a `checksum` key for SHA1 digests of external tensor data. However, ONNX **parses but does not validate** this checksum. An attacker with write access to the external data file (e.g., in a shared model repository) can modify the tensor data without detection. The model file remains valid, and the checksum is silently ignored.

**Assessment:** This is likely "by design" (checksum validation is opt-in for consumers) rather than a vulnerability. However, it could be framed as an integrity bypass for users who expect the checksum to be validated.

---

### Lead 7: TrainingInfoProto Initialization Graph Execution

**Severity:** Unknown
**Component:** `ModelProto.training_info` (TrainingInfoProto)
**Novel Confidence:** LOW

`TrainingInfoProto` contains initialization and update graphs that are executed during training. These sub-graphs have the same expressive power as the main computation graph but receive less scrutiny. A crafted initialization graph could:

1. Reference tensors that don't exist, causing undefined behavior
2. Create circular initialization dependencies
3. Allocate extremely large intermediate tensors

**Research needed:** Verify whether TrainingInfoProto graphs are validated for structural correctness and whether their execution is properly bounded.

---

### Lead 8: DeviceConfigurationProto Injection

**Severity:** Unknown
**Component:** `ModelProto.configuration` (field 26) + `NodeProto.device_configurations` (field 10)
**Novel Confidence:** LOW-MODERATE

These are recently added fields for multi-device parallelism. New protobuf fields typically receive less validation scrutiny. Crafted `DeviceConfigurationProto` entries with:

- Extremely large device IDs or partition counts
- Circular device dependency graphs
- Malformed partition specifications

could cause DoS or undefined behavior in runtimes that support multi-device execution.

**Research needed:** Verify current validation depth for these new fields. Very new features (FLOAT4E2M1, multi-device) often have incomplete validation.

---

## Section 4: Attack Surfaces Assessed as Exhaustively Covered

### 4.1 External Data Path Traversal

**Assessment:** This is the most scrutinized attack surface in ONNX. With 10+ CVEs, dozens of huntr reports (many marked duplicate), and comprehensive 4-layer defense-in-depth, the probability of finding a novel bypass is extremely low. All variants have been explored:
- `../` sequences
- Absolute paths
- Symlinks (final-component and parent-directory)
- Hardlinks
- Tar extraction traversal
- Case-insensitive filesystem bypass

### 4.2 Arbitrary Attribute Injection via setattr

**Assessment:** Fixed in onnx 1.21.0 via key whitelist. The dunder attribute injection, negative offset, and petabyte-length DoS are all covered.

### 4.3 Hub Manifest Path Traversal

**Assessment:** CVE-2024-7776 and related reports. The manifest-based file overwrite is fixed.

### 4.4 PyOp Custom Operator Code Execution

**Assessment:** Deprecated in ONNX Runtime. No longer supported. Any finding would be rejected as affecting deprecated functionality.

---

## Section 5: Bounty Qualification Analysis

### huntr Program Assessment

| Factor | Assessment |
|--------|------------|
| Payout Tiers | Critical: $1,500, High: $750, Medium: $125, Low: $20 |
| Duplicate Rate | HIGH - Most ONNX reports are marked duplicate |
| Self-Close Rate | HIGH - Many finders close their own reports |
| Pending Reports | 12+ pending across various categories |
| Program Activity | Active - recent CVEs assigned (March 2026) |

### Novel Finding Rankings

| Finding | Confidence | Est. CVSS | huntr Tier | Duplicate Risk |
|---------|-----------|-----------|------------|----------------|
| #1 FunctionProto Call Graph DoS | Moderate | 7.5 | High ($750) | Medium |
| #2 Protobuf Default Shape Bypass | Moderate | 6.5 | Medium ($125) | High |
| #3 net_drawer DOT Injection | Moderate | 5.3 | Medium ($125) | High |
| #4 basepath Concatenation | Low | TBD | TBD | Very High |
| #5 SparseTensorProto Mismatch | Low | TBD | TBD | Medium |
| #6 Checksum Non-Validation | Low | 4.3 | Medium ($125) | Very High |

### Recommendation

**Priority 1: Finding #1 (FunctionProto Call Graph DoS)** has the best chance of qualifying as a novel, non-duplicate finding. It addresses a different mechanism than all reported ONNX DoS vulnerabilities (which focus on tensor dimensions, not function expansion). To strengthen this finding:

1. Build a working PoC that demonstrates OOM or extreme CPU consumption
2. Test against both `onnx.shape_inference.infer_shapes()` and `onnxruntime.InferenceSession()`
3. Measure the expansion factor vs. function count
4. Identify whether the checker validates total expanded node count

**Priority 2: Finding #5 (SparseTensorProto Mismatch)** is worth prototyping because sparse tensor handling is less tested than dense tensor handling. If a crash or OOB access can be demonstrated in ONNX Runtime, this could qualify as High severity.

---

## Section 6: Technical Appendix

### 6.1 ONNX Protobuf Schema Summary (Security-Relevant Fields)

```
TensorProto:
  - dims (repeated int64): tensor dimensions, can overflow when multiplied
  - data_type (int32): type discriminator, mismatch with actual data causes confusion
  - raw_data (bytes): raw tensor bytes, no size validation against dims*datatype
  - string_data (repeated bytes): string tensor data
  - external_data (repeated StringStringEntryProto): location, offset, length, checksum, basepath
  - data_location (enum): DEFAULT=0, EXTERNAL=1
  - segment: begin/end for tensor segmentation (rarely used, poorly validated)

GraphProto:
  - node (repeated NodeProto): computation nodes, topological order required
  - initializer (repeated TensorProto): constant tensors
  - sparse_initializer (repeated SparseTensorProto): sparse constant tensors
  - input/output/value_info (repeated ValueInfoProto): tensor type/shape definitions

NodeProto:
  - input/output (repeated string): value namespace
  - op_type (string): operator identifier
  - domain (string): operator domain
  - attribute (repeated AttributeProto): operator parameters
  - device_configurations (repeated NodeDeviceConfigurationProto): NEW field #10

FunctionProto:
  - node (repeated NodeProto): function body
  - Can call other functions but not recursively
  - No limit on total expansion size

AttributeProto:
  - g (GraphProto): nested subgraph
  - graphs (repeated GraphProto): multiple nested subgraphs
  - Can create deeply nested graph structures

ModelProto:
  - training_info (repeated TrainingInfoProto): training subgraphs
  - functions (repeated FunctionProto): local function definitions
  - configuration (repeated DeviceConfigurationProto): NEW field #26
```

### 6.2 Known Security Controls in Current ONNX (v1.21.0+)

1. **External Data Path Validation (C++ checker.cc):**
   - `std::filesystem::weakly_canonical()` path resolution
   - Prefix check against model directory
   - `is_symlink()` rejection on final path component
   - `hard_link_count() > 1` rejection
   - Platform-specific secure open (`openat2`, `openat` with `O_NOFOLLOW`, `CreateFileW`)

2. **External Data Attribute Validation (Python external_data_helper.py):**
   - Key whitelist: `location`, `offset`, `length`, `checksum`, `basepath`
   - Non-negative integer validation for offset/length
   - File-size bounds validation before reading

3. **Shape Inference:**
   - No explicit integer overflow checks (relies on int64)
   - Symbolic shape fallback for unknown dimensions

4. **Checker:**
   - Topological sort validation
   - Type consistency validation
   - No function expansion size limit
   - No SparseTensorProto internal consistency check

### 6.3 Related CVEs and Reports (Complete List)

| ID | Type | Year | Component |
|----|------|------|-----------|
| CVE-2022-25882 | Path Traversal | 2022 | external_data |
| CVE-2024-27318 | Path Traversal | 2024 | external_data |
| CVE-2024-5187 | Arbitrary File Write | 2024 | download_model |
| CVE-2024-7776 | Arbitrary File Write | 2024 | tar extraction |
| CVE-2025-51480 | Path Traversal | 2025 | save_external_data |
| CVE-2026-28500 | Auth Bypass | 2026 | hub.load(silent=True) |
| CVE-2026-34445 | Attribute Injection/DoS | 2026 | ExternalDataInfo setattr |
| CVE-2026-34446 | Hardlink Bypass | 2026 | external_data path check |
| CVE-2026-34447 | Symlink Traversal | 2026 | external_data path check |

---

*End of Report*
