import os
import asyncio
import base64
import subprocess
import re
import uvicorn
import json
import pytesseract
from PIL import Image, ImageDraw
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Setup Environment untuk Xvfb (Virtual Display)
DISPLAY_NUM = 99
os.environ["DISPLAY"] = f":{DISPLAY_NUM}"

def start_xvfb():
    """Menjalankan Xvfb di background."""
    print(f"Starting Xvfb on display :{DISPLAY_NUM}...")
    subprocess.Popen([
        "Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1280x720x24"
    ])
    # Beri waktu Xvfb untuk start
    import time
    time.sleep(2)

app = FastAPI()

# HTML Dasar untuk Dashboard Pemantauan
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Zero-Cost Bot Panel</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        #live-container { background: #1e293b; border-radius: 12px; padding: 15px; border: 1px solid #334155; }
        #live-view { width: 100%; border-radius: 8px; background: #000; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
        .controls { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        button { width: 100%; padding: 12px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin-bottom: 10px; }
        button:hover { background: #2563eb; }
        #logs { height: 300px; overflow-y: auto; background: #020617; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #10b981; border: 1px solid #1e293b; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; background: #334155; font-size: 12px; margin-bottom: 10px; }
        .online { background: #059669; }
    </style>
</head>
<body>
    <h1>🚀 Zero-Cost Bot Dashboard</h1>
    <div class="grid">
        <div id="live-container">
            <div class="status-badge" id="bot-status">Status: Idle</div>
            <img id="live-view" src="" alt="Menunggu stream visual...">
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                <h4 style="margin: 0 0 10px 0; color: #f59e0b;">🔍 AI Vision Debug (Titik Klik)</h4>
                <img id="debug-view" src="" alt="Belum ada aksi klik..." style="width: 100%; border-radius: 8px; border: 2px dashed #f59e0b;">
            </div>
        </div>
        <div class="controls">
            <h3>Bot Control</h3>
            <button onclick="startBot()">Jalankan Bot (Test Hippo)</button>
            <button onclick="stopBot()" style="background: #ef4444;">Hentikan Paksa</button>
            
            <h3 style="margin-top: 20px; border-top: 1px solid #334155; padding-top: 20px;">Login Debug (Tanpa Proxy)</h3>
            <select id="account-select" style="width: 100%; padding: 10px; margin-bottom: 10px; background: #020617; color: white; border: 1px solid #334155; border-radius: 8px;">
                <option value="">Memuat akun...</option>
            </select>
            <button onclick="startLoginBot()" style="background: #10b981;">Login dengan Akun Terpilih</button>
            
            <h3>Aktivitas Log</h3>
            <div id="logs"></div>
        </div>
    </div>

    <script>
        let ws;
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            console.log("Connecting to:", wsUrl);
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log("Connected!");
                const logs = document.getElementById('logs');
                logs.innerHTML += '<div>[System] Connected to Server</div>';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'image') {
                    document.getElementById('live-view').src = 'data:image/jpeg;base64,' + data.content;
                } else if (data.type === 'debug_image') {
                    document.getElementById('debug-view').src = 'data:image/jpeg;base64,' + data.content;
                } else if (data.type === 'log') {
                    const logs = document.getElementById('logs');
                    const entry = document.createElement('div');
                    entry.textContent = `[${new Date().toLocaleTimeString()}] ${data.content}`;
                    logs.appendChild(entry);
                    logs.scrollTop = logs.scrollHeight;
                } else if (data.type === 'status') {
                    document.getElementById('bot-status').innerText = 'Status: ' + data.content;
                    if(data.content === 'Running') document.getElementById('bot-status').classList.add('online');
                    else document.getElementById('bot-status').classList.remove('online');
                }
            };
            ws.onerror = (e) => console.error("WS Error:", e);
            ws.onclose = () => {
                console.log("Disconnected, retrying...");
                setTimeout(connect, 2000);
            };
        }
        connect();

        function startBot() {
            if(ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'start'}));
            } else {
                alert("Koneksi belum siap, silakan tunggu atau refresh.");
            }
        }

        function startLoginBot() {
            const select = document.getElementById('account-select');
            const val = select.value;
            if(!val) return alert("Pilih akun terlebih dahulu!");
            if(ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'start_login', account: val}));
            }
        }

        function stopBot() {
            if(ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'stop'}));
            }
        }
        
        // Load accounts on load
        fetch('/accounts')
            .then(r => r.json())
            .then(data => {
                const select = document.getElementById('account-select');
                select.innerHTML = '<option value="">-- Pilih Akun --</option>';
                data.forEach(acc => {
                    const opt = document.createElement('option');
                    opt.value = acc.raw;
                    opt.textContent = acc.display;
                    select.appendChild(opt);
                });
            })
            .catch(e => console.error(e));
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML_TEMPLATE)

@app.get("/accounts")
async def get_accounts():
    import os
    if not os.path.exists("data/accounts.txt"):
        return []
    accs = []
    with open("data/accounts.txt", "r") as f:
        for line in f:
            if "|" in line:
                parts = line.strip().split("|")
                display = " ".join([p.strip() for p in parts[:2]])
                accs.append({"raw": line.strip(), "display": display})
    return accs[::-1] # Reverse to show newest first

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"DEBUG: New WS Connection from {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            print(f"DEBUG: Received message: {data}")
            if data.get("action") == "start":
                start_task(run_bot_task(websocket, mode="register"))
            elif data.get("action") == "start_login":
                account_raw = data.get("account", "")
                if account_raw:
                    start_task(run_bot_task(websocket, mode="login", account_data=account_raw))
            elif data.get("action") == "stop":
                from config_kill import emergency_stop
                await stop_task(websocket)
                await emergency_stop(websocket)
    except WebSocketDisconnect:
        print("DEBUG: WS Disconnected")

from app.bot_engine import run_bot_task
from app.task_manager import start_task, stop_task

if __name__ == "__main__":
    start_xvfb()
    uvicorn.run(app, host="0.0.0.0", port=8000)
