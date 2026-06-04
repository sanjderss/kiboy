import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        print("Navigating to register page...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Check elements with text 'I have read'
        locators = page.locator("text=I have read")
        count = await locators.count()
        print(f"Found {count} elements with 'I have read'")
        
        for i in range(count):
            el = locators.nth(i)
            print(f"Element {i}: Tag={await el.evaluate('el => el.tagName')}, Class={await el.evaluate('el => el.className')}")
            
        # Try to find checkboxes/radios
        radios = await page.evaluate("() => { return Array.from(document.querySelectorAll('.radio, .checkbox, [type=checkbox], [type=radio], uni-radio, uni-checkbox')).map(e => e.className + ' | ' + e.tagName); }")
        print("Radios/Checkboxes found:", radios)
        
        await browser.close()

asyncio.run(main())
