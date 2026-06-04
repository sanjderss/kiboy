from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import base64

app = FastAPI()

# HTML Dasar untuk Panel Monitoring
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Playwright AU Panel</title>
        <style>
            body { font-family: sans-serif; background: #1a1a1a; color: white; margin: 20px; }
            .container { display: flex; flex-direction: column; align-items: center; }
            #live-view { border: 2px solid #333; max-width: 400px; background: #000; }
            .status { margin: 10px; padding: 10px; background: #333; border-radius: 5px; width: 400px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AU Automation Panel</h1>
            <div class="status">Status: <span id="status">Idle</span></div>
            <button onclick="startAutomation()">Start Hippo Reg</button>
            <br>
            <img id="live-view" src="" alt="Live View akan muncul di sini...">
            <div id="logs" style="margin-top: 10px; width: 400px; height: 150px; overflow-y: auto; background: #000; padding: 5px; font-size: 12px; color: #0f0;"></div>
        </div>
        <script>
            let ws = new WebSocket(`ws://${window.location.host}/ws`);
            ws.onmessage = function(event) {
                let data = JSON.parse(event.data);
                if (data.type === 'image') {
                    document.getElementById('live-view').src = 'data:image/jpeg;base64,' + data.content;
                } else if (data.type === 'log') {
                    let logs = document.getElementById('logs');
                    logs.innerHTML += '<div>' + data.content + '</div>';
                    logs.scrollTop = logs.scrollHeight;
                } else if (data.type === 'status') {
                    document.getElementById('status').innerText = data.content;
                }
            };
            function startAutomation() {
                ws.send("start");
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if data == "start":
            await run_automation(websocket)

async def run_automation(websocket):
    async with async_playwright() as p:
        await websocket.send_json({"type": "status", "content": "Initializing..."})
        browser = await p.chromium.launch(headless=True) # Headless karena kita streaming screenshot
        context = await browser.new_context(**p.devices['iPhone 15 Pro Max'])
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        await websocket.send_json({"type": "status", "content": "Navigating to Hippo..."})
        await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded")
        
        # Loop Streaming
        try:
            for _ in range(100): # Simulasi monitoring selama beberapa waktu
                screenshot = await page.screenshot(type="jpeg", quality=50)
                b64_img = base64.b64encode(screenshot).decode('utf-8')
                await websocket.send_json({"type": "image", "content": b64_img})
                
                # Update Log
                url = page.url
                await websocket.send_json({"type": "log", "content": f"Current URL: {url}"})
                
                await asyncio.sleep(0.5)
        except Exception as e:
            await websocket.send_json({"type": "log", "content": f"Error: {str(e)}"})
        finally:
            await browser.close()
            await websocket.send_json({"type": "status", "content": "Finished"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
