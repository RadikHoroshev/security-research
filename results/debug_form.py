#!/usr/bin/env python3
"""
Debug script to inspect huntr.com form structure
"""

import asyncio
from playwright.async_api import async_playwright


async def debug_form():
    print("=" * 60)
    print("Huntr.com Form Debugger")
    print("=" * 60)
    print()
    
    async with async_playwright() as p:
        print("[*] Connecting to Chrome...")
        
        try:
            browser = await p.chromium.connect_over_cdp(
                "http://localhost:9222",
                timeout=30000
            )
            
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("[+] Connected!")
            print()
            
            # Show current URL
            url = page.url
            print(f"[*] Current URL: {url}")
            print()
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Find all input fields
            print("=" * 60)
            print("INPUT FIELDS FOUND:")
            print("=" * 60)
            inputs = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[type="text"], input[type="url"], textarea');
                return Array.from(inputs).map((el, i) => ({
                    index: i,
                    tag: el.tagName,
                    type: el.type,
                    name: el.name,
                    id: el.id,
                    placeholder: el.placeholder,
                    label: el.closest('div')?.querySelector('label')?.textContent?.trim() || '',
                    value: el.value.substring(0, 50) + (el.value.length > 50 ? '...' : '')
                })).filter(el => el.name || el.id || el.placeholder || el.label);
            }""")
            
            for inp in inputs[:20]:  # Show first 20
                print(f"\n  [{inp['index']}] {inp['tag']}")
                print(f"      Name: {inp['name'] or '(none)'}")
                print(f"      ID: {inp['id'] or '(none)'}")
                print(f"      Placeholder: {inp['placeholder'] or '(none)'}")
                print(f"      Label: {inp['label'] or '(none)'}")
                print(f"      Current value: {inp['value'] or '(empty)'}")
            
            print()
            print("=" * 60)
            print("CVSS DROPDOWNS:")
            print("=" * 60)
            
            # Find select elements
            selects = await page.evaluate("""() => {
                const selects = document.querySelectorAll('select, [role="listbox"], [data-testid*="cvss"]');
                return Array.from(selects).map((el, i) => ({
                    index: i,
                    tag: el.tagName,
                    id: el.id,
                    'data-testid': el.getAttribute('data-testid'),
                    ariaLabel: el.getAttribute('aria-label'),
                    options: el.options ? Array.from(el.options).map(o => o.value) : 'N/A'
                }));
            }""")
            
            for sel in selects[:10]:
                print(f"\n  [{sel['index']}] {sel['tag']}")
                print(f"      ID: {sel['id'] or '(none)'}")
                print(f"      Data-testid: {sel['data-testid'] or '(none)'}")
                print(f"      Aria-label: {sel['ariaLabel'] or '(none)'}")
            
            print()
            print("=" * 60)
            print("SUBMIT BUTTON:")
            print("=" * 60)
            
            # Find submit button
            submit_btn = await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button, [role="button"]');
                return Array.from(buttons)
                    .filter(btn => btn.textContent.toLowerCase().includes('submit'))
                    .map(btn => ({
                        tag: btn.tagName,
                        text: btn.textContent.trim().substring(0, 50),
                        type: btn.type
                    }));
            }""")
            
            for btn in submit_btn[:5]:
                print(f"  • {btn['tag']}: '{btn['text']}' (type: {btn['type']})")
            
            print()
            print("=" * 60)
            print("SCREENSHOT:")
            print("=" * 60)
            
            # Take screenshot
            from pathlib import Path
            screenshot_path = Path(__file__).parent / "huntr_form_debug.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[+] Screenshot saved to: {screenshot_path}")
            
            print()
            print("=" * 60)
            print("DEBUG COMPLETE!")
            print("=" * 60)
            print()
            print("Check the screenshot and output above to understand form structure.")
            print()
            
            await browser.close()
            
        except Exception as e:
            print()
            print("=" * 60)
            print("ERROR!")
            print("=" * 60)
            print()
            print(f"Could not connect: {e}")
            print()


if __name__ == "__main__":
    asyncio.run(debug_form())
