import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--autoplay-policy=no-user-gesture-required'
            ],
        )
        device_config = p.devices['iPhone 15 Pro Max'].copy()
        device_config['has_touch'] = False
        device_config['is_mobile'] = False
        context = await browser.new_context(**device_config)
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
                    print("Mengeklik tombol Start (pusat layar) untuk masuk ke Android...")
                    frame = page.frame_locator("iframe").first
                    await frame.locator("body").click(position={"x": 215, "y": 400}, force=True)
                    
                    print("Menunggu Android OS memuat penuh (15 detik)...")
                    await asyncio.sleep(15)
                    
                    print("Mengeklik ikon App Store di koordinat x=71, y=380 menggunakan mouse.click()...")
                    
                    frame_element = await page.locator("iframe").first.bounding_box()
                    offset_x = frame_element['x'] if frame_element else 0
                    offset_y = frame_element['y'] if frame_element else 0
                    
                    target_x = offset_x + 71
                    target_y = offset_y + 380
                    
                    await page.mouse.click(target_x, target_y)
                    
                    print("Menunggu App Store terbuka...")
                    await asyncio.sleep(10)
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/appstore.png")
                    print("Klik tab CommonApps di koordinat x=178, y=50...")
                    target_common_x = offset_x + 178
                    target_common_y = offset_y + 50
                    
                    await page.mouse.click(target_common_x, target_common_y)
                    print("Menunggu tab CommonApps termuat...")
                    await asyncio.sleep(5)
                    
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/commonapps.png")
                    print("Screenshot CommonApps diambil!")
                    
                    print("Mengeklik tombol Install Chrome di koordinat x=78, y=457...")
                    target_chrome_x = offset_x + 78
                    target_chrome_y = offset_y + 457
                    await page.mouse.click(target_chrome_x, target_chrome_y)
                    
                    print("Menunggu proses instalasi dimulai...")
                    await asyncio.sleep(8)
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/chrome_installing.png")
                    print("Screenshot proses instalasi Chrome diambil!")
                    
                    print("Menunggu instalasi selesai (30 detik)...")
                    await asyncio.sleep(30)
                    
                    print("Mengeklik tombol INSTALL di Android OS (x=362, y=668)...")
                    target_os_install_x = offset_x + 362
                    target_os_install_y = offset_y + 668
                    await page.mouse.click(target_os_install_x, target_os_install_y)
                    
                    print("Menunggu proses instalasi OS selesai (20 detik)...")
                    await asyncio.sleep(20)
                    print("Mengeklik tombol OPEN di Android OS (x=369, y=668)...")
                    target_os_open_x = offset_x + 369
                    target_os_open_y = offset_y + 668
                    await page.mouse.click(target_os_open_x, target_os_open_y)
                    
                    print("Menunggu Chrome terbuka (15 detik)...")
                    await asyncio.sleep(15)
                    print("Mengeklik tombol Done di Chrome (x=300, y=596)...")
                    target_chrome_done_x = offset_x + 300
                    target_chrome_done_y = offset_y + 596
                    await page.mouse.click(target_chrome_done_x, target_chrome_done_y)
                    
                    print("Menunggu layar berikutnya (5 detik)...")
                    await asyncio.sleep(5)
                    print("Mengeklik tombol More di Chrome (x=300, y=640)...")
                    target_chrome_more_x = offset_x + 300
                    target_chrome_more_y = offset_y + 640
                    await page.mouse.click(target_chrome_more_x, target_chrome_more_y)
                    
                    print("Menunggu (5 detik)...")
                    await asyncio.sleep(5)
                    await page.screenshot(path="/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/chrome_final.png")
                    print("Screenshot Chrome final diambil!")
                    
                    break
                    
        await browser.close()

asyncio.run(main())
