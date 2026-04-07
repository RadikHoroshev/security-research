# YAML Deserialization RCE in Hugging Face transformers (MobileViTV2 Converter)

## Summary
The `transformers` library's `convert_mlcvnets_to_pytorch.py` script for MobileViTV2 models is vulnerable to Remote Code Execution (RCE) through unsafe YAML deserialization. The script uses `yaml.load(..., Loader=yaml.FullLoader)` on a configuration file supplied by the user. `FullLoader` allows the instantiation of arbitrary Python objects, leading to immediate code execution upon loading.

While a similar vulnerability was previously addressed in other parts of the MobileViTV2 models (CVE-2024-11392), this specific instance in the converter script remains unpatched in the current `main` branch.

## Severity
CVSS 3.1 Score: **7.8 (High)**
Vector: `CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H`

## Root Cause
The vulnerability is located in `src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py` at line 57.

```python
with open(args.yaml_config, 'r') as yaml_file:
    cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
```

The script takes a `yaml_config` path as a command-line argument and loads it using `yaml.FullLoader`. This loader is unsafe because it permits tags that execute arbitrary Python code, such as `!!python/object/apply:os.system`.

## Steps to Reproduce

1.  Create a malicious YAML configuration file (`malicious.yaml`) with an RCE payload:
    ```yaml
    !!python/object/apply:os.system
    - touch /tmp/pwned_mobilevitv2
    ```
2.  Run the conversion script and specify the malicious configuration:
    ```bash
    python -m transformers.models.mobilevitv2.convert_mlcvnets_to_pytorch --yaml_config malicious.yaml --mlcvnets_ckpt checkpoint.pt --output_dir ./out
    ```
3.  Observe that `/tmp/pwned_mobilevitv2` is created, confirming RCE.

## Proof of Concept
A standalone PoC script is available at `poc_transformers_mobilevitv2_yaml.py`. It demonstrates the YAML deserialization vulnerability by simulating the vulnerable code pattern used in the script.

## Impact
Successful exploitation results in full code execution on the user's system with the privileges of the user running the conversion script. This can lead to sensitive information disclosure, installation of malicious software, and persistent access to the machine.

## Remediation
**Secure YAML Loading:** Replace `yaml.FullLoader` with `yaml.SafeLoader` or `yaml.safe_load()`. This ensures that only safe, basic data types are instantiated during the YAML loading process.

## Researcher's Note
This finding highlights the importance of thorough security audits after a vulnerability is reported. Although CVE-2024-11392 was issued for MobileViTV2, this specific converter script was either overlooked or improperly patched, leaving users vulnerable to a known attack vector.
