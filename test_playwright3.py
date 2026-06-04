import asyncio
from playwright.async_api import async_playwright

async def run():
    print("Membuka Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={
                "server": "http://proxy-server.scraperapi.com:8001",
                "username": "scraperapi",
                "password": "9b3fc835287bac35372791642377e6a0"
            }
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        async def intercept_route(route):
            if route.request.resource_type in ["image", "media", "font"]:
                await route.abort()
            else:
                await route.continue_()
                
        await page.route("**/*", intercept_route)
        
        print("Navigasi ke Hippo Cloud...")
        try:
            await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="load", timeout=90000)
            print("Berhasil! URL:", page.url)
            print("Title:", await page.title())
            await page.screenshot(path="test_playwright3.png")
            inputs = page.locator("input")
            await inputs.nth(0).wait_for(state="visible", timeout=30000)
            print("Form Input Ditemukan!")
        except Exception as e:
            print("Error:", str(e))
            await page.screenshot(path="test_playwright3_err.png")
        finally:
            await browser.close()

asyncio.run(run())
