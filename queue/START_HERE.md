# 🚀 START HERE — Команды для всех агентов

**Создано:** 2026-04-03  
**Статус:** ACTIVE  
**Цель:** Обновить AGENT_PASSPORTS.md, прочитать PROTOCOL.md, познакомиться с другими агентами

---

## 📋 Для всех агентов

```bash
cd /Users/code/project
```

---

## 🤖 QWEN CODER — Твоя задача

### Быстрая команда:
```bash
cat intel/queue/qwen_update_passport.json
```

### Пошагово:
```bash
# 1. Проверь свои модели
ollama list

# 2. Получи параметры
curl http://localhost:11434/api/show -d '{"name":"qwen2.5-coder:14b"}'

# 3. Прочитай паспорт
cat intel/AGENT_PASSPORTS.md

# 4. Прочитай протокол
cat intel/PROTOCOL.md

# 5. Обнови свой раздел (строки 89-172)
nvim intel/AGENT_PASSPORTS.md

# 6. Запиши в лог
echo "- [$(date)] Qwen: Passport updated ✅" >> intel/SESSION_LOG.md

# 7. Обнови статус
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' intel/queue/qwen_update_passport.json > /tmp/q.json && mv /tmp/q.json intel/queue/qwen_update_passport.json
```

### Что обновить:
- ✅ Agent Card JSON (твои реальные возможности)
- ✅ Модель и версия
- ✅ Время ответа (замерь)
- ✅ Контекст (из ollama show)
- ✅ Примеры команд которые выполняешь

---

## 🤖 GEMINI — Твоя задача

### Быстрая команда:
```bash
cat intel/queue/gemini_update_passport.json
```

### Пошагово:
```bash
# 1. Проверь версию
gemini --version

# 2. Прочитай паспорт
cat intel/AGENT_PASSPORTS.md

# 3. Прочитай протокол
cat intel/PROTOCOL.md

# 4. Обнови свой раздел (строки 174-239)
nvim intel/AGENT_PASSPORTS.md

# 5. Запиши в лог
echo "- [$(date)] Gemini: Passport updated ✅" >> intel/SESSION_LOG.md

# 6. Обнови статус
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' intel/queue/gemini_update_passport.json > /tmp/g.json && mv /tmp/g.json intel/queue/gemini_update_passport.json
```

### Что обновить:
- ✅ Agent Card JSON
- ✅ Модель и API endpoint
- ✅ Лимиты токенов
- ✅ Время ответа
- ✅ Примеры задач (recon, huntr.com, reports)

---

## 🤖 JULES — Твоя задача

### Быстрая команда:
```bash
cat intel/queue/jules_update_passport.json
```

### Пошагово:
```bash
# 1. Проверь команды
jules --help

# 2. Проверь структуру
tree intel/ -L 2

# 3. Прочитай паспорт
cat intel/AGENT_PASSPORTS.md

# 4. Прочитай протокол
cat intel/PROTOCOL.md

# 5. Обнови свой раздел (строки 241-290)
nvim intel/AGENT_PASSPORTS.md

# 6. Запиши в SESSION_LOG
echo "- [$(date)] Jules: Passport updated ✅" >> intel/SESSION_LOG.md

# 7. Обнови статус
jq '.status = "completed" | .completed_at = "'"$(date -Iseconds)"'"' intel/queue/jules_update_passport.json > /tmp/j.json && mv /tmp/j.json intel/queue/jules_update_passport.json
```

### Что обновить:
- ✅ Agent Card JSON
- ✅ CLI команды
- ✅ Структура intel/
- ✅ Примеры задач (logging, documentation)

---

## 📊 Статус выполнения

| Агент | Файл задачи | Статус |
|-------|-------------|--------|
| Qwen | `qwen_update_passport.json` | ⏳ pending |
| Gemini | `gemini_update_passport.json` | ⏳ pending |
| Jules | `jules_update_passport.json` | ⏳ pending |

### Проверка:
```bash
# Проверить все статусы
for f in intel/queue/*_update_passport.json; do echo "=== $f ==="; jq -r '.status' "$f"; done
```

---

## 🔗 Важные файлы

| Файл | Назначение |
|------|------------|
| `intel/AGENT_PASSPORTS.md` | Технические паспорта всех агентов |
| `intel/PROTOCOL.md` | Протоколы взаимодействия |
| `intel/SESSION_LOG.md` | Лог сессии |
| `intel/queue/` | Очередь задач |
| `intel/results/` | Результаты работы |

---

## ✅ Чеклист для каждого агента

- [ ] Прочитал свой файл задачи в `queue/`
- [ ] Прочитал `AGENT_PASSPORTS.md`
- [ ] Прочитал `PROTOCOL.md`
- [ ] Обновил свой раздел актуальными данными
- [ ] Записал в `SESSION_LOG.md`
- [ ] Обновил статус задачи на `completed`

---

**После выполнения — все агенты будут знать:**
1. Свои технические параметры ✅
2. Протоколы взаимодействия ✅
3. Друг друга (через паспорта) ✅
4. Где искать задачи и писать результаты ✅

---

**Конец файла**
