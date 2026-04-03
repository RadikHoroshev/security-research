# SELF IDENTIFY — Универсальное задание для любого агента

**Дата:** 2026-04-03  
**Версия:** 1.0  
**Статус:** ACTIVE  
**Применимость:** Любой агент в системе

---

## 🎯 Цель

Заполни/обнови свой раздел в `AGENT_PASSPORTS.md` актуальными данными о себе.

**Этот файл используется:**
- При первом подключении агента к системе
- При добавлении новых инструментов/навыков
- При изменении версии модели или параметров
- При обнаружении новых возможностей

---

## 🔍 Шаг 1: Самоидентификация

### Определи свои базовые параметры:

```bash
# Кто ты?
echo "Имя: $(whoami)"
echo "Тип: $(type <команда_агента> 2>/dev/null || echo 'unknown')"
echo "Окружение: $(uname -a)"
```

**Заполни поля:**
- **Имя:** Как тебя зовут в системе
- **Тип:** Local LLM / Cloud API / CLI Tool / Hybrid / Other
- **Роль:** Твоя основная функция (одним предложением)

---

## 🛠️ Шаг 2: Инвентаризация инструментов

### Автоматический поиск:

```bash
# Проверь что доступно
which ollama 2>/dev/null && echo "✅ Ollama доступен"
which gemini 2>/dev/null && echo "✅ Gemini доступен"
which jules 2>/dev/null && echo "✅ Jules доступен"
which claude 2>/dev/null && echo "✅ Claude доступен"
ls ~/.secrets/*.json 2>/dev/null && echo "✅ MCP конфиги найдены"

# Проверь API endpoints
curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✅ Ollama API (localhost:11434)"
curl -s http://localhost:8768/status > /dev/null 2>&1 && echo "✅ Proxy (localhost:8768)"
```

**Заполни список инструментов:**
```json
"tools": [
  "инструмент_1 (версия)",
  "инструмент_2 (версия)",
  "API_endpoint",
  "MCP_server",
  "утилита_командной_строки"
]
```

---

## ⚡ Шаг 3: Определение возможностей

### Задай себе вопросы:

| Вопрос | Ответ | Запиши как capability |
|--------|-------|---------------------|
| Могу ли анализировать код? | Да/Нет | `"code_analysis": true/false` |
| Могу искать в интернете? | Да/Нет | `"web_search": true/false` |
| Могу выполнять команды shell? | Да/Нет | `"shell_execution": true/false` |
| Могу работать с файлами? | Да/Нет | `"file_operations": true/false` |
| Могу генерировать отчёты? | Да/Нет | `"report_generation": true/false` |
| Есть ли у меня доступ к API? | Да/Нет | `"api_access": true/false` |
| Работаю ли я локально? | Да/Нет | `"local_only": true/false` |
| Требуется ли API ключ? | Да/Нет | `"requires_api_key": true/false` |

**Заполни capabilities:**
```json
"capabilities": {
  "skill_1": true,
  "skill_2": true,
  "limitation_1": false
}
```

---

## 🚀 Шаг 4: Измерение потенциала

### Проверь свои лимиты:

```bash
# Контекст (если LLM)
# Проверь документацию или конфиг

# Скорость (замери сам)
time echo "test" | wc -l

# Доступ к сети
ping -c 1 google.com > /dev/null 2>&1 && echo "✅ Network доступен" || echo "❌ Network недоступен"

# Файловая система
df -h . 2>/dev/null | tail -1
```

**Заполни potential:**
```json
"potential": {
  "max_context_tokens": "проверь_в_документации",
  "response_time": "замерь_в_секундах",
  "network_access": true/false,
  "filesystem_access": true/false,
  "best_for": ["задача_1", "задача_2", "задача_3"],
  "limitations": ["лимит_1", "лимит_2"],
  "api_quota": "если_применимо"
}
```

---

## 📋 Шаг 5: Примеры задач

### Перечисли 3-5 типовых задач которые ты выполняешь:

```json
"typical_tasks": [
  {
    "name": "Краткое_название",
    "description": "Что делаешь",
    "input": "Пример входных данных",
    "output": "Пример результата",
    "duration": "~N минут"
  }
]
```

---

## 📝 Шаг 6: Заполнение паспорта

### Открой файл:

```bash
nvim /Users/code/project/intel/AGENT_PASSPORTS.md
```

### Найди или создай свой раздел:

```markdown
## 🤖 [ТВОЁ_ИМЯ]

### Agent Card

```json
{
  "name": "[ТВОЁ_ИМЯ]",
  "description": "Описание в 1 предложении",
  "roles": ["роль1", "роль2"],
  "capabilities": { ... },
  "potential": { ... },
  "tools": [ ... ],
  "typical_tasks": [ ... ]
}
```

### Технические характеристики

| Параметр | Значение |
|----------|----------|
| **Имя** | [ТВОЁ_ИМЯ] |
| **Тип** | [Local/Cloud/Hybrid] |
| **Версия** | [версия модели/CLI] |
| **Возможности** | [список через запятую] |
| **Потенциал** | [контекст, скорость, лимиты] |
| **Инструменты** | [список] |

### Endpoints

| Тип | Значение |
|-----|----------|
| API | [если есть] |
| CLI | [команда запуска] |
| MCP | [если есть] |

### SLA

| Параметр | Значение |
|----------|----------|
| Время ответа | [секунд/минут] |
| Контекст | [токенов] |
| Надёжность | [high/medium/low] |

### Контакты

| Когда обращаться | Куда |
|------------------|------|
| Для задач типа X | [твоя роль] |
| Для вопросов по Y | [что умеешь] |
```

---

## ✅ Шаг 7: Фиксация изменений

### Обнови лог:

```bash
echo "- [$(date '+%Y-%m-%d %H:%M')] $(whoami): Self-identification complete | Tools: [перечисли] | Capabilities: [перечисли] | Version: [версия]" >> /Users/code/project/intel/SESSION_LOG.md
```

### Обнови статус задачи (если была создана):

```bash
# Найди свой JSON в queue/
ls /Users/code/project/intel/queue/*$(whoami)*.json 2>/dev/null

# Обнови статус
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' /Users/code/project/intel/queue/[твой_файл].json > /tmp/upd.json && mv /tmp/upd.json /Users/code/project/intel/queue/[твой_файйл].json
```

---

## 🔄 Периодическое обновление

**Обновляй паспорт когда:**

- [ ] Обновилась версия модели/CLI
- [ ] Добавился новый инструмент
- [ ] Открылась новая возможность
- [ ] Изменились лимиты (контекст, скорость)
- [ ] Появился новый MCP сервер
- [ ] Изменился API endpoint

**Команда для быстрого обновления:**
```bash
cd /Users/code/project && cat intel/queue/SELF_IDENTIFY.md && nvim intel/AGENT_PASSPORTS.md
```

---

## 📊 Валидация паспорта

### Проверь что заполнено:

```bash
# Проверь JSON валидность
jq '.agent_card' /Users/code/project/intel/AGENT_PASSPORTS.md

# Проверь размер файла
ls -lh /Users/code/project/intel/AGENT_PASSPORTS.md

# Проверь структуру
grep -c "## 🤖" /Users/code/project/intel/AGENT_PASSPORTS.md
```

---

## 🎯 Чеклист

- [ ] Имя и тип определены
- [ ] Capabilities перечислены
- [ ] Potential измерен
- [ ] Tools инвентаризированы
- [ ] Typical tasks описаны
- [ ] Endpoints указаны
- [ ] SLA параметры заполнены
- [ ] SESSION_LOG обновлён
- [ ] Файл сохранён

---

## 🔗 Связанные файлы

| Файл | Назначение |
|------|------------|
| `intel/AGENT_PASSPORTS.md` | Общий файл паспортов |
| `intel/SESSION_LOG.md` | Лог изменений |
| `intel/PROTOCOL.md` | Протоколы взаимодействия |
| `intel/queue/` | Очередь задач |
| `intel/results/` | Результаты работы |

---

**Универсальное правило:** *Если что-то изменилось — обнови паспорт!*

**Версия этого файла:** 1.0  
**Последнее обновление:** 2026-04-03
