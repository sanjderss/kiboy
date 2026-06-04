import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        device = p.devices['iPhone 15 Pro Max'].copy()
        device['has_touch'] = True # WAIT! Mobile devices need touch!
        context = await browser.new_context(**device)
        page = await context.new_page()
        print("Scale Factor:", device.get('device_scale_factor'))
        await browser.close()
asyncio.run(run())
