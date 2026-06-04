import asyncio
from playwright.async_api import async_playwright

async def intercept_route(route):
    # Block images, fonts, css, and media
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        await route.abort()
    else:
        await route.continue_()

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
        
        # Intercept and abort unnecessary requests
        await page.route("**/*", intercept_route)
        
        print("Navigasi ke Hippo Cloud...")
        try:
            await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded", timeout=60000)
            print("Berhasil! URL:", page.url)
            print("Title:", await page.title())
            inputs = page.locator("input")
            await inputs.nth(0).wait_for(state="visible", timeout=10000)
            print("Form Input Ditemukan!")
        except Exception as e:
            print("Error:", str(e))
        finally:
            await browser.close()

asyncio.run(run())
