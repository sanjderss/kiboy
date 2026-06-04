import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            proxy={"server": "http://127.0.0.1:8118"}
        )
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        url = "https://www.hippocloudphone.com/index.html#/pages/login/login"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        print("Filling credentials...")
        inputs = page.locator("input")
        await inputs.nth(0).fill("bot_2ywxxm39")
        await inputs.nth(1).fill("Bot123456!")
        
        print("Clicking Login...")
        await page.locator(".dlbutton", has_text="Login").click()
        
        print("Waiting 5 seconds to see what happens...")
        await asyncio.sleep(5)
        
        # Check if there's any modal, captcha or new elements
        body_text = await page.evaluate("() => document.body.innerText")
        print("Body Text after login attempt:")
        print(body_text)
        
        # Look for specific elements like slider captcha
        elements = await page.evaluate("""() => {
            const arr = Array.from(document.querySelectorAll('*'));
            return arr.filter(el => {
                if (!el.innerText) return false;
                const txt = el.innerText;
                // Look for Chinese keywords related to captcha or errors
                return txt.includes('向右') || txt.includes('滑') || txt.includes('拼图') || txt.includes('验证') || txt.includes('错误');
            }).map(el => ({tag: el.tagName, text: el.innerText.trim().slice(0, 50), class: el.className}));
        }""")
        print("Suspicious elements found:", elements)
        
        # Also check current URL
        print("URL after login:", page.url)
        
        await browser.close()

asyncio.run(main())
