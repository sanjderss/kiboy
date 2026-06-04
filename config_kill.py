import os
import signal
import psutil
import asyncio

async def force_kill_browser(websocket=None):
    """
    Menghentikan paksa semua proses browser Playwright atau Chrome yang menggantung (zombie processes).
    Berguna untuk opsi 'batal paksa' agar memory tidak bocor.
    """
    if websocket:
        await websocket.send_json({"type": "log", "content": "[Config-Kill] Menghentikan paksa semua instance browser..."})
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = " ".join(proc.info.get('cmdline', [])) if proc.info.get('cmdline') else ""
                
                # Matikan chrome, chromium, atau firefox bawaan playwright
                if 'chrome' in name or 'chromium' in name or 'playwright' in cmdline:
                    os.kill(proc.info['pid'], signal.SIGKILL)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if websocket:
            await websocket.send_json({"type": "log", "content": "[Config-Kill] Browser berhasil dihentikan secara paksa."})
    except Exception as e:
        if websocket:
            await websocket.send_json({"type": "log", "content": f"[Config-Kill] Error saat force kill: {str(e)}"})

async def emergency_stop(websocket=None):
    """
    Fungsi untuk dipanggil saat ada error tak terduga (agar sistem tidak crash).
    """
    if websocket:
        await websocket.send_json({"type": "log", "content": "[Config-Kill] Emergency Stop Ditekan! Membersihkan resource..."})
    await force_kill_browser(websocket)
