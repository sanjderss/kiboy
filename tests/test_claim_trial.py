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
        # Using the user's successfully registered email
        await inputs.nth(0).fill("sfgymqby@guerrillamail.info")
        await inputs.nth(1).fill("Bot123456!")
        
        print("Menekan tombol Login...")
        await page.locator(".dlbutton", has_text="Login").click()
        await asyncio.sleep(10)
        
        current_url = page.url
        print(f"URL setelah login: {current_url}")
        
        # Mengekstrak semua teks di body
        body_text = await page.evaluate("() => document.body.innerText")
        print("\n--- BODY TEXT ---")
        print(body_text)
        print("-----------------\n")
        
        # Mengambil daftar elemen untuk mencari tombol yang mungkin mengklaim trial
        elements = await page.evaluate("""() => {
            const arr = Array.from(document.querySelectorAll('*'));
            return arr.filter(el => {
                if (!el.innerText) return false;
                const txt = el.innerText.trim();
                // Cari teks pendek yang mengandung huruf Mandarin atau kata 'Free', 'Trial', 'Claim'
                return txt.length > 0 && txt.length < 50;
            }).map(el => ({tag: el.tagName, text: el.innerText.trim().replace(/\\n/g, ' '), class: el.className}));
        }""")
        
        print("Daftar elemen potensial di halaman dashboard:")
        for el in elements[-30:]:  # Print 30 terakhir biar gak spam
            print(el)
            
        await browser.close()

asyncio.run(main())
