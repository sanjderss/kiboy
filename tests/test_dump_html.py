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
            
            elements = page.locator("uni-image, img")
            count = await elements.count()
            for i in range(count):
                el = elements.nth(i)
                box = await el.bounding_box()
                if box and box['width'] > 50 and box['height'] > 100:
                    await el.click(timeout=5000)
                    print("Masuk ke layar Phone...")
                    await asyncio.sleep(10)
                    
                    # Print all elements in the DOM
                    print("--- HTML DUMP OF THE PAGE ---")
                    html = await page.evaluate("document.body.innerHTML")
                    with open("/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/page_dump.html", "w") as f:
                        f.write(html)
                    print("HTML saved to page_dump.html")
                    break
                    
        await browser.close()

asyncio.run(main())
