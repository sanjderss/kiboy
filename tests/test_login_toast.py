import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            proxy={"server": "http://127.0.0.1:8118"}
        )
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = page.locator("input")
        await inputs.nth(0).fill("bot_2ywxxm39")
        await inputs.nth(1).fill("Bot123456!")
        await page.locator(".dlbutton", has_text="Login").click()
        
        for _ in range(10):
            await asyncio.sleep(0.5)
            # Find toast/alert messages
            msgs = await page.evaluate("() => Array.from(document.querySelectorAll('.uni-toast, .uni-sample-toast, [class*=\"toast\"]')).map(el => el.innerText)")
            if msgs:
                print("Toasts:", msgs)
        
        await browser.close()

asyncio.run(main())
