---
id: SOL-010
name: "OpenCode — лёгкая альтернатива VS Code с 75+ провайдерами"
source_project: "sst/opencode"
source_url: "https://opencode.ai"
category: tools
tags: [ide, rust, tauri, lightweight, open-source, multi-provider, air-gapped]
quality: 4
applicability: 3
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
OpenCode — IDE на Rust/Tauri (~300MB RAM idle), полностью открытый исходный код, поддерживает 75+ провайдеров моделей включая Ollama. Поддерживает ACP протокол.

## Почему это хорошо
Для air-gapped security работы (когда нельзя отправлять код в облако): OpenCode + Ollama даёт полностью локальный стек без телеметрии. 300MB overhead vs 1.5GB у VS Code = дополнительные ~4GB контекста для модели.

## Как работает
```
OpenCode (Rust/Tauri, ~300MB)
    ↓ ACP протокол
Ollama (localhost:11434)
    ↓
qwen2.5-coder:7b / deepseek-r1:7b
```

Конфигурация провайдера:
```json
{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "baseUrl": "http://localhost:11434"
}
```

## Как применить у нас
Использовать как альтернативный интерфейс для работы с security-sensitive кодом когда нельзя использовать Claude Code (облако). Air-gapped режим: OpenCode + Ollama + наш security-team MCP.

## Зависимости
- `brew install opencode` или скачать с opencode.ai
- Ollama (уже есть)

## Ограничения
- Менее отполированный UI чем Cursor/Zed
- Меньше плагинов
- Основной use case для нас: air-gapped работа с чувствительными данными
