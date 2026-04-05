#!/usr/bin/env python3
"""
auto_session_logger.py — Автоматическое сохранение сессий Qwen Code

Каждый ответ агента автоматически логируется в Knowledge Base:
  1. Сохраняет в sessions/YYYY-MM-DD_HHMM.md
  2. Сохраняет в agent_actions/YYYY-MM-DD.jsonl
  3. Копирует в AnythingLLM hotdir для индексации
  4. Обновляет CONTINUATION_PLAN.md
"""

import json
import os
import sys
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

KB_DIR = os.path.expanduser("~/project/knowledge_base")
SESSIONS_DIR = os.path.join(KB_DIR, "sessions")
ACTIONS_DIR = os.path.join(KB_DIR, "agent_actions")
ATLLM_HOTDIR = os.path.expanduser(
    "~/Library/Application Support/anythingllm-desktop/storage/hotdir"
)
CONTINUATION_FILE = os.path.expanduser("~/project/CONTINUATION_PLAN.md")

for d in [SESSIONS_DIR, ACTIONS_DIR, ATLLM_HOTDIR]:
    os.makedirs(d, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
DATE_ONLY = datetime.now().strftime("%Y-%m-%d")

# ═══════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════

def log_session(topic: str, content: str, tags: list = None):
    """
    Сохранить сессию/ответ в базу знаний.

    topic: тема разговора
    content: содержание ответа
    tags: список тегов
    """
    tags = tags or []
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Сохраняем Markdown сессию
    session_md = os.path.join(SESSIONS_DIR, f"{TIMESTAMP}_auto.md")

    session_content = f"""# 💬 Auto-log: {topic}

**Время:** {timestamp}
**Агент:** qwen_code
**Теги:** {', '.join(f'#{t}' for t in tags)}

---

## Содержание
{content[:5000]}

---

*Сохранено автоматически: auto_session_logger.py*
"""

    # Append если файл уже есть (новая запись), или создать
    if os.path.exists(session_md):
        with open(session_md, "a") as f:
            f.write(f"\n\n---\n\n## {timestamp}\n{content[:3000]}\n")
    else:
        with open(session_md, "w") as f:
            f.write(session_content)

    # 2. Копируем в AnythingLLM hotdir
    try:
        import shutil
        shutil.copy2(session_md, os.path.join(ATLLM_HOTDIR, f"session_{TIMESTAMP}.md"))
    except Exception:
        pass

    # 3. Логируем в agent_actions JSONL
    actions_file = os.path.join(ACTIONS_DIR, f"{DATE_ONLY}.jsonl")
    entry = {
        "timestamp": timestamp,
        "agent": "qwen_code",
        "action": f"Auto-log: {topic}",
        "result": content[:1000],
        "status": "success",
        "tags": tags,
    }
    with open(actions_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {
        "session_file": session_md,
        "actions_file": actions_file,
        "synced_to_atllm": True,
    }


def update_continuation_plan(new_info: str):
    """Обновить CONTINUATION_PLAN.md новой информацией."""
    if not os.path.isfile(CONTINUATION_FILE):
        return

    with open(CONTINUATION_FILE, "r") as f:
        content = f.read()

    # Добавляем запись в конец (перед последней строкой)
    update = f"\n### {datetime.now().strftime('%H:%M')} | Auto-update\n{new_info[:500]}\n"

    # Находим позицию "---" в конце файла и вставляем перед ней
    lines = content.rsplit("\n---\n", 1)
    if len(lines) == 2:
        content = lines[0] + "\n---\n" + update + "\n---\n" + lines[1]
    else:
        content += "\n" + update

    with open(CONTINUATION_FILE, "w") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: auto_session_logger.py <topic> <content>")
        sys.exit(1)

    topic = sys.argv[1]
    content = sys.argv[2]
    tags = sys.argv[3].split(",") if len(sys.argv) > 3 else []

    result = log_session(topic, content, tags)
    print(f"✅ Сохранено: {result['session_file']}")

    if len(sys.argv) > 4 and sys.argv[4] == "--update-continuation":
        update_continuation_plan(content)
        print(f"📝 Continuation plan обновлён")
