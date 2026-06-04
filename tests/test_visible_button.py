import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Cari semua elemen button/div yang memiliki class 'dlbutton' atau text 'Sign up'
        # Periksa apakah mereka visible
        elements = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.dlbutton, button, [class*="button"]')).map((el, i) => {
                const rect = el.getBoundingClientRect();
                return {
                    idx: i,
                    tag: el.tagName,
                    text: el.innerText ? el.innerText.trim() : "",
                    class: el.className,
                    isVisible: rect.width > 0 && rect.height > 0
                }
            }).filter(x => (x.text.toLowerCase().includes('sign') || x.class.includes('dlbutton')));
        }""")
        
        print("Potential Sign Up Buttons:")
        for el in elements:
            print(el)
            
        await browser.close()

asyncio.run(main())
