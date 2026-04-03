---
id: SOL-006
name: "Sequential Thinking MCP — принудительное пошаговое планирование"
source_project: "modelcontextprotocol/servers"
source_url: "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"
category: tools
tags: [mcp, chain-of-thought, planning, anti-hallucination, quality]
quality: 5
applicability: 5
effort: 1
found_by: human-research
found_date: 2026-04-01
---

## Что это
MCP сервер который принуждает модель к явному пошаговому планированию перед выполнением. Модель не может перейти к следующему шагу не завершив предыдущий. Резко снижает галлюцинации при сложных задачах.

## Почему это хорошо
Без структурированного мышления модели "перескакивают" к ответу минуя логические шаги. Sequential Thinking MCP делает chain-of-thought обязательным — особенно критично для security analysis где пропущенный шаг = false negative.

## Как работает
MCP сервер предоставляет инструмент `think` который принимает текущий шаг и возвращает подтверждение. Модель вынуждена явно вызывать `think(step=1, content="...")` перед переходом к `think(step=2, ...)`.

```json
// В Claude Code settings.json добавить:
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

Применение в Security Team — добавить в system prompt агентов:
```
Before each action, use the 'think' tool to explicitly state:
1. What you know
2. What you need to find out
3. What action you will take
4. What result you expect
```

## Как применить у нас
1. Установить MCP сервер (1 команда)
2. Добавить в Claude Code settings.json
3. Включить в backstory агентов security-team инструкцию использовать structured thinking
4. Особенно полезно для reporter_agent при CVSS оценке

## Зависимости
- Node.js / npx (уже есть)
- Добавить в settings.json

## Влияние на качество
Согласно исследованиям: +15-25% точность при анализе безопасности когда модель явно формулирует reasoning steps.
