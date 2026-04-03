---
id: SOL-002
name: "Q4_K_M квантование — золотой стандарт для 16GB RAM"
source_project: "llama.cpp / Ollama"
source_url: "https://www.sitepoint.com/best-local-llm-models-2026/"
category: config-patterns
tags: [quantization, memory, ollama, 16gb, optimization, q4km]
quality: 5
applicability: 5
effort: 1
found_by: human-research
found_date: 2026-04-01
---

## Что это
Конкретная формула распределения памяти для 16GB Mac при запуске 7B моделей: Q4_K_M квантование оставляет оптимальный баланс между качеством и использованием памяти.

## Почему это хорошо
Протестированная формула для 16GB: модель 5.5GB + система 6GB + KV-cache 4GB = 15.5GB. Система не уходит в swap, нет деградации SSD.

## Как работает
```
7B модель @ Q4_K_M:
  Веса модели:  ~5.5 GB
  Система/ОС:   ~6.0 GB  (macOS + фоновые процессы)
  KV-cache:     ~4.0 GB  (контекст 8192 токенов)
  ─────────────────────
  Итого:        ~15.5 GB  ← безопасно для 16GB

7B модель @ Q8:
  Веса модели: ~8.5 GB   ← уже риск swap при 16GB
```

Ограничение контекста до 8192 токенов критично — при 16384 KV-cache вырастает до ~8GB и система уходит в swap.

## Как применить у нас
В `security-team/config/agents.yaml` зафиксировать:
```yaml
recon:
  model: qwen2.5-coder:7b   # всегда Q4_K_M
  num_ctx: 8192              # НЕ больше, иначе swap

scanner:
  model: qwen2.5-coder:7b
  num_ctx: 8192

reporter:
  model: kimi-k2.5:cloud     # облачная — без ограничений RAM
```

В Ollama Modelfile добавить:
```
PARAMETER num_ctx 8192
```

## Зависимости
- Ollama с поддержкой параметра `num_ctx`
- Модели в формате GGUF Q4_K_M (по умолчанию в Ollama)
