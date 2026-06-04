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
        
        print("Membuka halaman login...")
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = page.locator("input")
        print("Mengisi email dan password...")
        await inputs.nth(0).fill("sfgymqby@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        
        print("Menekan tombol Login...")
        await page.locator(".dlbutton", has_text="Login").click()
        await asyncio.sleep(10)
        
        print("Mencari grup '试用分组'...")
        group_element = page.locator("text=试用分组").first
        if await group_element.is_visible():
            print("Grup ditemukan! Mengklik grup...")
            await group_element.click()
            await asyncio.sleep(8)
            
            print("Mencari device/phone di dalam grup...")
            phone_element = page.locator(".item-icon").first
            if await phone_element.is_visible():
                print("Phone ditemukan! Mengklik phone tersebut...")
                await phone_element.click()
                await asyncio.sleep(8)
                
                print("\n--- BODY TEXT SETELAH KLIK PHONE ---")
                body_text = await page.evaluate("() => document.body.innerText")
                print(body_text)
                
                print("\nURL setelah klik phone:", page.url)
            else:
                print("Tidak dapat menemukan elemen phone di dalam grup.")
        else:
            print("Grup '试用分组' tidak ditemukan.")
            
        await browser.close()

asyncio.run(main())
