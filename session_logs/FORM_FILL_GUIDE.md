# Huntr Form Fill Guide
# Открой: https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms

## Уже заполнено автоматически:
- ✅ Repository: parisneo/lollms
- ✅ Package Manager: pypi
- ✅ Version Affected: >=9.0.0

## Заполни вручную:

### 1. Тип уязвимости (выпадающий список)
Выбери: **Path Traversal**

### 2. CVSS (кнопки)
- Attack Vector: **Network**
- Attack Complexity: **Low**
- Privileges Required: **Low**
- User Interaction: **None**
- Scope: **Unchanged**
- Confidentiality: **High**
- Integrity: **High**
- Availability: **High**

### 3. Title (заголовок отчёта)
```
Path Traversal in /upload_app leads to RCE via custom function injection
```

### 4. Description / PoC (большое поле)
Скопируй из файла:
/Users/code/project/intel/results/final_report.md
(весь файл, начиная с ## Executive Summary)

### 5. Impact (поле Impact)
```
An attacker who can establish a WebSocket connection (no credentials required by default) can:

1. Write an arbitrary directory to any filesystem path reachable from apps_zoo_path, including custom_function_calls/ where the server loads and executes Python code.

2. Achieve Remote Code Execution by placing a malicious function.py in custom_function_calls/<name>/, calling /mount_function_call, and triggering the LLM to invoke it.

3. Establish a persistent backdoor — the injected function survives server restart as it is stored on disk and registered in the config via save_config().

4. Full host compromise — lollms runs locally with access to the user's home directory, API keys, and environment variables.
```

### 6. Permalink (ссылка на уязвимый код)
```
https://github.com/parisneo/lollms-webui/blob/main/lollms/server/endpoints/lollms_apps.py#L340
```

Description для permalink:
```
app_name from description.yaml used in shutil.move() without sanitize_path() — direct path traversal via apps_zoo_path / app_name
```
