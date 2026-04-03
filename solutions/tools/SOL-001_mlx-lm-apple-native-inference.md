---
id: SOL-001
name: "MLX-LM — нативный инференс на Apple Silicon"
source_project: "apple/mlx-lm"
source_url: "https://github.com/ml-explore/mlx"
category: tools
tags: [apple-silicon, inference, mlx, performance, local]
quality: 5
applicability: 5
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
MLX-LM — библиотека Apple для запуска LLM напрямую через Metal GPU, без GGUF/llama.cpp overhead. Даёт 40–50 tok/sec на 7B моделях для M2/M3 — в 3 раза быстрее Ollama.

## Почему это хорошо
- Нативная интеграция с Apple Silicon через Metal
- 3× быстрее Ollama на тех же моделях
- Не требует конвертации — работает с MLX-форматом напрямую
- Минимальный overhead: нет Docker, нет лишних прослоек

## Как работает
MLX работает напрямую с унифицированной памятью Apple Silicon через Metal API. Модель загружается в unified memory и обрабатывается GPU без копирования данных между CPU и GPU (в отличие от CUDA-архитектуры).

```bash
pip install mlx-lm
mlx_lm.generate --model mlx-community/Qwen2.5-Coder-7B-Instruct-4bit \
  --prompt "Find SQL injection in this code:" --max-tokens 500
```

## Как применить у нас
Добавить MLX-LM как второй backend в Security Team рядом с Ollama:
1. Установить: `pip install mlx-lm`
2. В `security-team/config/agents.yaml` добавить опцию `backend: mlx`
3. Создать `MLXModel` класс как альтернативу `LLM(model="ollama/...")` в team.py
4. Использовать для recon и scanner агентов где нужна скорость

## Зависимости
- macOS с Apple Silicon (M1/M2/M3/M4)
- Python 3.8+
- `pip install mlx-lm`
- Модели в MLX-формате: `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`

## Ограничения
- Только Apple Silicon (не работает на Intel Mac или Linux)
- Ollama удобнее для управления несколькими моделями
- Для нашего fallback механизма нужно держать оба варианта
