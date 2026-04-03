# 🚀 Huntr Auto-Fill — Быстрая Шпаргалка

## ⚡ 30 СЕКУНД НА ЗАПУСК

```bash
# 1. Запусти Chrome (5 сек)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-session &

# 2. Залогинься на huntr.com (15 сек)
# Открой: https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms

# 3. Запусти скрипт (10 сек)
cd /Users/code/project/intel/results
python3 autofill_huntr_final.py
```

---

## 📋 ЧТО ЗАПОЛНЯЕТСЯ АВТОМАТИЧЕСКИ

| Поле | Статус |
|------|--------|
| Title | ✅ Авто |
| Description | ✅ Авто |
| Impact | ✅ Авто |
| Permalink | ✅ Авто |
| Occurrence Desc | ✅ Авто |
| CVSS (8 dropdowns) | ⚠️ Вручную (30 сек) |

---

## 🎯 CVSS ЗНАЧЕНИЯ

Запомни 8 значений для ручного выбора:

```
Network → Low → Low → None → Unchanged → High → High → High
```

Или по-русски:
```
Сеть → Низкий → Низкий → Никто → Без изменений → Высокий → Высокий → Высокий
```

---

## 🔧 ЕСЛИ НЕ РАБОТАЕТ

| Проблема | Решение |
|----------|---------|
| "Could not connect to Chrome" | `lsof -i :9222` → убей процесс → перезапусти Chrome |
| "Field not found" | `python3 debug_form.py` → узнай новые ID |
| Поля пустые | Проверь что Chrome запущен с флагом |

---

## 📁 ФАЙЛЫ

```
autofill_huntr_final.py    # ⭐ Запускать это
README_AUTOFILL.md         # 📖 Полная инструкция
debug_form.py              # 🔧 Отладка
```

---

## ⚠️ ВАЖНО

- ❌ НЕ модифицируй скрипт без тестирования
- ❌ НЕ передавай huntr_cookies.json никому
- ✅ Проверяй скриншот перед Submit
- ✅ Submit — только вручную

---

## 📞 ПОДДЕРЖКА

Полная документация: `README_AUTOFILL.md`

---

**Статус:** ✅ WORKING | **Последний тест:** 2026-04-02
