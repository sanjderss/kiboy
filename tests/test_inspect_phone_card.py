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
        
        print("Membuka halaman login...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = page.locator("input")
        await inputs.nth(0).fill("sfgymqby@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        
        await page.locator(".dlbutton", has_text="Login").click()
        await asyncio.sleep(10)
        
        group_element = page.locator("text=试用分组").first
        if await group_element.is_visible():
            await group_element.click()
            await asyncio.sleep(8)
            
            # Print all elements that might be the preview screen
            print("--- HTML KARTU DEVICE ---")
            card_html = await page.evaluate("""() => {
                const cards = document.querySelectorAll('.item-icon, .new-phone, .ip, .card-down, .dev-list');
                let result = '';
                cards.forEach(c => {
                    result += c.outerHTML + '\\n\\n';
                });
                return result;
            }""")
            print(card_html)
            
        await browser.close()

asyncio.run(main())
