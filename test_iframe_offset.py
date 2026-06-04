import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        device = p.devices['iPhone 15 Pro Max'].copy()
        device['has_touch'] = False
        device['is_mobile'] = False
        context = await browser.new_context(**device)
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login")
        await asyncio.sleep(2)
        await page.locator("input").nth(0).fill("erijldjp@guerrillamail.info")
        await page.locator("input").nth(1).fill("Bot123456!")
        await page.locator('.dlbutton').click()
        await asyncio.sleep(4)
        
        await page.locator("text=试用分组").first.click()
        await asyncio.sleep(4)
        
        els = page.locator("uni-image, img")
        for i in range(await els.count()):
            b = await els.nth(i).bounding_box()
            if b and b['width'] > 50 and b['height'] > 100:
                await els.nth(i).click()
                break
                
        await asyncio.sleep(5)
        
        iframe_box = await page.locator("iframe").bounding_box()
        print("IFRAME BOUNDING BOX:", iframe_box)
        await browser.close()

asyncio.run(run())
