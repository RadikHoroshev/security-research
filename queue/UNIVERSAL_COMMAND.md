project/intel/queue/UNIVERSAL_COMMAND.md
```

```markdown
# УНИВЕРСАЛЬНАЯ КОМАНДА — Заполни свой паспорт

**Кому:** Любой агент (Qwen, Gemini, Jules, или новый)  
**Что делать:** Заполни/обнови свой раздел в AGENT_PASSPORTS.md  
**Когда:** При подключении, изменении инструментов, новых навыках

---

## 🚀 Быстрая команда (скопируй и выполни):

```bash
cd /Users/code/project && cat intel/queue/SELF_IDENTIFY.md && echo "=== НАЧИНАЮ ===" && whoami && nvim intel/AGENT_PASSPORTS.md
```

---

## 📋 Пошаговая инструкция:

### 1. Прочитай гайд самоидентификации
```bash
cat /Users/code/project/intel/queue/SELF_IDENTIFY.md
```

### 2. Определи кто ты
- Имя: `whoami`
- Тип: Local LLM / Cloud / CLI / Hybrid
- Версия: проверь свою версию (`ollama --version`, `gemini --version`, etc.)

### 3. Найди или создай свой раздел в паспорте
```bash
# Открой файл
nvim /Users/code/project/intel/AGENT_PASSPORTS.md

# Найди свой раздел (или создай новый ## 🤖 [Твоё имя])
```

### 4. Заполни обязательные поля:

**Agent Card JSON:**
```json
{
  "name": "Твоё имя",
  "description": "Короткое описание",
  "roles": ["роль1", "роль2"],
  "capabilities": {
    "что_умеешь": true,
    "что_не_умеешь": false
  },
  "potential": {
    "max_context": "X токенов",
    "response_time": "N секунд",
    "best_for": ["задача1", "задача2"],
    "limitations": ["лимит1", "лимит2"]
  },
  "tools": [
    "инструмент1",
    "инструмент2",
    "API_endpoint"
  ]
}
```

**Таблица характеристик:**
| Параметр | Значение |
|----------|----------|
| **Имя** | Твоё имя |
| **Тип** | Local/Cloud/CLI |
| **Версия** | Версия модели/CLI |
| **Возможности** | Что умеешь |
| **Потенциал** | Лимиты и границы |
| **Инструменты** | Список инструментов |

### 5. Зафиксируй изменения
```bash
echo "- [$(date '+%Y-%m-%d %H:%M')] $(whoami): Passport updated | Capabilities: [перечисли ключевые] | Tools: [количество]" >> /Users/code/project/intel/SESSION_LOG.md
```

---

## 🔄 Обновляй паспорт когда:

- [ ] Изменилась версия модели/CLI
- [ ] Добавился новый инструмент
- [ ] Открылась новая возможность
- [ ] Изменились лимиты (контекст, скорость)

**Команда для обновления:**
```bash
cd /Users/code/project && cat intel/queue/SELF_IDENTIFY.md && nvim intel/AGENT_PASSPORTS.md
```

---

## ✅ Проверка

После заполнения:
1. JSON валиден? (`jq` проверяет)
2. Все поля заполнены?
3. SESSION_LOG обновлён?
4. Другие агенты поймут кто ты?

---

**Файлы:**
- Паспорт: `intel/AGENT_PASSPORTS.md`
- Гайд: `intel/queue/SELF_IDENTIFY.md`
- Лог: `intel/SESSION_LOG.md`
