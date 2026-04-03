#!/usr/bin/env python3
"""
Quick Huntr Form Filler
Run this and it will fill the form automatically
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("[*] Opening huntr.com...")
        await page.goto("https://huntr.com/bounties/disclose/opensource?target=https://github.com/parisneo/lollms")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Check if logged in
        title = await page.title()
        if "login" in title.lower():
            print("[!] Please log in first!")
            return
        
        print("[+] Ready to fill!")
        print("[*] Script will wait 10 seconds for you to prepare...")
        await asyncio.sleep(10)
        
        # Fill CVSS
        print("[*] Filling CVSS...")
        
        # The script will guide you through the process
        print("\n[!] MANUAL STEP: Fill CVSS dropdowns:")
        print("    Attack Vector: Network")
        print("    Attack Complexity: Low")
        print("    Privileges Required: Low")
        print("    User Interaction: None")
        print("    Scope: Unchanged")
        print("    Confidentiality: High")
        print("    Integrity: High")
        print("    Availability: High")
        
        await asyncio.sleep(15)
        
        # Fill text fields
        print("[*] Filling text fields...")
        
        # Title
        await page.evaluate('''() => {
            const title = "Path Traversal in /upload_app leads to RCE via custom function injection";
            document.querySelectorAll('input[type="text"]').forEach(i => {
                if (i.placeholder && i.placeholder.toLowerCase().includes("title")) {
                    i.value = title;
                    i.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }''')
        
        print("[+] Done! Check the form and submit manually.")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
