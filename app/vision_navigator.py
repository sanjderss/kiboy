import asyncio
import io
import time
import base64
from PIL import Image
import pytesseract

from config_coordinates import COORDS

async def get_screen_text(page, quality=50):
    """Membaca seluruh teks di layar untuk menentukan State (Posisi saat ini)."""
    try:
        try:
            frame = page.frame_locator("iframe").first
            video = frame.locator("video").first
            if await video.is_visible(timeout=1000):
                screenshot_bytes = await video.screenshot(type="jpeg", quality=100) # Tinggikan quality untuk OCR
            else:
                screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
        except:
            screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
            
        # Trik rahasia: Resize gambar 3x lipat agar Tesseract bisa baca tulisan kecil dengan akurat 100%
        img = Image.open(io.BytesIO(screenshot_bytes))
        width, height = img.size
        img = img.resize((width * 3, height * 3), Image.LANCZOS)
        
        # Konversi ke Grayscale agar contrast lebih jelas
        img = img.convert('L')
        
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        texts = []
        for i in range(len(data['text'])):
            t = data['text'][i].strip()
            conf = int(data['conf'][i]) if str(data['conf'][i]).isdigit() else 0
            if len(t) > 2 and conf > 10:
                texts.append(t.lower())
                
        print(f"DEBUG VISION: {texts}")
        return texts
    except Exception as e:
        print(f"DEBUG VISION ERROR: {e}")
        return []

async def determine_state(page):
    """Menentukan bot sedang berada di layar apa berdasarkan teks yang terlihat."""
    texts = await get_screen_text(page)
    screen_text = " ".join(texts)
    
    from config_vision import analyze_realtime_text
    
    # Deteksi state murni berdasarkan config rules (Modular)
    detected_state = analyze_realtime_text(screen_text)
    
    # Khusus untuk OS_INSTALLING agar lebih akurat jika di App Store
    if detected_state == "OS_INSTALLING":
        if "commonapps" in screen_text or "tools" in screen_text:
            return "APP_STORE_DOWNLOADING"
            
    return detected_state

async def click_hardcoded(page, websocket, action_name, coord_key, delay_after=2):
    """Mengeklik dengan koordinat absolut yang sudah dikalibrasi."""
    coord = COORDS.get(coord_key)
    if not coord:
        return
    await websocket.send_json({"type": "log", "content": f"[Vision-State] Eksekusi: {action_name} di (X:{coord['x']}, Y:{coord['y']})"})
    await page.mouse.click(coord['x'], coord['y'], delay=150)
    await asyncio.sleep(delay_after)

async def navigate_to_chrome(page, websocket):
    """
    State Machine Cerdas untuk navigasi.
    Akan terus looping menganalisis layar sampai mencapai GOAL (Chrome terbuka).
    """
    await websocket.send_json({"type": "log", "content": "[Vision-State] Memulai deteksi layar otonom..."})
    
    max_steps = 150
    step = 0
    
    while step < max_steps:
        state = await determine_state(page)
        await websocket.send_json({"type": "log", "content": f"[Vision-State] Bot mendeteksi posisi saat ini: {state}"})
        
        if state == "HOME_SCREEN":
            await click_hardcoded(page, websocket, "Buka App Store", "APP_STORE_ICON", delay_after=5)
            
        elif state == "APP_STORE":
            texts = await get_screen_text(page)
            if "open" in " ".join(texts):
                await click_hardcoded(page, websocket, "Buka Chrome (Sudah Terinstal)", "OPEN_CHROME", delay_after=5)
            else:
                await click_hardcoded(page, websocket, "Pindah Tab CommonApps", "TAB_COMMON_APPS", delay_after=3)
                await click_hardcoded(page, websocket, "Download Chrome", "INSTALL_CHROME", delay_after=5)
                
        elif state == "APP_STORE_DOWNLOADING":
            await websocket.send_json({"type": "log", "content": "[Vision-State] Sedang mendownload Chrome dari App Store... (Realtime Rendering)"})
            await asyncio.sleep(2)
                
        elif state == "INSTALL_POPUP":
            await click_hardcoded(page, websocket, "Konfirmasi Install OS", "POPUP_INSTALL", delay_after=3)
            
        elif state == "OS_INSTALLING":
            await websocket.send_json({"type": "log", "content": "[Vision-State] OS Android sedang memasang APK... (Realtime Rendering)"})
            await asyncio.sleep(2)
            
        elif state == "CHROME_FRE":
            from main import wait_and_click_ocr # Import OCR dinamis jika butuh
            await wait_and_click_ocr(page, websocket, "Accept", timeout=20)
            await asyncio.sleep(3)
            
        elif state == "CHROME_SYNC":
            from main import wait_and_click_ocr
            await wait_and_click_ocr(page, websocket, "No", timeout=20)
            await asyncio.sleep(3)
            return True # Berhasil mencapai titik akhir!
            
        elif state == "CHROME_MAIN":
            await websocket.send_json({"type": "log", "content": "[Vision-State] GOAL TERCAPAI: Chrome Siap Digunakan!"})
            return True
            
        else:
            await asyncio.sleep(0.5) # Realtime polling!
            
        step += 1
        
    await websocket.send_json({"type": "log", "content": "[Vision-State] GAGAL: Terlalu banyak langkah tersesat."})
    return False
