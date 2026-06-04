import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Check login button
        btns = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, .dlbutton, .btn, [class*="btn"], [class*="button"]')).map(el => {
                return {tag: el.tagName, text: el.innerText, class: el.className}
            });
        }""")
        print("Login Buttons:", btns)
        
        await browser.close()

asyncio.run(main())
