import asyncio
from playwright.async_api import async_playwright
from PIL import Image
import io

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        device_config = p.devices['iPhone 15 Pro Max'].copy()
        device_config['has_touch'] = False
        context = await browser.new_context(**device_config)
        page = await context.new_page()
        
        await page.goto("https://example.com")
        
        screenshot_bytes = await page.screenshot()
        img = Image.open(io.BytesIO(screenshot_bytes))
        
        print(f"Viewport CSS Size: {device_config['viewport']}")
        print(f"Screenshot Pixel Size: {img.size}")
        print(f"Device Pixel Ratio: {device_config.get('device_scale_factor', 'Not Set')}")
        
        await browser.close()

asyncio.run(run())
