import asyncio
import os
import base64
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

os.environ["DISPLAY"] = ":99"

async def debug_registration_page():
    async with async_playwright() as p:
        print("Membuka browser untuk mencari tombol Send...")
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.hippocloudphone.com/index.html#/pages/login/register"
        print(f"Navigasi ke {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Tunggu sampai input muncul
        try:
            await page.wait_for_selector('input', timeout=15000)
            print("Input terdeteksi!")
        except:
            print("Timeout: Input tidak muncul.")
            await page.screenshot(path="debug_no_input.png")
            await browser.close()
            return

        # Ambil screenshot visual untuk melihat teks tombol
        await page.screenshot(path="debug_form.png")
        
        # Ambil semua elemen di sekitar input
        elements = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('*')).map(el => {
                const text = el.innerText ? el.innerText.trim() : "";
                if (text.length > 0 && text.length < 100) {
                    return {
                        tag: el.tagName,
                        text: text,
                        class: el.className,
                        rect: el.getBoundingClientRect()
                    };
                }
                return null;
            }).filter(x => x !== null && x.rect.width > 0);
        }""")
        
        print("\n--- SEMUA ELEMEN BERTEKS ---")
        for e in elements:
            print(f"[{e['tag']}] '{e['text']}' | Class: {e['class']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_registration_page())
