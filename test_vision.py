import asyncio
from playwright.async_api import async_playwright
import time

ARTIFACT_DIR = "/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required'])
        device = p.devices['iPhone 15 Pro Max'].copy()
        device['has_touch'] = False
        device['is_mobile'] = False
        context = await browser.new_context(**device)
        page = await context.new_page()
        
        print("Login...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login")
        await asyncio.sleep(3)
        await page.locator("input").nth(0).fill("erijldjp@guerrillamail.info")
        await page.locator("input").nth(1).fill("Bot123456!")
        await page.locator('.dlbutton').click()
        await asyncio.sleep(5)
        
        print("Masuk grup...")
        await page.locator("text=试用分组").first.click()
        await asyncio.sleep(5)
        
        print("Klik phone...")
        els = page.locator("uni-image, img")
        for i in range(await els.count()):
            b = await els.nth(i).bounding_box()
            if b and b['width'] > 50 and b['height'] > 100:
                await els.nth(i).click()
                break
                
        await asyncio.sleep(10)
        
        print("Masuk iframe...")
        frame = page.frame_locator("iframe").first
        await frame.locator("body").click(position={"x":215, "y":400}, force=True)
        print("Menunggu OS 15 detik...")
        await asyncio.sleep(15)
        
        # Take home screenshot
        await page.screenshot(path=f"{ARTIFACT_DIR}/hc_01_home.jpg", type="jpeg")
        
        # Click App Store (Hardcoded X=67, Y=385)
        print("Klik App Store (67, 385)...")
        await page.mouse.click(67, 385, delay=150)
        await asyncio.sleep(8) # Wait for App Store to load
        
        await page.screenshot(path=f"{ARTIFACT_DIR}/hc_02_appstore.jpg", type="jpeg")
        
        # The Common tab is usually at the top right-ish. Let's capture it and find it!
        # First, I will let the script finish here so I can analyze the screenshot.
        await browser.close()
        print("Done!")

asyncio.run(run())
