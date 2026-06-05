import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            viewport={'width': 430, 'height': 932},
            is_mobile=True,
            has_touch=True
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)
        inputs = page.locator("input")
        await inputs.nth(0).fill("cjjrcmun@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        await page.locator('.dlbutton', has_text="Login").click()
        
        await asyncio.sleep(6)
        await page.locator("text=试用分组").first.click()
        await asyncio.sleep(5)
        await page.mouse.click(92, 222)
        
        await page.wait_for_selector("iframe", timeout=30000)
        await asyncio.sleep(5)
        
        # Dump HTML
        html = await page.content()
        with open("/workspaces/docker/au/dump.html", "w") as f:
            f.write(html)
            
        print("Mencari text 开始操作...")
        elems = await page.locator("text=开始操作").count()
        print(f"Elements outside iframe: {elems}")
        
        frame = page.frame_locator("iframe").first
        try:
            elems_in = await frame.locator("text=开始操作").count()
            print(f"Elements inside iframe: {elems_in}")
        except Exception as e:
            print(f"Iframe error: {e}")
            
        await browser.close()

asyncio.run(main())
