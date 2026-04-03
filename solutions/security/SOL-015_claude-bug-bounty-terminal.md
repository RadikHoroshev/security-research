---
id: SOL-015
name: "claude-bug-bounty — Terminal AI Bug Bounty Hunter"
source_project: "https://github.com/shuvonsec/claude-bug-bounty"
category: security
tags: [bug-bounty, claude-code, terminal, recon, vulnerability-scanning, autonomous]
quality: 4
applicability: 4
effort: 1
found_by: scout
found_date: 2026-04-02
---

## Что это
Терминальный инструмент на базе Claude Code для автономной охоты за багами: recon, 20 классов уязвимостей, генерация отчётов — всё внутри одной команды.

## Почему это хорошо
Минимальная установка (просто Claude Code + этот инструмент), покрывает 20 классов уязвимостей и автоматически генерирует готовые bug bounty отчёты.

## Как работает
Инструмент оборачивает Claude Code slash-команды в структурированный bug bounty workflow: /recon для сбора информации о цели, автоматический выбор векторов атаки из 20 классов (SQLi, XSS, SSRF, RCE и др.), автономное тестирование через shell-инструменты, финальная генерация отчёта в формате HackerOne/Bugcrowd.

## Как применить у нас
Установить как дополнение к существующему security-team MCP. Использовать для быстрого первичного сканирования новых целей перед запуском полного CrewAI-пайплайна. Интегрировать report-генератор в наш workflow через `security-team/mcp/server.py`.

## Зависимости
```bash
git clone https://github.com/shuvonsec/claude-bug-bounty
# требует: Claude Code CLI, стандартные security-инструменты (nmap, curl, subfinder)
```
