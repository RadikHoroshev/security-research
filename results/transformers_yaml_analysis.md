# Transformers YAML Vulnerability Analysis

## 1. Vulnerability Overview
The Hugging Face `transformers` library contains several instances of unsafe YAML loading using `yaml.FullLoader`, which can lead to Remote Code Execution (RCE) when processing malicious YAML configuration files.

## 2. Unsafe `yaml.load` Occurrences

### 2.1. `src/transformers/models/parakeet/convert_nemo_to_hf.py`
- **Line 360:** `nemo_config = yaml.load(open(model_files["model_config"], "r"), Loader=yaml.FullLoader)`
- **Vulnerability:** This script converts NVIDIA NeMo models to Hugging Face format. It downloads a `.nemo` archive from a user-specified `hf_repo_id`, extracts it, and then loads the `model_config` YAML file using `FullLoader`.
- **Attack Vector:** An attacker can upload a malicious repo to the Hugging Face Hub containing a `.nemo` file with a crafted YAML payload. When a user runs this conversion script pointing to the malicious repo, RCE is achieved.
- **Risk:** **Critical** (Automated download and execution via remote repo).

### 2.2. `src/transformers/models/mobilevitv2/convert_mlcvnets_to_pytorch.py`
- **Line 57:** `cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)`
- **Vulnerability:** Similar to above, this script converts `ml-cvnets` checkpoints. It takes a local configuration file path as an argument and loads it using `FullLoader`.
- **Risk:** **High** (Requires tricking a user into downloading and specifying a malicious local file).

## 3. Analysis of Loader Safety
- **Loader types in `transformers`:**
    - `yaml.BaseLoader`: Used in `marian` conversion scripts. Safe, as it loads all data as strings.
    - `yaml.FullLoader`: Used in `parakeet` and `mobilevitv2`. Unsafe in versions of PyYAML specified by `transformers` (`>=5.1`), as it permits the instantiation of arbitrary Python objects using tags like `!!python/object/new:...`.
    - `yaml.safe_load`: Used correctly in most other parts of the library (e.g., `hf_argparser.py`, `olmoe`, `chameleon`).

## 4. Bounties and CVEs
- **Existing Reports:** A similar vulnerability in `MobileViTV2` was previously reported on `huntr.com` (CVE-2024-11392).
- **Potential New Findings:** The vulnerability in `parakeet/convert_nemo_to_hf.py` appears to be a separate, potentially unpatched instance of the same pattern, involving remote model downloading.

## 5. Recommendation
Replace all occurrences of `yaml.load(..., Loader=yaml.FullLoader)` with `yaml.safe_load(...)` or `yaml.load(..., Loader=yaml.SafeLoader)`. Ensure that `PyYAML` version requirements are updated if specialized loaders are required.
