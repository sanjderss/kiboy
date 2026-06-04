import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        await page.goto("https://www.hippocloudphone.com/")
        await asyncio.sleep(2)
        links = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText, href: a.href}))")
        for l in links:
            print(f"{l['text']} -> {l['href']}")
        await browser.close()
asyncio.run(main())
