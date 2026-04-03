---
id: SOL-005
name: "Architect→Coder→Debug паттерн оркестрации"
source_project: "RooVetGit/Roo-Code"
source_url: "https://github.com/RooVetGit/Roo-Code"
category: orchestration
tags: [roles, planning, execution, debug, multi-agent, pattern]
quality: 5
applicability: 5
effort: 2
found_by: human-research
found_date: 2026-04-01
---

## Что это
Трёхфазный паттерн где разные роли (не агенты) обрабатывают задачу последовательно: Architect планирует, Coder исполняет, Debug разбирает ошибки. Каждая роль имеет свои инструменты и ограничения.

## Почему это хорошо
Специализация по фазам даёт лучшие результаты чем один universal агент: планировщик не отвлекается на детали реализации, исполнитель не занимается архитектурой. Ошибки изолируются в Debug фазе а не прерывают весь pipeline.

## Как работает
```
Входящая задача
       ↓
 [ARCHITECT]
 - Читает задачу
 - Разбивает на шаги
 - Определяет зависимости
 - НЕ пишет код
       ↓ структурированный план
 [CODER]
 - Реализует каждый шаг
 - Пишет файлы, запускает команды
 - При ошибке → передаёт в Debug
       ↓ результат
 [DEBUG] (если ошибка)
 - Анализирует stderr/traceback
 - Предлагает фикс
 - Передаёт обратно в Coder
       ↓
 Финальный результат
```

Ключевое: Architect использует reasoning модель (kimi), Coder — coding модель (qwen), Debug — любую с хорошим пониманием ошибок.

## Как применить у нас

В `dispatcher.py` реализовать как pipeline:
```python
class TaskPipeline:
    def run(self, task: str) -> str:
        # Фаза 1: планирование
        plan = self.architect.plan(task)  # kimi-k2.5:cloud

        # Фаза 2: исполнение
        for step in plan.steps:
            try:
                result = self.coder.execute(step)  # qwen2.5-coder:7b
            except ExecutionError as e:
                # Фаза 3: отладка
                fix = self.debugger.analyze(e)     # llama3.1:8b
                result = self.coder.execute(fix)

        return self.reporter.summarize(results)    # kimi-k2.5:cloud
```

Это прямое улучшение нашего текущего Security Team pipeline.

## Зависимости
- Несколько Ollama моделей (уже есть)
- dispatcher.py (Этап 2 нашего плана)
