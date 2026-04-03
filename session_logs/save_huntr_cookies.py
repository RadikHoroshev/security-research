#!/usr/bin/env python3
"""
Save Huntr.com authentication cookies
Uses your existing Chrome browser (with remote debugging enabled)

Usage:
  1. First, close all Chrome windows
  2. Launch Chrome with debugging:
     /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-session
  3. Run this script: python3 save_huntr_cookies.py
  4. Login in the Chrome window
  5. Press Enter in terminal
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def save_cookies():
    print("=" * 60)
    print("Huntr.com Cookie Saver (Chrome Integration)")
    print("=" * 60)
    print()
    print("⚠️  BEFORE RUNNING THIS SCRIPT:")
    print()
    print("  1. CLOSE all Chrome windows")
    print()
    print("  2. Launch Chrome with debugging enabled:")
    print("     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
    print("       --remote-debugging-port=9222 \\")
    print("       --user-data-dir=/tmp/chrome-debug-session")
    print()
    print("  3. In Chrome, go to: https://huntr.com/login")
    print("  4. Log in with your credentials")
    print()
    print("=" * 60)
    print()
    print("Press ENTER when Chrome is launched and you're ready to login...")
    print()
    
    # Wait for user to launch Chrome
    await asyncio.get_event_loop().run_in_executor(None, input)
    
    async with async_playwright() as p:
        print("[*] Connecting to your Chrome browser...")
        
        try:
            # Connect to existing Chrome instance
            browser = await p.chromium.connect_over_cdp(
                "http://localhost:9222",
                timeout=30000
            )
            
            # Get the first available context
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("[+] Connected to Chrome successfully!")
            print()
            print("[*] Navigating to huntr.com/login...")
            await page.goto("https://huntr.com/login")
            await page.wait_for_load_state("networkidle")
            
            print()
            print("=" * 60)
            print("LOGIN INSTRUCTIONS:")
            print("=" * 60)
            print()
            print("  1. Log in with your email/password in the Chrome window")
            print("  2. Wait until you see your profile/dashboard page")
            print("  3. Come back to terminal and press ENTER")
            print()
            print("⏳  Waiting for you to log in...")
            print()
            
            # Wait for user to press Enter after login
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            print()
            print("[*] Saving cookies...")
            
            # Get cookies
            cookies = await context.cookies()
            
            # Save to file
            cookie_file = Path(__file__).parent / "huntr_cookies.json"
            with open(cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)
            
            print(f"[+] Cookies saved to: {cookie_file}")
            print(f"[+] Total cookies saved: {len(cookies)}")
            print()
            print("=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Keep this cookie file secure (do not share)")
            print("  2. Next script will use these cookies to fill the form")
            print("  3. Delete cookie file after submission for security")
            print()
            
            await browser.close()
            
        except Exception as e:
            print()
            print("=" * 60)
            print("ERROR!")
            print("=" * 60)
            print()
            print(f"Could not connect to Chrome: {e}")
            print()
            print("Make sure:")
            print("  1. All Chrome windows were closed before launching")
            print("  2. Chrome was launched with --remote-debugging-port=9222")
            print("  3. No other process is using port 9222")
            print()
            print("To check if port 9222 is in use:")
            print("  lsof -i :9222")
            print()


if __name__ == "__main__":
    asyncio.run(save_cookies())
