import asyncio

# Global variable untuk menyimpan referensi task utama yang sedang berjalan
current_bot_task = None

def start_task(coroutine):
    """Memulai task baru dan menyimpannya di memory agar bisa dibatalkan."""
    global current_bot_task
    # Batalkan task lama jika masih berjalan
    if current_bot_task and not current_bot_task.done():
        current_bot_task.cancel()
    
    current_bot_task = asyncio.create_task(coroutine)
    return current_bot_task

async def stop_task(websocket):
    """Membatalkan (Kill Paksa) task utama jika sedang berjalan."""
    global current_bot_task
    if current_bot_task and not current_bot_task.done():
        current_bot_task.cancel()
        await websocket.send_json({"type": "log", "content": "[Task Manager] Perintah HENTIKAN PAKSA diterima! Membatalkan semua proses..."})
        return True
    else:
        await websocket.send_json({"type": "log", "content": "[Task Manager] Tidak ada proses yang sedang berjalan untuk dihentikan."})
        return False
