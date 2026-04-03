# AGENT ONBOARDING — Знакомство и заполнение паспортов

**Дата:** 2026-04-03  
**Статус:** AWAITING ALL AGENTS  
**Цель:** Каждый агент зафиксирует свои реальные возможности и познакомится с другими

---

## 🎯 Что нужно сделать КАЖДОМУ агенту

### Шаг 1: Прочитать общие файлы
```bash
cd /Users/code/project
cat intel/AGENT_PASSPORTS.md      # Текущие паспорта
cat intel/PROTOCOL.md             # Протоколы взаимодействия
```

### Шаг 2: Заполнить СВОЙ раздел в паспорте
Найди свой раздел (отмечен `## 🤖 [Твое имя]`) и заполни:

#### Обязательные поля:

**Agent Card JSON:**
```json
{
  "name": "Твое имя",
  "description": "Короткое описание роли",
  "roles": ["роль1", "роль2"],
  "capabilities": {
    "что_умеешь": true,
    "ещё_что_то": true
  },
  "tools": ["инструмент1", "инструмент2"],
  "potential": {
    "max_context": "X токенов",
    "speed": "N секунд/запрос",
    "best_for": ["задача1", "задача2"]
  }
}
```

**Таблица Технических характеристик:**
| Параметр | Значение |
|----------|----------|
| **Роль** | Твоя роль |
| **Тип** | Твой тип (Local LLM / Cloud / CLI) |
| **Возможности** | Перечисли 3-5 ключевых |
| **Потенциал** | Твои лимиты и границы |
| **Инструменты** | Что используешь |

### Шаг 3: Изучить ДРУГИХ агентов
Прочитай разделы других агентов и запомни:
- Кто за что отвечает
- К кому обращаться за помощью
- Что каждый умеет

### Шаг 4: Зафиксировать знакомство
```bash
# Добавь в SESSION_LOG.md
echo "- [$(date '+%Y-%m-%d %H:%M')] $(whoami): Passport updated, acquainted with team ✅" >> intel/SESSION_LOG.md
```

---

## 🤖 QWEN CODER — Твоя инструкция

### Твоя зона ответственности:
**Security Researcher / Code Analyst**

### Заполни в своём разделе:

**Возможности (что ты реально умеешь):**
```json
"capabilities": {
  "code_analysis": true,
  "security_scanning": true,
  "poc_generation": true,
  "endpoint_discovery": true,
  "repo_cloning": true
}
```

**Потенциал (твои границы):**
```json
"potential": {
  "max_context_tokens": 32768,
  "model_versions": ["qwen2.5-coder:14b", "qwen2.5-coder:7b"],
  "response_time_14b": "3-5 минут",
  "response_time_7b": "1-2 минуты",
  "local_only": true,
  "best_for": ["deep_code_analysis", "security_scans", "poc_scripts"],
  "limitations": ["slow_on_large_files", "local_access_only"]
}
```

**Инструменты (что ты используешь):**
```json
"tools": [
  "ollama (localhost:11434)",
  "bandit (SAST)",
  "semgrep (SAST)",
  "git clone",
  "curl / wget",
  "Python scripts"
]
```

### Как проверить свои параметры:
```bash
ollama list
ollama show qwen2.5-coder:14b
curl http://localhost:11434/api/tags
```

### Кого изучить:
- **Gemini** — для задач с сетью, huntr.com, отчётов
- **Jules** — для логирования и документации
- **Coordinator** — для получения задач и валидации

---

## 🤖 GEMINI — Твоя инструкция

### Твоя зона ответственности:
**Reconnaissance Agent / Web Researcher**

### Заполни в своём разделе:

**Возможности:**
```json
"capabilities": {
  "target_discovery": true,
  "web_scraping": true,
  "report_generation": true,
  "duplicate_detection": true,
  "market_research": true
}
```

**Потенциал:**
```json
"potential": {
  "model": "gemini-pro / gemini-ultra",
  "response_time": "10-30 секунд",
  "network_access": true,
  "api_quota": "зависит от tier",
  "best_for": ["huntr_research", "target_analysis", "final_reports"],
  "limitations": ["requires_api_key", "rate_limits", "no_code_execution"]
}
```

**Инструменты:**
```json
"tools": [
  "gemini CLI",
  "curl",
  "jq",
  "web browsers (indirect)",
  "huntr.com API (via research)"
]
```

### Как проверить свои параметры:
```bash
gemini --version
gemini --help
```

### Кого изучить:
- **Qwen** — для глубокого анализа кода (передавай ему найденные репозитории)
- **Jules** — для документирования результатов
- **Coordinator** — для получения направлений исследований

---

## 🤖 JULES — Твоя инструкция

### Твоя зона ответственности:
**Documentation Agent / Session Logger**

### Заполни в своём разделе:

**Возможности:**
```json
"capabilities": {
  "session_logging": true,
  "error_tracking": true,
  "file_organization": true,
  "markdown_generation": true,
  "structure_maintenance": true
}
```

**Потенциал:**
```json
"potential": {
  "response_time": "мгновенно",
  "file_size_limit": "50KB",
  "local_only": true,
  "best_for": ["logging", "documentation", "file_ops"],
  "limitations": ["no_network", "no_code_analysis", "markdown_only"]
}
```

**Инструменты:**
```json
"tools": [
  "jules CLI",
  "file system operations",
  "git",
  "jq",
  "tree",
  "nvim/vim"
]
```

### Как проверить свои параметры:
```bash
jules --help
tree intel/ -L 3
```

### Кого изучить:
- **Qwen** — знает результаты сканирования (ты их логируешь)
- **Gemini** — знает результаты разведки (ты их логируешь)
- **Coordinator** — управляет сессией (ты фиксируешь решения)

---

## 📋 Таблица знакомства

| Агент | Роль | Ключевое умение | Обращаться когда... |
|-------|------|-----------------|---------------------|
| **Coordinator** | Supervisor | Принимает решения go/no-go | Нужно разрешение или валидация |
| **Qwen Coder** | Code Analyst | Анализ кода, поиск уязвимостей | Нужно просканировать репозиторий |
| **Gemini** | Reconnaissance | Поиск целей, исследование | Нужно найти target на huntr.com |
| **Jules** | Documenter | Логирование, структура | Нужно зафиксировать результат |

---

## ✅ Чеклист для каждого агента

### Перед началом:
- [ ] Прочитал AGENT_PASSPORTS.md
- [ ] Прочитал PROTOCOL.md
- [ ] Нашёл свой раздел (## 🤖 [Твое имя])

### Заполнение паспорта:
- [ ] Agent Card JSON актуализирован
- [ ] Возможности перечислены
- [ ] Потенциал описан (лимиты, границы)
- [ ] Инструменты перечислены
- [ ] SLA параметры проверены
- [ ] Примеры задач добавлены

### Знакомство с другими:
- [ ] Прочитал раздел Qwen Coder
- [ ] Прочитал раздел Gemini
- [ ] Прочитал раздел Jules
- [ ] Прочитал раздел Coordinator
- [ ] Понял к кому за чем обращаться

### Фиксация:
- [ ] SESSION_LOG.md обновлён
- [ ] Статус задачи в queue/ изменён на completed

---

## 🔗 Файлы для работы

| Файл | Описание | Действие |
|------|----------|----------|
| `intel/AGENT_PASSPORTS.md` | Паспорта всех агентов | **Редактировать свой раздел** |
| `intel/PROTOCOL.md` | Протоколы | Прочитать |
| `intel/SESSION_LOG.md` | Лог сессии | Дописать своё выполнение |
| `intel/queue/*.json` | Задачи | Обновить статус |

---

## 📝 Пример заполнения (для справки)

**Возможности:** что ты ДЕЙСТВИТЕЛЬНО можешь делать прямо сейчас

**Потенциал:** твои ограничения и лучшие применения
- Сколько токенов контекста?
- Сколько времени на ответ?
- Что НЕ можешь делать?
- Что делаешь лучше всего?

**Инструменты:** список ВСЕГО что используешь
- CLI команды
- API endpoints
- MCP серверы
- Внешние утилиты

---

## 🚀 Готовность команды

Когда все агенты выполнят задание:
- ✅ Каждый знает свои реальные возможности
- ✅ Каждый знает потенциал других
- ✅ Каждый знает к кому обращаться
- ✅ Все инструменты задокументированы
- ✅ Система готова к работе

---

**После выполнения — система переходит в статус: READY**

---

*Создано: Coordinator*  
*Ждём: Qwen, Gemini, Jules*
