#!/usr/bin/env python3.11
"""
security_scout.py — Фоновый агент мониторинга безопасности

Задачи:
  1. Мониторинг huntr.com — новые баг баунти, изменения
  2. CVE мониторинг — новые уязвимости в популярных проектах
  3. Tool watch — обновления security инструментов
  4. Threat intel — новые техники атак, Shellshock-подобные
  5. Research monitoring — новые papers, техники

Режимы:
  --daemon  → фоновый режим (запуск через dev start)
  --once    → один проход
  --status  → статус мониторинга

Работает тихо, минимум ресурсов, сохраняет в KB.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

KB_DIR = os.path.expanduser("~/project/knowledge_base")
INTEL_DIR = os.path.expanduser("~/project/intel")
SCOUT_DATA = os.path.join(INTEL_DIR, "scout_data")
LOG_FILE = os.path.join(SCOUT_DATA, "security_scout.log")
ATLLM_HOTDIR = os.path.expanduser(
    "~/Library/Application Support/anythingllm-desktop/storage/hotdir"
)

for d in [SCOUT_DATA, os.path.join(SCOUT_DATA, "findings"), ATLLM_HOTDIR]:
    os.makedirs(d, exist_ok=True)

# API ключи (если есть)
OPENROUTER_API_KEY = ""  # Можно взять из Keychain
GEMINI_API_KEY = ""      # Для поиска через Gemini CLI

# Цели мониторининга
MONITOR_TARGETS = {
    "huntr_bounties": {
        "enabled": True,
        "interval_hours": 4,  # Проверять каждые 4 часа
        "description": "Новые bug bounty на huntr.com",
    },
    "cve_watch": {
        "enabled": True,
        "interval_hours": 6,
        "description": "Новые CVE в популярных проектах",
    },
    "tool_updates": {
        "enabled": True,
        "interval_hours": 12,
        "description": "Обновления security инструментов",
    },
    "threat_intel": {
        "enabled": True,
        "interval_hours": 8,
        "description": "Новые техники атак, уязвимости",
    },
    "research_papers": {
        "enabled": True,
        "interval_hours": 24,
        "description": "Новые исследования по AI security",
    },
}

# Проекты для CVE мониторинга
CVE_PROJECTS = [
    "express", "django", "flask", "fastapi",
    "react", "vue", "angular",
    "numpy", "pandas", "tensorflow", "pytorch",
    "requests", "urllib3", "openssl",
    "docker", "kubernetes", "nginx",
    "linux", "apache", "postgresql",
]

# Инструменты для мониторинга обновлений
SECURITY_TOOLS = [
    "nuclei", "subfinder", "httpx", "ffuf",
    "semgrep", "bandit", "trufflehog",
    "sqlmap", "nmap", "masscan",
    "metasploit", "burpsuite",
]


# ═══════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════

def log(message: str):
    """Логирование."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def save_finding(category: str, title: str, content: str, url: str = ""):
    """Сохранить находку + авто-копия в AnythingLLM hotdir."""
    finding = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "title": title,
        "content": content[:5000],
        "url": url,
    }

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{category}_{ts}.json"
    filepath = os.path.join(SCOUT_DATA, "findings", filename)

    with open(filepath, "w") as f:
        json.dump(finding, f, indent=2)

    # Копия в KB results
    kb_finding = os.path.join(KB_DIR, "results", f"scout_{filename.replace('.json', '.md')}")
    os.makedirs(os.path.dirname(kb_finding), exist_ok=True)
    with open(kb_finding, "w") as f:
        f.write(f"# 🔍 Scout: {title}\n\n**Категория:** {category}\n**Время:** {finding['timestamp']}\n\n{content}\n")

    # Копия в AnythingLLM hotdir (автоматическая индексация!)
    try:
        import shutil
        atllm_hot = os.path.join(ATLLM_HOTDIR, f"scout_{filename.replace('.json', '.md')}")
        shutil.copy2(kb_finding, atllm_hot)
    except Exception:
        pass

    log(f"💾 Находка сохранена: {title}")


def load_state() -> dict:
    """Загрузить состояние (что уже видели)."""
    state_file = os.path.join(SCOUT_DATA, "state.json")
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"seen": {}, "last_check": {}}


def save_state(state: dict):
    """Сохранить состояние."""
    state_file = os.path.join(SCOUT_DATA, "state.json")
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def should_check(category: str, interval_hours: int, state: dict) -> bool:
    """Проверить нужно ли проверять эту категорию."""
    last = state.get("last_check", {}).get(category, "")
    if not last:
        return True

    try:
        last_time = datetime.fromisoformat(last)
        return datetime.now() - last_time >= timedelta(hours=interval_hours)
    except Exception:
        return True


def web_search(query: str) -> str:
    """Поиск через Gemini CLI (если доступен)."""
    try:
        cmd = [
            "gemini", "-p",
            f"Search the web for: {query}. Return top 5 results with title, URL, and brief description.",
            "--yolo",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def fetch_url(url: str, timeout: int = 10) -> str:
    """Скачать URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SecurityScout/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
# МОНИТОРЫ
# ═══════════════════════════════════════════════════════════

def monitor_huntr(state: dict) -> dict:
    """Мониторинг huntr.com — новые bug bounty."""
    log("🔍 Проверка huntr.com...")

    # huntr API для последних баунти
    url = "https://api.huntr.com/bounties?limit=10&sort=latest"
    html = fetch_url(url)

    findings = []
    if html:
        try:
            data = json.loads(html)
            for bounty in data.get("bounties", [])[:5]:
                title = bounty.get("title", "")
                seen = state.get("seen", {}).get("huntr", [])
                if title not in seen:
                    findings.append({
                        "title": f"huntr: {title}",
                        "content": f"New bounty: {bounty.get('description', '')[:500]}",
                        "url": f"https://huntr.com/bounties/{bounty.get('id', '')}",
                    })
                    seen.append(title)
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: поиск через Gemini
    if not findings:
        result = web_search("site:huntr.com latest bug bounty 2026")
        if result and "not found" not in result.lower():
            findings.append({
                "title": "huntr: новые баунти (Gemini search)",
                "content": result[:1000],
                "url": "https://huntr.com",
            })

    state.setdefault("seen", {})["huntr"] = state.get("seen", {}).get("huntr", [])[-50:]
    state["last_check"]["huntr_bounties"] = datetime.now().isoformat()

    return findings


def monitor_cve(state: dict) -> dict:
    """CVE мониторинг — через NVD API."""
    log("🔍 Проверка новых CVE...")

    findings = []
    seen = state.get("seen", {}).get("cve", [])

    # Проверяем NVD API за последние 24 часа
    end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    start_date = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")

    for project in CVE_PROJECTS[:5]:  # Проверяем 5 проектов за раз
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={project}&lastModStartDate={start_date}&lastModEndDate={end_date}&resultsPerPage=3"
        try:
            html = fetch_url(url, timeout=15)
            if html:
                data = json.loads(html)
                for vuln in data.get("vulnerabilities", [])[:2]:
                    cve_id = vuln.get("cve", {}).get("id", "")
                    if cve_id and cve_id not in seen:
                        desc = vuln.get("cve", {}).get("descriptions", [{}])[0].get("value", "")[:300]
                        findings.append({
                            "title": f"CVE: {cve_id} ({project})",
                            "content": desc,
                            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                        })
                        seen.append(cve_id)
        except Exception:
            pass

        time.sleep(1)  # Rate limit

    state.setdefault("seen", {})["cve"] = seen[-100:]  # Храним последние 100
    state["last_check"]["cve_watch"] = datetime.now().isoformat()

    return findings


def monitor_tool_updates(state: dict) -> dict:
    """Мониторинг обновлений security инструментов."""
    log("🔍 Проверка обновлений инструментов...")

    findings = []
    seen = state.get("seen", {}).get("tools", [])

    # Проверяем GitHub releases
    for tool in SECURITY_TOOLS[:5]:
        url = f"https://api.github.com/repos/projectdiscovery/{tool}/releases/latest"
        # Попробуем разные репозитории
        repos = [
            f"https://api.github.com/repos/projectdiscovery/{tool}/releases/latest",
            f"https://api.github.com/repos/returntocorp/{tool}/releases/latest",
            f"https://api.github.com/repos/{tool}/{tool}/releases/latest",
        ]

        for repo_url in repos:
            try:
                html = fetch_url(repo_url, timeout=10)
                if html:
                    data = json.loads(html)
                    version = data.get("tag_name", "")
                    key = f"{tool}:{version}"
                    if version and key not in seen:
                        findings.append({
                            "title": f"Tool Update: {tool} {version}",
                            "content": data.get("name", "")[:500],
                            "url": data.get("html_url", ""),
                        })
                        seen.append(key)
                        break
            except Exception:
                continue

        time.sleep(0.5)

    state.setdefault("seen", {})["tools"] = seen[-50:]
    state["last_check"]["tool_updates"] = datetime.now().isoformat()

    return findings


def monitor_threat_intel(state: dict) -> dict:
    """Мониторинг новых техник атак."""
    log("🔍 Проверка threat intelligence...")

    findings = []

    # Поиск новых техник через Gemini
    queries = [
        "new critical vulnerability 2026 CVE like Shellshock Log4j",
        "latest AI security attack technique 2026",
        "new zero-day exploit discovered 2026",
    ]

    for query in queries:
        result = web_search(query)
        if result and len(result) > 50:
            findings.append({
                "title": f"Threat Intel: {query[:50]}",
                "content": result[:1000],
                "url": "",
            })
        time.sleep(2)

    state["last_check"]["threat_intel"] = datetime.now().isoformat()

    return findings


def monitor_research(state: dict) -> dict:
    """Мониторинг исследований по AI security."""
    log("🔍 Проверка исследований...")

    findings = []

    queries = [
        "AI agent security research paper 2026",
        "multi-agent system vulnerability research",
        "LLM prompt injection new technique 2026",
    ]

    for query in queries:
        result = web_search(f"site:arxiv.org OR site:github.com {query}")
        if result and len(result) > 50:
            findings.append({
                "title": f"Research: {query[:50]}",
                "content": result[:1000],
                "url": "",
            })
        time.sleep(2)

    state["last_check"]["research_papers"] = datetime.now().isoformat()

    return findings


# ═══════════════════════════════════════════════════════════
# ГЛАВНЫЙ ЦИКЛ
# ═══════════════════════════════════════════════════════════

def run_cycle():
    """Один цикл мониторинга."""
    log("🔍 Security Scout — цикл мониторинга")
    log("=" * 50)

    state = load_state()
    all_findings = []

    monitors = [
        ("huntr_bounties", MONITOR_TARGETS["huntr_bounties"], monitor_huntr),
        ("cve_watch", MONITOR_TARGETS["cve_watch"], monitor_cve),
        ("tool_updates", MONITOR_TARGETS["tool_updates"], monitor_tool_updates),
        ("threat_intel", MONITOR_TARGETS["threat_intel"], monitor_threat_intel),
        ("research_papers", MONITOR_TARGETS["research_papers"], monitor_research),
    ]

    for name, config, func in monitors:
        if not config.get("enabled", True):
            continue

        if not should_check(name, config.get("interval_hours", 24), state):
            continue

        try:
            findings = func(state)
            all_findings.extend(findings)
            for f in findings:
                save_finding(name, f["title"], f["content"], f.get("url", ""))
        except Exception as e:
            log(f"❌ Ошибка монитора {name}: {e}")

    save_state(state)

    log(f"📊 Найдено: {len(all_findings)} новых записей")
    log("=" * 50)

    return all_findings


def run_daemon():
    """Фоновый режим — запускается с dev start."""
    log("🔍 Security Scout — фоновый режим")
    log("   Интервал: 2 часа")
    log("   Для ручного запуска: scout.py --once")

    while True:
        try:
            run_cycle()
        except Exception as e:
            log(f"❌ Ошибка цикла: {e}")

        # Ждём 2 часа
        time.sleep(7200)


def show_status():
    """Показать статус мониторинга."""
    state = load_state()

    print("\n🔍 Security Scout — Статус")
    print("=" * 50)

    for name, config in MONITOR_TARGETS.items():
        last = state.get("last_check", {}).get(name, "never")
        enabled = "✅" if config.get("enabled") else "❌"
        print(f"  {enabled} {name:<25} last: {last}")

    seen_count = sum(len(v) for v in state.get("seen", {}).values())
    print(f"\n  Всего отслежено: {seen_count} записей")

    # Последние находки
    findings_dir = os.path.join(SCOUT_DATA, "findings")
    if os.path.isdir(findings_dir):
        recent = sorted(os.listdir(findings_dir), reverse=True)[:5]
        if recent:
            print(f"\n  Последние находки:")
            for f in recent:
                filepath = os.path.join(findings_dir, f)
                with open(filepath, "r") as fh:
                    data = json.load(fh)
                    print(f"    📄 {data.get('title', f)[:60]}")

    print("=" * 50)


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--daemon":
            run_daemon()
        elif cmd == "--once":
            run_cycle()
        elif cmd == "--status":
            show_status()
        else:
            print("Использование: scout.py [--daemon|--once|--status]")
    else:
        show_status()
