import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Gunakan DISPLAY yang sudah ada
os.environ["DISPLAY"] = ":99"

async def deep_inspect():
    async with async_playwright() as p:
        print("Membuka browser untuk inspeksi mendalam...")
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.hippocloudphone.com/index.html#/pages/login/register"
        print(f"Navigasi ke {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(5) # Tunggu render JS
        
        # 1. Ambil semua elemen Button/Div yang bisa diklik
        buttons = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('button, div, span, a').forEach(el => {
                const text = el.innerText ? el.innerText.trim() : "";
                if (text.length > 0 && text.length < 50) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            class: el.className,
                            id: el.id
                        });
                    }
                }
            });
            return results;
        }""")
        
        print("\\n--- DAFTAR ELEMEN CLICKABLE ---")
        for b in buttons:
            print(f"[{b['tag']}] '{b['text']}' | Class: {b['class']} | ID: {b['id']}")
            
        # 2. Ambil semua Input
        inputs = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(el => ({
                placeholder: el.placeholder,
                type: el.type,
                name: el.name,
                class: el.className
            }));
        }""")
        
        print("\\n--- DAFTAR INPUT ---")
        for i in inputs:
            print(f"Input: placeholder='{i['placeholder']}' | Type: {i['type']} | Name: {i['name']}")
            
        await page.screenshot(path="debug_deep.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(deep_inspect())
