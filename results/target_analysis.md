# Target Analysis — 2026-04-06

## 1. HuggingFace transformers ($1500)
**GitHub:** huggingface/transformers | ⭐ 158,879
**CVEs:** 8 (moderate)

### Dangerous patterns found:
- `eval(fs_config.conv_feature_layers)` — sew_d/convert_sew_d_original_pytorch_checkpoint_to_pytorch.py:184
- `eval(fs_config.conv_feature_layers)` — hubert/convert_distilhubert_original_s3prl_checkpoint_to_pytorch.py:161
- `eval(fs_config.conv_feature_layers)` — sew/convert_sew_original_pytorch_checkpoint_to_pytorch.py:180
- `yaml.load(cfg_str, Loader=yaml.BaseLoader)` — marian/convert_marian_to_pytorch.py:107, 684
- `yaml.load(open(...), Loader=yaml.FullLoader)` — parakeet/convert_nemo_to_hf.py:360

### Assessment:
- `eval()` in checkpoint converters — **LOW risk** (run locally during conversion, not at inference)
- `yaml.load` with `yaml.BaseLoader` — **MEDIUM risk** if untrusted YAML is loaded
- Most dangerous patterns are in `convert_*` scripts (one-time use, not runtime)
- **Verdict:** Hard to find exploitable RCE — most code is ML model loading, not web-facing

---

## 2. MLflow ($1500)  
**GitHub:** mlflow/mlflow | ⭐ 18,000+
**CVEs:** 27 (HEAVILY audited)

### Dangerous patterns found:
- `asyncio.create_subprocess_exec` — assistant/providers/claude_code.py:401 (AI agent code execution — intentional!)
- `yaml.load(..., yaml.SafeLoader)` — safe
- `ast.literal_eval()` — safe

### Assessment:
- 27 CVEs — очень хорошо аудитирован
- subprocess — intentional feature (MLflow AI assistant)
- YAML uses SafeLoader
- **Verdict:** SKIPPED — too mature, too many existing CVEs

---

## 3. LlamaIndex ($1500)
**GitHub:** run-llama/llama_index | ⭐ 35,000+
**CVEs:** 13 (moderate)

### Dangerous patterns found:
- NONE in grep search (clean!)
- MCP tool integration CVE — "no per-message authentication"

### Assessment:
- MCP integration has auth bypass potential
- Agent verification pilot — might have weak checks
- **Verdict:** PROMISING — MCP authentication gap is interesting

---

## Recommendations

### Best targets to pursue:
1. **llama_index MCP auth bypass** — 13 CVEs, relatively new attack surface
2. **transformers yaml.load with BaseLoader** — possible deserialization RCE if untrusted models loaded
3. **Model File Formats on huntr** — $1500-$4000, less audited (Pickle, ONNX, GGUF, SafeTensors)

### Skip:
- MLflow — слишком зрелый, 27 CVE
- transformers eval() — только в конвертерах, не exploitable
