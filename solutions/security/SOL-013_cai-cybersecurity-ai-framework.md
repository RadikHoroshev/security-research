---
id: SOL-013
name: "CAI — Cybersecurity AI Framework"
source_project: "https://github.com/aliasrobotics/cai"
category: security
tags: [multi-agent, offensive-security, ctf, bug-bounty, autonomous]
quality: 5
applicability: 4
effort: 2
found_by: scout
found_date: 2026-04-02
---

## Что это
Лёгкий open-source фреймворк для создания AI-агентов в области offensive/defensive security, достигший Top-10 на Dragos OT CTF 2025 и давший импульс HackerOne AI Deduplication Agent.

## Почему это хорошо
Доказанная боевая эффективность: 32/34 CTF-задач, 37% velocity-преимущество над топ человеческими командами, тысячи пользователей в продакшене.

## Как работает
CAI строит агентов поверх LLM с набором инструментов (shell, web, сканеры), организованных в конвейер атаки. Версия 0.5 добавила multi-agent режим с командами `/history`, `/compact`, `/graph`, `/memory`. Агент Retester автоматически дедуплицирует отчёты о уязвимостях в масштабе миллионов записей. Фреймворк намеренно минималистичен — никакой тяжёлой оркестрации, только агент + инструменты + контекст.

## Как применить у нас
Интегрировать CAI как бэкенд для security-team агентов: заменить или дополнить CrewAI-пайплайн в `project/security-team/team.py` CAI-агентами для recon и эксплуатации. Использовать CAI Retester-паттерн для автодедупликации находок nuclei/subfinder.

## Зависимости
```bash
pip install cai-framework  # или git clone aliasrobotics/cai
# требует: Python 3.10+, доступ к LLM API (через прокси localhost:8768)
```
