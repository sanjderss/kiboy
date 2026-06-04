import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        print("Navigating with mobile emulation...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        print("URL:", page.url)
        inputs = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map(el => ({placeholder: el.placeholder, type: el.type}))")
        print("Inputs:", inputs)
        
        body_text = await page.evaluate("() => document.body.innerText")
        print("Body Text excerpt:", body_text[:500])
        
        await browser.close()

asyncio.run(main())
