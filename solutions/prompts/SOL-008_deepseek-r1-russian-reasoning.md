---
id: SOL-008
name: "DeepSeek R1 для reasoning на русском — chain-of-thought анализ"
source_project: "deepseek-ai/DeepSeek-R1"
source_url: "https://www.sitepoint.com/local-llms-apple-silicon-mac-2026/"
category: prompts
tags: [deepseek, reasoning, russian, chain-of-thought, security-analysis, architecture]
quality: 5
applicability: 4
effort: 3
found_by: human-research
found_date: 2026-04-01
---

## Что это
DeepSeek R1 (и его дистилляты) — reasoning модели с explicit chain-of-thought на русском языке. Особенно эффективны для сложных архитектурных ошибок в коде которые требуют многоходового анализа.

## Почему это хорошо
Reasoning модели "думают вслух" перед ответом — `<think>...</think>` блок содержит весь анализ. Для security это критично: модель не угадывает уязвимость, а последовательно её выводит. На русском языке работает на 30-40% точнее чем Llama.

## Как работает
Модель генерирует `<think>` блок перед финальным ответом:
```
<think>
Смотрю на функцию `execute_query(user_input)`.
Параметр передаётся напрямую в SQL запрос без sanitization.
Пользователь контролирует `user_input`.
Это классический SQL Injection...
</think>

Найдена уязвимость SQL Injection в строке 42...
```

## Как применить у нас

**1. Установить через Ollama:**
```bash
ollama pull deepseek-r1:7b      # ~5GB, подходит для 16GB Mac
ollama pull deepseek-r1:14b     # ~9GB, только если RAM > 24GB
```

**2. Использовать в code_auditor агенте:**
```yaml
# security-team/config/agents.yaml
auditor:
  model: deepseek-r1:7b        # вместо qwen2.5-coder:7b
  temperature: 0.1
  max_iter: 12
```

**3. Промпт для reasoning на русском:**
```
Проанализируй код шаг за шагом.
Для каждой функции:
1. Что она делает
2. Какие данные принимает
3. Есть ли контроль этих данных
4. Возможна ли эксплуатация

Думай на русском, отвечай на русском.
```

## Зависимости
- Ollama >= 0.19
- `ollama pull deepseek-r1:7b`
- RAM: минимум 12GB свободных (используй Q4_K_M, см. SOL-002)

## Сравнение с текущим
| | qwen2.5-coder:7b | deepseek-r1:7b |
|--|--|--|
| Скорость | 35 tok/s | 25 tok/s |
| Код | ★★★★☆ | ★★★☆☆ |
| Reasoning | ★★★☆☆ | ★★★★★ |
| Русский | ★★★★☆ | ★★★★☆ |

Рекомендация: qwen для recon/scan, deepseek-r1 для audit (где нужно reasoning).
