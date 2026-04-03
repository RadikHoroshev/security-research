---
id: SOL-004
name: "Roo Code — ролевые режимы автономного агента"
source_project: "RooVetGit/Roo-Code"
source_url: "https://github.com/RooVetGit/Roo-Code"
category: tools
tags: [vscode, autonomous, roles, architect, coder, debug, ollama]
quality: 4
applicability: 4
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
Roo Code (бывший Cline) — VS Code расширение с ролевыми режимами: Architect (планирование), Coder (исполнение), Debug (отладка). Агент автономно манипулирует файлами и терминалом.

## Почему это хорошо
Разделение на роли даёт specialization внутри одного инструмента: Architect планирует на высоком уровне (понимает русский язык), Coder выполняет, Debug — анализирует ошибки. Это паттерн который мы должны применить в нашем dispatcher.

## Как работает
```
Пользователь → Architect mode (планирование, декомпозиция)
                    ↓ передаёт план
              Coder mode (выполнение, файлы, команды)
                    ↓ при ошибке
              Debug mode (анализ, исправление)
```

Каждый режим имеет свой system prompt и набор разрешённых действий. Режимы можно переключать вручную или настроить автоматическое переключение.

Конфигурация режима в `.roo/modes.json`:
```json
{
  "architect": {
    "model": "ollama/qwen2.5-coder:7b",
    "systemPrompt": "You are a software architect. Plan, don't code.",
    "allowedTools": ["read_file", "search"]
  },
  "coder": {
    "model": "ollama/qwen2.5-coder:7b",
    "systemPrompt": "You are a precise coder. Implement the plan exactly.",
    "allowedTools": ["read_file", "write_file", "execute_command"]
  }
}
```

## Как применить у нас
Паттерн ролевых режимов применить в dispatcher:
```python
ROLES = {
    "planner":  {"model": "kimi-k2.5:cloud",    "max_iter": 3},
    "executor": {"model": "qwen2.5-coder:7b",   "max_iter": 10},
    "reviewer": {"model": "llama3.1:8b",         "max_iter": 3},
}
```
- Planner декомпозирует задачу
- Executor выполняет каждый шаг
- Reviewer проверяет результат

## Зависимости
- VS Code
- Roo Code extension (`ext install RooVetGit.roo-cline`)
- Ollama или API ключ

## Ограничения
- VS Code весит 1.5GB RAM — дорого на 16GB Mac
- На 16GB: ограничить `num_ctx: 8192` в настройках модели
