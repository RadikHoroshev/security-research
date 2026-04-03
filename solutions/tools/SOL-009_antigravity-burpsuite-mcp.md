---
id: SOL-009
name: "Antigravity — Burp Suite через MCP для AI агентов"
source_project: "antigravity-mcp"
source_url: "https://github.com/PortSwigger/mcp-burp-suite"
category: tools
tags: [mcp, burpsuite, proxy, security, web-testing, traffic-analysis]
quality: 5
applicability: 5
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
MCP сервер который подключает Burp Suite к AI агентам. Агент получает доступ к перехваченному HTTP трафику, может анализировать запросы/ответы и автоматически находить уязвимости.

## Почему это хорошо
Burp Suite — золотой стандарт web security testing. Через MCP агент видит реальный трафик приложения в реальном времени, а не только статические результаты сканеров. Это качественно другой уровень анализа: агент может анализировать session tokens, CSRF patterns, hidden parameters которые nuclei не видит.

## Как работает
```
Browser → Burp Proxy (localhost:8080) → Target
              ↓
         Antigravity MCP
              ↓
         AI Agent (Claude/Goose)
              ↓ анализирует трафик
         "В запросе /api/user?id=123 параметр id
          не валидируется — возможен IDOR"
```

Burp Suite Community Edition бесплатна, Professional — $449/год.

## Как применить у нас
1. Установить Burp Suite Community: `brew install --cask burp-suite`
2. Установить Antigravity MCP в Claude Code settings.json
3. Добавить в Security Team как новый инструмент `BurpTool`
4. Использовать в scanner_agent для анализа реального трафика

Это закроет главный пробел нашего pipeline — мы сканируем снаружи, а Burp видит изнутри.

## Зависимости
- Burp Suite Community (бесплатно) или Professional
- Node.js для MCP сервера
- Доступ к целевому приложению через браузер

## Приоритет
ВЫСОКИЙ — добавить в Этап 4 (Усиление Security Team)
