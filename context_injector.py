#!/usr/bin/env python3.11
"""
context_injector.py — Автоматический инжектор контекста для любого агента

Когда агент получает задачу:
  1. Определяет тип задачи
  2. Ищет релевантный контекст в AnythingLLM RAG
  3. Ищет прошлые ошибки по теме
  4. Ищет историю похожих задач
  5. Формирует enriched prompt с контекстом
  6. Отдаёт агенту уже готовый prompt с полной картиной

Экономит 1000-3000 токенов на каждом вызове агента.
"""

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════

API_KEY = "9MMMM0Y-2YC4FGE-JD7VX41-5MY20RT"
WORKSPACE_SLUG = "moya-rabochaya-oblast"
API_URL = "http://localhost:3001/api/v1"
KB_DIR = os.path.expanduser("~/project/knowledge_base")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# ═══════════════════════════════════════════════════════════
# ОПРЕДЕЛЕНИЕ ТИПА ЗАДАЧИ
# ═══════════════════════════════════════════════════════════

def classify_task(task_text: str) -> dict:
    """
    Определить тип задачи по тексту.
    Возвращает: category, keywords, context_needs
    """
    task_lower = task_text.lower()

    # Ключевые слова → категории
    categories = {
        "coding": {
            "keywords": ["код", "функци", "напиш", "созда", "рефактор",
                        "исправ", "баг", "ошибк", "script", "code",
                        "function", "write", "create", "fix", "implement"],
            "context_topics": ["coding standards", "known bugs", "architecture"],
            "error_topics": ["code error", "bug", "fix"],
        },
        "security": {
            "keywords": ["уязвим", "security", "scan", "audit", "CVE",
                        "vulnerability", "exploit", "injection", "XSS",
                        "безопасн", "аудит", "скан"],
            "context_topics": ["security audit", "vulnerability patterns",
                              "previous scans"],
            "error_topics": ["security tool error", "scan failed"],
        },
        "deploy": {
            "keywords": ["deploy", "запуск", "разверн", "infrastructure",
                        "terraform", "bicep", "azure", "cloud", "docker"],
            "context_topics": ["deployment config", "infrastructure",
                              "previous deployments"],
            "error_topics": ["deploy error", "infrastructure error"],
        },
        "research": {
            "keywords": ["исслед", "research", "найди", "find", "изучи",
                        "explore", "investigate", "проверь"],
            "context_topics": ["previous research", "technology evaluation"],
            "error_topics": ["research error"],
        },
        "shell": {
            "keywords": ["команд", "command", "shell", "bash", "terminal",
                        "скрипт", "порт", "port", "process"],
            "context_topics": ["known shell commands", "port configurations"],
            "error_topics": ["shell error", "port conflict", "command failed"],
        },
    }

    best_match = {
        "category": "general",
        "confidence": 0.3,
        "context_topics": ["system architecture", "current tasks"],
        "error_topics": ["general errors"],
    }

    for cat, config in categories.items():
        score = sum(
            1 for kw in config["keywords"]
            if kw in task_lower
        )
        if score > best_match["confidence"] * 5:
            best_match = {
                "category": cat,
                "confidence": min(score / 5, 1.0),
                "context_topics": config["context_topics"],
                "error_topics": config["error_topics"],
            }

    # Извлекаем ключевые слова из задачи
    keywords = [w for w in task_lower.split() if len(w) > 3]
    best_match["keywords"] = keywords[:10]

    return best_match


# ═══════════════════════════════════════════════════════════
# СБОР КОНТЕКСТА
# ═══════════════════════════════════════════════════════════

def rag_query(question: str, top_k: int = 3) -> str:
    """RAG поиск по базе знаний."""
    url = f"{API_URL}/workspace/{WORKSPACE_SLUG}/chat"
    data = json.dumps({
        "message": question,
        "mode": "query",
        "topN": top_k,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("textResponse", "")
    except Exception:
        return ""


def search_action_logs(keywords: list, hours: int = 168) -> list:
    """Поиск похожих действий в action логах."""
    log_dir = os.path.join(KB_DIR, "agent_actions")
    if not os.path.isdir(log_dir):
        return []

    matches = []
    for f in os.listdir(log_dir):
        if not f.endswith(".jsonl"):
            continue
        filepath = os.path.join(log_dir, f)
        with open(filepath, "r") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                    text = f"{entry.get('action', '')} {entry.get('result', '')}"
                    if any(kw.lower() in text.lower() for kw in keywords):
                        matches.append(entry)
                except json.JSONDecodeError:
                    continue

    return matches[:5]


def search_known_errors(topics: list) -> list:
    """Поиск известных ошибок по теме."""
    error_log = os.path.join(KB_DIR, "error_solutions/ERROR_LOG.md")
    if not os.path.isfile(error_log):
        return []

    errors = []
    with open(error_log, "r") as f:
        content = f.read()

    # Разбиваем по записям
    entries = content.split("## ")
    for entry in entries[1:]:  # Пропускаем заголовок
        if any(t.lower() in entry.lower() for t in topics):
            # Берём только заголовок + решение
            lines = entry.split("\n")[:10]
            errors.append("\n".join(lines))

    return errors[:3]


def get_system_context() -> str:
    """Получить общий контекст системы."""
    ctx_file = os.path.expanduser("~/project/CONTINUATION_PLAN.md")
    if os.path.isfile(ctx_file):
        with open(ctx_file, "r") as f:
            content = f.read()
            # Берём только первые 50 строк — суть
            return "\n".join(content.split("\n")[:50])
    return ""


# ═══════════════════════════════════════════════════════════
# ИНЖЕКЦИЯ КОНТЕКСТА
# ═══════════════════════════════════════════════════════════

def inject_context(task: str, agent_name: str = "agent") -> dict:
    """
    Полный pipeline: задача → контекст → enriched prompt.

    Вызывается ПЕРЕД каждым вызовом агента.
    """
    # 1. Классификация
    task_class = classify_task(task)

    # 2. RAG поиск по теме
    rag_answer = rag_query(task, top_k=3)

    # 3. Похожие прошлые действия
    past_actions = search_action_logs(task_class["keywords"])

    # 4. Известные ошибки
    known_errors = search_known_errors(task_class["error_topics"])

    # 5. Системный контекст
    system_ctx = get_system_context()

    # Формируем enriched context
    context_block = f"""
# ═══════════════════════════════════════════════════════
# КОНТЕКСТ ДЛЯ АГЕНТА: {agent_name}
# Задача: {task[:100]}
# ═══════════════════════════════════════════════════════

## 📌 Системный контекст
{system_ctx[:1000]}

## 🔍 Контекст по задаче (RAG)
{rag_answer if rag_answer else "Нет релевантных данных в базе знаний."}

## 📋 Похожие прошлые действия"""

    if past_actions:
        for i, act in enumerate(past_actions[:3], 1):
            context_block += f"""

### Действие {i}
- Агент: {act.get('agent', 'unknown')}
- Действие: {act.get('action', '')[:200]}
- Результат: {act.get('result', '')[:200]}
- Статус: {act.get('status', '')}"""
    else:
        context_block += "\n(Нет похожих действий)"

    context_block += "\n\n## ⚠️ Известные ошибки (НЕ повторять)"

    if known_errors:
        for i, err in enumerate(known_errors[:3], 1):
            context_block += f"\n\n### Ошибка {i}\n{err[:300]}"
    else:
        context_block += "\n(Нет известных ошибок по этой теме)"

    context_block += """

# ═══════════════════════════════════════════════════════
# КОНЕЦ КОНТЕКСТА — ниже задача агента
# ═══════════════════════════════════════════════════════
"""

    return {
        "task": task,
        "agent": agent_name,
        "task_category": task_class["category"],
        "confidence": task_class["confidence"],
        "context": context_block,
        "rag_answer": rag_answer,
        "past_actions_count": len(past_actions),
        "known_errors_count": len(known_errors),
        "context_tokens_estimate": len(context_block) // 4,  # ~4 chars per token
    }


# ═══════════════════════════════════════════════════════════
# ИНТЕГРАЦИЯ С АГЕНТАМИ
# ═══════════════════════════════════════════════════════════

def call_agent_with_context(
    agent_type: str,
    task: str,
    agent_name: str = "agent",
    **kwargs
) -> dict:
    """
    Вызвать агента с автоматическим контекстом.

    agent_type: ollama | qwen_cli | gemini_cli | copilot | jules | shell
    task: задача
    agent_name: имя для логов
    """
    # Инжектируем контекст
    ctx = inject_context(task, agent_name)

    # Форми enriched prompt
    enriched_task = f"{ctx['context']}\n\nЗАДАЧА:\n{task}"

    # Вызываем агента
    if agent_type == "ollama":
        model = kwargs.get("model", "qwen2.5-coder:14b")
        result = subprocess.run(
            ["ollama", "run", model, enriched_task],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 120)
        )
        output = result.stdout.strip()

    elif agent_type == "qwen_cli":
        result = subprocess.run(
            ["qwen", "--prompt", enriched_task],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 300)
        )
        output = result.stdout.strip()

    elif agent_type == "gemini_cli":
        result = subprocess.run(
            ["gemini", "-p", enriched_task, "--yolo"],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 180)
        )
        output = result.stdout.strip()

    elif agent_type == "copilot":
        result = subprocess.run(
            [
                "copilot", "-p", enriched_task,
                "--model", "gpt-5-mini",
                "--allow-all", "--allow-all-tools", "--allow-all-urls",
            ],
            capture_output=True, text=True,
            timeout=kwargs.get("timeout", 60)
        )
        output = result.stdout.strip()

    elif agent_type == "jules":
        cmd = ["jules", "new", enriched_task]
        if kwargs.get("repo"):
            cmd.insert(2, "--repo")
            cmd.insert(3, kwargs["repo"])

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=kwargs.get("timeout", 600)
        )
        output = result.stdout.strip()

    elif agent_type == "shell":
        result = subprocess.run(
            task.split(), capture_output=True, text=True,
            timeout=kwargs.get("timeout", 30)
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    else:
        output = f"Unknown agent type: {agent_type}"

    # Логируем действие
    log_action(agent_name, task, output, "success")

    return {
        "task": task,
        "agent": agent_name,
        "agent_type": agent_type,
        "task_category": ctx["task_category"],
        "context_used": True,
        "context_tokens": ctx["context_tokens_estimate"],
        "past_actions_referenced": ctx["past_actions_count"],
        "errors_avoided": ctx["known_errors_count"],
        "result": output[:5000],
    }


def log_action(agent: str, task: str, result: str, status: str):
    """
    Записать действие в action log + автоматически сохранить в KB + AnythingLLM.
    КАЖДЫЙ вызов агента логируется — НЕ НУЖНО вызывать `s` вручную!
    """
    import json
    import shutil
    from datetime import datetime

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")
    file_ts = now.strftime("%Y-%m-%d_%H%M%S")

    # ── 1. JSONL лог (для agent_history) ──────────────────────────
    log_dir = os.path.join(KB_DIR, "agent_actions")
    os.makedirs(log_dir, exist_ok=True)

    date_file = os.path.join(log_dir, f"{date_str}.jsonl")
    entry = {
        "timestamp": timestamp,
        "agent": agent,
        "action": task[:500],
        "result": result[:2000],
        "status": status,
        "tags": [],
    }
    with open(date_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # ── 2. Markdown файл (для RAG индексации) ─────────────────────
    results_dir = os.path.join(KB_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)

    md_content = f"""# 🤖 {agent}: {task[:100]}

**Время:** {timestamp}
**Агент:** {agent}
**Статус:** {status}

## Задача
{task}

## Результат
{result[:3000]}

---

*Сохранено автоматически: context_injector.py*
"""
    md_file = os.path.join(results_dir, f"{file_ts}_{agent[:30]}.md")
    with open(md_file, "w") as f:
        f.write(md_content)

    # ── 3. Копия в AnythingLLM hotdir (авто-индексация) ────────────
    atllm_hotdir = os.path.expanduser(
        "~/Library/Application Support/anythingllm-desktop/storage/hotdir"
    )
    os.makedirs(atllm_hotdir, exist_ok=True)
    try:
        shutil.copy2(md_file, os.path.join(atllm_hotdir, f"{file_ts}_{agent[:30]}.md"))
    except Exception:
        pass  # Не критично если не получилось


# ═══════════════════════════════════════════════════════════
# ПРЕФИКС-КОМАНДЫ (@s, @q, @e, и т.д.)
# ═══════════════════════════════════════════════════════════

def handle_prefix_command(text: str) -> dict:
    """
    Обработать префикс-команду в тексте.
    @s → сохранить
    @q → RAG поиск
    @e → записать ошибку
    @t → задача
    @p → план
    @r → результат
    @a → аудит
    """
    text = text.strip()

    # Проверяем префикс
    if not text.startswith("@"):
        return {"type": "normal", "text": text}

    parts = text.split(" ", 1)
    prefix = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if prefix == "@s" or prefix == "@save":
        return {"type": "save", "arg": arg, "text": text}
    elif prefix == "@q" or prefix == "@query":
        return {"type": "query", "arg": arg, "text": text}
    elif prefix == "@e" or prefix == "@error":
        return {"type": "error", "arg": arg, "text": text}
    elif prefix == "@t" or prefix == "@task":
        return {"type": "task", "arg": arg, "text": text}
    elif prefix == "@p" or prefix == "@plan":
        return {"type": "plan", "arg": arg, "text": text}
    elif prefix == "@r" or prefix == "@result":
        return {"type": "result", "arg": arg, "text": text}
    elif prefix == "@a" or prefix == "@audit":
        return {"type": "audit", "arg": arg, "text": text}
    elif prefix == "@i" or prefix == "@info" or prefix == "@изучи":
        return {"type": "study", "arg": arg, "text": text}
    elif prefix == "@h" or prefix == "@help":
        return {"type": "help", "arg": arg, "text": text}

    return {"type": "normal", "text": text}

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование: context_injector.py <task> [agent_type] [agent_name]")
        print("  agent_type: ollama | qwen_cli | gemini_cli | copilot | shell")
        print("  agent_name: любое имя для логов")
        sys.exit(1)

    task = sys.argv[1]
    agent_type = sys.argv[2] if len(sys.argv) > 2 else "ollama"
    agent_name = sys.argv[3] if len(sys.argv) > 3 else agent_type

    print(f"🧠 Инжекция контекста для: {agent_name}")
    print(f"   Задача: {task[:80]}...")
    print()

    # Инжектируем
    ctx = inject_context(task, agent_name)

    print(f"📊 Контекст:")
    print(f"   Категория: {ctx['task_category']} (confidence: {ctx['confidence']:.1%})")
    print(f"   RAG ответ: {'✅' if ctx['rag_answer'] else '❌'} ({len(ctx['rag_answer'])} chars)")
    print(f"   Прошлые действия: {ctx['past_actions_count']}")
    print(f"   Известные ошибки: {ctx['known_errors_count']}")
    print(f"   Токены контекста: ~{ctx['context_tokens_estimate']}")
    print()

    # Вызываем агента
    print(f"⚡ Вызов агента: {agent_type}")
    result = call_agent_with_context(agent_type, task, agent_name)

    print()
    print(f"✅ Результат:")
    print(result["result"][:500])
