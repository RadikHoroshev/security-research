# 📊 СВОДНЫЙ ОТЧЁТ — Результаты анализа новых уязвимостей
**Дата:** 2026-04-07
**Аналитик:** Qwen (координация) + 4 суб-агента (исследование)
**Цель:** Найти уязвимости с bounty $4,000 (Model File Formats)

---

## 🔥 РЕЙТИНГ НОВЫХ НАХОДОК (по приоритету)

### 🥇 #1 — SafeTensors C++: Integer Overflow в get_shape_size()
| Параметр | Значение |
|---|---|
| **Формат** | SafeTensors C++ parser |
| **Bounty** | $4,000 |
| **CVSS** | 8.1 High |
| **Новизна** | HIGH — нет CVE, нет huntr репортов |
| **Файл** | `safetensors-cpp` — `get_shape_size()` умножает dimensions без проверки overflow |
| **Атака** | Crafted tensor shape → integer overflow → heap-buffer-overflow → RCE |
| **PoC** | Требуется: создать .safetensors с dimensions=[0xFFFF, 0xFFFF, 0xFFFF] |
| **Шанс** | ⭐⭐⭐⭐⭐ ВЫСОКИЙ |

**Почему это лучшая находка:**
- Rust ядро SafeTensors защищено (Trail of Bits аудит)
- Но C++ binding (`safetensors-cpp`) НЕ аудирован
- `get_shape_size()` умножает dimensions без проверки → overflow → wrong allocation size
- Нет ни одного CVE для этого конкретного бага

---

### 🥈 #2 — Joblib: Cache Location Path Traversal (N004)
| Параметр | Значение |
|---|---|
| **Формат** | Joblib (.joblib/.pkl) |
| **Bounty** | $4,000 |
| **CVSS** | 8.1 High |
| **Новизна** | HIGH — не пересекается с существующими репортами |
| **Файл** | `joblib/_store_backends.py` — `FileSystemStoreBackend.get_cached_func()` |
| **Атака** | Malicious cache location → path traversal → arbitrary file read |
| **PoC** | Требуется: создать .joblib файл с crafted location |
| **Шанс** | ⭐⭐⭐⭐ ВЫСОКИЙ |

---

### 🥉 #3 — Joblib: LZMA Decompression Bomb (N001)
| Параметр | Значение |
|---|---|
| **Формат** | Joblib compressed (.joblib with lzma) |
| **Bounty** | $4,000 |
| **CVSS** | 7.5 High |
| **Новизна** | HIGH — другой класс уязвимости (resource exhaustion) |
| **Файл** | `joblib/numpy_pickle.py` — `LZMAFile` без `maxsize` limit |
| **Атака** | Маленкий .joblib → LZMA decompression → GB памяти → DoS |
| **PoC** | Требуется: создать .joblib с LZMA compressed payload |
| **Шанс** | ⭐⭐⭐⭐ ВЫСОКИЙ |

---

### #4 — Keras Native: ZIP Path Traversal via DiskIOStore
| Параметр | Значение |
|---|---|
| **Формат** | Keras Native (.keras ZIP) |
| **Bounty** | $4,000 |
| **CVSS** | 7.8 High |
| **Новизна** | MEDIUM-HIGH — bypass существующих защит |
| **Файл** | `keras/saving/saving_lib.py` — `DiskIOStore.__getitem__()` line 467 |
| **Атака** | ZIP with crafted entry → `zf.extract()` без filter → file write |
| **PoC** | Требуется: подтвердить что zf.extract() не проходит filter_safe_zipinfos |
| **Шанс** | ⭐⭐⭐ MEDIUM (60-70%) |

**Проблема:** Keras уже имеет `filter_safe_zipinfos()` — нужно найти bypass.

---

### #5 — ONNX: FunctionProto Exponential Expansion DoS
| Параметр | Значение |
|---|---|
| **Формат** | ONNX (.onnx protobuf) |
| **Bounty** | $4,000 |
| **CVSS** | 7.5 High |
| **Новизна** | MEDIUM — DoS через function expansion, не tensor |
| **Файл** | ONNX function inlining — нет limits на DAG expansion |
| **Атака** | Nested FunctionProto → exponential node growth → OOM/CPU exhaustion |
| **PoC** | Требуется: создать .onnx с цепочкой функций |
| **Шанс** | ⭐⭐⭐ MEDIUM |

**Проблема:** ONNX очень crowded — 9+ CVEs, 12+ huntr репортов. Duplicate risk высокий.

---

### #6 — SafeTensors C++: Missing validate_data_offsets (VULN-6)
| Параметр | Значение |
|---|---|
| **Формат** | SafeTensors C++ |
| **Bounty** | $4,000 |
| **CVSS** | 7.5 High |
| **Новизна** | HIGH |
| **Файл** | safetensors-cpp — `validate_data_offsets()` declared but may not be called |
| **Атака** | Tensor data_offsets超出文件范围 → OOB read |
| **Шанс** | ⭐⭐⭐ MEDIUM |

---

### #7 — open-webui: Embedding Abuse Escalation (#10)
| Параметр | Значение |
|---|---|
| **Формат** | N/A (web application) |
| **Bounty** | Уже сабмитнут ($0, UNPROVEN) |
| **Новое** | Подтверждено: НЕ запатчен |
| **Файл** | `backend/open_webui/routers/openai.py` — `embeddings()` без `Depends(get_verified_user)` |
| **Действие** | Постить escalation comment из `/Users/code/project/intel/results/openwebui_embedding_escalation_comment.md` |

---

## 📋 ПЛАН ДЕЙСТВИЙ

### Немедленно (сегодня):
1. **[ ] Сабмит R1+R2** — Claude Code сабмитнит на huntr (задача выше)
2. **[ ] Создать PoC для SafeTensors C++ integer overflow** — самый высокий шанс на $4,000
3. **[ ] Постить escalation comment для open-webui #10**

### Завтра:
4. **[ ] Создать PoC для Joblib LZMA decompression bomb** — $4,000, чистый DoS
5. **[ ] Создать PoC для Joblib cache path traversal** — $4,000
6. **[ ] Верифицировать Keras ZIP traversal bypass**

### Послезавтра:
7. **[ ] Сабмит лучших находок** на huntr.com
8. **[ ] Новый recon** — найти ещё bounty programs

---

## 💰 ПОТЕНЦИАЛЬНЫЙ ДОХОД

| Категория | Сумма | Статус |
|---|---|---|
| Подтверждённые bounty | $1,625-$1,975 | llama_index + ollama + nltk |
| Готовы к сабмиту (R1+R2) | $700-$2,000 | transformers YAML |
| SafeTensors C++ overflow | $4,000 | PoC нужен |
| Joblib LZMA bomb | $4,000 | PoC нужен |
| Joblib path traversal | $4,000 | PoC нужен |
| Keras ZIP bypass | $4,000 | Верификация нужна |
| ONNX function DoS | $1,500-$4,000 | PoC нужен |
| **ИТОГО потенциал** | **$15,325-$21,975** | |

---

## 📁 СОХРАНЁННЫЕ ФАЙЛЫ

| Файл | Содержание |
|---|---|
| `analysis_safetensors_vulns.md` | SafeTensors C++ integer overflow + 6 findings |
| `analysis_joblib_vulns.md` | Joblib LZMA bomb + path traversal + 5 findings |
| `analysis_keras_native_vulns.md` | Keras ZIP path traversal bypass |
| `analysis_onnx_vulns.md` | ONNX FunctionProto exponential DoS |
| `openwebui_embedding_escalation_comment.md` | Comment для huntr #10 |

---

*Отчёт сгенерирован: 2026-04-07 14:00 UTC*
