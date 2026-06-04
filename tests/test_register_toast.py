import asyncio
from playwright.async_api import async_playwright
import re
from app.mail_handler import get_free_email, wait_for_otp

async def main():
    email_obj = get_free_email()
    email_addr = email_obj.address
    print(f"Using email: {email_addr}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            proxy={"server": "http://127.0.0.1:8118"}
        )
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        inputs = page.locator("input")
        await inputs.nth(0).fill(email_addr)
        
        username = f"bot_{email_addr.split('@')[0][:8]}"
        await inputs.nth(2).fill(username)
        password = "Bot123456!"
        await inputs.nth(3).fill(password)
        await inputs.nth(4).fill(password)
        
        print("Clicking Send OTP...")
        await page.locator('text="发送"').first.click()
        
        print("Waiting for OTP...")
        otp_code = None
        for i in range(15):
            otp_code = await asyncio.to_thread(wait_for_otp, email_obj, 5)
            if otp_code:
                break
            await asyncio.sleep(1)
            
        if not otp_code:
            print("Failed to get OTP")
            return
            
        print("OTP Received:", otp_code)
        await inputs.nth(1).fill(otp_code)
        
        checkbox = page.locator('.cuIcon-round').first
        if await checkbox.is_visible():
            await checkbox.click()
            
        print("Clicking Sign up...")
        await page.locator('.dlbutton', has_text="Sign up").click()
        
        print("Listening for toasts for 10 seconds...")
        for _ in range(20):
            await asyncio.sleep(0.5)
            msgs = await page.evaluate("() => Array.from(document.querySelectorAll('.uni-toast, .uni-sample-toast, [class*=\"toast\"]')).map(el => el.innerText)")
            if msgs:
                print("Toasts:", msgs)
                
        print("Final URL:", page.url)
        await browser.close()

asyncio.run(main())
