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
        import app.shared_ws as shared_ws
        
        # Wait up to 5 seconds for a frame to be available from stream_visuals
        for _ in range(25):
            if shared_ws.latest_frame_bytes is not None:
                break
            await asyncio.sleep(0.2)
            
        screenshot_bytes = shared_ws.latest_frame_bytes
        if not screenshot_bytes:
            # Fallback if stream_visuals is somehow not running
            screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
            print("DEBUG SCREENSHOT SOURCE: fullpage_fallback")
        else:
            print(f"DEBUG SCREENSHOT SOURCE: shared_ws ({len(screenshot_bytes)} bytes)")
            
        img = Image.open(io.BytesIO(screenshot_bytes))
        width, height = img.size
        print(f"DEBUG SCREENSHOT SIZE: {width}x{height}")
        
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

async def click_by_ocr(page, websocket, target_words, action_name, delay_after=2, click_last=False):
    """Mencari teks di layar secara dinamis dan mengeklik di tengah tulisan tersebut.
    Jika click_last=True, akan memilih hasil dengan nilai Y terbesar (paling bawah)."""
    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Mencari elemen '{action_name}'..."})
    await _broadcast_log(f"[Vision-OCR] Mencari elemen '{action_name}'...")
    results = await get_screen_text_with_boxes(page)
    
    matches = []
    for r in results:
        for target in target_words:
            if target.lower() in r['text']:
                matches.append(r)
                break
                
    if matches:
        if click_last:
            # Sort by Y descending (highest Y = bottom of screen)
            matches.sort(key=lambda item: item['y'], reverse=True)
            
        r = matches[0]
        try:
            iframe = await page.query_selector("iframe")
            if iframe:
                box = await iframe.bounding_box()
                if box:
                    # OCR Image is 1290x2217. Scale it down to iframe css size.
                    # We subtract 30 on the ORIGINAL scale to click slightly above text
                    original_y = r['y'] - 30
                    
                    scale_x = box["width"] / 1290
                    scale_y = box["height"] / 2217
                    
                    click_x = box["x"] + (r['x'] * scale_x)
                    click_y = box["y"] + (original_y * scale_y)
                    
                    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Ketemu '{r['text']}'! Mengeklik (X:{click_x:.1f}, Y:{click_y:.1f})"})
                    await _broadcast_log(f"[Vision-OCR] Ketemu '{r['text']}'! Mengeklik (X:{click_x:.1f}, Y:{click_y:.1f})")
                    
                    await page.mouse.click(click_x, click_y, delay=150)
                    await asyncio.sleep(delay_after)
                    return True
        except Exception as e:
            print(f"Error in click_by_ocr: {e}")
                    
    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Gagal menemukan '{target_words}' di layar."})
    await _broadcast_log(f"[Vision-OCR] Gagal menemukan '{target_words}' di layar.")
    return False

async def click_install_for_app(page, websocket, app_name_words, action_name, delay_after=2):
    """Mencari nama aplikasi, lalu mengeklik tombol 'install' yang posisinya tepat di bawah nama aplikasi tersebut."""
    await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Mencari elemen '{action_name}'..."})
    await _broadcast_log(f"[Vision-OCR] Mencari elemen '{action_name}'...")
    results = await get_screen_text_with_boxes(page)
    
    # Cari nama app
    app_r = None
    for r in results:
        for target in app_name_words:
            if target.lower() in r['text']:
                app_r = r
                break
        if app_r: break
        
    if not app_r:
        await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Gagal menemukan app '{app_name_words}'."})
        await _broadcast_log(f"[Vision-OCR] Gagal menemukan app '{app_name_words}'.")
        return False
        
    # Cari tombol 'install' atau 'download' di bawah app_r
    install_r = None
    for r in results:
        if "install" in r['text'] or "download" in r['text']:
            # Cek apakah satu kolom (X berdekatan) dan berada di bawahnya
            if abs(r['x'] - app_r['x']) < 150 and r['y'] > app_r['y'] and (r['y'] - app_r['y']) < 300:
                install_r = r
                break
                
    if not install_r:
        # Jika text install tidak ketemu dari OCR (mungkin OCR jelek), klik fallback dengan offset Y+180
        install_r = {'text': 'install_fallback', 'x': app_r['x'], 'y': app_r['y'] + 180}
        
    try:
        iframe = await page.query_selector("iframe")
        if iframe:
            box = await iframe.bounding_box()
            if box:
                scale_x = box["width"] / 1290
                scale_y = box["height"] / 2217
                
                click_x = box["x"] + (install_r['x'] * scale_x)
                click_y = box["y"] + (install_r['y'] * scale_y)
                
                await websocket.send_json({"type": "log", "content": f"[Vision-OCR] Ketemu '{install_r['text']}' milik {app_r['text']}! Mengeklik (X:{click_x:.1f}, Y:{click_y:.1f})"})
                await _broadcast_log(f"[Vision-OCR] Ketemu '{install_r['text']}' milik {app_r['text']}! Mengeklik (X:{click_x:.1f}, Y:{click_y:.1f})")
                
                await page.mouse.click(click_x, click_y, delay=150)
                await asyncio.sleep(delay_after)
                return True
    except Exception as e:
        print(f"Error in click_install_for_app: {e}")
        
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
    
    # Broadcast OCR text ke debug clients
    await _broadcast_ocr(texts, detected_state)
            
    return detected_state

async def click_hardcoded(page, websocket, action_name, coord_key, delay_after=2):
    """Mengeklik dengan koordinat absolut yang sudah dikalibrasi."""
    coord = COORDS.get(coord_key)
    if not coord:
        return
        
    click_x = coord['x']
    click_y = coord['y']
        
    await websocket.send_json({"type": "log", "content": f"[Vision-State] Eksekusi: {action_name} di (X:{click_x:.1f}, Y:{click_y:.1f})"})
    await _broadcast_log(f"[Vision-State] Eksekusi: {action_name} di (X:{click_x:.1f}, Y:{click_y:.1f})")
    await page.mouse.click(click_x, click_y, delay=150)
    await asyncio.sleep(delay_after)

# ============================================================
# STATE DESCRIPTIONS — untuk ditampilkan di Debug Dashboard
# ============================================================
STATE_DESCRIPTIONS = {
    "HOME_SCREEN": "Berada di Home Screen Android. Mencari App Store/RPA Store...",
    "APP_STORE": "Di dalam App Store. Mencari Chrome untuk diinstall...",
    "INSTALL_POPUP": "Popup konfirmasi install muncul. Mengkonfirmasi install...",
    "APP_STORE_DOWNLOADING": "Chrome sedang didownload dari App Store. Menunggu...",
    "OS_INSTALLING": "Sistem sedang memasang APK. Menunggu selesai...",
    "APP_INSTALLED": "Aplikasi selesai diinstal. Mencari tombol Open...",
    "CHROME_FRE": "Chrome First Run Experience. Menyetujui persyaratan...",
    "CHROME_SYNC": "Chrome menawarkan sinkronisasi. Menolak...",
    "CHROME_MAIN": "Chrome terbuka! Mencari search bar untuk ketik query...",
    "GOAL_COMPLETE": "🎉 MISI SELESAI! Query sudah diketik di Chrome search bar!",
    "UNKNOWN": "Layar belum dikenali. Kemungkinan masih loading/booting...",
    "IDLE": "Bot belum berjalan.",
}

async def navigate_to_chrome(page, websocket):
    """
    State Machine Cerdas untuk navigasi.
    Akan terus looping menganalisis layar sampai mencapai GOAL (Chrome terbuka).
    """
    await websocket.send_json({"type": "log", "content": "[Vision-State] Memulai deteksi layar otonom..."})
    await _broadcast_log("[Vision-State] Memulai deteksi layar otonom...")
    
    max_steps = 150
    step = 0
    
    while step < max_steps:
        state = await determine_state(page)
        await websocket.send_json({"type": "log", "content": f"[Vision-State] Bot mendeteksi posisi saat ini: {state}"})
        
        # Broadcast AI state ke debug dashboard
        await _broadcast_ai_state(state, step, max_steps)
        await _broadcast_log(f"[Vision-State] Bot mendeteksi posisi saat ini: {state}")
        
        if state == "HOME_SCREEN":
            unknown_count = 0
            found = await click_by_ocr(page, websocket, ["store", "app", "rpa"], "Buka App Store", delay_after=5)
            if not found:
                await click_hardcoded(page, websocket, "Fallback Buka App Store", "APP_STORE_ICON", delay_after=5)
                
        elif state == "UNKNOWN":
            unknown_count = locals().get('unknown_count', 0) + 1
            if unknown_count > 2:
                await websocket.send_json({"type": "log", "content": "[Vision-State] Terlalu lama UNKNOWN. Mengklik tombol Home di overlay cloud!"})
                await _broadcast_log("[Vision-State] Terlalu lama UNKNOWN. Mengklik tombol Home...")
                await click_hardcoded(page, websocket, "Klik Home Overlay", "HOME_BUTTON", delay_after=5)
                unknown_count = 0
            else:
                await websocket.send_json({"type": "log", "content": "[Vision-State] Layar belum dikenali. Menunggu..."})
                await asyncio.sleep(2)
            
        elif state == "APP_STORE":
            unknown_count = 0
            texts = await get_screen_text(page)
            if "open" in " ".join(texts) and "chrome" in " ".join(texts):
                found = await click_by_ocr(page, websocket, ["open"], "Buka Chrome (Sudah Terinstal)", delay_after=5)
                if not found:
                    await click_hardcoded(page, websocket, "Fallback Buka Chrome", "OPEN_CHROME", delay_after=5)
            else:
                # Cari tab CommonApps
                await click_by_ocr(page, websocket, ["common", "apps"], "Pindah Tab CommonApps", delay_after=3)
                
                # Cari text chrome dulu
                chrome_found = await click_by_ocr(page, websocket, ["chrome"], "Cari text Chrome", delay_after=3)
                
                if not chrome_found:
                    await websocket.send_json({"type": "log", "content": "[Vision-Action] Chrome tidak terlihat. Membuka fitur Search..."})
                    await _broadcast_log("[Vision-Action] Chrome tidak terlihat. Membuka fitur Search...")
                    # Klik di pojok kanan atas (icon search)
                    await page.mouse.click(380, 45)
                    await asyncio.sleep(1)
                    # Jika itu textbox lebar, klik juga di tengah
                    await page.mouse.click(200, 45)
                    await asyncio.sleep(2)
                    
                    await page.keyboard.type("chrome")
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(5)
                    
                    chrome_found = await click_by_ocr(page, websocket, ["chrome"], "Cari text Chrome (Setelah Search)", delay_after=3)

                # Lalu cari tombol install/download HANYA jika kita sudah menemukan/search chrome
                if chrome_found or True: 
                    # Gunakan fungsi click_install_for_app agar tidak salah klik install milik aplikasi lain!
                    install_found = await click_install_for_app(page, websocket, ["chrome"], "Download Chrome Spesifik", delay_after=5)
                    if not install_found:
                        await click_hardcoded(page, websocket, "Fallback Download Chrome", "INSTALL_CHROME", delay_after=5)
                
        elif state == "APP_STORE_DOWNLOADING":
            unknown_count = 0
            await websocket.send_json({"type": "log", "content": "[Vision-State] Sedang mendownload Chrome dari App Store... (Realtime Rendering)"})
            await _broadcast_log("[Vision-State] Sedang mendownload Chrome dari App Store... (Realtime Rendering)")
            await asyncio.sleep(2)
                
        elif state == "INSTALL_POPUP":
            await click_hardcoded(page, websocket, "Konfirmasi Install OS", "POPUP_INSTALL", delay_after=3)
            
        elif state == "OS_INSTALLING":
            await websocket.send_json({"type": "log", "content": "[Vision-State] OS Android sedang memasang APK... (Realtime Rendering)"})
            await _broadcast_log("[Vision-State] OS Android sedang memasang APK... (Realtime Rendering)")
            await asyncio.sleep(2)
            
        elif state == "APP_INSTALLED":
            unknown_count = 0
            await websocket.send_json({"type": "log", "content": "[Vision-State] Aplikasi berhasil diinstal. Mengeklik tombol Open..."})
            await _broadcast_log("[Vision-State] Aplikasi berhasil diinstal. Mengeklik tombol Open...")
            # Di popup instalasi selesai, tombol open ada di sana
            await click_by_ocr(page, websocket, ["open"], "Buka Aplikasi Terinstal", delay_after=5)

        elif state == "CHROME_FRE":
            # Klik 'Use without an account' atau 'Accept'
            found = await click_by_ocr(page, websocket, ["without", "tanpa", "no thanks", "accept", "continue"], "Bypass Chrome Login", delay_after=5)
            if not found:
                from app.vision_utils import wait_and_click_ocr
                await wait_and_click_ocr(page, websocket, "without", timeout=10)
            await asyncio.sleep(3)
            
        elif state == "CHROME_SYNC":
            from app.vision_utils import wait_and_click_ocr
            await wait_and_click_ocr(page, websocket, "No", timeout=20)
            await asyncio.sleep(3)
            return True # Berhasil mencapai titik akhir!
            
        elif state == "CHROME_PRIVACY":
            # Klik 'More' atau 'Got it'/'Done'
            found = await click_by_ocr(page, websocket, ["got it", "done"], "Bypass Privacy Done", delay_after=3)
            if not found:
                await click_by_ocr(page, websocket, ["more"], "Bypass Privacy More", delay_after=2, click_last=True)
            await asyncio.sleep(2)
            
        elif state == "CHROME_MAIN":
            await websocket.send_json({"type": "log", "content": "[Vision-State] Chrome terbuka! Sekarang ketik di search bar..."})
            await _broadcast_log("[Vision-State] Chrome terbuka! Sekarang ketik di search bar...")
            await _broadcast_ai_state("CHROME_MAIN", step, max_steps)
            
            # Ketik di Chrome search bar
            typed = await type_in_chrome_search(page, websocket, "termux f-droid")
            if typed:
                await websocket.send_json({"type": "log", "content": "[Vision-State] 🎉 MISI SELESAI: 'termux f-droid' sudah diketik di Chrome!"})
                await _broadcast_log("[Vision-State] 🎉 MISI SELESAI: 'termux f-droid' sudah diketik di Chrome!")
                await _broadcast_ai_state("GOAL_COMPLETE", step, max_steps)
                return True
            else:
                await websocket.send_json({"type": "log", "content": "[Vision-State] Gagal ketik di search bar, coba lagi..."})
                await _broadcast_log("[Vision-State] Gagal ketik di search bar, coba lagi...")
            
        else:
            await asyncio.sleep(0.5) # Realtime polling!
            
        step += 1
        
    await websocket.send_json({"type": "log", "content": "[Vision-State] GAGAL: Terlalu banyak langkah tersesat."})
    await _broadcast_log("[Vision-State] GAGAL: Terlalu banyak langkah tersesat.")
    return False


async def type_in_chrome_search(page, websocket, search_text):
    """
    Ketik teks di Chrome search bar.
    Chrome main page biasanya punya search/omnibox di tengah atas.
    """
    await websocket.send_json({"type": "log", "content": f"[Vision-Search] Mencari search bar untuk ketik '{search_text}'..."})
    await _broadcast_log(f"[Vision-Search] Mencari search bar untuk ketik '{search_text}'...")
    
    try:
        # Coba klik search bar dengan OCR dulu
        results = await get_screen_text_with_boxes(page)
        
        # Cari elemen search / google / "search or type"
        search_clicked = False
        for r in results:
            if any(kw in r['text'] for kw in ['search', 'google', 'type', 'url']):
                try:
                    iframe = await page.query_selector("iframe")
                    if iframe:
                        box = await iframe.bounding_box()
                        if box:
                            scale_x = box["width"] / 1290
                            scale_y = box["height"] / 2217
                            click_x = box["x"] + (r['x'] * scale_x)
                            click_y = box["y"] + (r['y'] * scale_y)
                            await websocket.send_json({"type": "log", "content": f"[Vision-Search] Menemukan search bar: '{r['text']}' di (X:{click_x:.1f}, Y:{click_y:.1f})"})
                            await _broadcast_log(f"[Vision-Search] Menemukan search bar: '{r['text']}' di (X:{click_x:.1f}, Y:{click_y:.1f})")
                            await page.mouse.click(click_x, click_y, delay=150)
                            search_clicked = True
                            break
                except Exception as e:
                    print(f"Error clicking search bar: {e}")
        
        if not search_clicked:
            # Fallback: klik tengah atas layar (posisi umum search bar Chrome mobile)
            await websocket.send_json({"type": "log", "content": "[Vision-Search] OCR gagal, fallback klik search bar di tengah atas..."})
            await _broadcast_log("[Vision-Search] OCR gagal, fallback klik search bar di tengah atas...")
            await page.mouse.click(210, 160, delay=150)  # Posisi umum omnibox
        
        await asyncio.sleep(2)
        
        # Ketik search text menggunakan keyboard
        await websocket.send_json({"type": "log", "content": f"[Vision-Search] Mengetik: '{search_text}'..."})
        await _broadcast_log(f"[Vision-Search] Mengetik: '{search_text}'...")
        await page.keyboard.type(search_text, delay=80)  # Ketik pelan-pelan kayak manusia
        await asyncio.sleep(1)
        
        # Screenshot setelah ketik (debug)
        await websocket.send_json({"type": "log", "content": f"[Vision-Search] ✅ Berhasil ketik '{search_text}' di Chrome search bar!"})
        await _broadcast_log(f"[Vision-Search] ✅ Berhasil ketik '{search_text}' di Chrome search bar!")
        
        return True
        
    except Exception as e:
        await websocket.send_json({"type": "log", "content": f"[Vision-Search] Error saat ketik: {e}"})
        await _broadcast_log(f"[Vision-Search] Error saat ketik: {e}")
        return False


# ============================================================
# BROADCAST HELPERS — Kirim data ke debug dashboard
# ============================================================

async def _broadcast_debug(data):
    """Broadcast data ke semua debug WebSocket clients."""
    try:
        from app.shared_ws import debug_clients
        dead = set()
        for ws in debug_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        debug_clients -= dead
    except ImportError:
        pass

async def _broadcast_ai_state(state, step, max_steps):
    """Broadcast AI state update ke debug dashboard."""
    desc = STATE_DESCRIPTIONS.get(state, "State tidak dikenali.")
    await _broadcast_debug({
        "type": "ai_state",
        "state": state,
        "step": step,
        "max_steps": max_steps,
        "description": desc,
    })

async def _broadcast_ocr(texts, matched_state):
    """Broadcast OCR detected text ke debug dashboard."""
    from config_vision import VISION_CONFIG_RULES
    
    # Cari keyword yang matched
    matched_words = []
    for rule in VISION_CONFIG_RULES:
        if rule["state_name"] == matched_state:
            for kw_group in rule["keywords"]:
                matched_words.extend(kw_group)
            break
    
    await _broadcast_debug({
        "type": "ocr_text",
        "content": texts[:30],  # Max 30 kata untuk performa
        "matched": matched_words,
    })

async def _broadcast_log(content):
    """Broadcast log message ke debug dashboard."""
    await _broadcast_debug({
        "type": "log",
        "content": content,
    })
