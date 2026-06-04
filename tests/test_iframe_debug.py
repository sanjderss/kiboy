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
                    
                    frame = page.frame_locator("iframe").first
                    
                    print("Mengambil screenshot SEBELUM klik iframe...")
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/iframe_before.png")
                    
                    print("--- DUMP HTML IFRAME ---")
                    try:
                        html = await frame.locator("body").evaluate("el => el.innerHTML")
                        with open("/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/iframe_dump.html", "w") as f:
                            f.write(html)
                        print("Iframe HTML saved.")
                    except Exception as e:
                        print("Gagal dump iframe HTML:", e)
                        
                    print("Mencoba klik tombol mulai di iframe...")
                    try:
                        btn = frame.locator("text=开始操作").first
                        if await btn.is_visible(timeout=5000):
                            await btn.click(force=True)
                            print("Tombol 开始操作 berhasil diklik!")
                        else:
                            print("Teks 开始操作 tidak ditemukan. Mengeklik area tengah iframe...")
                            await frame.locator("body").click(position={"x": 215, "y": 350}, force=True)
                    except Exception as e:
                        print("Error klik iframe:", e)
                        
                    await asyncio.sleep(15)
                    print("Mengambil screenshot SETELAH klik iframe dan menunggu...")
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/iframe_after.png")
                    
                    break
                    
        await browser.close()

asyncio.run(main())
