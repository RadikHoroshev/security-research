---
id: SOL-014
name: "Event-Driven Learning Loop — самообучение на основе событий"
source_project: "internal / self_improve.py refactor"
source_url: "N/A"
category: self-improve
tags: [self-improve, event-driven, learning, telemetry, feedback-loop]
quality: 5
applicability: 5
effort: 3
found_by: audit
found_date: 2026-04-01
---

## Что это
Паттерн самообучения, при котором агенты не просто генерируют текстовые отчёты, а испускают структурированные события (events) на каждом шаге выполнения. Эти события собираются в единый поток, анализируются, и на их основе обновляются рейтинги техник, паттерны поведения и конфигурации агентов.

## Почему это хорошо
- **Реальное обучение**: Вместо текстового парсинга отчётов — анализ фактических метрик выполнения.
- **Быстрая обратная связь**: Ошибки и успехи фиксируются мгновенно, а не постфактум.
- **Адаптивность**: Система автоматически подстраивает параметры (timeout, model, tools) на основе истории.
- **Измеримость**: Каждый шаг имеет `latency_ms`, `exit_code`, `confidence`, `evidence_refs` — можно строить дашборды.

## Как работает
1. **Event Emission**: Каждый инструмент/агент при завершении шага записывает событие:
   ```json
   {
     "event_id": "evt_001",
     "task_id": "recon_001",
     "agent": "recon",
     "tool": "subfinder",
     "args_hash": "a1b2c3d4",
     "latency_ms": 1250,
     "exit_code": 0,
     "output_size_bytes": 4500,
     "confidence": 0.85,
     "evidence_refs": ["subdomains.txt", "live_hosts.txt"],
     "timestamp": "2026-04-01T10:00:00Z"
   }
   ```
2. **Event Collection**: События пишутся в `knowledge/events.db` (SQLite) или JSONL-файл.
3. **Analysis**: `self_improve.py` анализирует события:
   - Успешные техники → повышают рейтинг
   - Ошибки/таймауты → понижают рейтинг, добавляют в `noisy_techniques`
   - Паттерны → обновляют `proven_techniques` в `research.yaml`
4. **Feedback**: Обновлённые конфиги загружаются при следующем запуске без перезапуска системы.

## Как применить у нас
1. **Рефакторинг `team.py`**:
   - Вместо передачи `agent_logs` как строки — передавать список событий (dict).
   - Добавить `emit_event()` обёртку вокруг каждого вызова инструмента.
2. **Обновление `db.py`**:
   - Добавить таблицу `events`:
     ```sql
     CREATE TABLE events (
       id INTEGER PRIMARY KEY,
       event_id TEXT UNIQUE,
       task_id TEXT,
       agent TEXT,
       tool TEXT,
       latency_ms INTEGER,
       exit_code INTEGER,
       confidence REAL,
       evidence_refs TEXT,
       created_at TEXT
     );
     ```
   - Индексы на `task_id`, `agent`, `tool`.
3. **Обновление `self_improve.py`**:
   - Заменить парсинг текста на анализ событий из БД.
   - Рассчитывать `success_rate`, `avg_latency`, `error_rate` по каждой технике.
   - Автоматически обновлять `agents.yaml` (например, менять `max_iter` или `model` если техника стабильно падает).
4. **CLI для анализа**:
   - `python3 self_improve.py --analyze-events --last 100` — показать топ техник.
   - `python3 self_improve.py --export-lessons` — сгенерировать `lessons.md`.

## Зависимости
- Python 3.11+
- Рефакторинг `team.py` (добавление event emission)
- Обновление `db.py` (новая таблица `events`)
- `self_improve.py` (новый анализатор событий)

## Ограничения
- **Накладные расходы**: Запись событий добавляет ~5-10% overhead к выполнению.
- **Хранение**: При интенсивном использовании events.db может расти быстро (нужна ротация).
- **Сложность**: Требует дисциплины — каждый инструмент должен корректно испускать события, иначе данные будут неполными.
- **Миграция**: Существующие данные в `patterns` и `errors` нужно будет мигрировать или оставить как legacy.
