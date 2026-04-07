#!/usr/bin/env python3
"""
================================================================================
  Huntr.com Auto-Fill Script (Chrome Integration) v2.0
================================================================================

  ⚠️  SAFETY RULES:
  - НЕ ИСПОЛЬЗУЙ этот скрипт без валидации данных
  - Всегда проверя screenshot перед submit
  - НИКОГДА не отправляй форму автоматически (CAPTCHA риск)

  Изменения в v2.0:
  - Удалён хардкод (данные принимаются из JSON файла)
  - Добавлена валидация полей перед заполнением
  - Добавлено логирование всех действий
  - Добавлена обработка ошибок
  - Добавлен режим dry-run (без подключения к Chrome)

  Usage:
    python3 autofill_huntr_v2.py report_READY.json              # Заполнить форму
    python3 autofill_huntr_v2.py report_READY.json --dry-run    # Только валидация
    python3 autofill_huntr_v2.py report_READY.json --no-wait    # Без ожидания

  Requirements:
    - Chrome running with --remote-debugging-port=9222
    - User logged in to huntr.com
    - Form page open in browser
    - JSON файл с данными заявки

  JSON формат (report_READY.json):
    {
      "title": "макс 100 символов",
      "description": "markdown описание",
      "impact": "влияние уязвимости",
      "occurrences": {
        "permalink": "https://github.com/...",
        "description": "описание местонахождения"
      },
      "cvss": {
        "attack_vector": "Network|Adjacent|Local|Physical",
        "attack_complexity": "Low|High",
        "privileges_required": "None|Low|High",
        "user_interaction": "None|Required",
        "scope": "Unchanged|Changed",
        "confidentiality": "None|Low|High",
        "integrity": "None|Low|High",
        "availability": "None|Low|High"
      }
    }

  Last modified: 2026-04-05
  Based on: autofill_huntr_final.py (tested 2026-04-02)

================================================================================

"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

DEBUG_PORT = 9222
TIMEOUT_MS = 30000
REVIEW_SECONDS = 90
CVSS_WAIT_SECONDS = 35

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "autofill_huntr.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("autofill")

# ═══════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════

CVSS_VALID_VALUES = {
    "attack_vector": ["Network", "Adjacent", "Local", "Physical"],
    "attack_complexity": ["Low", "High"],
    "privileges_required": ["None", "Low", "High"],
    "user_interaction": ["None", "Required"],
    "scope": ["Unchanged", "Changed"],
    "confidentiality": ["None", "Low", "High"],
    "integrity": ["None", "Low", "High"],
    "availability": ["None", "Low", "High"],
}

def validate_form_data(data):
    """Валидация данных заявки. Возвращает список ошибок."""
    errors = []
    warnings = []
    
    # Title
    title = data.get("title", "")
    if not title:
        errors.append("title: отсутствует")
    elif len(title) > 100:
        errors.append(f"title: слишком длинный ({len(title)} > 100 символов)")
    elif len(title) < 10:
        warnings.append(f"title: слишком короткий ({len(title)} < 10 символов)")
    
    # Description
    desc = data.get("description", "")
    if not desc:
        errors.append("description: отсутствует")
    elif len(desc) > 10000:
        warnings.append(f"description: очень длинный ({len(desc)} символов)")
    elif "# Description" not in desc and "## " not in desc:
        warnings.append("description: не найден markdown заголовок")
    
    # Impact
    impact = data.get("impact", "")
    if not impact:
        errors.append("impact: отсутствует")
    
    # Occurrences
    occurrences = data.get("occurrences", {})
    if not isinstance(occurrences, dict):
        errors.append("occurrences: должен быть объектом")
    else:
        if not occurrences.get("permalink"):
            errors.append("occurrences.permalink: отсутствует")
        elif "http" not in occurrences["permalink"]:
            errors.append("occurrences.permalink: не URL")
        if not occurrences.get("description"):
            errors.append("occurrences.description: отсутствует")
    
    # CVSS
    cvss = data.get("cvss", {})
    if not isinstance(cvss, dict):
        errors.append("cvss: должен быть объектом")
    else:
        for field, valid_values in CVSS_VALID_VALUES.items():
            value = cvss.get(field)
            if value is None:
                errors.append(f"cvss.{field}: отсутствует")
            elif value not in valid_values:
                errors.append(f"cvss.{field}: '{value}' не в {valid_values}")
    
    return errors, warnings

def validate_and_report(data):
    """Валидация с логированием. Возвращает True если ОК."""
    errors, warnings = validate_form_data(data)
    
    logger.info(f"Validation: {len(errors)} errors, {len(warnings)} warnings")
    for w in warnings:
        logger.warning(f"  ⚠️  {w}")
    for e in errors:
        logger.error(f"  ❌ {e}")
    
    if errors:
        logger.error(f"VALIDATION FAILED: {len(errors)} ошибок. Исправьте перед запуском.")
        return False
    
    logger.info("✅ Validation passed")
    return True

# ═══════════════════════════════════════════════════════════
# FORM FILLING
# ═══════════════════════════════════════════════════════════

async def fill_field(page, selector, value, label, max_length=None):
    """Заполнить одно поле с валидацией и логированием."""
    try:
        element = page.locator(selector)
        count = await element.count()
        if count == 0:
            logger.warning(f"  ⚠️  {label}: поле не найдено ({selector})")
            return False
        
        text = str(value)[:max_length] if max_length else str(value)
        await element.fill(text)
        logger.info(f"  ✅ {label}: заполнено ({len(text)} символов)")
        await asyncio.sleep(0.5)
        return True
        
    except Exception as e:
        logger.error(f"  ❌ {label}: ошибка — {str(e)[:80]}")
        return False

async def autofill_form(data, dry_run=False, no_wait=False):
    """Основная функция заполнения формы."""
    logger.info("=" * 60)
    logger.info("Huntr.com Auto-Fill v2.0")
    logger.info("=" * 60)
    
    # Validation
    if not validate_and_report(data):
        logger.error("❌ Валидация не пройдена. Скрипт остановлен.")
        return False
    
    # Dry run mode
    if dry_run:
        logger.info("🔍 DRY RUN MODE — валидация завершена, без подключения к Chrome")
        return True
    
    # Chrome connection
    logger.info(f"[*] Подключение к Chrome (port {DEBUG_PORT})...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(
                f"http://localhost:{DEBUG_PORT}",
                timeout=TIMEOUT_MS
            )
            
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            logger.info("[+] Chrome подключён!")
            
            # Check URL
            current_url = page.url
            logger.info(f"[*] Текущий URL: {current_url}")
            
            if "huntr.com" not in current_url:
                logger.warning("[!] Не на huntr.com. Переход на форму...")
                await page.goto("https://huntr.com/bounties/disclose")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
            
            # Instructions
            logger.info("=" * 60)
            logger.info("ИНСТРУКЦИЯ:")
            logger.info("=" * 60)
            logger.info("  1. CVSS dropdowns — выберите вручную (30 сек)")
            logger.info("  2. Текстовые поля — заполнятся автоматически")
            logger.info("  3. Скриншот — для проверки")
            logger.info("  4. Submit — вручную")
            
            if not no_wait:
                logger.info("Press ENTER to continue...")
                await asyncio.get_event_loop().run_in_executor(None, input)
            
            # CVSS Dropdowns (manual)
            logger.info("")
            logger.info("=" * 60)
            logger.info("STEP 1: CVSS Dropdowns (MANUAL)")
            logger.info("=" * 60)
            
            cvss = data["cvss"]
            for field, value in cvss.items():
                logger.info(f"  • {field}: {value}")
            
            wait_time = CVSS_WAIT_SECONDS if not no_wait else 2
            logger.info(f"⏳ {wait_time} секунд на выбор CVSS...")
            await asyncio.sleep(wait_time)
            
            # Auto-fill text fields
            logger.info("")
            logger.info("=" * 60)
            logger.info("STEP 2: Auto-fill text fields")
            logger.info("=" * 60)
            
            filled_count = 0
            total_fields = 5
            
            filled_count += await fill_field(page, "#write-up-title", data["title"], "Title", max_length=100)
            filled_count += await fill_field(page, "#readmeProp-input", data["description"][:5000], "Description", max_length=5000)
            filled_count += await fill_field(page, "#impactProp-input", data["impact"], "Impact")
            filled_count += await fill_field(page, "#permalink-url-0", data["occurrences"]["permalink"], "Permalink")
            filled_count += await fill_field(page, "#description-0", data["occurrences"]["description"], "Occurrence desc")
            
            logger.info(f"Заполнено: {filled_count}/{total_fields} полей")
            
            if filled_count < total_fields:
                logger.warning(f"⚠️  {total_fields - filled_count} полей не заполнено! Проверьте вручную.")
            
            # Scroll & screenshot
            logger.info("[*] Скриншот...")
            await page.evaluate("window.scrollTo(0, 0)")
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            screenshot_path = SCRIPT_DIR / f"huntr_filled_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"[+] Скриншот: {screenshot_path}")
            
            # Log form data summary
            logger.info("")
            logger.info("=" * 60)
            logger.info("AUTO-FILL COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"Title: {data['title'][:60]}...")
            logger.info(f"Description: {len(data['description'])} символов")
            logger.info(f"Impact: {len(data['impact'])} символов")
            logger.info(f"CVSS: {data['cvss'].get('attack_vector')}/{data['cvss'].get('confidentiality')}/{data['cvss'].get('integrity')}/{data['cvss'].get('availability')}")
            
            # Save filled data for reference
            filled_data_path = SCRIPT_DIR / f"huntr_filled_data_{timestamp}.json"
            filled_data_path.write_text(json.dumps(data, indent=2))
            logger.info(f"💾 Данные сохранены: {filled_data_path}")
            
            review_time = REVIEW_SECONDS if not no_wait else 5
            logger.info(f"⏳ {review_time} секунд для проверки формы...")
            logger.info("Не забудьте вручную нажать 'Submit Report'!")
            await asyncio.sleep(review_time)
            
            await browser.close()
            logger.info("[+] Готово!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {str(e)[:200]}")
            logger.error("")
            logger.error("Убедитесь что:")
            logger.error(f"  1. Chrome запущен с --remote-debugging-port={DEBUG_PORT}")
            logger.error("  2. Вы залогинены на huntr.com")
            logger.error("  3. Форма открыта в браузере")
            return False

# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def load_json_file(path):
    """Загрузить и распарсить JSON файл."""
    filepath = Path(path)
    if not filepath.exists():
        logger.error(f"Файл не найден: {filepath}")
        sys.exit(1)
    
    try:
        with open(filepath) as f:
            data = json.load(f)
        logger.info(f"✅ Загружено: {filepath.name}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка JSON в {filepath}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Huntr.com Auto-Fill v2.0")
    parser.add_argument("json_file", help="JSON файл с данными заявки")
    parser.add_argument("--dry-run", action="store_true", help="Только валидация, без Chrome")
    parser.add_argument("--no-wait", action="store_true", help="Без ожиданий (для тестов)")
    args = parser.parse_args()
    
    data = load_json_file(args.json_file)
    
    success = asyncio.run(autofill_form(data, dry_run=args.dry_run, no_wait=args.no_wait))
    
    sys.exit(0 if success else 1)
