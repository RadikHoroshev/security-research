# AGENT COMMANDS — Команды для обновления паспортов

**Создано:** 2026-04-03  
**Статус:** ACTIVE  
**Цель:** Каждый агент обновляет свой раздел в `AGENT_PASSPORTS.md` актуальными данными

---

## 📋 Быстрый старт

```bash
# Перейти в директорию проекта
cd /Users/code/project

# Посмотреть все задачи в очереди
ls -la intel/queue/

# Проверить статус задач
cat intel/queue/*/update_passport.json | jq '.status'
```

---

## 🤖 Команда для Qwen Coder

### Задача:
Обновить раздел **Qwen Coder** в файле `intel/AGENT_PASSPORTS.md`

### Пошаговая инструкция:

```bash
# 1. Прочитай свой файл задачи
cat intel/queue/qwen_update_passport.json

# 2. Проверь актуальные модели в Ollama
curl http://localhost:11434/api/tags

# 3. Получи параметры своей модели
curl http://localhost:11434/api/show -d '{"name":"qwen2.5-coder:14b"}'

# 4. Прочитай текущий паспорт
cat intel/AGENT_PASSPORTS.md | bat -l markdown

# 5. Обнови секцию "Qwen Coder" (строки ~89-172)
# Используй nvim или другой редактор
nvim intel/AGENT_PASSPORTS.md
```

### Что нужно обновить:

| Поле | Как проверить |
|------|---------------|
| `model` | `ollama list` |
| `context_length` | `ollama show qwen2.5-coder:14b --modelfile` |
| `response_time` | Замерить при выполнении задачи |
| `capabilities` | Перечислить реальные возможности |
| `endpoints` | Проверить актуальный MCP endpoint |

### После обновления:

```bash
# 1. Сохрани файл
# 2. Запиши в лог
echo "- [$(date)] Qwen: Passport updated" >> intel/SESSION_LOG.md

# 3. Обнови статус задачи
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' \
  intel/queue/qwen_update_passport.json > /tmp/tmp.json && \
  mv /tmp/tmp.json intel/queue/qwen_update_passport.json
```

---

## 🤖 Команда для Gemini

### Задача:
Обновить раздел **Gemini** в файле `intel/AGENT_PASSPORTS.md`

### Пошаговая инструкция:

```bash
# 1. Прочитай свой файл задачи
cat intel/queue/gemini_update_passport.json

# 2. Проверь свою версию
gemini --version

# 3. Проверь доступные команды
gemini --help

# 4. Прочитай текущий паспорт
cat intel/AGENT_PASSPORTS.md

# 5. Обнови секцию "Gemini" (строки ~174-239)
nvim intel/AGENT_PASSPORTS.md
```

### Что нужно обновить:

| Поле | Как проверить |
|------|---------------|
| `model` | `gemini --version` |
| `api_endpoint` | Проверить в конфиге CLI |
| `capabilities` | Перечислить реальные возможности |
| `rate_limits` | Проверить в Google Cloud Console |
| `response_time` | Замерить при выполнении задачи |

### После обновления:

```bash
# 1. Сохрани файл
# 2. Запиши в лог
echo "- [$(date)] Gemini: Passport updated" >> intel/SESSION_LOG.md

# 3. Обнови статус задачи
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' \
  intel/queue/gemini_update_passport.json > /tmp/tmp.json && \
  mv /tmp/tmp.json intel/queue/gemini_update_passport.json
```

---

## 🤖 Команда для Jules

### Задача:
Обновить раздел **Jules** в файле `intel/AGENT_PASSPORTS.md`

### Пошаговая инструкция:

```bash
# 1. Прочитай свой файл задачи
cat intel/queue/jules_update_passport.json

# 2. Проверь доступные команды
jules --help

# 3. Проверь структуру intel/
tree intel/ -L 2

# 4. Прочитай текущий паспорт
cat intel/AGENT_PASSPORTS.md

# 5. Обнови секцию "Jules" (строки ~241-290)
nvim intel/AGENT_PASSPORTS.md
```

### Что нужно обновить:

| Поле | Как проверить |
|------|---------------|
| `cli_commands` | `jules --help` |
| `filesystem_paths` | `tree intel/` |
| `capabilities` | Перечислить реальные возможности |
| `response_time` | Замерить при выполнении команды |

### После обновления:

```bash
# 1. Сохрани файл
# 2. Запиши в SESSION_LOG.md
echo "- [$(date)] Jules: Passport updated" >> intel/SESSION_LOG.md

# 3. Обнови статус задачи
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' \
  intel/queue/jules_update_passport.json > /tmp/tmp.json && \
  mv /tmp/tmp.json intel/queue/jules_update_passport.json
```

---

## ✅ Валидация

После обновления всеми агентами:

```bash
# 1. Проверь что все задачи выполнены
for f in intel/queue/*_update_passport.json; do
  echo "=== $f ==="
  jq '.status' "$f"
done

# 2. Проверь размер файла
ls -lh intel/AGENT_PASSPORTS.md

# 3. Валидируй JSON Agent Cards
# (используй jsonschema или онлайн валидатор)

# 4. Прочитай обновлённый паспорт
bat intel/AGENT_PASSPORTS.md
```

---

## 📊 Статус выполнения

| Агент | Задача | Статус | Обновил |
|-------|--------|--------|---------|
| Qwen | `qwen_update_passport.json` | ⏳ pending | ❓ |
| Gemini | `gemini_update_passport.json` | ⏳ pending | ❓ |
| Jules | `jules_update_passport.json` | ⏳ pending | ❓ |

---

## 🔗 Ссылки

- **Паспорта:** `file:///Users/code/project/intel/AGENT_PASSPORTS.md`
- **Лог сессии:** `file:///Users/code/project/intel/SESSION_LOG.md`
- **Очередь задач:** `file:///Users/code/project/intel/queue/`

---

**Конец документа**
