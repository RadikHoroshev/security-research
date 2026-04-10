# Security Research — Project Rules for Jules

## ⚠️ PROTECTED FILES — DO NOT MODIFY OR DELETE

The following files contain vulnerability research that may be referenced
in active security submissions. Their paths and names must remain unchanged:

```
results/report_*.md               ← submitted vulnerability reports
results/poc_*.py                  ← proof-of-concept scripts
results/xinference_*.md           ← Xinference research
results/xinference_*.py
results/minirag_*.md
results/minirag_*.py
results/langflow_*.md
results/langflow_*.txt
results/litellm_*.md
results/llamaindex_*.md
results/huntr_submission_content.md
results/verification.json
results/submission_status.json
xinference_auth_audit.md          ← root-level research files
xinference_eval_rce.md
minirag_path_traversal_check.md
scripts/                          ← analysis scripts
```

> Do not rename, move, or delete these files. Submission reports on Huntr
> may reference specific file paths as evidence.

---

## Allowed Work Areas

Jules may freely create and modify files in:

```
results/             ← add new research files only
targets/             ← add new target subdirectories
knowledge_base/      ← add vulnerability pattern notes
scripts/             ← add new analysis scripts
```

---

## Tasks Jules May Perform

- Add new vulnerability research as new files in `results/`
- Add new target research under `targets/`
- Update `knowledge_base/` with new patterns or references
- Write new PoC scripts for new targets
- Run `scripts/custom_ast_scanner.py` for code analysis

---

## Tasks Jules Must NOT Perform

- Rename, move, or delete any existing file in `results/`
- Modify existing report or PoC files
- Add config files, agent files, or tooling docs at the repository root
- Commit credentials, API keys, tokens, or personal data
- Reference internal tooling, workflow details, or agent infrastructure in any file
- Add `.log`, `.bak`, state files, or cache directories

---

## Repository Purpose

Independent security research on AI/ML infrastructure vulnerabilities.
Research supports responsible disclosure via Huntr bug bounty program.
