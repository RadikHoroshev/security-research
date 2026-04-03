---
id: SOL-003
name: "Zed + ACP/MCP — лёгкий кокпит для агентов"
source_project: "zed-industries/zed"
source_url: "https://zed.dev"
category: tools
tags: [ide, zed, acp, mcp, apple-silicon, rust, lightweight]
quality: 4
applicability: 3
effort: 3
found_by: human-research
found_date: 2026-04-01
---

## Что это
Zed — IDE на Rust/GPUI, потребляет ~200MB RAM в idle против 1.2GB у Cursor и 1.5GB у VS Code. Поддерживает ACP (Agent Client Protocol) и MCP нативно — агенты подключаются как внешние процессы.

## Почему это хорошо
На 16GB Mac экономия 1-1.3GB на IDE = дополнительный контекст для модели или более крупная модель. 120 FPS рендеринг не создаёт нагрузки на CPU/GPU в отличие от Electron.

## Как работает
Zed запускает агентов как отдельные процессы через ACP — редактор остаётся быстрым, вся нагрузка LLM изолирована. MCP-серверы подключаются через `settings.json`.

Настройка агента в Zed:
```json
{
  "agent": {
    "default_model": {
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    }
  },
  "context_servers": {
    "security-team": {
      "command": "python3",
      "args": ["~/project/security-team/mcp/server.py"]
    }
  }
}
```

Важные фиксы:
```json
// keybindings.json — фикс для agent panel (не assistant::ToggleFocus!)
{"context": "Workspace", "bindings": {"cmd-shift-a": "agent::ToggleFocus"}}

// settings.json — фикс таймаута для тяжёлых MCP
{"context_server_timeout": 600}
```

## Как применить у нас
1. Установить Zed: `brew install zed`
2. Подключить наш security-team MCP сервер через `context_servers`
3. Подключить Ollama как provider
4. Использовать как альтернативный интерфейс к системе (рядом с Claude Code)

## Зависимости
- macOS (нативная поддержка Apple Silicon)
- `brew install zed`
- Ollama запущена на localhost:11434

## Ограничения
- Меньше плагинов чем VS Code
- ACP — более новый протокол, меньше инструментов
- Наша система уже работает через Claude Code — Zed как дополнение, не замена
