"""
Debug - cari elemen yang benar diklik di phone card
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

EMAIL = "cjjrcmun@guerrillamail.info"
PASS = "Bot123456!"

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        device_config = p.devices['iPhone 15 Pro Max'].copy()
        device_config['has_touch'] = False
        device_config['is_mobile'] = False
        context = await browser.new_context(**device_config)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(4)
        inputs = page.locator("input")
        await inputs.nth(0).fill(EMAIL)
        await inputs.nth(1).fill(PASS)
        login_btn = page.locator('.dlbutton', has_text="Login")
        await login_btn.click(timeout=10000)
        await asyncio.sleep(6)

        group_element = page.locator("text=试用分组").first
        await group_element.wait_for(state="visible", timeout=60000)
        await group_element.click()
        await asyncio.sleep(15)
        
        print("=== URL:", page.url)
        
        # Cari elemen yang ada text ID:336 dan parent-parentnya
        print("\n=== Elemen dengan 'ID:' ===")
        id_el = page.locator("text=/ID:\\s*\\d+/").first
        bbox = await id_el.bounding_box()
        print(f"  ID text bbox: {bbox}")
        
        # Naik 3 level parent untuk cari container card
        for level in range(1, 5):
            selector = ".. " * level
            try:
                parent = id_el
                for _ in range(level):
                    parent = parent.locator("..")
                ptag = await parent.evaluate("el => el.tagName")
                pcls = await parent.get_attribute("class") or ""
                pbbox = await parent.bounding_box()
                print(f"  Level +{level}: <{ptag}> class='{pcls[:60]}' bbox={pbbox}")
            except Exception as e:
                print(f"  Level +{level}: error {e}")

        # Coba klik parent level 2
        print("\n\n=== Test Klik Parent Level 2 ===")
        parent2 = id_el.locator("../..") 
        p2cls = await parent2.get_attribute("class") or ""
        p2bbox = await parent2.bounding_box()
        print(f"  Parent2: class='{p2cls}' bbox={p2bbox}")
        print(f"  Klik...")
        await parent2.click()
        await asyncio.sleep(5)
        print(f"  URL setelah klik: {page.url}")
        
        await browser.close()

asyncio.run(debug())
