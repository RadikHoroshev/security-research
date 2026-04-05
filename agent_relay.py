#!/usr/bin/env python3
"""
agent_relay.py — Reliable inter-agent communication via Goose

Принцип:
  1. Qwen кладёт задачу в intel/outbox/*.md
  2. agent_relay вызывает goose run -f task.md
  3. Результат сохраняется в intel/inbox/*.md
  4. Qwen читает результат из inbox/

Использует:
  - Goose run (non-interactive) → вызывает MCP → маршрутизирует к агентам
  - Файловый протокол → нет таймаутов, retry автоматический
"""

import json
import os
import subprocess
import time
import hashlib
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTBOX = PROJECT_ROOT / "intel" / "outbox"
INBOX = PROJECT_ROOT / "intel" / "inbox"
RELAY_LOG = PROJECT_ROOT / "knowledge_base" / "agent_relay.log"

# ═══════════════════════════════════════════════════════════
# RELAY
# ═══════════════════════════════════════════════════════════

def send_task(agent: str, task: str, timeout: int = 120):
    """Отправить задачу агенту через Goose.
    
    agent: имя целевого агента (gemini, copilot, codex, jules)
    task: описание задачи
    timeout: секунд на выполнение
    
    Returns: path to result file in inbox/
    """
    OUTBOX.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)
    
    # Создаём задачу
    task_id = hashlib.md5(f"{agent}-{task[:50]}-{time.time()}".encode()).hexdigest()[:8]
    task_file = OUTBOX / f"{agent}_{task_id}.md"
    
    content = f"""# Task for {agent.upper()}

**From:** Qwen Code
**Date:** {datetime.utcnow().isoformat()}Z
**Task ID:** {task_id}

## Instructions
{task}

## Required Output
Save your complete result to: intel/inbox/{agent}_result_{task_id}.md

Use this format:
```markdown
# {agent.upper()} Result — Task {task_id}

**Completed:** [timestamp]
**Status:** success/error

## Result
[your complete result here]
```

Execute all commands. Do not ask for confirmation.
"""
    task_file.write_text(content)
    
    # Запускаем Goose
    instruction = f"""
Read the task file at intel/outbox/{task_file.name}.
Execute ALL instructions in the task file.
You have access to MCP tools including agent_bridge.
Use the appropriate tool to complete the task.
Save the complete result to intel/inbox/{agent}_result_{task_id}.md
Do NOT ask for confirmation. Execute immediately.
"""
    
    _log(f"SENDING task {task_id} to {agent}")
    _log(f"  File: {task_file}")
    
    try:
        result = subprocess.run(
            ["goose", "run", "-t", instruction],
            capture_output=True, text=True, timeout=timeout
        )
        
        _log(f"  Goose exit code: {result.returncode}")
        
        # Проверяем результат
        inbox_files = list(INBOX.glob(f"{agent}_result_{task_id}*"))
        if inbox_files:
            _log(f"  ✅ Result received: {inbox_files[0].name}")
            return inbox_files[0]
        else:
            _log(f"  ⚠️ No result in inbox, saving goose output")
            result_file = INBOX / f"{agent}_result_{task_id}.md"
            result_file.write_text(f"""# {agent.upper()} Result — Task {task_id}

**Completed:** {datetime.utcnow().isoformat()}Z
**Status:** goose_completed

## Goose Output
{result.stdout[:5000]}

## Errors
{result.stderr[:2000]}
""")
            return result_file
            
    except subprocess.TimeoutExpired:
        _log(f"  ❌ Timeout after {timeout}s")
        error_file = INBOX / f"{agent}_error_{task_id}.md"
        error_file.write_text(f"# {agent.upper()} Error — Task {task_id}\n\n**Error:** Timeout after {timeout}s\n**Task:** {task[:200]}")
        return error_file
    except Exception as e:
        _log(f"  ❌ Exception: {e}")
        error_file = INBOX / f"{agent}_error_{task_id}.md"
        error_file.write_text(f"# {agent.upper()} Error — Task {task_id}\n\n**Error:** {str(e)}\n**Task:** {task[:200]}")
        return error_file


def read_result(filepath: Path) -> str:
    """Прочитать результат из inbox."""
    if filepath.exists():
        return filepath.read_text()
    return f"File not found: {filepath}"


def list_pending(agent: str = None) -> list:
    """Показать ожидающие задачи в outbox."""
    files = list(OUTBOX.glob("*.md"))
    if agent:
        files = [f for f in files if f.stem.startswith(agent)]
    return files


def list_results(agent: str = None) -> list:
    """Показать результаты в inbox."""
    files = list(INBOX.glob("*.md"))
    if agent:
        files = [f for f in files if f.stem.startswith(agent)]
    return files


def _log(msg: str):
    print(f"  [{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")
    RELAY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RELAY_LOG, "a") as f:
        f.write(f"[{datetime.utcnow().isoformat()}Z] {msg}\n")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print(f"  python3 agent_relay.py send <agent> 'task description'")
        print(f"  python3 agent_relay.py results [agent]")
        print(f"  python3 agent_relay.py pending [agent]")
        print(f"\nAgents: gemini, copilot, codex, jules, goose")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "send":
        agent = sys.argv[2]
        task = " ".join(sys.argv[3:])
        result = send_task(agent, task)
        print(f"\n  Result saved to: {result}")
    elif cmd == "results":
        agent = sys.argv[2] if len(sys.argv) > 2 else None
        files = list_results(agent)
        if files:
            print(f"Results ({len(files)}):")
            for f in sorted(files):
                print(f"  📄 {f.name} ({f.stat().st_size} bytes)")
        else:
            print("No results in inbox")
    elif cmd == "pending":
        agent = sys.argv[2] if len(sys.argv) > 2 else None
        files = list_pending(agent)
        if files:
            print(f"Pending tasks ({len(files)}):")
            for f in sorted(files):
                print(f"  ⏳ {f.name}")
        else:
            print("No pending tasks in outbox")
