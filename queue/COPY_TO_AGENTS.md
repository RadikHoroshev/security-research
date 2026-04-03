# COPY TO AGENTS — Отправь каждому агенту его команду

---

## 🤖 QWEN CODER — Отправь эту команду:

```bash
cd /Users/code/project && cat intel/queue/AGENT_ONBOARDING.md | grep -A 50 "QWEN CODER" && echo "=== ТВОЯ ЗАДАЧА ===" && nvim intel/AGENT_PASSPORTS.md +89
```

**Или полная инструкция:**

```bash
# 1. Прочитай онбординг
cat /Users/code/project/intel/queue/AGENT_ONBOARDING.md

# 2. Проверь свои модели
ollama list && ollama show qwen2.5-coder:14b

# 3. Обнови свой раздел в паспорте (строки 89-172)
nvim /Users/code/project/intel/AGENT_PASSPORTS.md

# 4. Заполни: Возможности, Потенциал, Инструменты

# 5. Зафиксируй выполнение
echo "- [$(date '+%Y-%m-%d %H:%M')] Qwen: Passport updated, capabilities listed ✅" >> /Users/code/project/intel/SESSION_LOG.md

# 6. Обнови статус задачи
jq '.status = "completed"' /Users/code/project/intel/queue/qwen_update_passport.json > /tmp/q.json && mv /tmp/q.json /Users/code/project/intel/queue/qwen_update_passport.json
```

---

## 🤖 GEMINI — Отправь эту команду:

```bash
cd /Users/code/project && cat intel/queue/AGENT_ONBOARDING.md | grep -A 50 "GEMINI" && echo "=== ТВОЯ ЗАДАЧА ===" && nvim intel/AGENT_PASSPORTS.md +174
```

**Или полная инструкция:**

```bash
# 1. Прочитай онбординг
cat /Users/code/project/intel/queue/AGENT_ONBOARDING.md

# 2. Проверь свою версию
gemini --version && gemini --help

# 3. Обнови свой раздел в паспорте (строки 174-239)
nvim /Users/code/project/intel/AGENT_PASSPORTS.md

# 4. Заполни: Возможности, Потенциал, Инструменты

# 5. Зафиксируй выполнение
echo "- [$(date '+%Y-%m-%d %H:%M')] Gemini: Passport updated, capabilities listed ✅" >> /Users/code/project/intel/SESSION_LOG.md

# 6. Обнови статус задачи
jq '.status = "completed"' /Users/code/project/intel/queue/gemini_update_passport.json > /tmp/g.json && mv /tmp/g.json /Users/code/project/intel/queue/gemini_update_passport.json
```

---

## 🤖 JULES — Отправь эту команду:

```bash
cd /Users/code/project && cat intel/queue/AGENT_ONBOARDING.md | grep -A 50 "JULES" && echo "=== ТВОЯ ЗАДАЧА ===" && nvim intel/AGENT_PASSPORTS.md +241
```

**Или полная инструкция:**

```bash
# 1. Прочитай онбординг
cat /Users/code/project/intel/queue/AGENT_ONBOARDING.md

# 2. Проверь свои команды
jules --help && tree /Users/code/project/intel/ -L 2

# 3. Обнови свой раздел в паспорте (строки 241-290)
nvim /Users/code/project/intel/AGENT_PASSPORTS.md

# 4. Заполни: Возможности, Потенциал, Инструменты

# 5. Зафиксируй выполнение
echo "- [$(date '+%Y-%m-%d %H:%M')] Jules: Passport updated, capabilities listed ✅" >> /Users/code/project/intel/SESSION_LOG.md

# 6. Обнови статус задачи
jq '.status = "completed"' /Users/code/project/intel/queue/jules_update_passport.json > /tmp/j.json && mv /tmp/j.json /Users/code/project/intel/queue/jules_update_passport.json
```

---

## ✅ Проверка выполнения

После того как все агенты выполнили задание:

```bash
# Проверь статусы всех задач
cd /Users/code/project
for f in intel/queue/*_update_passport.json; do
  echo "=== $(basename $f) ==="
  jq -r '"Status: \(.status) | Assigned: \(.assigned_to)"' "$f"
done

# Проверь лог сессии
tail -20 intel/SESSION_LOG.md

# Проверь обновлённый паспорт
wc -l intel/AGENT_PASSPORTS.md && head -100 intel/AGENT_PASSPORTS.md
```

---

## 📋 Что должно получиться

Каждый агент заполнит в своём разделе:

### Agent Card JSON:
```json
{
  "name": "Имя",
  "capabilities": { ... },
  "potential": { ... },
  "tools": [ ... ]
}
```

### Таблица:
| Возможности | Потенциал | Инструменты |
|-------------|-----------|-------------|
| Что умеет | Лимиты | Что использует |

---

## 🎯 Главный файл

**Все агенты должны прочитать:**
```
/Users/code/project/intel/queue/AGENT_ONBOARDING.md
```

**И обновить:**
```
/Users/code/project/intel/AGENT_PASSPORTS.md
```

**И зафиксировать в:**
```
/Users/code/project/intel/SESSION_LOG.md
```

---

**После выполнения всех агентов — команда готова к работе! 🚀**
