#!/usr/bin/env python3
"""
kb_sync_daemon.py — Auto-Logger + Auto-Sync for Knowledge Base

Микро-модуль который:
1. Логирует ВСЕ действия агентов автоматически
2. Синхронизирует новые файлы в AnythingLLM
3. Ведёт журнал ошибок с решениями
4. Работает как демон в фоне

Запуск:
  python3 intel/kb_sync_daemon.py --daemon     # Фоновый режим
  python3 intel/kb_sync_daemon.py --sync       # Разовый sync
  python3 intel/kb_sync_daemon.py --log "msg"  # Записать лог
"""

import json
import os
import sys
import time
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
ATLLM_STORAGE = Path.home() / "Library/Application Support/anythingllm-desktop/storage/documents/custom-documents"
ATLLM_HOTDIR = Path.home() / "Library/Application Support/anythingllm-desktop/storage/hotdir"
ACTIONS_DIR = KB_DIR / "agent_actions"
SESSIONS_DIR = KB_DIR / "sessions"
ERROR_JOURNAL = KB_DIR / "error_solutions/ERROR_LOG.md"
SYNC_LOG = KB_DIR / "sync.log"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

ANYTHINGLLM_API = "http://localhost:3001/api/v1"
ANYTHINGLLM_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "9MMMM0Y-2YC4FGE-JD7VX41-5MY20RT")
WORKSPACE = "moya-rabochaya-oblast"

# ═══════════════════════════════════════════════════════════
# AUTO-LOGGER
# ═══════════════════════════════════════════════════════════

def log_action(agent: str, action: str, result: str = "", status: str = "success", tags: list = None):
    """Автоматически логирует действие агента."""
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent,
        "action": action,
        "result": result[:2000] if result else "",  # Limit size
        "status": status,
        "tags": tags or []
    }

    # Append to today's JSONL
    actions_file = ACTIONS_DIR / f"{TODAY}.jsonl"
    with open(actions_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Console output
    icon = {"success": "✅", "error": "❌", "warning": "⚠️"}.get(status, "ℹ️")
    print(f"  {icon} [{agent}] {action[:80]}")

    # Copy to AnythingLLM hotdir for indexing
    _copy_to_atllm_hotdir(entry)

    return entry


def _copy_to_atllm_hotdir(entry: dict):
    """Копирует запись в AnythingLLM hotdir для авто-индексации."""
    try:
        hash_id = hashlib.sha256(f"{entry['timestamp']}-{entry['agent']}".encode()).hexdigest()[:8]
        filename = f"action_{entry['agent']}_{hash_id}.md"
        filepath = ATLLM_HOTDIR / filename

        content = f"""# Agent Action — {entry['agent']}

**Time:** {entry['timestamp']}
**Action:** {entry['action']}
**Status:** {entry['status']}
**Result:** {entry['result'][:500]}
**Tags:** {', '.join(entry.get('tags', []))}
"""
        with open(filepath, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"  ⚠️ hotdir copy failed: {e}")


def start_session(agent: str, task: str, tags: list = None):
    """Начало сессии — создаёт session log."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_file = SESSIONS_DIR / f"{TODAY}_{datetime.utcnow().strftime('%H%M')}_{agent.replace(' ', '_')}.md"

    content = f"""# Session: {agent}

**Started:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC
**Task:** {task}
**Tags:** {', '.join(tags or [])}

---

## Actions

"""
    with open(session_file, "w") as f:
        f.write(content)

    log_action(agent, f"Session started: {task}", status="success", tags=tags or ["session_start"])
    return session_file


def append_to_session(session_file: Path, action: str, result: str):
    """Добавить действие в текущую сессию."""
    try:
        with open(session_file, "a") as f:
            f.write(f"### {datetime.utcnow().strftime('%H:%M:%S')} — {action}\n")
            f.write(f"{result[:1000]}\n\n")
    except:
        pass


def log_error(agent: str, error: str, context: str = "", solution: str = ""):
    """Записать ошибку в error journal."""
    ERROR_JOURNAL.parent.mkdir(parents=True, exist_ok=True)

    entry = f"""
---

## {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} | {error[:80]}

**Категория:** #{agent.replace(' ', '_').lower()}
**Severity:** MEDIUM
**Статус:** {'✅ Решено' if solution else '🔴 Открыто'}

### Проблема
{error}

### Контекст
{context}

### Решение
{solution or 'Ожидает решения...'}

### Как избежать
{'Добавить проверку...' if solution else 'TBD'}
"""
    with open(ERROR_JOURNAL, "a") as f:
        f.write(entry)

    log_action(agent, f"Error logged: {error[:50]}", error, "error", ["error", agent])


# ═══════════════════════════════════════════════════════════
# AUTO-SYNC
# ═══════════════════════════════════════════════════════════

def sync_kb_to_atllm(quick: bool = False):
    """Синхронизирует KB файлы в AnythingLLM storage."""
    if not ATLLM_STORAGE.exists():
        print(f"  ❌ AnythingLLM storage not found: {ATLLM_STORAGE}")
        return 0

    count = 0
    kb_files = list(KB_DIR.rglob("*.md")) + list(KB_DIR.rglob("*.jsonl"))

    for src in kb_files:
        if quick and _is_already_synced(src):
            continue

        rel = src.relative_to(KB_DIR)
        dest_name = f"{str(rel).replace('/', '_')}-{hashlib.sha256(str(src).encode()).hexdigest()[:8]}.json"
        dest = ATLLM_STORAGE / dest_name

        try:
            content = src.read_text()
            doc = {
                "title": src.name,
                "path": str(src),
                "content": content,
                "synced_at": datetime.utcnow().isoformat() + "Z"
            }
            dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
            count += 1
        except Exception as e:
            print(f"  ⚠️ Failed to sync {src.name}: {e}")

    if count > 0:
        _log_sync(f"Synced {count} files to AnythingLLM")
        print(f"  ✅ Synced {count} files → AnythingLLM")
    else:
        print(f"  ℹ️  No new files to sync")

    return count


def _is_already_synced(src: Path) -> bool:
    """Проверяет что файл уже скопирован (по mtime)."""
    mtime = src.stat().st_mtime
    for f in ATLLM_STORAGE.iterdir():
        if f.name.startswith(src.stem) and f.stat().st_mtime > mtime - 60:
            return True
    return False


def _log_sync(message: str):
    with open(SYNC_LOG, "a") as f:
        f.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


# ═══════════════════════════════════════════════════════════
# DAEMON MODE
# ═══════════════════════════════════════════════════════════

def run_daemon(sync_interval: int = 300):
    """Фоновый режим — проверяет изменения каждые N секунд."""
    print(f"📚 KB Sync Daemon starting (sync every {sync_interval}s)")
    print(f"   KB: {KB_DIR}")
    print(f"   AnythingLLM: {ATLLM_STORAGE}")

    last_sync = 0
    try:
        while True:
            now = time.time()
            if now - last_sync > sync_interval:
                synced = sync_kb_to_atllm()
                if synced > 0:
                    print(f"  📚 {synced} files synced at {datetime.utcnow().strftime('%H:%M:%S')}")
                last_sync = now
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n  🛑 KB Sync Daemon stopped")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python3 kb_sync_daemon.py --daemon [interval_sec]  # Background sync")
        print(f"  python3 kb_sync_daemon.py --sync [--quick]         # One-time sync")
        print(f"  python3 kb_sync_daemon.py --log 'message'           # Log action")
        print(f"  python3 kb_sync_daemon.py --error 'error'           # Log error")
        print(f"  python3 kb_sync_daemon.py --status                  # Show today's logs")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "--daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        run_daemon(interval)

    elif cmd == "--sync":
        quick = "--quick" in sys.argv
        sync_kb_to_atllm(quick=quick)

    elif cmd == "--log":
        msg = " ".join(sys.argv[2:])
        log_action("system", msg)

    elif cmd == "--error":
        msg = " ".join(sys.argv[2:])
        log_error("system", msg)

    elif cmd == "--status":
        actions_file = ACTIONS_DIR / f"{TODAY}.jsonl"
        if actions_file.exists():
            with open(actions_file) as f:
                lines = f.readlines()
            print(f"\n📊 Today's actions ({len(lines)} entries):\n")
            for line in lines[-20:]:
                entry = json.loads(line)
                icon = {"success": "✅", "error": "❌", "warning": "⚠️"}.get(entry["status"], "ℹ️")
                print(f"  {icon} {entry['timestamp']} [{entry['agent']}] {entry['action'][:70]}")
        else:
            print(f"No actions logged today ({TODAY})")
