# AGENT PASSPORTS — Технические характеристики агентов

**Создано:** 2026-04-03  
**Обновлено:** 2026-04-03  
**Статус:** ACTIVE  
**Соответствие:** A2A Protocol v1.0.0 ✅

---

## 📋 Оглавление

1. [Coordinator (Claude)](#coordinator-claude)
2. [Qwen Coder](#qwen-coder)
3. [Gemini](#gemini)
4. [Jules](#jules)
5. [Qwen Code](#qwen-code)
6. [A2A Integration](#a2a-integration)
7. [JSON Schema](#json-schema)

---

## 🤖 Coordinator (Zed IDE)

### Agent Card

```json
{
  "name": "Coordinator (Zed IDE)",
  "description": "AI-ассистент в Zed IDE для управления мульти-агентной системой безопасности",
  "roles": [
    "orchestrator",
    "validator",
    "decision_maker",
    "architect",
    "system_designer"
  ],
  "capabilities": {
    "task_delegation": true,
    "result_validation": true,
    "session_management": true,
    "go_no_go_decisions": true,
    "architecture_design": true,
    "code_review": true,
    "documentation_generation": true,
    "multi_agent_coordination": true,
    "context_management": true,
    "tool_selection": true,
    "file_operations": true,
    "json_schema_validation": true,
    "protocol_design": true,
    "workflow_optimization": true
  },
  "potential": {
    "model": "Claude via Zed IDE (Anthropic API)",
    "context_window": "200K tokens",
    "response_time": "1-3 seconds (receive) + N minutes (process)",
    "best_for": [
      "system_architecture",
      "task_orchestration",
      "code_review",
      "documentation",
      "protocol_design",
      "agent_coordination",
      "decision_making"
    ],
    "limitations": [
      "no_direct_code_execution",
      "no_network_access",
      "no_local_shell",
      "requires_human_approval_for_destructive_ops",
      "50KB_output_limit"
    ],
    "api_access": true,
    "local_only": false
  },
  "tools": [
    "read_file",
    "edit_file",
    "list_directory",
    "grep",
    "find_path",
    "spawn_agent",
    "qwen_code",
    "claude_cli",
    "codex_cli",
    "openclaw_cli",
    "file_system_operations",
    "json_schema_validation",
    "mcp_tools (30+ servers)"
  ],
  "endpoints": {
    "input": "chat_context",
    "output": "queue/{phase}{task}.json",
    "read": "results/{phase}{agent}.json",
    "logs": "intel/SESSION_LOG.md"
  },
  "constraints": {
    "max_result_size": "50KB",
    "no_heavy_computation": true,
    "manual_approval_required": true,
    "no_destructive_operations_without_confirmation": true
  }
}
```

### Технические характеристики

| Параметр         | Значение                                                                                                                                           |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Имя**          | Coordinator (Zed IDE)                                                                                                                              |
| **Тип**          | AI Assistant в Zed IDE (via Anthropic API)                                                                                                         |
| **Платформа**    | Zed Editor (zed.dev)                                                                                                                               |
| **AI Провайдер** | Claude via Zed IDE                                                                                                                                 |
| **Роли**         | IDE Assistant, Orchestrator, Validator, Decision Maker, Architect                                                                                  |
| **Возможности**  | IDE integration, Task delegation, Result validation, Session management, Architecture design, Code review, Documentation, Multi-agent coordination |
| **Потенциал**    | 200K context, real-time inline, best for: ide_assistance, orchestration, design, review                                                            |
| **Инструменты**  | Zed panels, inline assist, file_ops, grep, spawn_agent, qwen_code, MCP tools, JSON validation                                                      |
| **Ограничения**  | No code execution, no network, no shell, 50KB output limit, requires Zed IDE                                                                       |

### Возможности (Capabilities)

| Capability                   | Описание                             | Использовать когда...                           |
| ---------------------------- | ------------------------------------ | ----------------------------------------------- |
| **Task Delegation**          | Распределение задач между агентами   | Нужно выполнить специализированную работу       |
| **Result Validation**        | Проверка результатов от агентов      | Получен результат, нужна проверка               |
| **Session Management**       | Управление контекстом и состоянием   | Длительная сессия, нужна память о прошлых шагах |
| **Go/No-Go Decisions**       | Принятие решений о продолжении       | Нужно решение по риску/качеству                 |
| **Architecture Design**      | Проектирование систем и протоколов   | Нужна архитектура новой системы                 |
| **Code Review**              | Ревью кода без выполнения            | Нужна проверка кода, не запуск                  |
| **Documentation**            | Создание документации                | Нужен протокол, гайд, схема                     |
| **Protocol Design**          | Разработка протоколов взаимодействия | Нужен новый формат обмена данными               |
| **Multi-Agent Coordination** | Координация нескольких агентов       | Задача требует несколько агентов                |
| **Context Management**       | Управление большим контекстом        | Сложная система, много компонентов              |
| **Tool Selection**           | Выбор подходящих инструментов        | Нужно решить какими инструментами пользоваться  |
| **JSON Schema Validation**   | Проверка схем данных                 | Работа с task/result файлами                    |

### Потенциал (Potential)

| Параметр             | Значение                         | Комментарий                             |
| -------------------- | -------------------------------- | --------------------------------------- |
| **Контекст**         | 200K tokens                      | Огромный контекст для понимания системы |
| **Скорость ответа**  | 1-3 секунды                      | Получение задачи                        |
| **Время обработки**  | 1-5 минут                        | Зависит от сложности                    |
| **Лучше всего для**  | Архитектура, Оркестрация, Ревью  | Стратегические задачи                   |
| **Ограничения**      | Нет выполнения кода, сети, shell | Делегирую это другим агентам            |
| **API**              | Anthropic API                    | Через proxy (localhost:8768)            |
| **Локальная работа** | Нет                              | Облачный сервис                         |

### Инструменты (Tools)

| Инструмент         | Назначение            | Пример использования              |
| ------------------ | --------------------- | --------------------------------- |
| **read_file**      | Чтение файлов         | Анализ кода, документов           |
| **edit_file**      | Редактирование файлов | Создание/обновление документов    |
| **list_directory** | Список директорий     | Исследование структуры            |
| **grep**           | Поиск в файлах        | Поиск символов, паттернов         |
| **find_path**      | Поиск файлов          | Нахождение файлов                 |
| **spawn_agent**    | Запуск агентов        | Делегация задач                   |
| **qwen_code**      | Вызов Qwen            | Анализ кода, сканирование         |
| **claude_cli**     | Вызов Claude CLI      | Резервный канал                   |
| **codex_cli**      | Вызов Codex           | Альтернативный агент              |
| **openclaw_cli**   | Вызов OpenClaw        | Альтернативный агент              |
| **MCP tools**      | 30+ серверов          | Security, k8s, Google Suite, etc. |
| **json_schema**    | Валидация JSON        | Проверка task/result схем         |

### Endpoints

| Тип        | Путь/Метод                         | Описание                        |
| ---------- | ---------------------------------- | ------------------------------- |
| **Ввод**   | Chat context                       | Получение задач от пользователя |
| **Вывод**  | `queue/{phase}{task}.json`         | Создание задач для агентов      |
| **Чтение** | `results/{phase}{agent}.json`      | Чтение результатов              |
| **Логи**   | `intel/SESSION_LOG.md`             | Фиксация решений                |
| **API**    | `proxy-managed` via localhost:8768 | Anthropic API через прокси      |

### SLA

| Параметр            | Значение    | Примечание             |
| ------------------- | ----------- | ---------------------- |
| **Время ответа**    | 1-3 секунды | На получение задачи    |
| **Время обработки** | 1-5 минут   | Зависит от сложности   |
| **Контекст**        | 200K tokens | Общий контекст сессии  |
| **Лимит вывода**    | 50KB        | На один результат      |
| **Надёжность**      | High        | Облачный API Anthropic |
| **Доступность**     | 24/7        | Кроме тех. работ       |

### Типовые задачи (Typical Tasks)

| Задача                       | Вход                     | Выход                       | Примерное время |
| ---------------------------- | ------------------------ | --------------------------- | --------------- |
| **System Design**            | Требования               | Архитектура + документация  | 5-10 мин        |
| **Task Delegation**          | Цель + контекст          | Задачи в queue/\*.json      | 1-3 мин         |
| **Code Review**              | Ссылка на PR/файл        | Отчёт о проверке            | 3-5 мин         |
| **Protocol Design**          | Требования к обмену      | JSON Schema + описание      | 10-15 мин       |
| **Multi-Agent Coordination** | Сложная задача           | Очередь задач + оркестрация | 5-10 мин        |
| **Documentation Update**     | Изменения в системе      | Обновлённые документы       | 3-7 мин         |
| **Architecture Review**      | Существующая архитектура | Рекомендации по улучшению   | 5-10 мин        |

### Когда обращаться к Coordinator

| Ситуация                       | Что делает Coordinator                     |
| ------------------------------ | ------------------------------------------ |
| Нужно спроектировать систему   | Создаёт архитектуру, документацию          |
| Нужно выполнить сложную задачу | Разбивает на подзадачи, делегирует агентам |
| Получен результат от агента    | Валидирует, принимает решение go/no-go     |
| Нужна документация             | Создаёт протоколы, гайды, схемы            |
| Нужно принять решение          | Анализирует, советует, ждёт подтверждения  |
| Что-то пошло не так            | Анализирует ошибку, планирует исправление  |

---

## 🤖 Qwen Coder

### Agent Card

```json
{
  "name": "Qwen Coder",
  "description": "Security Researcher и Code Analyst для локального анализа кода",
  "roles": ["security_researcher", "code_analyst", "poc_writer"],
  "capabilities": {
    "repo_cloning": true,
    "static_analysis": true,
    "vulnerability_scanning": true,
    "endpoint_discovery": true,
    "poc_generation": true
  },
  "endpoints": {
    "api": "http://localhost:11434/api/generate",
    "mcp": "qwen_ask"
  },
  "constraints": {
    "local_only": true,
    "slow_on_large_context": true,
    "max_context_tokens": 32768
  }
}
```

### Технические характеристики

| Параметр            | Значение                                                                                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Роль**            | Security Researcher / Code Analyst                                                                                                                                                          |
| **Тип**             | Local LLM via Ollama                                                                                                                                                                        |
| **Модели**          | `qwen2.5-coder:14b` (основная), `qwen2.5-coder:7b` (быстрые задачи)                                                                                                                         |
| **Ответственность** | Clone репозиториев в `/tmp/`, Запуск `bandit -r /tmp/REPO -ll -f json`, Запуск `semgrep --config auto /tmp/REPO --json`, Поиск HTTP endpoints и file upload функций, Написание PoC скриптов |
| **Ограничения**     | Медленный (3-5 минут на большой промпт), Для быстрых задач использовать `qwen2.5-coder:7b`, Только локальный доступ                                                                         |

### Endpoints

| Тип | Путь                 | Описание               |
| --- | -------------------- | ---------------------- |
| API | `POST /api/generate` | Ollama API endpoint    |
| MCP | `qwen_ask`           | MCP server integration |

### SLA

| Параметр              | Значение                         |
| --------------------- | -------------------------------- |
| Время ответа          | 3-5 минут (14b), 1-2 минуты (7b) |
| Максимальный контекст | 32K токенов                      |
| Лимит результата      | 50KB                             |

### Формат ввода

```json
{
  "task": "string",
  "repo_path": "string",
  "scan_type": "bandit|semgrep|endpoint_search",
  "output_format": "json"
}
```

### Формат вывода

```json
{
  "status": "success|error",
  "findings": [],
  "summary": "string",
  "artifacts": {
    "poc_script": "string",
    "endpoints": []
  }
}
```

---

## 🤖 Gemini

### Agent Card

```json
{
  "name": "Gemini",
  "description": "Advanced CLI Orchestrator & Generalist — автономный агент для исследования, кодинга и управления системой",
  "roles": ["orchestrator", "generalist", "researcher", "coder", "debugger"],
  "capabilities": {
    "code_analysis": true,
    "code_generation": true,
    "shell_execution": true,
    "file_operations": true,
    "web_search": true,
    "report_generation": true,
    "mcp_integration": true,
    "skill_activation": true,
    "task_delegation": true,
    "local_execution": true,
    "api_access": true
  },
  "potential": {
    "model": "Gemini 2.0 Flash / Pro (Google AI)",
    "max_context_tokens": "1M+ tokens",
    "response_time": "3-15 секунд",
    "network_access": true,
    "filesystem_access": true,
    "best_for": [
      "complex_codebase_investigation",
      "multi_step_problem_solving",
      "system_refactoring",
      "security_research",
      "task_automation"
    ],
    "limitations": [
      "requires_api_key (via proxy)",
      "approval_required_for_modifying_commands"
    ]
  },
  "tools": [
    "read_file (чтение)",
    "write_file (запись)",
    "replace (хирургическое редактирование)",
    "run_shell_command (bash)",
    "grep_search (ripgrep)",
    "glob (поиск файлов)",
    "web_fetch (анализ URL)",
    "google_web_search (поиск)",
    "codebase_investigator (анализ системы)",
    "activate_skill (23+ Azure skills)",
    "generalist (sub-agent)",
    "save_memory (global facts)"
  ],
  "typical_tasks": [
    {
      "name": "Codebase Investigation",
      "description": "Глубокий анализ архитектуры и поиск багов",
      "input": "Описание проблемы или вопроса",
      "output": "Структурированный отчет с путями и символами",
      "duration": "2-5 мин"
    },
    {
      "name": "Surgical Refactoring",
      "description": "Точечное исправление кода без регрессий",
      "input": "Цель изменения + контекст",
      "output": "Проверенный и оттестированный код",
      "duration": "3-7 мин"
    }
  ]
}
```

### Технические характеристики

| Параметр            | Значение                                   |
| ------------------- | ------------------------------------------ |
| **Роль**            | Advanced CLI Orchestrator                  |
| **Тип**             | Cloud Hybrid (API + Local Tools)           |
| **Модель**          | Gemini 2.0 (Google AI)                     |
| **Ответственность** | Координация, Исследование, Кодинг, Тулчейн |
| **Ограничения**     | Требует API ключ через прокси              |

### Endpoints

| Тип   | Значение                           | Описание                    |
| ----- | ---------------------------------- | --------------------------- |
| API   | `proxy-managed` via localhost:8768 | Google AI API через прокси  |
| CLI   | `npx @google/gemini-cli`           | Прямой вызов CLI            |
| MCP   | Интегрирован                       | Доступ к 30+ MCP серверам   |

### SLA

| Параметр       | Значение                           |
| -------------- | ---------------------------------- |
| Время ответа   | 5-15 секунд                        |
| Контекст       | До 1,000,000 токенов               |
| Надёжность     | High (Google Cloud Infrastructure) |
| Сетевой доступ | Разрешён                           |

### Формат ввода

```bash
gemini -p "Найти цели для bug bounty на huntr.com" --yolo
```

### Формат вывода

```json
{
  "targets": [
    {
      "name": "string",
      "url": "string",
      "program": "string",
      "bounty_range": "string",
      "technologies": []
    }
  ],
  "duplicates_checked": true,
  "timestamp": "ISO8601"
}
```

---

## 🤖 Jules

### Agent Card

```json
{
  "name": "Jules",
  "description": "Google's asynchronous coding agent — автономные coding сессии с параллельным выполнением задач и применением патчей",
  "roles": [
    "async_coding_agent",
    "test_writer",
    "code_implementer",
    "patch_creator",
    "parallel_worker"
  ],
  "capabilities": {
    "async_sessions": true,
    "parallel_execution": true,
    "repo_cloning": true,
    "patch_generation": true,
    "patch_application": true,
    "session_management": true,
    "remote_execution": true,
    "code_generation": true,
    "test_creation": true,
    "refactoring": true,
    "bug_fixing": true,
    "multi_session_orchestration": true,
    "network_access": true,
    "requires_api_key": true
  },
  "potential": {
    "model": "Google Gemini (proprietary)",
    "context_window": "~100K-200K tokens (оценка, зависит от версии)",
    "response_time": "асинхронный — результат по завершении сессии",
    "network_access": true,
    "filesystem_access": true,
    "best_for": [
      "unit_test_generation",
      "feature_implementation",
      "bug_fixing",
      "code_refactoring",
      "parallel_task_execution",
      "remote_code_review"
    ],
    "limitations": [
      "асинхронный — нет интерактивного общения",
      "требует git репозиторий",
      "результат = патч, не прямой edit",
      "ограниченный контроль во время выполнения"
    ],
    "api_quota": "Зависит от Google API квоты",
    "parallel_sessions": "до N сессий одновременно (--parallel N)"
  },
  "tools": [
    "jules new (создание coding сессии)",
    "jules remote list (список сессий/репо)",
    "jules remote pull (получение результата)",
    "jules remote pull --apply (применение патча)",
    "jules TUI (интерактивный мониторинг)"
  ],
  "endpoints": {
    "cli": "jules new 'задача' [--repo path] [--parallel N]",
    "tui": "jules (launch TUI)",
    "remote_api": "Google Cloud (managed)"
  },
  "typical_tasks": [
    {
      "name": "Написать unit-тесты",
      "description": "Создать тесты для существующего кода",
      "input": "jules new 'write unit tests for auth module'",
      "output": "Patch с тестами, применяемый через jules remote pull --apply",
      "duration": "3-10 мин (асинхронно)"
    },
    {
      "name": "Реализовать фичу",
      "description": "Написать код по описанию задачи",
      "input": "jules new 'add rate limiting to API endpoint'",
      "output": "Patch с реализацией",
      "duration": "5-15 мин (асинхронно)"
    },
    {
      "name": "Параллельная работа",
      "description": "Несколько задач одновременно",
      "input": "jules new --parallel 3 'task 1' 'task 2' 'task 3'",
      "output": "3 независимых патча",
      "duration": "5-15 мин параллельно"
    },
    {
      "name": "Исправить баг",
      "description": "Найти и исправить ошибку",
      "input": "jules new 'fix NullPointerException in UserService.java'",
      "output": "Patch с исправлением",
      "duration": "3-10 мин (асинхронно)"
    },
    {
      "name": "Рефакторинг",
      "description": "Улучшить код без изменения поведения",
      "input": "jules new 'refactor Database class to use dependency injection'",
      "output": "Patch с рефакторингом",
      "duration": "5-20 мин (асинхронно)"
    }
  ]
}
```

### Технические характеристики

| Параметр            | Значение                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------ |
| **Имя**             | Jules                                                                                      |
| **Тип**             | Cloud Async Coding Agent (Google)                                                          |
| **Модель**          | Google Gemini (proprietary)                                                                |
| **Роли**            | Async Coding Agent, Test Writer, Code Implementer, Patch Creator, Parallel Worker          |
| **Возможности**     | Асинхронные сессии, параллельное выполнение, генерация патчей, управление репозиториями     |
| **Потенциал**       | ~100K-200K контекст, асинхронный результат, до N параллельных сессий                       |
| **Инструменты**     | jules new, remote list, remote pull, remote pull --apply, TUI                              |
| **Ограничения**     | Асинхронный (нет интерактива), требует git repo, результат = патч                           |

### Возможности (Capabilities)

| Capability                        | Описание                                       | Использовать когда...                          |
| --------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Async Sessions**                | Создание фоновых coding сессий                 | Задача не требует мгновенного результата       |
| **Parallel Execution**            | Несколько сессий одновременно (--parallel N)   | Независимые задачи, нужно ускорить             |
| **Repo Cloning**                  | Работа с любым git репозиторием                | Код не в текущей директории                    |
| **Patch Generation**              | Результат = git patch                          | Безопасное изменение через PR/review           |
| **Patch Application**             | Применение патча локально (--apply)            | Принять результат сессии                       |
| **Session Management**            | Мониторинг и управление сессиями               | Отмена, проверка статуса, pull результата      |
| **Remote Execution**              | Выполнение на Google Cloud                     | Не нагружает локальную машину                   |
| **Code Generation**               | Создание кода по описанию                      | Новая фича, скрипт, модуль                     |
| **Test Creation**                 | Генерация unit/integration тестов              | Покрытие кода тестами                          |
| **Multi-Session Orchestration**   | Координация нескольких сессий                  | Сложные задачи с независимыми частями          |

### Потенциал (Potential)

| Параметр             | Значение                                    | Комментарий                                      |
| -------------------- | ------------------------------------------- | ------------------------------------------------ |
| **Контекст**         | ~100K-200K tokens (оценка)                  | Зависит от версии модели Google                  |
| **Скорость ответа**  | Асинхронный                                 | Результат по завершении, не интерактивный        |
| **Время обработки**  | 3-20 минут                                  | Зависит от сложности задачи                      |
| **Лучше всего для**  | Тесты, фичи, баг-фиксы, рефакторинг         | Задачи с чётким ТЗ, не требующие интерактива     |
| **Ограничения**      | Нет интерактивного общения, требует git repo | Для интерактивной работы → Qwen Code             |
| **Параллелизм**      | До N сессий (--parallel N)                  | Ключевое преимущество перед другими агентами     |
| **API**              | Google Cloud (managed)                      | Авторизация через Google OAuth                   |

### Инструменты (Tools)

| Инструмент                  | Назначение                         | Пример использования                               |
| --------------------------- | ---------------------------------- | -------------------------------------------------- |
| **jules new**               | Создание coding сессии             | `jules new 'write tests for utils.py'`             |
| **jules new --repo**        | Сессия для конкретного репозитория | `jules new --repo org/repo 'fix bug in main'`      |
| **jules new --parallel**    | Параллельные сессии                | `jules new --parallel 3 'task1' 'task2' 'task3'`   |
| **jules remote list**       | Список сессий/репозиториев         | `jules remote list --session`                      |
| **jules remote pull**       | Получение результата (патча)       | `jules remote pull --session 123456`               |
| **jules remote pull --apply** | Применение патча локально        | `jules remote pull --session 123456 --apply`       |
| **jules (TUI)**             | Интерактивный мониторинг           | `jules` — открыть TUI для управления               |

### Endpoints

| Тип           | Команда/Путь                              | Описание                                |
| ------------- | ----------------------------------------- | --------------------------------------- |
| CLI           | `jules new 'задача'`                      | Создание асинхронной сессии             |
| CLI (--repo)  | `jules new --repo org/repo 'задача'`      | Сессия для удалённого репозитория       |
| CLI (--apply) | `jules remote pull --session ID --apply`  | Применение результата                   |
| TUI           | `jules`                                   | Интерактивный интерфейс мониторинга     |
| Remote API    | Google Cloud (managed)                    | Облачное выполнение сессий              |

### SLA

| Параметр         | Значение           | Примечание                              |
| ---------------- | ------------------ | --------------------------------------- |
| **Время ответа** | Асинхронный        | Результат по завершении сессии          |
| **Время сессии** | 3-20 минут         | Зависит от сложности задачи             |
| **Контекст**     | ~100K-200K tokens  | Оценка, зависит от модели               |
| **Параллелизм**  | До N сессий        | Ограничено квотой Google API            |
| **Надёжность**   | High               | Google Cloud Infrastructure             |
| **Доступность**  | По запросу         | Запускается по команде, работает в фоне |

### Когда обращаться к Jules

| Ситуация                               | Что делает Jules                                       |
| -------------------------------------- | ------------------------------------------------------ |
| Нужно написать тесты                   | Создаёт сессию → генерирует тесты → возвращает патч    |
| Нужно реализовать фичу (не срочно)     | Асинхронная реализация с готовым патчем                |
| Нужно исправить баг                    | Анализ + исправление → патч для ревью                   |
| Нужно выполнить несколько задач        | Параллельные сессии (--parallel N)                     |
| Код в удалённом репозитории            | Клонирует, работает, возвращает патч                   |
| Нужен результат для code review        | Патч готов к ревью, не прямой edit в рабочей копии     |

### Jules vs Qwen Code — когда кого выбрать

| Критерий              | Jules                                | Qwen Code                           |
| --------------------- | ------------------------------------ | ----------------------------------- |
| **Режим**             | Асинхронный (fire-and-forget)        | Синхронный (интерактивный)          |
| **Результат**         | Git patch                            | Прямые изменения в файлах           |
| **Параллелизм**       | Встроенный (--parallel N)            | Через делегацию (agent tool)        |
| **Интерактив**        | Нет (TUI только для мониторинга)     | Да (полный диалог)                  |
| **Требует git repo**  | Да                                   | Нет                                 |
| **Лучше для**         | Тесты, фичи, batch-задачи            | Рефакторинг, дебаг, скрипты, анализ |

---

## 🤖 Qwen Code

### Agent Card

```json
{
  "name": "Qwen Code",
  "description": "Autonomous CLI coding agent — пишет, исполняет и ревьюит код по запросу на естественном языке",
  "roles": [
    "coding_agent",
    "shell_executor",
    "file_editor",
    "code_reviewer",
    "debugger",
    "test_runner"
  ],
  "capabilities": {
    "code_generation": true,
    "shell_execution": true,
    "file_operations": true,
    "code_analysis": true,
    "debugging": true,
    "test_execution": true,
    "git_operations": true,
    "package_management": true,
    "web_search": false,
    "report_generation": true,
    "multi_file_editing": true,
    "regex_search": true,
    "documentation_writing": true,
    "local_only": false,
    "requires_api_key": true
  },
  "potential": {
    "model": "Qwen (Alibaba Cloud)",
    "context_window": "128K-256K tokens (varies by model version)",
    "response_time": "2-10 секунд на операцию",
    "network_access": true,
    "filesystem_access": true,
    "best_for": [
      "writing_code_from_scratch",
      "refactoring",
      "bug_fixing",
      "test_creation",
      "shell_automation",
      "file_manipulation",
      "code_explanation"
    ],
    "limitations": [
      "requires_human_approval_for_destructive_ops",
      "no_direct_web_browsing",
      "output_depends_on_model_version"
    ],
    "api_quota": "Зависит от используемой модели и провайдера",
    "approval_modes": ["default", "yolo", "auto-edit"]
  },
  "tools": [
    "read_file (чтение файлов)",
    "write_file (создание файлов)",
    "edit (поиск и замена в файлах)",
    "list_directory (обзор директорий)",
    "grep_search (regex поиск в файлах)",
    "glob (поиск файлов по паттерну)",
    "run_shell_command (выполнение bash команд)",
    "todo_write (управление задачами)",
    "agent (делегация sub-агентам)",
    "skill (вызов специализированных навыков)",
    "ask_user_question (запрос уточнений у пользователя)",
    "save_memory (долгосрочная память)"
  ],
  "endpoints": {
    "cli": "qwen --approval-mode yolo 'задача'",
    "mcp": "qwen_code (task, cwd)",
    "api": "через прокси localhost:8768"
  },
  "typical_tasks": [
    {
      "name": "Написать скрипт",
      "description": "Создать Python/Bash скрипт по описанию",
      "input": "'Напиши скрипт бэкапа конфигов'",
      "output": "Готовый файл скрипта в нужной директории",
      "duration": "~1-3 минут"
    },
    {
      "name": "Рефакторинг кода",
      "description": "Улучшить существующий код",
      "input": "Путь к файлу + описание изменений",
      "output": "Обновлённый файл с пояснениями",
      "duration": "~2-5 минут"
    },
    {
      "name": "Написать тесты",
      "description": "Создать unit/integration тесты",
      "input": "Путь к коду + фреймворк",
      "output": "Файл тестов + результат запуска",
      "duration": "~3-7 минут"
    },
    {
      "name": "Исправить баг",
      "description": "Найти и исправить ошибку по описанию",
      "input": "Stack trace или описание проблемы",
      "output": "Исправленный код + объяснение фикса",
      "duration": "~2-5 минут"
    },
    {
      "name": "Анализ кода",
      "description": "Найти уязвимости, code smells, проблемы",
      "input": "Путь к файлу/директории",
      "output": "Отчёт с находками и рекомендациями",
      "duration": "~3-10 минут"
    }
  ]
}
```

### Технические характеристики

| Параметр        | Значение                                                                 |
| --------------- | ------------------------------------------------------------------------ |
| **Имя**         | Qwen Code                                                                |
| **Тип**         | Hybrid (Cloud API через прокси + Local shell)                            |
| **Версия**      | CLI через npm (`@anthropic/qwen-code` или актуальный пакет)              |
| **Роли**        | Coding Agent, Shell Executor, File Editor, Code Reviewer, Debugger       |
| **Возможности** | Генерация кода, выполнение shell, редактирование файлов, тесты, дебаг    |
| **Потенциал**   | 128K-256K контекст, 2-10с на операцию, автономная работа по задачам      |
| **Инструменты** | read_file, write_file, edit, grep, glob, shell, todo_write, agent, skill |
| **Ограничения** | Нет прямого веб-браузинга, approval для деструктивных операций           |

### Возможности (Capabilities)

| Capability                | Описание                                  | Использовать когда...                     |
| ------------------------- | ----------------------------------------- | ----------------------------------------- |
| **Code Generation**       | Создание кода с нуля по описанию          | Нужен новый скрипт, функция, модуль       |
| **Shell Execution**       | Выполнение bash команд                    | Установка пакетов, git, запуск тестов     |
| **File Operations**       | Чтение, запись, редактирование файлов     | Создание/изменение кода, конфигов, доков  |
| **Code Analysis**         | Статический анализ, поиск проблем         | Ревью кода, поиск багов, аудит            |
| **Debugging**             | Диагностика и исправление ошибок          | Stack trace, тесты падают, логика сломана |
| **Test Execution**        | Создание и запуск тестов                  | Нужны unit/integration тесты              |
| **Multi-file Editing**    | Одновременное изменение нескольких файлов | Рефакторинг, добавление фич               |
| **Documentation Writing** | Генерация документации                    | README, API docs, инструкции              |
| **Task Management**       | Планирование через todo list              | Сложные многошаговые задачи               |
| **Agent Delegation**      | Вызов sub-агентов для параллельной работы | Исследование, поиск, параллельные задачи  |

### Потенциал (Potential)

| Параметр            | Значение                              | Комментарий                                    |
| ------------------- | ------------------------------------- | ---------------------------------------------- |
| **Контекст**        | 128K-256K tokens                      | Зависит от выбранной модели через прокси       |
| **Скорость ответа** | 2-10 секунд на операцию               | Зависит от сложности и размера файлов          |
| **Время обработки** | 1-10 минут                            | Зависит от задачи (простой код vs рефакторинг) |
| **Лучше всего для** | Написание кода, тесты, фиксы, скрипты | Практическая работа с кодом и файлами          |
| **Ограничения**     | Нет прямого брауузинга                | Для веб-поиска делегирую Gemini/OpenClaw       |
| **API**             | Через прокси localhost:8768           | Ключ `proxy-managed`                           |
| **Режимы approval** | default, yolo, auto-edit              | `yolo` для автономной работы                   |

### Инструменты (Tools)

| Инструмент            | Назначение                       | Пример использования                 |
| --------------------- | -------------------------------- | ------------------------------------ |
| **read_file**         | Чтение файлов                    | Анализ кода, конфигов, логов         |
| **write_file**        | Создание файлов                  | Новые скрипты, конфиги, документы    |
| **edit**              | Поиск и замена в файлах          | Рефакторинг, исправление багов       |
| **list_directory**    | Список директорий                | Обзор структуры проекта              |
| **grep_search**       | Regex поиск в файлах             | Поиск функций, переменных, паттернов |
| **glob**              | Поиск файлов по паттерну         | Найти все .py, .ts, .yaml файлы      |
| **run_shell_command** | Выполнение bash команд           | pip install, git, pytest, make       |
| **todo_write**        | Управление задачами              | Планирование многошаговых задач      |
| **agent**             | Делегация sub-агентам            | Параллельное исследование, поиск     |
| **skill**             | Вызов специализированных навыков | Azure, PDF, XLSX, security skills    |

### Endpoints

| Тип | Команда/Путь                         | Описание                          |
| --- | ------------------------------------ | --------------------------------- |
| CLI | `qwen --approval-mode yolo 'задача'` | Автономный запуск задачи          |
| MCP | `qwen_code (task, cwd)`              | Вызов из других агентов через MCP |
| API | через прокси localhost:8768          | Облачная модель через прокси      |

### SLA

| Параметр         | Значение         | Примечание                   |
| ---------------- | ---------------- | ---------------------------- |
| **Время ответа** | 2-10 секунд      | На одну операцию             |
| **Контекст**     | 128K-256K tokens | Зависит от модели            |
| **Надёжность**   | High             | При работающем прокси и сети |
| **Доступность**  | По запросу       | Запускается по команде       |

### Когда обращаться к Qwen Code

| Ситуация                      | Что делает Qwen Code                          |
| ----------------------------- | --------------------------------------------- |
| Нужно написать код с нуля     | Создаёт файлы с реализацией                   |
| Нужно исправить баг           | Находит причину, применяет фикс               |
| Нужны тесты                   | Пишет и запускает тесты                       |
| Нужно отрефакторить код       | Улучшает структуру, читаемость, производитель |
| Нужен скрипт автоматизации    | Создаёт bash/python скрипт                    |
| Нужна документация            | Генерирует README, API docs                   |
| Нужно выполнить shell команду | Запускает команды, обрабатывает результат     |

---

## 🔌 A2A Integration

### Discovery

Агенты обнаруживаются через:

| Агент  | Метод обнаружения                                     |
| ------ | ----------------------------------------------------- |
| Claude | `file:///Users/code/project/intel/AGENT_PASSPORTS.md` |
| Qwen   | `http://localhost:11434/api/tags`                     |
| Gemini | `gemini-cli://local` (через `--help`)                 |
| Jules  | `jules-cli://local` (через `--help`)                  |

### Communication Pattern

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Coordinator│────▶│    Queue    │────▶│   Worker    │
│   (Claude)  │     │  (files)    │     │   Agent     │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                                      │
       │                                      ▼
       │                              ┌─────────────┐
       │                              │   Results   │
       └──────────────────────────────│  (files)    │
                                      └─────────────┘
```

### Task Lifecycle (A2A Compliant)

1. **Task Creation:** Claude создаёт `queue/{phase}{task}.json`
2. **Task Discovery:** Агент читает `queue/*.json`
3. **Task Execution:** Агент выполняет работу
4. **Result Writing:** Агент пишет `results/{phase}{agent}.json`
5. **Validation:** Claude проверяет результат
6. **Task Completion:** Статус обновляется в `SESSION_LOG.md`

### Security

| Аспект           | Реализация                     |
| ---------------- | ------------------------------ |
| Authentication   | Не требуется (локальная среда) |
| Authorization    | File system permissions        |
| Data Privacy     | Все данные локальные           |
| Input Validation | JSON schema validation         |

---

## 📐 JSON Schema

### Task Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "A2A Task",
  "type": "object",
  "required": ["id", "type", "payload", "status"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^phase[1-4]_[a-z0-9]+$"
    },
    "type": {
      "type": "string",
      "enum": ["recon", "scan", "analyze", "report", "document"]
    },
    "payload": {
      "type": "object",
      "properties": {
        "target": { "type": "string" },
        "parameters": { "type": "object" },
        "deadline": { "type": "string", "format": "date-time" }
      }
    },
    "status": {
      "type": "string",
      "enum": ["pending", "in_progress", "completed", "failed"]
    },
    "assigned_to": {
      "type": "string",
      "enum": ["qwen", "gemini", "jules"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "completed_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### Result Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "A2A Result",
  "type": "object",
  "required": ["task_id", "agent", "status", "data"],
  "properties": {
    "task_id": {
      "type": "string"
    },
    "agent": {
      "type": "string",
      "enum": ["qwen", "gemini", "jules"]
    },
    "status": {
      "type": "string",
      "enum": ["success", "partial", "error"]
    },
    "data": {
      "type": "object"
    },
    "artifacts": {
      "type": "array",
      "items": { "type": "string" }
    },
    "errors": {
      "type": "array",
      "items": { "type": "string" }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "duration_seconds": { "type": "number" },
        "tokens_used": { "type": "number" },
        "model_version": { "type": "string" }
      }
    }
  }
}
```

---

## 📎 ПРИЛОЖЕНИЕ: A2A vs MCP

### A2A (Agent2Agent)

Коммуникация между агентами:

- ✅ Discovery агентов
- ✅ Task delegation
- ✅ Multi-turn conversations

Этот документ описывает A2A compliance.

### MCP (Model Context Protocol)

Доступ к инструментам:

- ✅ Tool integration
- ✅ Resource access
- ✅ Function calling

Используется внутри агентов.

### Взаимодействие

```
┌─────────────────────────────────────────────────┐
│              A2A Protocol Layer                 │
│         (меж-агентная коммуникация)             │
├─────────────────────────────────────────────────┤
│              MCP Protocol Layer                 │
│         (доступ к инструментам)                 │
├─────────────────────────────────────────────────┤
│           Individual Agent Core                 │
│         (LLM + local processing)                │
└─────────────────────────────────────────────────┘
```

---

**Конец документа**
