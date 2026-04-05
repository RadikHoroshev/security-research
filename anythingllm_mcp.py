#!/usr/bin/env python3
"""
anythingllm_mcp.py — Центральная память мульти-агентной системы

Роль: Central Knowledge Memory (RAG + Auto-logging)

Все агенты:
  1. Пишут сюда каждое действие (auto-log)
  2. Ищут контекст перед принятием решений (RAG query)
  3. Получают точные ответы без пересказа истории

Интегрирован в Goose Hub через MCP.
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ — IRON-CLAD (читаем из .env, fallback на hardcode)
# ═══════════════════════════════════════════════════════════

# Читаем из .env.anythingllm если существует
_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.anythingllm")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith("ANYTHINGLLM_API_KEY="):
                API_KEY = _line.split("=", 1)[1]
                break
        else:
            API_KEY = "9MMMM0Y-2YC4FGE-JD7VX41-5MY20RT"  # Fallback
else:
    API_KEY = "9MMMM0Y-2YC4FGE-JD7VX41-5MY20RT"  # Iron-clad fallback

HOST = os.environ.get("ANYTHINGLLM_HOST", "http://localhost:3001")
WORKSPACE = os.environ.get("ANYTHINGLLM_WORKSPACE", "moya-rabochaya-oblast")
WORKSPACE_SLUG = "moya-rabochaya-oblast"
API_URL = "http://localhost:3001/api/v1"
STORAGE_DIR = os.path.expanduser(
    "~/Library/Application Support/anythingllm-desktop/storage"
)
DOCS_DIR = os.path.join(STORAGE_DIR, "documents", "custom-documents")
HOTDIR = os.path.join(STORAGE_DIR, "hotdir")
KB_DIR = os.path.expanduser("~/project/knowledge_base")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

mcp = FastMCP("AnythingLLM")

for d in [DOCS_DIR, HOTDIR, KB_DIR]:
    os.makedirs(d, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# RAG QUERY — Главная функция поиска
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def rag_query(
    question: str,
    mode: str = "query",
    top_k: int = 5,
) -> dict:
    """
    RAG-поиск по всей базе знаний.
    Ищет в документах, session logs, error logs, research.

    mode: 'query' (точный ответ) | 'chat' (диалог)
    top_k: количество источников (2-10)

    Возвращает: ответ + источники + confidence
    """
    url = f"{API_URL}/workspace/{WORKSPACE_SLUG}/chat"
    data = json.dumps({
        "message": question,
        "mode": mode,
        "topN": top_k,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        sources = result.get("sources", [])
        return {
            "answer": result.get("textResponse", ""),
            "sources": [
                {
                    "title": s.get("title", s.get("name", "unknown")),
                    "score": s.get("score", 0),
                    "chunk": s.get("chunk", "")[:300],
                }
                for s in sources[:top_k]
            ],
            "source_count": len(sources),
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
        }
    except urllib.error.URLError as e:
        return {
            "error": f"AnythingLLM не отвечает: {str(e)}",
            "hint": "Проверь что AnythingLLM Desktop запущен",
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# AUTO-LOG — Автоматическое сохранение действий
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def log_action(
    agent: str,
    action: str,
    result: str,
    status: str = "success",
    tags: list = None,
) -> dict:
    """
    Записать действие агента в центральную память.

    agent: имя агента (qwen_cli, goose, security_team, и т.д.)
    action: что сделано
    result: результат выполнения
    status: success | error | warning | info
    tags: список тегов для поиска

    Автоматически:
    1. Сохраняет в session log файл
    2. Отправляет в AnythingLLM для индексации
    3. Возвращает ID записи
    """
    tags = tags or []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Формируем запись
    entry = {
        "timestamp": timestamp,
        "agent": agent,
        "action": action,
        "result": result[:2000],  # Лимит для embedding
        "status": status,
        "tags": tags,
    }

    # Сохраняем в JSON лог
    log_dir = os.path.join(KB_DIR, "agent_actions")
    os.makedirs(log_dir, exist_ok=True)

    date_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.jsonl")
    with open(date_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Создаём Markdown для AnythingLLM
    md_content = f"""# {agent}: {action}

**Время:** {timestamp}
**Статус:** {status}
**Теги:** {', '.join(f'#{t}' for t in tags)}

## Действие
{action}

## Результат
{result[:2000]}
"""
    md_file = os.path.join(
        DOCS_DIR,
        f"action_{agent}_{datetime.now().strftime('%H%M%S')}.md"
    )
    with open(md_file, "w") as f:
        f.write(md_content)

    # Отправляем в hotdir для индексации
    hot_file = os.path.join(
        HOTDIR,
        f"action_{agent}_{datetime.now().strftime('%H%M%S')}.md"
    )
    with open(hot_file, "w") as f:
        f.write(md_content)

    return {
        "status": "logged",
        "agent": agent,
        "action": action[:100],
        "file": md_file,
        "timestamp": timestamp,
    }


# ═══════════════════════════════════════════════════════════
# AGENT HISTORY — История конкретного агента
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def agent_history(
    agent: str,
    hours: int = 24,
    limit: int = 20,
) -> list:
    """
    Получить историю действий конкретного агента.

    agent: имя агента
    hours: за сколько часов
    limit: максимум записей
    """
    log_dir = os.path.join(KB_DIR, "agent_actions")
    if not os.path.isdir(log_dir):
        return []

    entries = []
    cutoff = time.time() - (hours * 3600)

    for f in sorted(os.listdir(log_dir), reverse=True):
        if not f.endswith(".jsonl"):
            continue

        filepath = os.path.join(log_dir, f)
        with open(filepath, "r") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("agent") == agent:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

                if len(entries) >= limit:
                    break
        if len(entries) >= limit:
            break

    return entries


# ═══════════════════════════════════════════════════════════
# CONTEXT SEARCH — Поиск контекста перед принятием решений
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def search_context(topic: str, max_sources: int = 5) -> dict:
    """
    Найти весь контекст по теме в базе знаний.
    Используется ПЕРЕД принятием решений чтобы:
    - Не повторять ошибки
    - Использовать прошлые решения
    - Понимать контекст системы

    topic: тема поиска
    max_sources: максимум источников
    """
    # RAG поиск
    rag = rag_query(topic, mode="query", top_k=max_sources)

    if "error" in rag:
        return {"error": rag["error"]}

    # Дополнительно ищем в agent action logs
    log_dir = os.path.join(KB_DIR, "agent_actions")
    related_actions = []

    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            if not f.endswith(".jsonl"):
                continue
            filepath = os.path.join(log_dir, f)
            with open(filepath, "r") as fh:
                for line in fh:
                    try:
                        entry = json.loads(line.strip())
                        if (
                            topic.lower() in entry.get("action", "").lower()
                            or topic.lower() in entry.get("result", "").lower()
                            or any(
                                topic.lower() in t.lower()
                                for t in entry.get("tags", [])
                            )
                        ):
                            related_actions.append(entry)
                    except json.JSONDecodeError:
                        continue

    return {
        "rag_answer": rag.get("answer", ""),
        "rag_sources": rag.get("sources", []),
        "related_actions": related_actions[:max_sources],
        "total_context_items": len(rag.get("sources", [])) + len(related_actions),
    }


# ═══════════════════════════════════════════════════════════
# BATCH INGEST — Массовая индексация
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def ingest_files(file_paths: list, workspace: str = None) -> dict:
    """
    Добавить файлы в AnythingLLM для индексации.

    file_paths: список путей к файлам
    workspace: slug workspace (по умолчанию основной)
    """
    import shutil

    workspace = workspace or WORKSPACE_SLUG
    ingested = []
    errors = []

    for path in file_paths:
        if not os.path.isfile(path):
            errors.append({"path": path, "error": "File not found"})
            continue

        try:
            # Копируем в hotdir
            base = os.path.basename(path)
            dest = os.path.join(HOTDIR, f"{base}")
            shutil.copy2(path, dest)
            ingested.append(path)
        except Exception as e:
            errors.append({"path": path, "error": str(e)})

    return {
        "ingested": len(ingested),
        "errors": len(errors),
        "files": ingested,
        "error_details": errors,
    }


# ═══════════════════════════════════════════════════════════
# SYSTEM STATUS
# ═══════════════════════════════════════════════════════════

@mcp.tool()
def memory_status() -> dict:
    """Статус центральной памяти системы."""
    # Файлы в documents
    doc_count = 0
    if os.path.isdir(DOCS_DIR):
        doc_count = len([
            f for f in os.listdir(DOCS_DIR) if f.endswith((".md", ".json"))
        ])

    # Action logs
    action_log_count = 0
    action_log_dir = os.path.join(KB_DIR, "agent_actions")
    if os.path.isdir(action_log_dir):
        for f in os.listdir(action_log_dir):
            if f.endswith(".jsonl"):
                with open(os.path.join(action_log_dir, f)) as fh:
                    action_log_count += sum(1 for _ in fh)

    # Workspace info
    workspace_info = {}
    try:
        url = f"{API_URL}/workspace/{WORKSPACE_SLUG}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ws = data.get("workspace", [{}])[0]
            workspace_info = {
                "name": ws.get("name", "unknown"),
                "documents": len(ws.get("documents", [])),
                "chat_model": ws.get("chatModel", "unknown"),
            }
    except Exception:
        workspace_info = {"error": "Cannot reach AnythingLLM API"}

    return {
        "status": "online",
        "workspace": workspace_info,
        "documents_ingested": doc_count,
        "action_log_entries": action_log_count,
        "knowledge_base_path": KB_DIR,
    }


if __name__ == "__main__":
    mcp.run()
