import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.hippocloudphone.com/")
        await asyncio.sleep(2)
        
        print("Clicking Login...")
        login_btn = page.locator("text=登录").first
        
        try:
            async with context.expect_page(timeout=5000) as new_page_info:
                await login_btn.click()
            new_page = await new_page_info.value
            await new_page.wait_for_load_state("domcontentloaded")
            print(f"New page URL: {new_page.url}")
        except Exception as e:
            print(f"No new page opened. Error: {e}")
            print(f"Current URL: {page.url}")
            
        await browser.close()

asyncio.run(main())
