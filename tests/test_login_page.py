import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        # URL login (biasanya hapus /register di akhir)
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map(el => ({placeholder: el.placeholder, type: el.type}))")
        print("Login Inputs:", inputs)
        
        body_text = await page.evaluate("() => document.body.innerText")
        print("Login Body Text excerpt:", body_text[:500])
        
        await browser.close()

asyncio.run(main())
