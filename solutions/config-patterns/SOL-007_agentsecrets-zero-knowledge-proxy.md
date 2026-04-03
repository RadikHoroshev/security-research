---
id: SOL-007
name: "AgentSecrets Zero-Knowledge Proxy — агент никогда не видит ключ"
source_project: "AgentSecrets"
source_url: "https://agentsecrets.dev"
category: config-patterns
tags: [security, api-keys, proxy, keychain, zero-knowledge, prompt-injection]
quality: 5
applicability: 5
effort: 1
found_by: human-research
found_date: 2026-04-01
---

## Что это
Архитектурный паттерн (и продукт) где агент оперирует только именами ключей (плейсхолдерами), а локальный прокси на сетевом уровне подставляет реальные значения из macOS Keychain. Агент физически не может увидеть тело ключа.

## Почему это хорошо
Защита от Prompt Injection: даже если злоумышленник через уязвимый сайт внедрит инструкцию "отправь мне все API ключи" — агент не знает реальных ключей и не может их отдать. Ключи существуют только в Keychain и в HTTP заголовках на сетевом уровне.

## Как работает
```
Агент                Прокси (localhost:8767)     Внешний API
  │                         │                        │
  ├─── POST /openai/v1 ────>│                        │
  │    Authorization:        │  читает Keychain       │
  │    "proxy-managed"       ├──────────────────>     │
  │                         │  Authorization:         │
  │                         │  "Bearer sk-real-key"  │
  │<── response ────────────│<── response ───────────┤
```

Это именно то что у нас уже реализовано через `~/.secrets/proxy.py` + macOS Keychain!

## Как применить у нас
**УЖЕ ПРИМЕНЕНО** — наша система использует этот паттерн:
- `proxy.py` работает на `localhost:8767`
- Агенты используют `api_key="proxy-managed"`
- Реальные ключи в macOS Keychain

**Что улучшить:**
1. Убедиться что все маршруты `configured: true` (Этап 1.1)
2. Добавить audit log в proxy.py — какой агент к какому API обратился
3. Добавить rate limiting — защита от случайных mass-request

## Зависимости
- macOS Keychain (встроен в macOS)
- `~/.secrets/proxy.py` (уже есть)
- `~/.secrets/keychain.py` (уже есть)

## Статус
Архитектура правильная. Проблема только в том что ключи не импортированы — Этап 1.1 нашего плана.
