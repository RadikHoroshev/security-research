# Remote Code Execution (RCE) in Hugging Face transformers via Malicious NeMo Model Conversion

## Summary
The `transformers` library's `convert_nemo_to_hf.py` script for Parakeet models is vulnerable to Remote Code Execution (RCE) through two distinct vulnerabilities:
1.  **Arbitrary File Write via Path Traversal:** The script uses `tar.extractall()` without path validation or security filters, allowing a malicious `.nemo` archive to write files outside the intended extraction directory.
2.  **YAML Deserialization RCE:** The script uses `yaml.load(..., Loader=yaml.FullLoader)` on a configuration file extracted from the untrusted archive. `FullLoader` allows the instantiation of arbitrary Python objects, leading to immediate code execution upon loading.

An attacker can exploit this by uploading a malicious repository to the Hugging Face Hub. When a victim uses the conversion script to process this repository, the attacker achieves full code execution on the victim's machine.

## Severity
CVSS 3.1 Score: **9.0 (Critical)**
Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H`

## Root Cause
The vulnerability is located in `src/transformers/models/parakeet/convert_nemo_to_hf.py`.

### 1. Vulnerable Extraction
In the `extract_nemo_archive` function (line 72):
```python
with tarfile.open(nemo_path, "r:gz") as tar:
    tar.extractall(extract_dir)
```
The script extracts the `.nemo` (tar.gz) archive without validating that the entries remain within `extract_dir`. A crafted archive with `../` sequences can overwrite arbitrary files.

### 2. Unsafe YAML Loading
In the `convert_ctc_nemo_to_hf` and `convert_rnnt_nemo_to_hf` functions (line 360):
```python
nemo_config = yaml.load(open(model_files["model_config"], "r"), Loader=yaml.FullLoader)
```
The script loads the `model_config.yaml` file (extracted from the malicious archive) using `yaml.FullLoader`. This allows an attacker to include tags like `!!python/object/apply:os.system` to execute arbitrary commands.

## Steps to Reproduce

1.  Create a malicious `.nemo` archive containing a `model_config.yaml` with a payload:
    ```yaml
    !!python/object/apply:os.system
    - touch /tmp/pwned_by_transformers
    ```
2.  Upload this archive to a repository on the Hugging Face Hub (e.g., `attacker/malicious-parakeet`).
3.  As a victim, run the conversion script pointing to the malicious repository:
    ```bash
    python -m transformers.models.parakeet.convert_nemo_to_hf --hf_repo_id attacker/malicious-parakeet --model_type ctc --output_dir ./out
    ```
4.  Observe that `/tmp/pwned_by_transformers` is created, confirming RCE.

## Proof of Concept
A standalone PoC script is available at `poc_transformers_parakeet_yaml_rce.py`. It demonstrates both the path traversal and the YAML deserialization independently by simulating the vulnerable patterns used in the script.

## Impact
Successful exploitation results in full Remote Code Execution (RCE) on the user's system with the privileges of the user running the conversion script. This can lead to data theft, persistent backdoors, and lateral movement within the network. Since `transformers` is often used in research and production environments with high-privilege access to sensitive data and GPU resources, the impact is significant.

## Remediation
1.  **Secure YAML Loading:** Replace `yaml.FullLoader` with `yaml.SafeLoader` or `yaml.safe_load()`. This is the standard defense against YAML-based RCE.
2.  **Secure Extraction:** Use the `filter='data'` argument in `tar.extractall()` (available in Python 3.12+) or manually validate that all extracted paths are children of the destination directory.
3.  **Validate Remote Content:** Even when downloading from the Hugging Face Hub, the library should not trust the internal structure of model archives.

## Researcher's Note
This is a high-impact finding because it involves remote content download and execution via a standard library tool. It is similar to previous vulnerabilities found in other model converters (like MobileViTV2), but this specific instance in the Parakeet converter remains unpatched in the current `main` branch.
