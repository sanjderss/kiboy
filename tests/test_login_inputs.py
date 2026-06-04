import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Test input visibility
        inputs = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map((el, i) => { const rect = el.getBoundingClientRect(); return {idx: i, type: el.type, isVisible: rect.width > 0 && rect.height > 0} })")
        print("Login inputs visibility:", inputs)
        
        await browser.close()

asyncio.run(main())
