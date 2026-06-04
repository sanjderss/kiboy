import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def inspect_hippo():
    async with async_playwright() as p:
        # Gunakan browser asli yang sudah diinstall tadi
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to Hippo Landing Page...")
        await page.goto("https://www.hippocloudphone.com/", wait_until="networkidle")
        await asyncio.sleep(3)
        
        print(f"Current URL: {page.url}")
        
        # Cari tombol Login (登录)
        login_btn = page.get_by_text("登录").first
        if await login_btn.is_visible():
            print("Found Login button. Clicking...")
            await login_btn.click()
            await asyncio.sleep(5)
            print(f"URL after Login click: {page.url}")
            
            # Cari link Register (注册) di halaman login
            register_link = page.get_by_text("注册").first
            if await register_link.is_visible():
                print("Found Register link. Clicking...")
                await register_link.click()
                await asyncio.sleep(5)
                print(f"Final Register URL: {page.url}")
        
        await page.screenshot(path="hippo_final_v2.png")
        
        inputs = await page.query_selector_all("input")
        print(f"Found {len(inputs)} inputs:")
        for i, input_el in enumerate(inputs):
            placeholder = await input_el.get_attribute("placeholder")
            print(f"Input {i}: placeholder='{placeholder}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_hippo())
