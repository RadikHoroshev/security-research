# 🤖 Huntr.com Auto-Fill Script — Документация для Агентов

> **⚠️ ВАЖНО: Только для чтения!**  
> Этот скрипт настроен и протестирован. **НЕ модифицируйте** без веской причины и тестирования.

---

## 📋 Назначение

Скрипт автоматически заполняет форму отправки уязвимостей на **huntr.com**:
- ✅ Подключается к существующему браузеру Chrome
- ✅ Автоматически заполняет текстовые поля (Title, Description, Impact, Occurrences)
- ⚠️ CVSS dropdowns — вручную (30 секунд, защита от ботов)
- ✅ Делает скриншот для верификации
- ❌ Submit — только вручную (контроль человека)

---

## 🔐 ТРЕБОВАНИЯ БЕЗОПАСНОСТИ

### Обязательно перед запуском:

1. **Chrome запущен с флагом отладки:**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-debug-session
   ```

2. **Пользователь авторизован на huntr.com**
   - Залогиньтесь вручную
   - Откройте форму: `https://huntr.com/bounties/disclose/opensource?target=...`

3. **Файл cookie сохранён (опционально):**
   ```bash
   python3 save_huntr_cookies.py
   ```

---

## 🚀 БЫСТРЫЙ СТАРТ

```bash
# 1. Перейди в директорию со скриптом
cd /Users/code/project/intel/results

# 2. Запусти скрипт
python3 autofill_huntr_final.py

# 3. Следуй инструкциям в терминале
```

---

## 📖 ПОДРОБНАЯ ИНСТРУКЦИЯ

### Шаг 1: Подготовка Chrome

```bash
# Закрой все окна Chrome
killall "Google Chrome" 2>/dev/null || true

# Запусти Chrome с отладочным портом
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-session &
```

### Шаг 2: Авторизация

1. В Chrome перейди на **https://huntr.com**
2. **Залогинься** (email/пароль + 2FA если есть)
3. Перейди на форму отправки:
   ```
   https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms
   ```

### Шаг 3: Запуск скрипта

```bash
cd /Users/code/project/intel/results
python3 autofill_huntr_final.py
```

### Шаг 4: Следуй инструкциям

Скрипт покажет:

```
============================================================
AUTO-FILL INSTRUCTIONS:
============================================================

This script will:
  1. Show CVSS dropdown values to select manually (30 sec)
  2. Auto-fill all text fields (Title, Description, Impact, etc.)
  3. Take a screenshot for review
  4. You review and click 'Submit Report' manually

Press ENTER to continue...
```

**Нажми Enter** для продолжения.

### Шаг 5: Выбери CVSS (30 секунд)

Скрипт покажет значения для ручного выбора:

```
Select these values in the CVSS section:

  • Attack Vector: Network
  • Attack Complexity: Low
  • Privileges Required: Low
  • User Interaction: None
  • Scope: Unchanged
  • Confidentiality: High
  • Integrity: High
  • Availability: High

⏳  You have 35 seconds to select CVSS values...
```

**Вручную выбери** эти значения в dropdown формы.

### Шаг 6: Автозаполнение

Скрипт автоматически заполнит:

```
[*] Filling Title...
    ✓ Title filled
[*] Filling Description...
    ✓ Description filled
[*] Filling Impact...
    ✓ Impact filled
[*] Filling Occurrences Permalink...
    ✓ Permalink filled
[*] Filling Occurrences Description...
    ✓ Occurrence description filled
```

### Шаг 7: Проверка

```
[*] Taking screenshot...
[+] Screenshot saved to: /Users/code/project/intel/results/huntr_form_filled.png
```

**Проверь:**
1. Скриншот в браузере
2. Файл `huntr_form_filled.png`

### Шаг 8: Submit (вручную!)

```
📋 NEXT STEPS:

  1. Review the filled form in your browser
  2. Check the screenshot: huntr_form_filled.png
  3. Scroll down to find 'Submit Report' button
  4. Click 'Submit Report' when ready
```

**⚠️ ВАЖНО:** Нажми **"Submit Report"** только если уверен что всё заполнено правильно!

---

## ⚙️ КОНФИГУРАЦИЯ

### Изменение данных формы

Данные формы хранятся в переменной `FORM_DATA` в начале скрипта:

```python
FORM_DATA = {
    "title": "Path Traversal in /upload_app leads to RCE via custom function injection",
    "description": """# Description\n\nA critical Path Traversal...""",
    "impact": """This vulnerability allows...""",
    "occurrences": {
        "permalink": "https://github.com/ParisNeo/lollms/blob/main/...",
        "description": "Unsanitized 'name' field..."
    },
    "cvss": { ... }
}
```

### ⚠️ ПРЕДУПРЕЖДЕНИЕ

**Перед изменением FORM_DATA:**

1. ✅ Создай резервную копию скрипта
2. ✅ Протестируй изменения
3. ✅ Убедись что селекторы правильные (ID полей могут измениться)

---

## 🔧 ОТЛАДКА

### Ошибка: "Could not connect to Chrome"

**Причины:**
1. Chrome не запущен с `--remote-debugging-port=9222`
2. Порт 9222 занят другим процессом
3. Chrome запущен раньше без флагов

**Решение:**
```bash
# Проверь что использует порт 9222
lsof -i :9222

# Убей процесс если нужно
kill -9 <PID>

# Перезапусти Chrome с флагами
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-session
```

### Ошибка: "Field not found"

**Причина:** ID полей на huntr.com изменились

**Решение:** Запусти отладочный скрипт:
```bash
python3 debug_form.py
```

Он покажет актуальные ID полей формы.

### Скрипт работает но поля пустые

**Причина:** Playwright не может взаимодействовать с React-компонентами

**Решение:** Использовать `page.locator().fill()` вместо `page.evaluate()` (уже исправлено в текущей версии)

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
/Users/code/project/intel/results/
├── autofill_huntr_final.py    # ⭐ ГЛАВНЫЙ СКРИПТ (не модифицировать!)
├── save_huntr_cookies.py      # Сохранение cookie сессии
├── launch_chrome.sh           # Helper для запуска Chrome
├── debug_form.py              # Отладка структуры формы
├── README_COOKIE_SAVER.md     # Инструкция по сохранению cookie
├── README_AUTOFILL.md         # Этот файл
└── huntr_form_filled.png      # Скриншот после заполнения
```

---

## 🛡️ ЗАЩИТА ОТ МОДИФИКАЦИЙ

### Для других агентов:

```
┌─────────────────────────────────────────────────────────┐
│  ⚠️  ЭТОТ СКРИПТ НАСТРОЕН И ПРОТЕСТИРОВАН               │
│                                                         │
│  НЕ модифицируй без:                                    │
│  1. Веской причины                                      │
│  2. Создания резервной копии                            │
│  3. Полного тестирования                                │
│                                                         │
│  Изменения могут сломать:                               │
│  - Селекторы полей                                      │
│  - Тайминги                                             │
│  - Логику заполнения                                    │
└─────────────────────────────────────────────────────────┘
```

### Если нужно изменить:

1. **Создай резервную копию:**
   ```bash
   cp autofill_huntr_final.py autofill_huntr_final.py.backup
   ```

2. **Внеси изменения**

3. **Протестируй:**
   ```bash
   python3 autofill_huntr_final.py
   ```

4. **Проверь скриншот** что все поля заполнены

---

## 📊 ТЕКУЩАЯ КОНФИГУРАЦИЯ

### Заполняемые поля:

| Поле | ID селектора | Статус |
|------|--------------|--------|
| Title | `#write-up-title` | ✅ Авто |
| Description | `#readmeProp-input` | ✅ Авто |
| Impact | `#impactProp-input` | ✅ Авто |
| Permalink | `#permalink-url-0` | ✅ Авто |
| Occurrence Desc | `#description-0` | ✅ Авто |
| CVSS (8 dropdowns) | N/A | ⚠️ Вручную |

### CVSS значения (по умолчанию):

```python
"cvss": {
    "attack_vector": "Network",
    "attack_complexity": "Low",
    "privileges_required": "Low",
    "user_interaction": "None",
    "scope": "Unchanged",
    "confidentiality": "High",
    "integrity": "High",
    "availability": "High"
}
```

**CVSS Score:** 8.8 (High)

---

## 🎯 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Быстрое заполнение

```bash
# Уже залогинен и форма открыта
python3 autofill_huntr_final.py
# Нажми Enter
# Выбери CVSS (30 сек)
# Готово!
```

### Пример 2: Новая уязвимость

1. Отредактируй `FORM_DATA` в начале скрипта
2. Запусти: `python3 autofill_huntr_final.py`
3. Проверь скриншот
4. Нажми Submit

### Пример 3: Отладка

```bash
# Узнай ID полей формы
python3 debug_form.py

# Посмотри скриншот
open huntr_form_debug.png
```

---

## ❓ FAQ

### Q: Можно ли использовать без Chrome?
**A:** Нет. Скрипт требует Chrome с `--remote-debugging-port=9222`.

### Q: Можно ли автоматизировать CVSS dropdowns?
**A:** Нет. Huntr использует JavaScript защиту от ботов. Требуется ручной клик.

### Q: Можно ли автоматизировать Submit?
**A:** Технически да, но **НЕ рекомендуется**. Submit должен контролировать человек.

### Q: Как использовать cookie файл?
**A:** Cookie файл (`huntr_cookies.json`) используется для сохранения сессии. Запусти `save_huntr_cookies.py` один раз.

### Q: Скрипт перестал работать после обновления huntr.com
**A:** Запусти `debug_form.py` чтобы узнать новые ID полей. Обнови селекторы в скрипте.

---

## 📞 ПОДДЕРЖКА

### Если что-то пошло не так:

1. **Проверь Chrome запущен с флагами**
2. **Проверь авторизацию** на huntr.com
3. **Запусти отладку:** `python3 debug_form.py`
4. **Посмотри скриншот:** `huntr_form_debug.png`

### Логи ошибок:

Скрипт выводит подробные логи:
```
[*] Connecting to Chrome...
[+] Connected to Chrome successfully!
[*] Filling Title...
    ✓ Title filled
...
```

Если видишь `⚠ Field not found` — ID поля изменился.

---

## ⚠️ ПРЕДУПРЕЖДЕНИЯ

### Никогда не делай:

- ❌ **НЕ передавай** `huntr_cookies.json` никому
- ❌ **НЕ загружай** cookie файл на GitHub
- ❌ **НЕ модифицируй** скрипт без тестирования
- ❌ **НЕ отправляй** дубликаты репортов

### Всегда делай:

- ✅ **Проверяй** скриншот перед Submit
- ✅ **Удаляй** cookie файл после отправки
- ✅ **Создавай** резервную копию перед изменениями
- ✅ **Тестируй** изменения перед использованием

---

## 📝 ИСТОРИЯ ИЗМЕНЕНИЙ

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-04-02 | Первая версия (ручное заполнение) |
| 1.1 | 2026-04-02 | Chrome integration |
| 1.2 | 2026-04-02 | Исправлены селекторы полей |
| 1.3 | 2026-04-02 | Добавлена документация |

---

## 🎯 КОНТРОЛЬНЫЙ СПИСОК ПЕРЕД ЗАПУСКОМ

```
[ ] Chrome запущен с --remote-debugging-port=9222
[ ] Пользователь авторизован на huntr.com
[ ] Форма открыта в браузере
[ ] Все окна Chrome закрыты перед запуском (если нужно)
[ ] Порт 9222 не занят другим процессом
[ ] Скрипт имеет права на выполнение (chmod +x)
[ ] Playwright установлен (pip install playwright)
```

---

**✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ!**

**Последнее обновление:** 2 апреля 2026  
**Статус:** ✅ Протестировано и работает
