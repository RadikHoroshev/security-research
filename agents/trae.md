# AGENT PASSPORT — Trae (IDE Assistant)

**ID:** trae  
**Подписано:** Trae  
**Дата:** 2026-04-05  
**Статус:** ACTIVE  
**Соответствие:** A2A Protocol v1.0.0 ✅

---

## 🤖 Agent Card

```json
{
  "name": "Trae (IDE Assistant)",
  "description": "Продвинутый AI-ассистент, интегрированный в Trae IDE — координатор, архитектор и исполнитель задач с полным доступом к контексту проекта, файловой системе и инструментам разработки",
  "roles": [
    "orchestrator",
    "code_author",
    "architect",
    "validator",
    "researcher",
    "debugger"
  ],
  "capabilities": {
    "file_operations": true,
    "shell_execution": true,
    "web_search": true,
    "web_fetch": true,
    "code_generation": true,
    "code_analysis": true,
    "multi_file_editing": true,
    "symbol_rename": true,
    "file_relocate": true,
    "sub_agent_delegation": true,
    "mcp_integration": true,
    "documentation_generation": true,
    "diagnostics": true,
    "todo_management": true,
    "memory_management": true
  },
  "potential": {
    "model": "Gemini-3-Flash-Preview (via Trae IDE)",
    "context_window": "1M+ tokens",
    "response_time": "1-5 секунд",
    "network_access": true,
    "filesystem_access": true,
    "best_for": [
      "complex_refactoring",
      "architecture_design",
      "codebase_exploration",
      "multi_agent_orchestration",
      "security_audits",
      "documentation"
    ],
    "limitations": [
      "requires_user_approval_for_commands",
      "no_direct_gui_interaction"
    ]
  },
  "tools": [
    "Read / Write / SearchReplace",
    "RunCommand / CheckCommandStatus / StopCommand",
    "LS / Glob / Grep",
    "WebSearch / WebFetch",
    "GetDiagnostics",
    "TodoWrite",
    "manage_core_memory",
    "SearchCodebase",
    "AskUserQuestion",
    "OpenPreview"
  ],
  "endpoints": {
    "input": "Trae IDE Chat / Inline Edit",
    "output": "Filesystem / Chat Response / Preview",
    "api": "Google AI API via Trae IDE"
  },
  "constraints": {
    "max_read_lines": 1000,
    "max_result_size": "50KB",
    "requires_workspace": true
  }
}
```

---

## 📋 Технические характеристики

| Параметр         | Значение                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------- |
| **Имя**          | Trae                                                                                        |
| **Тип**          | IDE-integrated AI Assistant                                                                 |
| **Платформа**    | Trae IDE                                                                                    |
| **AI Провайдер** | Google AI (Gemini-3-Flash-Preview)                                                          |
| **Роли**         | Orchestrator, Code Author, Architect, Validator, Researcher, Debugger                       |
| **Контекст**     | 1,000,000+ tokens                                                                           |
| **Инструменты**  | File ops, shell, web search, Todo, Memory, Codebase search, Diagnostics, Preview            |
| **Ограничения**  | Требует подтверждения команд, нет прямого взаимодействия с GUI                              |

---

## ⚡ Возможности (Capabilities)

| Capability               | Описание                                          | Использовать когда...                          |
| ------------------------ | ------------------------------------------------- | ---------------------------------------------- |
| **Code Generation**      | Создание и редактирование кода в файлах           | Нужен новый модуль, скрипт, компонент          |
| **Multi-file Editing**   | Одновременное изменение нескольких файлов         | Рефакторинг, переименование символов           |
| **Codebase Exploration** | Глубокий поиск и анализ через SearchCodebase      | Незнакомая кодовая база, поиск зависимостей    |
| **Web Search + Fetch**   | Поиск актуальной информации в интернете           | Версии библиотек, документация, CVE            |
| **Shell Execution**      | Выполнение команд в терминале                     | Запуск тестов, проверка статуса, build         |
| **Todo Management**      | Ведение списка задач через TodoWrite              | Сложные многошаговые задачи                    |
| **Memory Management**    | Управление долгосрочной памятью проекта           | Сохранение важных правил и опыта               |
| **Diagnostics**          | Проверка синтаксических и типовых ошибок          | После редактирования кода                      |
| **Sub-agent Delegation** | Делегация задач (через CLI инструменты)           | Сложные исследования, параллельные задачи      |

---

## 🛠️ Инструменты (Tools)

| Инструмент              | Назначение                              | Пример использования                        |
| ----------------------- | --------------------------------------- | ------------------------------------------- |
| **SearchCodebase**      | Семантический поиск по всему проекту    | Изучить как работает авторизация            |
| **Write / SearchReplace**| Создание и точечное изменение файлов    | Новый скрипт, исправление бага              |
| **RunCommand**          | Выполнение shell команд                 | `make test`, `npm start`, `curl ...`        |
| **GetDiagnostics**      | Получение ошибок от VS Code/Trae        | Проверка типов после рефакторинга           |
| **WebSearch**           | Поиск в интернете                       | Актуальные CVE, версии пакетов              |
| **TodoWrite**           | Структурирование текущей работы         | Планирование этапов миграции                |
| **manage_core_memory**  | Сохранение знаний в Core Memory         | Запись конвенций именования                 |

---

## 🎯 Типовые задачи (Typical Tasks)

| Задача                    | Вход                          | Выход                            |
| ------------------------- | ----------------------------- | -------------------------------- |
| **Написать код**          | Описание задачи               | Файлы с реализацией              |
| **Исследовать проект**    | Вопрос об архитектуре      | Анализ + рекомендации            |
| **Безопасность**          | Аудит кода / поиск CVE        | Отчёт об уязвимостях             |
| **Рефакторинг**           | Файлы + цель изменения        | Обновлённые файлы                |
| **Веб-поиск**             | Вопрос / тема                 | Актуальная информация с ссылками |
| **Документация**          | Код / функционал              | .md файлы с описанием            |

---

**Конец паспорта**
