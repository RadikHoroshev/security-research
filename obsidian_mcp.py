#!/usr/bin/env python3.11
"""
obsidian_mcp.py — MCP сервер для Obsidian Vault

Позволяет Goose и другим MCP-клиентам:
  - Искать заметки
  - Читать/писать заметки
  - Просматривать структуру
  - Работать с graph links
"""

import os
import re
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

VAULT_DIR = os.path.expanduser("~/Documents/Obsidian Vault")

mcp = FastMCP("ObsidianVault")


@mcp.tool()
def search(query: str, max_results: int = 10) -> list:
    """Поиск по всем заметкам в Obsidian Vault."""
    if not os.path.isdir(VAULT_DIR):
        return [{"error": f"Vault не найден: {VAULT_DIR}"}]

    results = []
    query_lower = query.lower()

    for root, _, files in os.walk(VAULT_DIR):
        # Пропускаем служебные папки
        if "/.git/" in root or "/.obsidian/" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, "r", errors="replace") as fh:
                    content = fh.read()
                if query_lower in content.lower():
                    rel = os.path.relpath(path, VAULT_DIR)
                    # Находим контекст вокруг совпадения
                    idx = content.lower().index(query_lower)
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 200)
                    context = content[start:end].strip()
                    results.append({
                        "path": rel,
                        "context": f"...{context}...",
                        "size_kb": round(len(content) / 1024, 1),
                    })
            except Exception:
                continue

            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    return results


@mcp.tool()
def read(path: str) -> str:
    """Прочитать заметку по пути относительно vault."""
    full = os.path.join(VAULT_DIR, path)
    if not path.endswith(".md"):
        full += ".md"
    if not os.path.isfile(full):
        return f"Заметка не найдена: {path}"
    with open(full, "r", errors="replace") as f:
        return f.read()


@mcp.tool()
def write(path: str, content: str, append: bool = False) -> str:
    """Создать или обновить заметку."""
    full = os.path.join(VAULT_DIR, path)
    if not path.endswith(".md"):
        full += ".md"
    os.makedirs(os.path.dirname(full), exist_ok=True)

    mode = "a" if append else "w"
    if append and os.path.isfile(full):
        content = "\n\n" + content

    with open(full, mode, errors="replace") as f:
        f.write(content)

    return f"Сохранено: {path}"


@mcp.tool()
def list_notes(folder: str = "") -> list:
    """Список всех заметок (опционально по папке)."""
    target = os.path.join(VAULT_DIR, folder) if folder else VAULT_DIR
    if not os.path.isdir(target):
        return [{"error": f"Папка не найдена: {folder or 'root'}"}]

    notes = []
    for root, _, files in os.walk(target):
        if "/.git/" in root or "/.obsidian/" in root:
            continue
        for f in sorted(files):
            if f.endswith(".md"):
                full = os.path.join(root, f)
                notes.append({
                    "path": os.path.relpath(full, VAULT_DIR),
                    "size_kb": round(os.path.getsize(full) / 1024, 1),
                    "modified": datetime.fromtimestamp(
                        os.path.getmtime(full)
                    ).strftime("%Y-%m-%d %H:%M"),
                })
    return sorted(notes, key=lambda x: x["path"])


@mcp.tool()
def folders() -> list:
    """Список папок в Vault."""
    if not os.path.isdir(VAULT_DIR):
        return [{"error": "Vault не найден"}]
    folders_list = []
    for root, dirs, _ in os.walk(VAULT_DIR):
        if "/.git/" in root or "/.obsidian/" in root:
            continue
        for d in sorted(dirs):
            full = os.path.join(root, d)
            folders_list.append({
                "path": os.path.relpath(full, VAULT_DIR),
                "notes": len([
                    f for f in os.listdir(full)
                    if f.endswith(".md")
                ]),
            })
    return sorted(folders_list, key=lambda x: x["path"])


@mcp.tool()
def recent(days: int = 7) -> list:
    """Недавно изменённые заметки."""
    notes = []
    cutoff = datetime.now().timestamp() - (days * 86400)

    for root, _, files in os.walk(VAULT_DIR):
        if "/.git/" in root or "/.obsidian/" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            mtime = os.path.getmtime(path)
            if mtime >= cutoff:
                notes.append({
                    "path": os.path.relpath(path, VAULT_DIR),
                    "modified": datetime.fromtimestamp(mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "size_kb": round(os.path.getsize(path) / 1024, 1),
                })

    return sorted(notes, key=lambda x: x["modified"], reverse=True)


if __name__ == "__main__":
    mcp.run()
