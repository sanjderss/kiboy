import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Log all requests
        page.on("request", lambda request: print(">>", request.method, request.url))
        
        print("Navigating...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register")
        await page.wait_for_timeout(5000)
        
        print("Done")
        await browser.close()

asyncio.run(run())
