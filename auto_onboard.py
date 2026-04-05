#!/usr/bin/env python3.11
"""
auto_onboard.py — Авто-обнаружение новых AI продуктов

Быстрая версия: проверяет конкретный список продуктов.
При обнаружении нового — генерирует документацию и добавляет в KB.

Запуск: auto_onboard.py (через dev start)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

KB_DIR = os.path.expanduser("~/project/knowledge_base")
REF_DIR = os.path.join(KB_DIR, "reference")
INTEL_DIR = os.path.expanduser("~/project/intel")
ATLLM_HOTDIR = os.path.expanduser(
    "~/Library/Application Support/anythingllm-desktop/storage/hotdir"
)
REGISTRY_FILE = os.path.join(INTEL_DIR, "known_products.json")
LOG_FILE = os.path.join(KB_DIR, "auto_onboard.log")

for d in [REF_DIR, ATLLM_HOTDIR]:
    os.makedirs(d, exist_ok=True)

# Реестр известных продуктов
KNOWN_PRODUCTS = {}
if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, "r") as f:
        KNOWN_PRODUCTS = {p["name"]: p for p in json.load(f).get("products", [])}

# ═══════════════════════════════════════════════════════════
# ПРОДУКТЫ ДЛЯ МОНИТОРИНГА
# ═══════════════════════════════════════════════════════════

WATCHLIST = [
    # AI Агенты (CLI)
    {"name": "claude", "type": "cli", "cmd": "claude --version", "category": "ai-agent",
     "docs": "https://docs.anthropic.com/en/docs/claude-code/overview"},
    {"name": "codex", "type": "cli", "cmd": "codex --version", "category": "ai-agent",
     "docs": "https://github.com/openai/codex"},
    {"name": "jules", "type": "cli", "cmd": "jules --version", "category": "ai-agent",
     "docs": "https://github.blog/changelog/label/jules/"},
    {"name": "goose", "type": "cli", "cmd": "goose --version", "category": "ai-agent",
     "docs": "https://block.github.io/goose/docs"},
    {"name": "copilot", "type": "cli", "cmd": "copilot --version", "category": "ai-agent",
     "docs": "https://docs.github.com/en/copilot/concepts/agents/copilot-cli"},
    {"name": "qwen", "type": "cli", "cmd": "qwen --version", "category": "ai-agent",
     "docs": "https://qwenlm.github.io/"},
    {"name": "gemini", "type": "cli", "cmd": "gemini --version", "category": "ai-agent",
     "docs": "https://ai.google.dev/gemini-api/docs"},
    {"name": "ollama", "type": "cli", "cmd": "ollama --version", "category": "ai-runtime",
     "docs": "https://ollama.com/docs"},
    # Security
    {"name": "nuclei", "type": "cli", "cmd": "nuclei -version", "category": "security",
     "docs": "https://docs.projectdiscovery.io/tools/nuclei/"},
    {"name": "subfinder", "type": "cli", "cmd": "subfinder -version", "category": "security",
     "docs": "https://docs.projectdiscovery.io/tools/subfinder/"},
    {"name": "httpx", "type": "cli", "cmd": "httpx -version", "category": "security",
     "docs": "https://docs.projectdiscovery.io/tools/httpx/"},
    {"name": "ffuf", "type": "cli", "cmd": "ffuf -V", "category": "security",
     "docs": "https://github.com/ffuf/ffuf"},
    {"name": "semgrep", "type": "cli", "cmd": "semgrep --version", "category": "security",
     "docs": "https://semgrep.dev/docs/"},
    {"name": "bandit", "type": "cli", "cmd": "bandit --version", "category": "security",
     "docs": "https://bandit.readthedocs.io/"},
    {"name": "aisec", "type": "cli", "cmd": "aisec --version", "category": "security",
     "docs": "https://github.com/semgrep/aisec"},
    {"name": "trufflehog", "type": "cli", "cmd": "trufflehog --version", "category": "security",
     "docs": "https://github.com/trufflesecurity/trufflehog"},
    {"name": "sqlmap", "type": "cli", "cmd": "sqlmap --version", "category": "security",
     "docs": "https://sqlmap.org/"},
    {"name": "nmap", "type": "cli", "cmd": "nmap --version", "category": "security",
     "docs": "https://nmap.org/"},
    {"name": "masscan", "type": "cli", "cmd": "masscan --version", "category": "security",
     "docs": "https://github.com/robertdavidgraham/masscan"},
    # Cloud/DevOps
    {"name": "az", "type": "cli", "cmd": "az version", "category": "cloud",
     "docs": "https://learn.microsoft.com/en-us/cli/azure/"},
    {"name": "terraform", "type": "cli", "cmd": "terraform version", "category": "cloud",
     "docs": "https://developer.hashicorp.com/terraform/docs"},
    {"name": "docker", "type": "cli", "cmd": "docker --version", "category": "cloud",
     "docs": "https://docs.docker.com/"},
    {"name": "kubectl", "type": "cli", "cmd": "kubectl version", "category": "cloud",
     "docs": "https://kubernetes.io/docs/reference/kubectl/"},
    {"name": "helm", "type": "cli", "cmd": "helm version", "category": "cloud",
     "docs": "https://helm.sh/docs/"},
    {"name": "gh", "type": "cli", "cmd": "gh --version", "category": "dev-tool",
     "docs": "https://cli.github.com/"},
    # Editors/Terminals
    {"name": "zed", "type": "app", "cmd": None, "category": "editor",
     "docs": "https://zed.dev/docs"},
    {"name": "warp", "type": "app", "cmd": None, "category": "terminal",
     "docs": "https://docs.warp.dev"},
    {"name": "obsidian", "type": "app", "cmd": None, "category": "knowledge",
     "docs": "https://help.obsidian.md"},
    {"name": "claude-desktop", "type": "app", "cmd": None, "category": "ai-agent",
     "docs": "https://docs.anthropic.com/en/docs/claude-code/overview"},
    {"name": "cursor", "type": "app", "cmd": None, "category": "ai-agent",
     "docs": "https://docs.cursor.com/"},
    {"name": "windsurf", "type": "app", "cmd": None, "category": "ai-agent",
     "docs": "https://docs.codeium.com/windsurf/"},
    {"name": "anythingllm", "type": "app", "cmd": None, "category": "rag",
     "docs": "https://docs.anythingllm.com"},
]


# ═══════════════════════════════════════════════════════════
# ФУНКЦИИ
# ═══════════════════════════════════════════════════════════

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def check_cli(product: dict) -> dict:
    """Проверить CLI продукт."""
    try:
        result = subprocess.run(
            product["cmd"].split(), capture_output=True,
            text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            version = re.sub(r'[^\w\.\-\:\/ ]', '', version)[:60]
            return {"found": True, "version": version}
    except Exception:
        pass
    return {"found": False, "version": None}


def check_app(product: dict) -> dict:
    """Проверить macOS приложение."""
    app_names = {
        "zed": "Zed",
        "warp": "Warp",
        "obsidian": "Obsidian",
        "claude-desktop": "Claude",
        "cursor": "Cursor",
        "windsurf": "Windsurf",
        "anythingllm": "AnythingLLM",
    }

    app_name = app_names.get(product["name"], product["name"])
    app_path = f"/Applications/{app_name}.app"

    if os.path.exists(app_path):
        # Получаем версию
        try:
            result = subprocess.run(
                ["mdls", "-name", "kMDItemVersion", app_path],
                capture_output=True, text=True, timeout=5
            )
            version = "unknown"
            if result.returncode == 0:
                match = re.search(r'kMDItemVersion\s*=\s*"([^"]+)"', result.stdout)
                if match:
                    version = match.group(1)
            return {"found": True, "version": version}
        except Exception:
            return {"found": True, "version": "unknown"}

    return {"found": False, "version": None}


def generate_doc(product: dict, version: str) -> str:
    """Сгенерировать документацию."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    name = product["name"]

    md = f"""# 📦 {name.title()}

**Обнаружен:** {now}
**Категория:** {product['category']}
**Версия:** {version}
**Документация:** {product['docs']}

---

## Описание

{name.title()} — продукт категории {product['category']}.

## Версия

```
{version}
```

## Роль в системе

_Добавить описание роли._

## Ссылки

- [Документация]({product['docs']})

---

*Сгенерировано автоматически: auto_onboard.py*
"""
    return md


def save_doc(product: dict, version: str) -> str:
    """Сохранить документ."""
    import shutil

    safe_name = product["name"].replace("-", "_")
    md = generate_doc(product, version)

    md_file = os.path.join(REF_DIR, f"PRODUCT_{safe_name.upper()}.md")
    with open(md_file, "w") as f:
        f.write(md)

    # AnythingLLM
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    try:
        shutil.copy2(md_file, os.path.join(ATLLM_HOTDIR, f"onboard_{safe_name}_{ts}.md"))
    except Exception:
        pass

    return md_file


def update_registry(product: dict, version: str):
    """Обновить реестр."""
    registry = {"products": list(KNOWN_PRODUCTS.values())}

    entry = {
        "name": product["name"],
        "version": version,
        "category": product["category"],
        "last_seen": datetime.now().isoformat(),
    }

    # Обновить или добавить
    found = False
    for i, existing in enumerate(registry["products"]):
        if existing["name"] == product["name"]:
            registry["products"][i] = entry
            found = True
            break

    if not found:
        registry["products"].append(entry)

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def run():
    log("🔍 Auto-Onboard — проверка продуктов")
    log("=" * 50)

    new_found = []
    updated = []
    all_products = []  # Собираем все для batch update

    for product in WATCHLIST:
        # Проверяем
        if product["type"] == "cli":
            result = check_cli(product)
        else:
            result = check_app(product)

        if not result["found"]:
            continue

        name = product["name"]
        version = result["version"]
        is_known = name in KNOWN_PRODUCTS
        old_version = KNOWN_PRODUCTS.get(name, {}).get("version", "unknown")

        entry = {
            "name": name,
            "version": version,
            "category": product["category"],
            "last_seen": datetime.now().isoformat(),
        }
        all_products.append(entry)

        if not is_known:
            log(f"🆕 Новый продукт: {name} v{version}")
            md_file = save_doc(product, version)
            log(f"   💾 {md_file}")
            new_found.append({"name": name, "version": version})
        elif old_version != version:
            log(f"🔄 Обновление: {name} {old_version} → {version}")
            md_file = save_doc(product, version)
            updated.append({"name": name, "old": old_version, "new": version})
        else:
            log(f"   ✅ {name} {version} (без изменений)")

    # Batch update registry — один раз запуск
    if all_products:
        registry_file = REGISTRY_FILE
        existing = {}
        if os.path.exists(registry_file):
            try:
                with open(registry_file, "r") as f:
                    existing = {p["name"]: p for p in json.load(f).get("products", [])}
            except Exception:
                pass

        # Мержим
        for entry in all_products:
            existing[entry["name"]] = entry

        with open(registry_file, "w") as f:
            json.dump({"products": sorted(existing.values(), key=lambda x: x["name"])}, f, indent=2)

    log("=" * 50)
    if new_found:
        log(f"📦 Новых: {len(new_found)}")
        for p in new_found:
            log(f"   ✅ {p['name']} ({p['version']})")
    if updated:
        log(f"🔄 Обновлено: {len(updated)}")

    return new_found, updated


if __name__ == "__main__":
    run()
