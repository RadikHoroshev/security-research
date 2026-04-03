# Huntr Bug Bounty Report Template
# Агенты: заполнять строго по этому шаблону

---

## Summary
<!-- 1 предложение: тип уязвимости + компонент + максимальный impact -->
[VULN_TYPE] in [COMPONENT] allows [ATTACKER_ROLE] to [IMPACT] via [METHOD].

## Severity
**CVSS 3.1 Score:** X.X ([Critical/High/Medium/Low])
**Vector:** `CVSS:3.1/AV:_/AC:_/PR:_/UI:_/S:_/C:_/I:_/A:_`

| Metric | Value | Reason |
|--------|-------|--------|
| Attack Vector | Network/Local | |
| Attack Complexity | Low/High | |
| Privileges Required | None/Low/High | |
| User Interaction | None/Required | |
| Confidentiality | None/Low/High | |
| Integrity | None/Low/High | |
| Availability | None/Low/High | |

## Affected Component
- **File:** `path/to/file.py`
- **Line:** 000
- **Function:** `function_name()`
- **Version:** commit hash or release tag

## Vulnerable Code
```python
# Exact vulnerable snippet with line numbers
line_N: vulnerable_code_here
```

## Steps to Reproduce
<!-- Пронумерованные шаги, каждый выполним без объяснений -->
1. Clone the repository: `git clone https://github.com/ORG/REPO`
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `python app.py`
4. Run the PoC: `python poc.py`
5. Observe: [EXACT EXPECTED OUTPUT]

## ✅ Proof of Concept
<!-- ОБЯЗАТЕЛЬНО: рабочий скрипт, который заказчик может запустить за 30 секунд -->
<!-- Скрипт должен: создать условия → выполнить атаку → показать результат -->

```python
#!/usr/bin/env python3
"""
PoC: [VULN_TYPE] in [REPO]
Target: http://localhost:PORT
Requirements: pip install requests
Usage: python poc.py
Expected output: [WHAT SUCCESS LOOKS LIKE]
"""
import requests
import os

TARGET = "http://localhost:9600"  # изменить если нужно

# Step 1: Setup
# ...

# Step 2: Attack
# ...

# Step 3: Verify
# ...

print("[+] Vulnerability confirmed!" if SUCCESS else "[-] Not vulnerable")
```

**Expected output when vulnerable:**
```
[+] Connected to target
[+] Payload delivered
[+] RCE confirmed: uid=1000(user) gid=1000(user)
```

## Impact
<!-- Конкретно что может сделать атакующий, без воды -->
An attacker with [PRIVILEGE_LEVEL] can:
- [IMPACT_1]
- [IMPACT_2]
- [IMPACT_3]

**Real-world scenario:** [ONE SENTENCE REAL ATTACK SCENARIO]

## Remediation
<!-- Конкретный код-фикс, не общие слова -->
Add path sanitization before using user-supplied values:

```python
# BEFORE (vulnerable):
app_name = description.get("name")
app_dir = apps_zoo_path / app_name

# AFTER (fixed):
from lollms.security import sanitize_path
app_name = sanitize_path(description.get("name"))
app_dir = apps_zoo_path / app_name
# Defense in depth: verify result stays within intended directory
if not str(app_dir.resolve()).startswith(str(apps_zoo_path.resolve())):
    raise HTTPException(status_code=400, detail="Invalid app name")
```

---
## Checklist (перед отправкой)
- [ ] PoC запускается с нуля без дополнительных объяснений
- [ ] CVSS score обоснован в таблице
- [ ] Указан конкретный файл и строка
- [ ] Steps to Reproduce проверены вручную
- [ ] Нет дублей на huntr (проверено через duplicate_check.json)
- [ ] Severity соответствует реальному impact
