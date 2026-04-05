#!/usr/bin/env python3
"""
queue_watcher.py — Auto-dispatcher for agent task queue

Микро-модуль который:
1. Мониторит intel/queue/ на новые JSON файлы
2. При появлении задачи — логирует и оповещает
3. Отмечает выполненные задачи
4. Работает как демон

Запуск:
  python3 intel/queue_watcher.py --daemon [interval_sec]
  python3 intel/queue_watcher.py --check          # Разовая проверка
  python3 intel/queue_watcher.py --status         # Статус очереди
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
QUEUE_DIR = PROJECT_ROOT / "intel" / "queue"
RESULTS_DIR = PROJECT_ROOT / "intel" / "results"
WATCHER_LOG = PROJECT_ROOT / "knowledge_base" / "queue_watcher.log"
STATE_FILE = PROJECT_ROOT / "var" / "run" / "queue_state.json"

# ═══════════════════════════════════════════════════════════
# QUEUE MONITOR
# ═══════════════════════════════════════════════════════════

def get_queue_status():
    """Получить статус всех задач в очереди."""
    if not QUEUE_DIR.exists():
        return {"error": "Queue directory not found"}

    tasks = []
    for f in sorted(QUEUE_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            tasks.append({
                "file": f.name,
                "id": data.get("task_id", data.get("id", f.stem)),
                "type": data.get("type", data.get("task_type", "unknown")),
                "status": data.get("status", "pending"),
                "assigned_to": data.get("assigned_agent", data.get("assigned_to", "unassigned")),
                "priority": data.get("priority", "medium"),
                "created": data.get("created_at", "unknown"),
                "description": (data.get("description", data.get("task", "")) or "")[:80]
            })
        except (json.JSONDecodeError, KeyError):
            tasks.append({
                "file": f.name,
                "status": "invalid",
                "description": "Invalid JSON"
            })

    return {
        "total": len(tasks),
        "pending": sum(1 for t in tasks if t.get("status") in ("pending", "unassigned")),
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "completed": sum(1 for t in tasks if t.get("status") in ("completed", "success")),
        "failed": sum(1 for t in tasks if t.get("status") == "failed"),
        "tasks": tasks,
        "checked_at": datetime.utcnow().isoformat() + "Z"
    }


def print_status():
    """Красивый вывод статуса очереди."""
    status = get_queue_status()
    if "error" in status:
        print(f"❌ {status['error']}")
        return

    print(f"\n{'='*60}")
    print(f"📋 QUEUE STATUS — {status['checked_at'][:19]}")
    print(f"{'='*60}")
    print(f"  Total: {status['total']} | Pending: {status['pending']} | In Progress: {status['in_progress']} | Done: {status['completed']} | Failed: {status['failed']}")
    print(f"{'='*60}")

    for t in status.get("tasks", []):
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "success": "✅", "failed": "❌", "invalid": "⚠️"}.get(t.get("status", "?"), "?")
        agent = t.get("assigned_to", "?")
        desc = t.get("description", t.get("file", ""))[:60]
        print(f"  {status_icon} [{t.get('priority', '?')}] {desc}")
        print(f"     Agent: {agent} | Status: {t.get('status', '?')}")

    print(f"{'='*60}\n")


def check_new_tasks():
    """Проверить новые задачи с последней проверки."""
    state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
        except:
            state = {}

    known = set(state.get("known_files", []))
    new_tasks = []

    if QUEUE_DIR.exists():
        for f in QUEUE_DIR.glob("*.json"):
            if f.name not in known:
                new_tasks.append(f.name)

    if new_tasks:
        print(f"  🆕 {len(new_tasks)} new task(s):")
        for t in new_tasks:
            print(f"    📄 {t}")
            _log_event("NEW_TASK", t)

        known.update(new_tasks)
        state["known_files"] = list(known)
        state["last_check"] = datetime.utcnow().isoformat() + "Z"

        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    return new_tasks


def _log_event(event: str, details: str):
    """Записать событие в лог."""
    try:
        WATCHER_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(WATCHER_LOG, "a") as f:
            f.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {event}: {details}\n")
    except:
        pass


def run_daemon(interval: int = 30):
    """Фоновый режим."""
    print(f"📋 Queue Watcher starting (check every {interval}s)")
    print(f"   Queue: {QUEUE_DIR}")
    print(f"   Log: {WATCHER_LOG}")

    # Initial check
    check_new_tasks()

    try:
        while True:
            new = check_new_tasks()
            if new:
                print_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n  🛑 Queue Watcher stopped")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python3 queue_watcher.py --daemon [interval_sec]  # Background monitoring")
        print(f"  python3 queue_watcher.py --check                   # Check for new tasks")
        print(f"  python3 queue_watcher.py --status                  # Full queue status")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "--daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        run_daemon(interval)
    elif cmd == "--check":
        new = check_new_tasks()
        if not new:
            print("  ℹ️  No new tasks")
        else:
            print_status()
    elif cmd == "--status":
        print_status()
