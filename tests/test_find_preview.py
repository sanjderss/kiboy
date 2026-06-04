import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
        )
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = page.locator("input")
        await inputs.nth(0).fill("sfgymqby@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        await page.locator(".dlbutton", has_text="Login").click()
        await asyncio.sleep(10)
        
        group = page.locator("text=试用分组").first
        if await group.is_visible():
            await group.click()
            await asyncio.sleep(8)
            
            # Cari dan dump seluruh container dari device
            print("--- HTML KESELURUHAN DEVICE LIST ---")
            html = await page.evaluate("""() => {
                const el = document.querySelector('.dev-list') || document.body;
                return el.innerHTML.substring(0, 5000); // Batasi 5000 karakter
            }""")
            print(html)
        await browser.close()

asyncio.run(main())
