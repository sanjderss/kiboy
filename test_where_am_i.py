import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    print("Mulai login (tanpa proxy) seperti di UI...")
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
        await page.locator("text=试用分组").first.wait_for(state="visible", timeout=60000)
        await page.locator("text=试用分组").first.click()
        
        await asyncio.sleep(5)
        print("Klik Phone Thumbnail X:92 Y:222")
        await page.mouse.click(92, 222)
        
        print("Menunggu WebRTC Iframe...")
        try:
            await page.wait_for_selector("iframe", timeout=30000)
            await asyncio.sleep(3)
            # klik play button yang tadi Y=510
            print("Klik Play di X:215 Y:510")
            await page.mouse.click(215, 510)
            await asyncio.sleep(0.5)
            await page.mouse.click(215, 510)
            
            print("Tunggu 15 detik untuk OS loading...")
            await asyncio.sleep(15)
            
            frame = page.frame_locator("iframe").first
            video = frame.locator("video").first
            if await video.is_visible(timeout=5000):
                await video.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/where_am_i_after_play.jpg", type="jpeg")
                print("Screenshot video setelah 15 detik diambil!")
            else:
                await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/where_am_i_after_play.jpg", type="jpeg")
                print("Screenshot halaman (fallback) setelah 15 detik diambil!")
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/where_am_i_after_play.jpg", type="jpeg")
            
        await browser.close()

asyncio.run(main())
