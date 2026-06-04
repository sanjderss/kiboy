import asyncio
import io
import time
import base64
from PIL import Image
import pytesseract

from config_coordinates import COORDS

async def get_screen_text_with_boxes(page):
    """Membaca teks di layar beserta koordinat bounding box-nya."""
    try:
        try:
            frame = page.frame_locator("iframe").first
            video = frame.locator("video").first
            if await video.is_visible(timeout=1000):
                screenshot_bytes = await video.screenshot(type="jpeg", quality=100)
            else:
                screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
        except:
            screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
            
        img = Image.open(io.BytesIO(screenshot_bytes))
        width, height = img.size
        # Scale up 3x for OCR accuracy
        scale = 3
        img = img.resize((width * scale, height * scale), Image.LANCZOS)
        img = img.convert('L')
        
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        results = []
        for i in range(len(data['text'])):
            t = data['text'][i].strip()
            conf = int(data['conf'][i]) if str(data['conf'][i]).isdigit() else 0
            if len(t) > 2 and conf > 10:
                # Calculate original coordinate center
                x = data['left'][i] // scale
                y = data['top'][i] // scale
                w = data['width'][i] // scale
                h = data['height'][i] // scale
                cx = x + (w // 2)
                cy = y + (h // 2)
                results.append({"text": t.lower(), "x": cx, "y": cy, "conf": conf})
        return results
    except Exception as e:
        print(f"DEBUG OCR ERROR: {e}")
        return []

async def get_screen_text(page, quality=50):
    """Membaca seluruh teks di layar untuk menentukan State."""
    results = await get_screen_text_with_boxes(page)
    texts = [r["text"] for r in results]
    print(f"DEBUG VISION: {texts}")
    return texts

async def click_by_ocr(page, websocket, target_words, action_name, delay_after=2):
    """Mencari teks di layar secara dinamis dan mengeklik di tengah tulisan tersebut."""
    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Mencari elemen '{action_name}'..."})
    results = await get_screen_text_with_boxes(page)
    
    # Coba cari kecocokan kata
    for r in results:
        for target in target_words:
            if target.lower() in r['text']:
                # Ditemukan! Klik sedikit di atas teks (karena biasanya icon ada di atas teks)
                click_y = r['y'] - 30 # Offset y ke atas untuk klik icon, bukan textnya langsung
                await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Ketemu '{r['text']}'! Mengeklik (X:{r['x']}, Y:{click_y})"})
                await page.mouse.click(r['x'], click_y, delay=150)
                await asyncio.sleep(delay_after)
                return True
                
    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Gagal menemukan '{target_words}' di layar."})
    return False

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
        
        if state == "HOME_SCREEN" or state == "UNKNOWN":
            # Jika di Home Screen ATAU state UNKNOWN (karena kadang gagal baca "Virtual Location"), 
            # coba paksakan OCR mencari tulisan "App Store"
            found = await click_by_ocr(page, websocket, ["store", "app", "rpa"], "Buka App Store", delay_after=5)
            if not found:
                # Jika OCR gagal baca, baru pakai fallback hardcoded config
                await click_hardcoded(page, websocket, "Fallback Buka App Store", "APP_STORE_ICON", delay_after=5)
            
        elif state == "APP_STORE":
            texts = await get_screen_text(page)
            if "open" in " ".join(texts):
                found = await click_by_ocr(page, websocket, ["open"], "Buka Chrome (Sudah Terinstal)", delay_after=5)
                if not found:
                    await click_hardcoded(page, websocket, "Fallback Buka Chrome", "OPEN_CHROME", delay_after=5)
            else:
                found = await click_by_ocr(page, websocket, ["common", "apps"], "Pindah Tab CommonApps", delay_after=3)
                if not found:
                    await click_hardcoded(page, websocket, "Fallback Pindah Tab", "TAB_COMMON_APPS", delay_after=3)
                    
                install_found = await click_by_ocr(page, websocket, ["install", "download"], "Download Chrome", delay_after=5)
                if not found:
                    await click_hardcoded(page, websocket, "Fallback Download Chrome", "INSTALL_CHROME", delay_after=5)
                
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
