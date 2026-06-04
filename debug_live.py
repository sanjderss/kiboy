"""
Debug script - buka browser langsung, login, screenshot tiap langkah
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

EMAIL = "cjjrcmun@guerrillamail.info"
USER = "bot_cjjrcmun"
PASS = "Bot123456!"
SS_DIR = "/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch"

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required']
        )
        device_config = p.devices['iPhone 15 Pro Max'].copy()
        device_config['has_touch'] = False
        device_config['is_mobile'] = False
        device_config['ignore_https_errors'] = True
        context = await browser.new_context(**device_config)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        print("1. Buka halaman login...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(4)
        await page.screenshot(path=f"{SS_DIR}/dbg_01_login.png")
        print("   SS: dbg_01_login.png")

        print("2. Isi form login...")
        inputs = page.locator("input")
        await inputs.nth(0).fill(EMAIL)
        await inputs.nth(1).fill(PASS)
        await asyncio.sleep(1)
        await page.screenshot(path=f"{SS_DIR}/dbg_02_form_filled.png")
        print("   SS: dbg_02_form_filled.png")

        print("3. Klik Login...")
        login_btn = page.locator('.dlbutton', has_text="Login")
        await login_btn.click(timeout=10000)
        await asyncio.sleep(6)
        await page.screenshot(path=f"{SS_DIR}/dbg_03_after_login.png")
        print(f"   SS: dbg_03_after_login.png | URL: {page.url}")

        print("4. Cari Grup Trial...")
        group_element = page.locator("text=试用分组").first
        if await group_element.is_visible(timeout=60000):
            print("   FOUND group!")
            await page.screenshot(path=f"{SS_DIR}/dbg_04_before_group_click.png")
            print("   SS: dbg_04_before_group_click.png")
            await group_element.click()
            await asyncio.sleep(5)
            await page.screenshot(path=f"{SS_DIR}/dbg_05_after_group_click.png")
            print("   SS: dbg_05_after_group_click.png")

            print("5. Tunggu 10 detik (loading phone list)...")
            await asyncio.sleep(10)
            await page.screenshot(path=f"{SS_DIR}/dbg_06_after_10s_wait.png")
            print("   SS: dbg_06_after_10s_wait.png  <-- INI KONDISI SAAT BOT KLIK")

            print("6. Klik koordinat X:185, Y:350...")
            await page.mouse.click(185, 350)
            await asyncio.sleep(8)
            await page.screenshot(path=f"{SS_DIR}/dbg_07_after_phone_click.png")
            print(f"   SS: dbg_07_after_phone_click.png | URL: {page.url}")

            print("7. Tunggu WebRTC + spam klik...")
            for i in range(5):
                await page.mouse.click(215, 400)
                await asyncio.sleep(1)
                await page.screenshot(path=f"{SS_DIR}/dbg_08_spam_{i}.png")
                print(f"   SS: dbg_08_spam_{i}.png")
        else:
            print("   Group NOT found!")
            await page.screenshot(path=f"{SS_DIR}/dbg_04_no_group.png")

        await browser.close()
        print("DONE!")

asyncio.run(debug())
