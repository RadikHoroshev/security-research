---
id: SOL-011
name: "1Password CLI — инъекция секретов в runtime без .env файлов"
source_project: "1Password/onepassword-operator"
source_url: "https://developer.1password.com/docs/cli"
category: config-patterns
tags: [secrets, 1password, security, runtime, no-env, keychain, alternative]
quality: 4
applicability: 3
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
1Password CLI (`op`) позволяет инжектировать секреты напрямую в переменные окружения в момент запуска процесса, без создания .env файлов на диске.

## Почему это хорошо
.env файлы на диске — риск: их можно случайно закоммитить, прочитать другому процессу, найти в swap. 1Password CLI инжектирует секреты только в память процесса через `op run`.

## Как работает
```bash
# Вместо: export OPENAI_API_KEY=sk-...
# Используй:
op run --env-file=.env.template -- python3 my_agent.py

# .env.template содержит только ссылки:
OPENAI_API_KEY=op://Personal/OpenAI/api_key
ANTHROPIC_API_KEY=op://Personal/Anthropic/api_key
```

1Password CLI расшифровывает значения из vault и инжектирует в env процесса. Ни один файл на диске не содержит реального ключа.

## Как применить у нас
**Сравнение с нашим решением:**

| | Наш proxy.py | 1Password CLI |
|--|--|--|
| Ключи в контексте агента | НЕТ | НЕТ |
| Хранение | macOS Keychain | 1Password Vault |
| Работа без интернета | ДА | ДА (локальный vault) |
| Стоимость | Бесплатно | $3/мес |
| Поддержка агентов | Через HTTP proxy | Через env vars |

**Вывод:** Наш подход через macOS Keychain + proxy.py лучше для агентов (не нужен env). 1Password полезен как резервный вариант для скриптов.

## Зависимости
- `brew install 1password-cli`
- Аккаунт 1Password ($3/мес)

## Статус
НЕ ПРИОРИТЕТНО — наш proxy.py решает ту же задачу бесплатно
