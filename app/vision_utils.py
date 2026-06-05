import asyncio
import io
import time
import base64
from PIL import Image, ImageDraw
import pytesseract

async def wait_and_click_ocr(page, websocket, target_text, timeout=60, confidence_threshold=10, offset_y=0):
    """Mencari teks di layar dengan OCR dan mengekliknya secara presisi."""
    start_time = time.time()
    await websocket.send_json({"type": "log", "content": f"[Vision] Mencari '{target_text}' di layar..."})
    
    while time.time() - start_time < timeout:
        try:
            screenshot_bytes = await page.screenshot(type="jpeg", quality=100)
            img = Image.open(io.BytesIO(screenshot_bytes))
            
            # Trik Rahasia: Resize 3x dan convert ke Grayscale agar akurasi 100%
            width, height = img.size
            img_processed = img.resize((width * 3, height * 3), Image.LANCZOS).convert('L')
            
            data = pytesseract.image_to_data(img_processed, output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                try:
                    conf = int(data['conf'][i])
                except:
                    conf = 0
                
                if target_text.lower() in text.lower() and len(text) <= len(target_text) + 2 and conf >= confidence_threshold:
                    # Karena gambar di-resize 3x, kembalikan koordinat aslinya (dibagi 3)
                    x = data['left'][i] / 3
                    y = data['top'][i] / 3
                    w = data['width'][i] / 3
                    h = data['height'][i] / 3
                    
                    center_x = x + (w / 2)
                    center_y = y + (h / 2)
                    
                    target_click_y = center_y + offset_y
                    
                    try:
                        draw = ImageDraw.Draw(img)
                        draw.rectangle([x, y, x+w, y+h], outline="red", width=5)
                        draw.ellipse([center_x-5, target_click_y-5, center_x+5, target_click_y+5], fill="yellow")
                        
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        b64_debug = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        await websocket.send_json({"type": "debug_image", "content": b64_debug})
                        # Broadcast ke debug clients juga
                        await _broadcast_debug({"type": "debug_image", "content": b64_debug})
                    except Exception: pass
                    
                    css_x = center_x / 3
                    css_y = target_click_y / 3
                    
                    await websocket.send_json({"type": "log", "content": f"[Vision] '{text}' ditemukan! Mengeklik koordinat Asli:({int(center_x)}, {int(target_click_y)}) -> CSS:({int(css_x)}, {int(css_y)})"})
                    await page.mouse.click(css_x, css_y, delay=150)
                    return True
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
            
        await asyncio.sleep(2)
        
    try:
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        b64_debug = base64.b64encode(buffered.getvalue()).decode('utf-8')
        await websocket.send_json({"type": "debug_image", "content": b64_debug})
        await _broadcast_debug({"type": "debug_image", "content": b64_debug})
    except: pass
    
    await websocket.send_json({"type": "log", "content": f"[Vision] TIMEOUT: Gagal menemukan '{target_text}' dalam {timeout} detik."})
    return False

async def stream_visuals(page, websocket, stop_event):
    """Task background untuk mengirim screenshot ke dashboard secara realtime (Viewport HP)."""
    while not stop_event.is_set():
        try:
            screenshot_bytes = None
            
            # Strategy 1: iframe > video
            try:
                frame = page.frame_locator("iframe").first
                video = frame.locator("video").first
                if await video.is_visible(timeout=500):
                    screenshot_bytes = await video.screenshot(type="jpeg", quality=40)
            except:
                pass
            
            # Strategy 2: direct video
            if not screenshot_bytes:
                try:
                    video_direct = page.locator("video").first
                    if await video_direct.is_visible(timeout=500):
                        screenshot_bytes = await video_direct.screenshot(type="jpeg", quality=40)
                except:
                    pass
            
            # Strategy 3: canvas
            if not screenshot_bytes:
                try:
                    canvas = page.locator("canvas").first
                    if await canvas.is_visible(timeout=500):
                        screenshot_bytes = await canvas.screenshot(type="jpeg", quality=40)
                except:
                    pass
            
            # Strategy 4: full page
            if not screenshot_bytes:
                screenshot_bytes = await page.screenshot(type="jpeg", quality=40)
            
            import app.shared_ws as shared_ws
            shared_ws.latest_frame_bytes = screenshot_bytes
                
            b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            await websocket.send_json({"type": "image", "content": b64_img})
            # Broadcast ke semua debug clients juga
            await _broadcast_debug({"type": "image", "content": b64_img})
        except asyncio.CancelledError:
            break
        except Exception:
            pass
        await asyncio.sleep(0.2) # Refresh rate ~5 fps (REALTIME!)


async def _broadcast_debug(data):
    """Helper: Broadcast data ke semua debug WebSocket clients."""
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
        pass  # Server belum ready, skip
