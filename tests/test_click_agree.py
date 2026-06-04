import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Click the agreeContent
        print("Clicking agreeContent...")
        agree = page.locator(".agreeContent").first
        await agree.click()
        await asyncio.sleep(1)
        
        # Check what changed in its parent
        html = await agree.evaluate("el => el.parentElement.outerHTML")
        print("Parent HTML after clicking agreeContent:")
        print(html)
        
        await browser.close()

asyncio.run(main())
