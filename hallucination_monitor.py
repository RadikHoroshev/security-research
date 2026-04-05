#!/usr/bin/env python3
"""
hallucination_monitor.py — Система контроля сбоев и галлюцинаций

Принцип:
  1. Каждый агент проверяет результат другого
  2. При подозрении → ALERT в шину
  3. 2+ ALERT от разных агентов → карантин (5 мин)
  4. По истечении → проверка → recover или extended quarantine

Запуск:
  python3 intel/hallucination_monitor.py --watch    # фоновый мониторинг
  python3 intel/hallucination_monitor.py --report   # отчёт по агентам
  python3 intel/hallucination_monitor.py --check    # проверка карантина
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PROTOCOL = ROOT / "intel" / "protocol.py"
QUARANTINE_FILE = ROOT / "intel" / "quarantine.json"
MONITOR_LOG = ROOT / "knowledge_base" / "hallucination_monitor.log"

KNOWN_AGENTS = {
    "qwen": {"type": "cli", "check": ["qwen", "--version"]},
    "gemini": {"type": "cli", "check": ["gemini", "--version"]},
    "codex": {"type": "cli", "check": ["codex", "--version"]},
    "jules": {"type": "cli", "check": ["jules", "remote", "list", "--session"]},
    "goose": {"type": "orchestrator", "check": ["goose", "--version"]},
    "ollama": {"type": "api", "check": ["curl", "-s", "-o", "/dev/null", "-w", "200", "http://localhost:11434"]},
    "anythingllm": {"type": "api", "check": ["curl", "-s", "-o", "/dev/null", "-w", "200", "http://localhost:3001"]},
    "opencode": {"type": "ide", "check": ["curl", "-s", "-o", "/dev/null", "-w", "200", "http://localhost:4096"]},
    "warp": {"type": "ide", "check": ["test", "-f", "/Users/code/project/.env.warp"]},
    "kiro": {"type": "ide", "check": ["test", "-d", "/Users/code/.kiro"]},
    "copilot": {"type": "cli", "check": ["gh", "copilot", "suggest", "--help"]},
}

def check_health(agent: str) -> bool:
    """Проверить здоровье агента."""
    cfg = KNOWN_AGENTS.get(agent)
    if not cfg:
        return True
    try:
        r = subprocess.run(cfg["check"], capture_output=True, timeout=10)
        return r.returncode == 0
    except:
        return False

def check_all() -> dict:
    """Проверить все агенты."""
    status = {}
    for name in KNOWN_AGENTS:
        status[name] = "online" if check_health(name) else "offline"
    return status

def auto_quarantine(sick_agents: list):
    """Поместить offline агентов в карантин."""
    for agent in sick_agents:
        subprocess.run(
            ["python3", str(PROTOCOL), "quarantine", agent, "health check failed", "300"],
            capture_output=True
        )
        _log(f"🔒 {agent} → quarantine (health check failed)")

def auto_recover(freed_agents: list):
    """Восстановить агентов из карантина."""
    for agent in freed_agents:
        if check_health(agent):
            subprocess.run(
                ["python3", str(PROTOCOL), "send",
                 json.dumps({"t":"RECOVER","agent":agent,"ts":int(time.time())}, separators=(",",":"))],
                capture_output=True
            )
            _log(f"✅ {agent} → recovered")
        else:
            subprocess.run(
                ["python3", str(PROTOCOL), "quarantine", agent, "health check still failing", "600"],
                capture_output=True
            )
            _log(f"🔒 {agent} → extended quarantine (still sick)")

def run_cycle():
    """Один цикл мониторинга."""
    # 1. Проверяем здоровье
    health = check_all()
    sick = [a for a, s in health.items() if s == "offline"]

    # 2. Проверяем карантин
    result = subprocess.run(
        ["python3", str(PROTOCOL), "check"],
        capture_output=True, text=True
    )
    quarantined = []
    if "Sick agents:" in result.stdout:
        quarantined = result.stdout.split("Sick agents: ")[1].strip().split(", ")

    # 3. Новые sick → карантин
    new_sick = [a for a in sick if a not in quarantined]
    if new_sick:
        auto_quarantine(new_sick)

    # 4. Freed из карантина → проверить
    freed_result = subprocess.run(
        ["python3", str(PROTOCOL), "check"],
        capture_output=True, text=True
    )

    # 5. Статус в шину
    status_msg = subprocess.run(
        ["python3", str(PROTOCOL), "send",
         json.dumps({"t":"STATUS","from":"monitor","agents":health,"ts":int(time.time())}, separators=(",",":"))],
        capture_output=True, text=True
    )

    return health, sick, quarantined

def print_report():
    """Отчёт по всем агентам."""
    health = check_all()
    print(f"\n{'='*60}")
    print(f"🏥 Agent Health Report — {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    print(f"{'='*60}")

    for name in sorted(health):
        icon = "✅" if health[name] == "online" else "❌"
        cfg = KNOWN_AGENTS.get(name, {})
        print(f"  {icon} {name:15s} {health[name]:10s} ({cfg.get('type', '?')})")

    # Карантин
    q_result = subprocess.run(["python3", str(PROTOCOL), "check"], capture_output=True, text=True)
    if "Sick agents:" in q_result.stdout:
        sick = q_result.stdout.split("Sick agents: ")[1].strip()
        print(f"\n  🔒 Quarantined: {sick}")
    else:
        print(f"\n  ✅ No agents in quarantine")

    print(f"{'='*60}")

def _log(msg: str):
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_LOG, "a") as f:
        f.write(f"[{datetime.utcnow().isoformat()}Z] {msg}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 hallucination_monitor.py --check    # check quarantine")
        print("  python3 hallucination_monitor.py --report   # health report")
        print("  python3 hallucination_monitor.py --cycle    # single monitoring cycle")
        print("  python3 hallucination_monitor.py --watch    # continuous (every 60s)")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "--check":
        subprocess.run(["python3", str(PROTOCOL), "check"])
    elif cmd == "--report":
        print_report()
    elif cmd == "--cycle":
        health, sick, q = run_cycle()
        print(f"Health: {sum(1 for v in health.values() if v=='online')}/{len(health)} online")
        if sick: print(f"Sick: {sick}")
    elif cmd == "--watch":
        print("🏥 Hallucination Monitor — watching every 60s")
        while True:
            run_cycle()
            time.sleep(60)
