# INTEL — Библиотека технических решений

**Назначение:** Структурированное хранилище лучших решений из open-source проектов.
**Цель:** Собрать лучшее из чужих проектов и применить в нашей системе.
**Формат:** Оптимизирован для работы AI-агентов — frontmatter, теги, ссылки.

---

## Структура

```
intel/
├── README.md                ← Этот файл (индекс)
├── synthesis.md             ← Финальный анализ: что берём, что нет
├── projects/                ← Разборы проектов (1 файл = 1 проект)
└── solutions/               ← Извлечённые решения по категориям
    ├── orchestration/       ← Паттерны оркестрации агентов
    ├── prompts/             ← Эффективные промпты и роли
    ├── pipelines/           ← Архитектуры пайплайнов
    ├── tools/               ← Интеграции инструментов
    ├── self-improve/        ← Механизмы самообучения
    └── config-patterns/     ← Конфигурации и схемы
```

## Статус решений

| Статус          | Решения                                                       |
| --------------- | ------------------------------------------------------------- |
| ✅ **ADOPT**    | SOL-002, SOL-005, SOL-006, SOL-007, SOL-009, SOL-013, SOL-014 |
| 🟡 **EVALUATE** | SOL-001, SOL-008, SOL-012                                     |
| 🔴 **DEFER**    | SOL-003, SOL-004, SOL-010, SOL-011                            |

_Подробная матрица решений и roadmap: `intel/synthesis.md`_

---

## Индекс проектов

| ID  | Проект                                       | Категория                  | Статус | Решений извлечено |
| --- | -------------------------------------------- | -------------------------- | ------ | ----------------- |
| P1  | MacBook Pro 16GB AI Ecosystem 2026 — часть 1 | tools/config/orchestration | DONE   | 8                 |
| P2  | MacBook Pro 16GB AI Ecosystem 2026 — часть 2 | tools/config/market-data   | DONE   | 4                 |

---

## Индекс решений

| ID      | Название                                                    | Категория       | Источник             | Quality | Applicability |
| ------- | ----------------------------------------------------------- | --------------- | -------------------- | ------- | ------------- |
| SOL-001 | MLX-LM — нативный инференс Apple Silicon                    | tools           | apple/mlx-lm         | 5       | 5             |
| SOL-002 | Q4_K_M квантование — формула для 16GB RAM                   | config-patterns | sitepoint.com        | 5       | 5             |
| SOL-003 | Zed + ACP/MCP — лёгкий кокпит для агентов                   | tools           | zed.dev              | 4       | 3             |
| SOL-004 | Roo Code — ролевые режимы автономного агента                | tools           | RooVetGit/Roo-Code   | 4       | 4             |
| SOL-005 | Architect→Coder→Debug паттерн оркестрации                   | orchestration   | Roo Code             | 5       | 5             |
| SOL-006 | Sequential Thinking MCP — принудительное планирование       | tools           | modelcontextprotocol | 5       | 5             |
| SOL-007 | AgentSecrets Zero-Knowledge Proxy                           | config-patterns | agentsecrets.dev     | 5       | 5             |
| SOL-008 | DeepSeek R1 для reasoning на русском                        | prompts         | deepseek-ai          | 5       | 4             |
| SOL-009 | Antigravity — Burp Suite через MCP                          | tools           | PortSwigger/mcp-burp | 5       | 5             |
| SOL-010 | OpenCode — лёгкая IDE air-gapped                            | tools           | sst/opencode         | 4       | 3             |
| SOL-011 | 1Password CLI — инъекция секретов в runtime                 | config-patterns | 1Password            | 4       | 3             |
| SOL-012 | Bug Bounty рынок 2026 — стратегические данные               | config-patterns | HackerOne Report     | 5       | 5             |
| SOL-013 | DAG Orchestration — граф задач вместо последовательности    | pipelines       | internal / audit     | 5       | 5             |
| SOL-014 | Event-Driven Learning Loop — самообучение на основе событий | self-improve    | internal / audit     | 5       | 5             |

---

## Как пользоваться

### Для агента-исследователя:

1. Открой ТЗ: `research/R7_TECH_INTELLIGENCE.md`
2. Выбери проект из списка
3. Проанализируй по методике (Шаги 1-4)
4. Сохрани проект в `intel/projects/NAME.md`
5. Сохрани решения в `intel/solutions/CATEGORY/SOL-XXX.md`
6. Обнови этот индекс

### Для агента-разработчика:

1. Открой `intel/synthesis.md` — там топ решений для внедрения
2. Или ищи по категории в `intel/solutions/`
3. Каждое решение содержит "Как применить у нас"

### Для координатора:

1. `intel/synthesis.md` — полная картина
2. Этот файл — статус исследования

---

_Создано: 2026-04-01_
