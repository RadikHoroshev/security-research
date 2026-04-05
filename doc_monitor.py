#!/usr/bin/env python3.11
"""
doc_monitor.py — Автоматический мониторинг документации ВСЕХ продуктов

Каждый день:
  1. Проверяет версии всех установленных продуктов
  2. Скачивает актуальную документацию (через web/API)
  3. Обновляет knowledge_base/reference/
  4. Логирует изменения
  5. Синхронизирует с AnythingLLM

Продукты для мониторинга:
  - Goose CLI
  - GitHub Copilot CLI
  - Ollama
  - Qwen Code
  - Gemini CLI
  - Jules
  - Codex CLI
  - Warp
  - Zed IDE
  - AnythingLLM
  - Obsidian
  - Azure CLI / azd
  - Security Team tools (nuclei, semgrep, bandit, subfinder)
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

KB_DIR = os.path.expanduser("~/project/knowledge_base")
REF_DIR = os.path.join(KB_DIR, "reference")
LOG_FILE = os.path.join(KB_DIR, "doc_monitor.log")
ATLLM_HOTDIR = os.path.expanduser(
    "~/Library/Application Support/anythingllm-desktop/storage/hotdir"
)

os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(ATLLM_HOTDIR, exist_ok=True)

# ── Реестр продуктов ─────────────────────────────────────

PRODUCTS = [
    {
        "id": "goose",
        "name": "Goose CLI",
        "version_cmd": "goose --version",
        "docs_url": "https://block.github.io/goose/docs",
        "category": "ai-agent",
        "importance": "core",
    },
    {
        "id": "copilot",
        "name": "GitHub Copilot CLI",
        "version_cmd": "copilot --version",
        "docs_url": "https://docs.github.com/en/copilot/concepts/agents/copilot-cli",
        "category": "ai-agent",
        "importance": "core",
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "version_cmd": "ollama --version",
        "docs_url": "https://ollama.com/docs",
        "category": "ai-runtime",
        "importance": "core",
    },
    {
        "id": "qwen",
        "name": "Qwen Code",
        "version_cmd": "qwen --version",
        "docs_url": "https://qwenlm.github.io/blog/",
        "category": "ai-agent",
        "importance": "core",
    },
    {
        "id": "gemini",
        "name": "Gemini CLI",
        "version_cmd": "gemini --version",
        "docs_url": "https://ai.google.dev/gemini-api/docs",
        "category": "ai-agent",
        "importance": "core",
    },
    {
        "id": "jules",
        "name": "Jules",
        "version_cmd": "jules --version",
        "docs_url": "https://github.blog/changelog/label/jules/",
        "category": "ai-agent",
        "importance": "optional",
    },
    {
        "id": "codex",
        "name": "OpenAI Codex CLI",
        "version_cmd": "codex --version",
        "docs_url": "https://github.com/openai/codex",
        "category": "ai-agent",
        "importance": "optional",
    },
    {
        "id": "warp",
        "name": "Warp Terminal",
        "version_cmd": "/Applications/Warp.app/Contents/MacOS/Warp --version 2>/dev/null || echo 'check via plist'",
        "docs_url": "https://docs.warp.dev",
        "category": "terminal",
        "importance": "optional",
    },
    {
        "id": "zed",
        "name": "Zed IDE",
        "version_cmd": "zed --version 2>/dev/null || echo 'check via app'",
        "docs_url": "https://zed.dev/docs",
        "category": "editor",
        "importance": "optional",
    },
    {
        "id": "anythingllm",
        "name": "AnythingLLM",
        "version_cmd": "cat ~/Library/Application\\ Support/anythingllm-desktop/package.json 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"version\",\"?\"))' 2>/dev/null",
        "docs_url": "https://docs.anythingllm.com",
        "category": "rag",
        "importance": "core",
    },
    {
        "id": "obsidian",
        "name": "Obsidian",
        "version_cmd": "mdls -name kMDItemVersion /Applications/Obsidian.app 2>/dev/null | head -1",
        "docs_url": "https://help.obsidian.md",
        "category": "knowledge",
        "importance": "optional",
    },
    {
        "id": "azure-cli",
        "name": "Azure CLI",
        "version_cmd": "az version 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"azure-cli\",\"?\"))' 2>/dev/null",
        "docs_url": "https://learn.microsoft.com/en-us/cli/azure/",
        "category": "cloud",
        "importance": "optional",
    },
    {
        "id": "nuclei",
        "name": "Nuclei (security)",
        "version_cmd": "~/bin/nuclei -version 2>/dev/null || nuclei -version 2>/dev/null || echo 'not found'",
        "docs_url": "https://docs.projectdiscovery.io/tools/nuclei/",
        "category": "security",
        "importance": "optional",
    },
    {
        "id": "semgrep",
        "name": "Semgrep (security)",
        "version_cmd": "semgrep --version 2>/dev/null || echo 'not found'",
        "docs_url": "https://semgrep.dev/docs/",
        "category": "security",
        "importance": "optional",
    },
]


# ═══════════════════════════════════════════════════════════
# ФУНКЦИИ
# ═══════════════════════════════════════════════════════════

def get_version(product: dict) -> str:
    """Получить версию продукта."""
    try:
        result = subprocess.run(
            product["version_cmd"],
            capture_output=True, text=True, timeout=10
        )
        version = result.stdout.strip().split("\n")[0]
        # Очистка от мусора
        version = re.sub(r'[^\w\.\-\:\/ ]', '', version)[:50]
        return version if version else "unknown"
    except Exception:
        return "error"


def check_for_updates(product: dict) -> dict:
    """Проверить есть ли обновления (через npm/gh/pip)."""
    pid = product["id"]
    updates = {}

    if pid in ["goose", "codex"]:
        try:
            pkg = "@github/copilot" if pid == "copilot" else "@github/copilot"
            result = subprocess.run(
                ["npm", "outdated", "-g", pid],
                capture_output=True, text=True, timeout=15
            )
            updates["npm"] = "update available" if result.returncode == 0 else "latest"
        except Exception:
            pass

    elif pid in ["ollama"]:
        try:
            result = subprocess.run(
                ["brew", "outdated", "ollama"],
                capture_output=True, text=True, timeout=15
            )
            updates["brew"] = "update available" if result.stdout.strip() else "latest"
        except Exception:
            pass

    return updates


def collect_tool_info() -> dict:
    """Собрать информацию о всех установленных инструментах."""
    tools = {}

    for product in PRODUCTS:
        version = get_version(product)
        updates = check_for_updates(product)

        tools[product["id"]] = {
            "name": product["name"],
            "version": version,
            "category": product["category"],
            "importance": product["importance"],
            "docs_url": product["docs_url"],
            "updates_available": updates,
            "last_check": datetime.now().isoformat(),
        }

    return tools


def generate_doc_report(tools: dict) -> str:
    """Сгенерировать Markdown отчёт."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# 📚 Документация и версии продуктов

**Обновлено:** {now}
**Монитор:** doc_monitor.py (автоматически)

---

## AI Агенты

| Продукт | Версия | Статус | Документация |
|---|---|---|---|
"""

    # AI Agents
    for pid, info in tools.items():
        if info["category"] == "ai-agent":
            status = "✅" if info["version"] != "not found" else "❌"
            md += f"| {info['name']} | {info['version']} | {status} | [docs]({info['docs_url']}) |\n"

    md += """
## Инфраструктура

| Продукт | Версия | Категория | Документация |
|---|---|---|---|
"""

    for pid, info in tools.items():
        if info["category"] in ["terminal", "editor", "rag", "knowledge"]:
            status = "✅" if info["version"] != "not found" else "❌"
            md += f"| {info['name']} | {info['version']} | {info['category']} | [docs]({info['docs_url']}) |\n"

    md += """
## Cloud & Security

| Продукт | Версия | Категория | Документация |
|---|---|---|---|
"""

    for pid, info in tools.items():
        if info["category"] in ["cloud", "security"]:
            status = "✅" if info["version"] not in ["not found", "error"] else "❌"
            md += f"| {info['name']} | {info['version']} | {info['category']} | [docs]({info['docs_url']}) |\n"

    md += f"""
---

## Команды быстрого доступа

| Команда | Что делает |
|---|---|
| `d` | Запустить систему |
| `ds` | Остановить |
| `dt` | Статус |
| `c` | Контекст |
| `cb` | Кратко |
| `ce` | Ошибки |
| `ct` | Задачи |
| `i [тема]` | Изучить контекст |
| `s [имя]` | Сохранить чат |
| `q "вопрос"` | RAG поиск |
| `h` | Шпаргалка |
| `m` | Модули |
| `ma [тип]` | Доступный агент |
| `mf` | Fallback цепи |

## Префикс-команды (для агентов)

| Префикс | Что делает |
|---|---|
| `@s` | Сохранить |
| `@q` | RAG поиск |
| `@e` | Ошибка |
| `@t` | Задача |
| `@p` | План |
| `@r` | Результат |
| `@a` | Аудит |
| `@i` | Изучить контекст |
| `@h` | Шпаргалка |

---

*Сгенерировано автоматически: doc_monitor.py*
"""

    return md


def save_report(md: str, tools: dict):
    """Сохранить отчёт и синхронизировать."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    # 1. Markdown файл
    md_file = os.path.join(REF_DIR, "PRODUCT_DOCS.md")
    with open(md_file, "w") as f:
        f.write(md)

    # 2. JSON с метаданными
    json_file = os.path.join(REF_DIR, "product_versions.json")
    with open(json_file, "w") as f:
        json.dump({
            "updated": datetime.now().isoformat(),
            "products": tools,
            "total_products": len(tools),
        }, f, indent=2)

    # 3. Копия в AnythingLLM hotdir
    import shutil
    try:
        shutil.copy2(md_file, os.path.join(ATLLM_HOTDIR, f"product_docs_{timestamp}.md"))
    except Exception:
        pass

    # 4. Лог
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] Documentation updated: {len(tools)} products\n")

    return md_file


def check_for_changes() -> list:
    """Проверить что изменилось с последнего запуска."""
    changes = []
    json_file = os.path.join(REF_DIR, "product_versions.json")

    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            old_data = json.load(f)

        old_products = old_data.get("products", {})

        for product in PRODUCTS:
            pid = product["id"]
            old_version = old_products.get(pid, {}).get("version", "unknown")
            new_version = get_version(product)

            if old_version != new_version:
                changes.append({
                    "product": product["name"],
                    "old_version": old_version,
                    "new_version": new_version,
                    "changed": True,
                })

    return changes


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def run_monitor():
    """Основной цикл мониторинга."""
    print("📚 Doc Monitor — запуск...")
    print(f"   Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Продуктов: {len(PRODUCTS)}")
    print()

    # Проверяем изменения
    changes = check_for_changes()
    if changes:
        print(f"🔄 Изменения обнаружены:")
        for c in changes:
            print(f"   {c['product']}: {c['old_version']} → {c['new_version']}")
    else:
        print("✅ Изменений нет (или первый запуск)")

    # Собираем информацию
    tools = collect_tool_info()

    # Генерируем отчёт
    md = generate_doc_report(tools)

    # Сохраняем
    md_file = save_report(md, tools)

    # Выводим результат
    print()
    print(f"💾 Сохранено: {md_file}")
    print(f"📊 Продуктов: {len(tools)}")
    if changes:
        print(f"🔄 Изменений: {len(changes)}")
    print()

    # Краткий статус
    print("Статус продуктов:")
    for pid, info in tools.items():
        icon = "✅" if info["version"] not in ["not found", "error", "unknown"] else "❌"
        print(f"  {icon} {info['name']:<25} {info['version']}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--changes":
        changes = check_for_changes()
        if changes:
            for c in changes:
                print(f"{c['product']}: {c['old_version']} → {c['new_version']}")
        else:
            print("No changes detected")
    else:
        run_monitor()
