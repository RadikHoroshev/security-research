# Multi-Agent System Configuration

**Версия:** 3.2 — Qwen Desktop Only (No CLI)  
**Дата:** 2026-04-03  
**Статус:** ACTIVE  
**Оркестратор:** Goose v1.29.0

---

## 🎯 Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Goose Orchestrator                   │
│  Extensions: Terminal, Browser, Filesystem, GitHub      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────
        │            │            │
        ▼            ▼            ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│   Qwen    │  │  Gemini   │  │   Jules   │
│  Desktop  │  │    CLI    │  │    CLI    │
│   (GUI)   │  │           │  │           │
└───────────┘  └───────────┘  └───────────┘
   Code/Analysis   Recon/      Documentation
   (Manual)        Reports     (Auto)
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────▼────────────┐
        │   File Protocol Layer   │
        │  queue/*.json → results │
        └─────────────────────────┘
```

---

## 🤖 Агенты (Активные — Только CLI + GUI)

| ID | Агент | Тип | Запуск | Сильные Стороны | Гибкая Роль |
|----|-------|-----|--------|-----------------|-------------|
| **A1** | `qwen-desktop` | **GUI (локальный)** | **Ручное копирование промпта** | Глубокий анализ, PoC, код | Analyst / ExploitDev / Reviewer |
| **A2** | `gemini-cli` | CLI (cloud) | `gemini -p "PROMPT" --yolo` | Веб-поиск, Huntr, отчёты | Recon / Reporter / DuplicateCheck |
| **A3** | `jules-cli` | CLI (локальный) | `jules "PROMPT"` | Документация, логи, GitHub | Scribe / Logger / DocWriter |
| **A4** | `goose` | Orchestrator | `goose run FILE.md` | Terminal + Browser + FS | Coordinator / Executor |

> ⚠️ **qwen-desktop требует ручного копирования** — нет CLI автоматизации, только GUI интерфейс.
> 
> 🔒 **qwen-cli исключён** — ненадёжный, требует `-y` флага, проблемы с подтверждением команд.

---

## 📁 Протокол Взаимодействия (PROTOCOL.md v2)

### Структура Файлов
```
intel/
├── queue/                  # Задачи (пишет Координатор)
│   └── {phase}_{task}.json
├── results/                # Результаты (пишут Агенты)
│   └── {phase}_{agent}.json
├── SESSION_LOG.md          # Журнал сессии
├── SESSION_ERRORS.md       # Извлечённые уроки
├── MULTI_AGENT_CONFIG.md   # Этот файл
├── AGENT_ROLES.md          # Текущие назначения ролей (dynamic)
└── prompts/                # Готовые промпты для Qwen Desktop
    └── phase2_qwen_prompt.txt
```

### Формат Задачи (Queue)
```json
{
  "phase": 2,
  "task": "clone_and_scan",
  "target": "mlflow/mlflow",
  "assigned_agent": "qwen-desktop",
  "execution_mode": "manual",
  "prompt_file": "prompts/phase2_qwen_prompt.txt",
  "args": {
    "clone_path": "/tmp/mlflow",
    "tools": ["bandit", "semgrep", "gitleaks"],
    "focus": ["file_upload", "path_handling"]
  },
  "output": "results/phase2_qwen.json",
  "timeout_sec": 300,
  "priority": "high"
}
```

### Формат Результата (Results)
```json
{
  "phase": 2,
  "agent": "qwen-desktop",
  "status": "ok|fail|partial|skip",
  "ts": 1712160000,
  "duration_sec": 145,
  "data": {
    "vulnerabilities": [],
    "suspicious_files": [],
    "endpoints": []
  },
  "errors": []
}
```

---

## 🔄 Пайплайн Bug Bounty (5 Этапов)

| Этап | Задача | Агент | Режим | Выход |
|------|--------|-------|-------|-------|
| **1** | Поиск целей на Huntr | `gemini-cli` | ✅ Авто | `results/phase1_gemini.json` |
| **2** | Clone + Scan кода | `qwen-desktop` | ⚠️ **Ручной** | `results/phase2_qwen.json` |
| **3** | Глубокий анализ | `qwen-desktop` | ⚠️ **Ручной** | `results/phase3_analysis.json` |
| **4** | PoC + Верификация | `qwen-desktop` | ⚠️ **Ручной** | `results/phase4_poc.json` |
| **5** | Отчёт + Сабмит | `gemini-cli` + `jules-cli` | ✅ Авто | `results/final_report.md` |

---

## 🚀 Команды Агентам

### A1: Qwen Desktop (Ручное Копирование)

**Шаг 1:** Открой Qwen Desktop приложение  
**Шаг 2:** Скопируй промпт из `intel/prompts/phase2_qwen_prompt.txt`  
**Шаг 3:** Вставь в Qwen Desktop и отправь  
**Шаг 4:** Дождись результата в `results/phase2_qwen.json`

**Пример промпта для Phase 2:**
```
Read /Users/code/project/intel/queue/phase2_analyze.json.
Target: mlflow/mlflow. Clone to /tmp/mlflow.
Run bandit -r /tmp/mlflow -f json.
Find file upload endpoints.
Output JSON to /Users/code/project/intel/results/phase2_qwen.json
```

### A2: Gemini CLI (Автоматически)
```bash
export PATH="/opt/homebrew/bin:$PATH" && \
gemini -p 'Read queue/phase1_find_targets.json. 
Search huntr.com/bounties/disclose/opensource. 
Output JSON to results/phase1_gemini.json' --yolo
```

### A3: Jules CLI (Автоматически)
```bash
jules "Update SESSION_LOG.md: Phase 2 complete, 3 vulnerabilities found in mlflow"
```

### A4: Goose Orchestrator (Автоматически)
```bash
cd /Users/code/project/intel && goose run phase1_instruction.md
```

---

## 🧩 Масштабируемость

### Добавление Нового Агента

1. **Создай паспорт агента** в `intel/agents/{agent_id}.md`
2. **Обнови `MULTI_AGENT_CONFIG.md`** — добавь строку в таблицу
3. **Укажи режим выполнения:** `auto` (CLI) или `manual` (GUI)

### Динамическая Смена Ролей

Измени назначение в файме задачи:
```json
{
  "phase": 2,
  "assigned_agent": "goose",
  "execution_mode": "auto"
}
```

---

## ⚠️ Известные Ошибки (SESSION_ERRORS.md)

| # | Ошибка | Решение |
|---|--------|---------|
| 1 | React-dropdown не кликается | javascript_tool или ручной гайд |
| 2 | Вкладка браузера hidden | `show()` + пауза 2 сек |
| 3 | Фон-процессы теряют вывод | Запускать синхронно (без `&`) |
| 4 | Субагенты без сетевых прав | Веб-поиск напрямую в главном контексте |
| 5 | ~~Qwen 14b медленно~~ | **РЕШЕНО: Qwen Desktop GUI** |
| 6 | ~~Qwen CLI требует -y~~ | **РЕШЕНО: Убран Qwen CLI** |
| 7 | Неправильная цель (AnythingLLM) | Приоритет: звёзды < 10k, Python/Node + file upload |

---

## 📊 Текущая Сессия

| Этап | Статус | Цель | Агент | Режим | Результат |
|------|--------|------|-------|-------|-----------|
| **1** | ✅ DONE | huntr.com | gemini-cli | Авто | 5 targets, `mlflow/mlflow` |
| **2** | 🔄 READY | mlflow/mlflow | qwen-desktop | **Ручной** | Задача в `queue/phase2_analyze.json` |
| **3** | ⏳ PENDING | — | — | — | — |
| **4** | ⏳ PENDING | — | — | — | — |
| **5** | ⏳ PENDING | — | — | — | — |

---

## 🎯 Быстрый Старт

```bash
# 1. Проверка CLI агентов
gemini --version && jules --version && goose --version

# 2. Проверка очереди
cat /Users/code/project/intel/queue/*.json

# 3. Phase 2 (Qwen Desktop - вручную)
# Открой Qwen Desktop → скопируй промпт из prompts/phase2_qwen_prompt.txt

# 4. Проверка результата
cat /Users/code/project/intel/results/phase2_qwen.json
```

---

**Создано:** 2026-04-03  
**Обновлено:** 2026-04-03 (v3.2 — Qwen Desktop GUI Only)  
**Следующая проверка:** После каждого этапа
