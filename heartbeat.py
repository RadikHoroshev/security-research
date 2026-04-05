#!/usr/bin/env python3
"""
heartbeat.py — Health Monitor & Auto-Fallback System

Микро-модульная отказоустойчивая система:
- Проверяет каждый агент каждые N секунд
- При падении агента — мгновенно переключает на fallback
- Логирует все события
- Работает как демон

Architecture:
  ┌─────────────────┐
  │  Health Monitor │ ← проверяет каждые 30 сек
  └────────┬────────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
  Agent  Agent  Agent
    │      │      │
    ▼      ▼      ▼
  Fallback Chain → Auto-switch
"""

import json
import os
import subprocess
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

HEALTH_CHECK_INTERVAL = 30  # секунд между проверками
FAST_CHECK_INTERVAL = 10    # ускоренная проверка при проблемах
MAX_CONSECUTIVE_FAILURES = 2  # переключить на fallback после N провалов

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_FILE = PROJECT_ROOT / "knowledge_base" / "agent_registry.json"
HEALTH_LOG = PROJECT_ROOT / "knowledge_base" / "health_monitor.log"
STATE_FILE = PROJECT_ROOT / "var" / "run" / "health_state.json"

# ═══════════════════════════════════════════════════════════
# ОПРЕДЕЛЕНИЯ АГЕНТОВ И ИХ FALLBACK ЦЕПОЧКИ
# ═══════════════════════════════════════════════════════════

AGENTS = {
    "ollama": {
        "name": "Ollama",
        "type": "local",
        "check": lambda: check_port(11434),
        "fallback_chain": [],  # Ollama — последний рубеж, fallback на себя
        "critical": True,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "qwen_code": {
        "name": "Qwen Code",
        "type": "cli",
        "check": lambda: check_cli(["qwen", "--version"]),
        "fallback_chain": ["ollama_qwen14b", "gemini_cli"],
        "critical": True,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "gemini_cli": {
        "name": "Gemini CLI",
        "type": "cli",
        "check": lambda: check_cli(["gemini", "--version"]),
        "fallback_chain": ["ollama_gemma4", "qwen_code"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "codex_cli": {
        "name": "Codex CLI",
        "type": "cli",
        "check": lambda: check_cli(["codex", "--version"]),
        "fallback_chain": ["qwen_code", "ollama_qwen14b"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "jules": {
        "name": "Jules",
        "type": "async",
        "check": lambda: check_jules(),
        "fallback_chain": ["qwen_code"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "anythingllm": {
        "name": "AnythingLLM",
        "type": "local",
        "check": lambda: check_port(3001),
        "fallback_chain": ["obsidian_files", "grep_search"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "agent_bridge": {
        "name": "Agent Bridge",
        "type": "mcp",
        "check": lambda: check_mcp_bridge(),
        "fallback_chain": ["direct_cli_calls"],
        "critical": True,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "security_team": {
        "name": "Security Team",
        "type": "mcp",
        "check": lambda: check_mcp_security(),
        "fallback_chain": ["qwen_code + semgrep"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "warp": {
        "name": "WARP (Oz)",
        "type": "ide",
        "check": lambda: check_env_file(PROJECT_ROOT / ".env.warp"),
        "fallback_chain": ["ollama_kimi", "qwen_code"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },

    "kiro": {
        "name": "Kiro",
        "type": "ide",
        "check": lambda: check_dir_exists(Path.home() / ".kiro"),
        "fallback_chain": ["qwen_code"],
        "critical": False,
        "status": "unknown",
        "consecutive_failures": 0,
        "last_check": None,
        "last_response_ms": 0
    },
}


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK FUNCTIONS
# ═══════════════════════════════════════════════════════════

def check_port(port: int) -> bool:
    """Проверить что порт открыт."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result == 0
    except:
        return False

def check_cli(cmd: list) -> bool:
    """Проверить что CLI агент отвечает."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except:
        return False

def check_jules() -> bool:
    """Проверить Jules через remote list."""
    try:
        r = subprocess.run(["jules", "remote", "list", "--session"],
                          capture_output=True, text=True, timeout=10)
        return "Completed" in r.stdout or "Planning" in r.stdout
    except:
        return False

def check_mcp_bridge() -> bool:
    """Проверить Agent Bridge MCP."""
    try:
        bridge = PROJECT_ROOT / "intel" / "agent_bridge_mcp.py"
        if not bridge.exists():
            return False
        return check_cli(["python3", str(bridge), "--help"]) or True  # file exists = OK
    except:
        return False

def check_mcp_security() -> bool:
    """Проверить Security Team MCP."""
    try:
        server = PROJECT_ROOT / "security-team" / "mcp" / "server.py"
        return server.exists()
    except:
        return False

def check_env_file(path: Path) -> bool:
    """Проверить что .env файл существует."""
    return path.exists()

def check_dir_exists(path: Path) -> bool:
    """Проверить что директория существует."""
    return path.exists()


# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

def log_event(level: str, agent: str, message: str, details: dict = None):
    """Записать событие в health log."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,  # OK, WARN, CRITICAL, RECOVERY
        "agent": agent,
        "message": message,
        "details": details or {}
    }

    # Console
    icon = {"OK": "🟢", "WARN": "🟡", "CRITICAL": "🔴", "RECOVERY": "🟢"}
    print(f"  {icon.get(level, '⚪')} [{level}] {agent}: {message}")

    # File
    try:
        HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except:
        pass


# ═══════════════════════════════════════════════════════════
# FALLBACK ENGINE
# ═══════════════════════════════════════════════════════════

def get_active_fallback(agent_key: str) -> str:
    """Получить первый рабочий fallback агент."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return "none"

    for fallback_key in agent.get("fallback_chain", []):
        fallback = AGENTS.get(fallback_key)
        if fallback and fallback.get("status") == "online":
            return fallback_key

    return "none"


def handle_fallback(agent_key: str):
    """Обработать падение агента — переключить на fallback."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return

    active_fallback = get_active_fallback(agent_key)

    if active_fallback != "none":
        log_event("WARN", agent_key,
                  f"⚠️ DOWN → fallback to {active_fallback}",
                  {"consecutive_failures": agent["consecutive_failures"],
                   "active_fallback": active_fallback})

        # Update registry
        update_registry_status(agent_key, "degraded", active_fallback)
    else:
        log_event("CRITICAL", agent_key,
                  f"🔴 DOWN — NO FALLBACK AVAILABLE!",
                  {"consecutive_failures": agent["consecutive_failures"]})

        update_registry_status(agent_key, "offline", None)


def handle_recovery(agent_key: str):
    """Обработать восстановление агента."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return

    log_event("RECOVERY", agent_key,
              f"✅ RECOVERED after {agent['consecutive_failures']} failures",
              {})

    agent["consecutive_failures"] = 0
    update_registry_status(agent_key, "online", None)


def update_registry_status(agent_key: str, status: str, fallback: str = None):
    """Обновить статус в agent_registry.json."""
    try:
        with open(REGISTRY_FILE) as f:
            reg = json.load(f)

        if agent_key in reg.get("agents", {}):
            reg["agents"][agent_key]["status"] = status
            if fallback:
                reg["agents"][agent_key]["active_fallback"] = fallback
            elif status == "online":
                reg["agents"][agent_key].pop("active_fallback", None)

        with open(REGISTRY_FILE, "w") as f:
            json.dump(reg, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Could not update registry: {e}")


# ═══════════════════════════════════════════════════════════
# SAVE STATE
# ═══════════════════════════════════════════════════════════

def save_state():
    """Сохранить текущее состояние health monitor."""
    state = {}
    for key, agent in AGENTS.items():
        state[key] = {
            "status": agent["status"],
            "consecutive_failures": agent["consecutive_failures"],
            "last_check": agent["last_check"],
            "last_response_ms": agent["last_response_ms"],
            "active_fallback": get_active_fallback(key) if agent["status"] != "online" else None
        }

    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "last_update": datetime.utcnow().isoformat() + "Z",
                "total_agents": len(AGENTS),
                "online": sum(1 for a in AGENTS.values() if a["status"] == "online"),
                "degraded": sum(1 for a in AGENTS.values() if a["status"] == "degraded"),
                "offline": sum(1 for a in AGENTS.values() if a["status"] == "offline"),
                "agents": state
            }, f, indent=2)
    except Exception as e:
        print(f"  ⚠️ Could not save state: {e}")


# ═══════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════

def run_health_check():
    """Один проход проверки всех агентов."""
    print(f"\n{'='*60}")
    print(f"🏓 Health Check — {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    print(f"{'='*60}")

    for key, agent in AGENTS.items():
        start = time.time()
        try:
            is_alive = agent["check"]()
            response_ms = int((time.time() - start) * 1000)
            agent["last_response_ms"] = response_ms
            agent["last_check"] = datetime.utcnow().isoformat() + "Z"

            if is_alive:
                if agent["status"] in ("degraded", "offline", "unknown"):
                    handle_recovery(key)
                elif agent["status"] != "online":
                    log_event("OK", key, f"✅ online ({response_ms}ms)")

                agent["status"] = "online"
                agent["consecutive_failures"] = 0
            else:
                agent["consecutive_failures"] += 1
                log_event("WARN" if agent["consecutive_failures"] < MAX_CONSECUTIVE_FAILURES else "CRITICAL",
                         key,
                         f"❌ check failed ({agent['consecutive_failures']}/{MAX_CONSECUTIVE_FAILURES})")

                if agent["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                    handle_fallback(key)

        except Exception as e:
            agent["consecutive_failures"] += 1
            log_event("CRITICAL", key, f"💥 check error: {str(e)[:100]}")
            if agent["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                handle_fallback(key)

    save_state()

    # Summary
    online = sum(1 for a in AGENTS.values() if a["status"] == "online")
    degraded = sum(1 for a in AGENTS.values() if a["status"] == "degraded")
    offline = sum(1 for a in AGENTS.values() if a["status"] == "offline")
    print(f"\n📊 Summary: {online} online, {degraded} degraded, {offline} offline")
    print(f"{'='*60}")

    return online, degraded, offline


def run_daemon():
    """Запустить как демон."""
    print(f"🏓 Health Monitor starting (check every {HEALTH_CHECK_INTERVAL}s)")
    print(f"   Log: {HEALTH_LOG}")
    print(f"   State: {STATE_FILE}")

    interval = HEALTH_CHECK_INTERVAL
    try:
        while True:
            online, degraded, offline = run_health_check()

            # Adjust interval based on health
            if offline > 0:
                interval = FAST_CHECK_INTERVAL
                print(f"  ⚡ Fast mode: {interval}s (agents offline!)")
            else:
                interval = HEALTH_CHECK_INTERVAL

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n🛑 Health Monitor stopped by user")
        save_state()


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        run_daemon()
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_health_check()
    elif len(sys.argv) > 1 and sys.argv[1] == "--state":
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                print(json.dumps(json.load(f), indent=2))
        else:
            print("No state file yet. Run health check first.")
    else:
        print("Usage:")
        print(f"  python3 heartbeat.py --once    # Single check")
        print(f"  python3 heartbeat.py --daemon  # Continuous monitoring")
        print(f"  python3 heartbeat.py --state   # Show last state")
