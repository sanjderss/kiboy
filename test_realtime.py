import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time

async def test():
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
        
        print("[*] Buka Login...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)
        inputs = page.locator("input")
        await inputs.nth(0).fill("cjjrcmun@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        await page.locator('.dlbutton', has_text="Login").click()
        
        print("[*] Tunggu Grup...")
        await asyncio.sleep(6)
        await page.locator("text=试用分组").first.wait_for(state="visible", timeout=60000)
        await page.locator("text=试用分组").first.click()
        
        print("[*] Masuk halaman Phone, tunggu thumbnail...")
        await asyncio.sleep(5)
        # Koordinat thumbnail (X:92, Y:222)
        await page.mouse.click(92, 222)
        print("[*] Phone Thumbnail diklik!")
        
        # REALTIME POLLING IFRAME & WEBRTC
        print("[*] Mulai Realtime Polling Screen...")
        for i in range(30):
            try:
                frame = page.frame_locator("iframe").first
                video = frame.locator("video").first
                if await video.is_visible(timeout=1000):
                    print(f"[{i}] VIDEO TAG MUNCUL! Coba screenshot...")
                    await video.screenshot(path=f"/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/rt_webrtc_{i}.jpg", type="jpeg")
                    # Klik play button (blind click di tengah)
                    await page.mouse.click(215, 400)
                else:
                    print(f"[{i}] Screenshot fallback...")
                    await page.screenshot(path=f"/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/rt_page_{i}.jpg", type="jpeg")
            except Exception as e:
                print(f"[{i}] Error: {e}")
            await asyncio.sleep(1)
        
        await browser.close()

asyncio.run(test())
