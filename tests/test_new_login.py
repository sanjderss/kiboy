import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        await page.goto("https://www.hippocloudphone.com/login!index", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        print("Clicking Register...")
        await page.get_by_text("注册领免费试用").click()
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        
        print("URL after clicking register:", page.url)
        inputs = await page.evaluate("() => Array.from(document.querySelectorAll('input')).map(el => ({placeholder: el.placeholder, type: el.type, id: el.id, name: el.name}))")
        print("Inputs on register page:", inputs)
        
        await browser.close()

asyncio.run(main())
