import sys
import os
# Fix PYTHONPATH agar 'from app.xxx import' bisa ditemukan
sys.path.insert(0, "/workspaces/docker/au")

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
# playwright_stealth diimport lazy saat dibutuhkan saja

# Setup Environment untuk Xvfb (Virtual Display)
DISPLAY_NUM = 99
os.environ["DISPLAY"] = f":{DISPLAY_NUM}"

def start_xvfb():
    """Menjalankan Xvfb di background."""
    print(f"Starting Xvfb on display :{DISPLAY_NUM}...")
    import subprocess
    subprocess.Popen([
        "Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "1280x720x24"
    ])

app = FastAPI()

# ============================================================
# WEBSOCKET CONNECTIONS MANAGEMENT
# ============================================================
# Daftar semua WebSocket client (dashboard utama + debug)

from app.shared_ws import debug_clients, dashboard_clients

async def broadcast_to_all(data):
    """Kirim data ke semua client (dashboard + debug)."""
    dead = set()
    for ws in dashboard_clients | debug_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    dashboard_clients.discard(*dead) if dead else None
    debug_clients.discard(*dead) if dead else None

async def broadcast_to_debug(data):
    """Kirim data khusus ke debug clients saja."""
    dead = set()
    for ws in debug_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    debug_clients -= dead


# ============================================================
# HTML Dashboard Utama (Sama seperti sebelumnya, + link ke /debug)
# ============================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Zero-Cost Bot Panel</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .topbar h1 { margin: 0; }
        .topbar a { color: #06b6d4; text-decoration: none; font-weight: bold; padding: 8px 16px; border: 1px solid #06b6d4; border-radius: 8px; transition: all 0.2s; }
        .topbar a:hover { background: #06b6d4; color: #0f172a; }
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
    <div class="topbar">
        <h1>🚀 Zero-Cost Bot Dashboard</h1>
        <a href="/debug" target="_blank">🔍 Open Debug Preview</a>
    </div>
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
            
            <h3 style="margin-top: 20px; border-top: 1px solid #334155; padding-top: 20px;">Upload Image & Send Command</h3>
            <form id="upload-form" style="margin-bottom: 10px;">
                <input type="file" id="image-upload" accept="image/*" style="width: 100%; margin-bottom: 5px; color: white;">
                <button type="submit" style="background: #8b5cf6;">Upload Image</button>
            </form>
            <form id="command-form" style="margin-bottom: 10px;">
                <input type="text" id="command-input" placeholder="Type a command..." style="width: 100%; padding: 10px; margin-bottom: 5px; background: #020617; color: white; border: 1px solid #334155; border-radius: 8px; box-sizing: border-box;">
                <button type="submit" style="background: #8b5cf6;">Send Command</button>
            </form>
            
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

        document.getElementById('upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('image-upload');
            if (fileInput.files.length === 0) return;
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            await fetch('/upload', { method: 'POST', body: formData });
            fileInput.value = '';
        });

        document.getElementById('command-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const cmdInput = document.getElementById('command-input');
            const cmd = cmdInput.value.trim();
            if (!cmd) return;
            const formData = new FormData();
            formData.append('command', cmd);
            await fetch('/command', { method: 'POST', body: formData });
            cmdInput.value = '';
        });
    </script>
</body>
</html>
"""

# ============================================================
# ROUTES
# ============================================================

@app.get("/")
async def get():
    return HTMLResponse(HTML_TEMPLATE)

@app.get("/debug")
async def get_debug():
    """Halaman Debug Preview Realtime — halaman terpisah."""
    from app.debug_dashboard import DEBUG_DASHBOARD_HTML
    return HTMLResponse(DEBUG_DASHBOARD_HTML)

@app.get("/proxy_stats")
async def get_proxy_stats():
    """Mengembalikan daftar Github repo dan API yang digunakan Proxy Hunter."""
    import sys
    sys.path.append("/workspaces/docker/au")
    try:
        from proxy_hunter import PROXY_SOURCES
        import os
        active_count = 0
        used_count = 0
        if os.path.exists("data/active_proxies.txt"):
            with open("data/active_proxies.txt", "r") as f:
                active_count = len(f.read().splitlines())
        if os.path.exists("data/used_proxies.txt"):
            with open("data/used_proxies.txt", "r") as f:
                used_count = len(f.read().splitlines())
                
        import app.shared_ws as shared_ws
        return {
            "sources": PROXY_SOURCES,
            "active_pool": active_count,
            "blacklisted": used_count,
            "current_proxy": getattr(shared_ws, "current_proxy", "Direct (Tanpa Proxy)"),
            "current_account": getattr(shared_ws, "current_account", "Tidak ada")
        }
    except Exception as e:
        return {"error": str(e)}

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

from fastapi import File, UploadFile, Form
import shutil

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    import os
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Broadcast log
    await broadcast_to_all({"type": "log", "content": f"Image uploaded by user: {file.filename}"})
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}

@app.post("/command")
async def send_command(command: str = Form(...)):
    # Broadcast command to logs
    await broadcast_to_all({"type": "log", "content": f"[USER COMMAND]: {command}"})
    return {"status": "ok", "command": command}

# ============================================================
# WebSocket: Dashboard Utama (untuk kontrol bot)
# ============================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    dashboard_clients.add(websocket)
    print(f"DEBUG: Dashboard WS Connected from {websocket.client}")
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
        print("DEBUG: Dashboard WS Disconnected")
    finally:
        dashboard_clients.discard(websocket)

# ============================================================
# WebSocket: Debug Preview (read-only, hanya menerima stream)
# ============================================================
@app.websocket("/ws/debug")
async def debug_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    debug_clients.add(websocket)
    print(f"DEBUG: Debug WS Connected from {websocket.client}")
    try:
        while True:
            # Debug client hanya menerima data, tapi kita perlu keep-alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("DEBUG: Debug WS Disconnected")
    finally:
        debug_clients.discard(websocket)

from app.bot_engine import run_bot_task
from app.task_manager import start_task, stop_task

if __name__ == "__main__":
    start_xvfb()
    uvicorn.run(app, host="0.0.0.0", port=8000)
