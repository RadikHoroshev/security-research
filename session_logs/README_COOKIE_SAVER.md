# Huntr.com Cookie Saver - Инструкция

## 📋 Что это делает?

Этот скрипт сохраняет твои cookie от huntr.com для автоматического заполнения формы.

---

## 🚀 ПОШАГОВАЯ ИНСТРУКЦИЯ

### ШАГ 1: Запусти Chrome с отладкой

**Вариант A: Использовать helper скрипт (проще)**
```bash
cd /Users/code/project/intel/results
./launch_chrome.sh
```

**Вариант B: Запустить Chrome вручную (если скрипт не работает)**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-session
```

---

### ШАГ 2: Залогинься на Huntr

1. В открытом Chrome перейди на **https://huntr.com/login**
2. Введи свой **email** и **пароль**
3. Пройди **2FA** если включено
4. Дождись страницы **профиля/dashboard** (успешный логин)

---

### ШАГ 3: Сохрани cookie

**В ДРУГОМ терминале** (первый с Chrome не закрывай!):

```bash
cd /Users/code/project/intel/results
python3 save_huntr_cookies.py
```

Скрипт:
- Подключится к твоему Chrome
- Перейдёт на huntr.com/login
- Сохранит cookie после нажатия Enter

---

### ШАГ 4: Подтверди сохранение

После успешного сохранения увидишь:

```
============================================================
SUCCESS!
============================================================

[+] Cookies saved to: /Users/code/project/intel/results/huntr_cookies.json
[+] Total cookies saved: 5

Next steps:
  1. Keep this cookie file secure (do not share)
  2. Next script will use these cookies to fill the form
  3. Delete cookie file after submission for security
```

---

## 📁 Где файл с cookie?

```
/Users/code/project/intel/results/huntr_cookies.json
```

---

## ⚠️ БЕЗОПАСНОСТЬ

### Что можно:
- ✅ Использовать cookie для автоматизации
- ✅ Хранить локально на своём компьютере

### Что НЕЛЬЗЯ:
- ❌ **НЕ передавай файл `huntr_cookies.json` никому**
- ❌ **НЕ загружай на GitHub или в публичный доступ**
- ❌ **НЕ отправляй по email/чату**

### После использования:
```bash
# Удали файл с cookie для максимальной безопасности
rm /Users/code/project/intel/results/huntr_cookies.json
```

---

## 🔧 Решение проблем

### Ошибка: "Could not connect to Chrome"

**Причина 1:** Chrome не запущен с флагами
```bash
# Закрой все окна Chrome и запусти заново:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-session
```

**Причина 2:** Порт 9222 уже занят
```bash
# Проверь что использует порт:
lsof -i :9222

# Убей процесс если нужно:
kill -9 <PID>
```

**Причина 3:** Chrome запущен раньше без флагов
```bash
# Закрой ВСЕ окна Chrome полностью:
killall "Google Chrome"

# Затем запусти с флагами
```

---

### Ошибка: "Browser closed unexpectedly"

**Решение:**
1. Убедись что Chrome запущен с `--remote-debugging-port=9222`
2. Не закрывай Chrome пока скрипт работает
3. Запусти скрипт заново

---

## 📞 Что дальше?

После успешного сохранения cookie:

1. ✅ Файл `huntr_cookies.json` создан
2. ✅ Запусти скрипт автозаполнения (будет создан следующим шагом)
3. ✅ Форма заполнится автоматически
4. ✅ Удали cookie файл после отправки

---

## 🎯 Быстрый старт (копия-вставка)

```bash
# 1. Запусти Chrome
cd /Users/code/project/intel/results
./launch_chrome.sh

# 2. В Chrome перейди на https://huntr.com/login и залогинься

# 3. В другом терминале сохрани cookie
cd /Users/code/project/intel/results
python3 save_huntr_cookies.py
# Нажми Enter после успешного логина

# 4. Готово!
```
