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

# FastAPI & UI routes removed for modularity
from config_coordinates import COORDS
from app.mail_handler import get_free_email, wait_for_otp
from app.proxy_handler import mark_proxy_used, get_working_proxy
from app.vision_navigator import navigate_to_chrome
from app.task_manager import start_task, stop_task
from app.vision_utils import wait_and_click_ocr, stream_visuals

# Lock untuk membatasi hanya 1 bot yang jalan
bot_lock = asyncio.Lock()



async def run_bot_task(websocket, mode="register", account_data=None):
    """Fungsi utama bot: Registrasi Otomatis & Login (Async Optimized)."""
    if bot_lock.locked():
        await websocket.send_json({"type": "log", "content": "Bot sedang berjalan..."})
        return

    async with bot_lock:
        await websocket.send_json({"type": "status", "content": "Running"})
        stop_visuals = asyncio.Event()
        
        try:
            if mode == "login":
                # Parse account data: "Email: xxx | User: yyy | Pass: zzz"
                import re
                email_match = re.search(r"Email:\s*(.*?)\s*\|", account_data)
                pass_match = re.search(r"Pass:\s*(.*)", account_data)
                
                email_addr = email_match.group(1) if email_match else "unknown"
                password = pass_match.group(1) if pass_match else "unknown"
                
                await websocket.send_json({"type": "log", "content": f"Mode Login: {email_addr}"})
                
                async with async_playwright() as p:
                    # Skip to the login portion directly
                    pass # We will handle this in the next chunk
            else:
                # 0. Get Working Proxy from Pool
                await websocket.send_json({"type": "log", "content": "Mengambil Proxy Instan dari Kolam Hunter..."})
                from app.proxy_handler import get_working_proxy
                working_proxy = await asyncio.to_thread(get_working_proxy)
                if working_proxy:
                    await websocket.send_json({"type": "log", "content": f"Menggunakan Proxy Instan: {working_proxy}"})
                else:
                    await websocket.send_json({"type": "log", "content": "Kolam Proxy kosong! Menunggu Hunter..."})
                    working_proxy = None
            
                # 1. Email Setup
                await websocket.send_json({"type": "log", "content": "Membuat email temporer gratis..."})
                email_obj = get_free_email()
                email_addr = email_obj.address
                await websocket.send_json({"type": "log", "content": f"Email siap: {email_addr}"})

                async with async_playwright() as p:
                    launch_options = {
                        "headless": True,
                        "args": [
                            '--no-sandbox', 
                            '--disable-setuid-sandbox',
                            '--autoplay-policy=no-user-gesture-required'
                        ]
                    }
                    if working_proxy:
                        launch_options["proxy"] = {"server": f"http://{working_proxy}"}
                    
                    browser = await p.chromium.launch(**launch_options)
                    device_config = p.devices['iPhone 15 Pro Max'].copy()
                    device_config['has_touch'] = False
                    device_config['is_mobile'] = False
                    device_config['ignore_https_errors'] = True
                    context = await browser.new_context(**device_config)
                    page = await context.new_page()
                    await Stealth().apply_stealth_async(page)
                
                    # Block heavy assets to speed up slow proxies
                    async def intercept_route(route):
                        if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                            await route.abort()
                        else:
                            await route.continue_()
                
                    await page.route("**/*", intercept_route)

                    # Mulai Stream Visual di Background
                    visual_task = asyncio.create_task(stream_visuals(page, websocket, stop_visuals))

                    await websocket.send_json({"type": "log", "content": "Membuka Hippo Cloud..."})
                    # Tunggu sampai network benar-benar tenang dengan retry (karena proxy gratis lambat)
                    for attempt in range(3):
                        try:
                            await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register", wait_until="domcontentloaded", timeout=90000)
                            break
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            if attempt == 2:
                                raise e
                            await websocket.send_json({"type": "log", "content": f"Timeout halaman, mencoba ulang (Attempt {attempt+2}/3)..."})
                            await asyncio.sleep(3)
                    await asyncio.sleep(5)
                
                    # 2. Tunggu Form & Input Data
                    current_url = page.url
                    await websocket.send_json({"type": "log", "content": f"URL Saat Ini: {current_url}"})
                    await websocket.send_json({"type": "log", "content": "Menunggu form Hippo muncul..."})
                
                    try:
                        inputs = page.locator("input")
                        await inputs.nth(0).wait_for(state="visible", timeout=30000)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        await page.screenshot(path="form_failure.png")
                        await websocket.send_json({"type": "log", "content": f"Form gagal dideteksi. Screenshot tersimpan. Error: {str(e)}"})
                        return

                    # Isi Email
                    await inputs.nth(0).fill(email_addr)
                    # Isi Username (Gunakan prefix bot + random string)
                    username = f"bot_{email_addr.split('@')[0][:8]}"
                    await inputs.nth(2).fill(username)
                
                    # Isi Password & Konfirmasi
                    password = "Bot123456!"
                    await inputs.nth(3).fill(password)
                    await inputs.nth(4).fill(password)
                
                    await websocket.send_json({"type": "log", "content": f"Data Form terisi (User: {username})"})

                    # 3. Klik Send OTP (发送)
                    await websocket.send_json({"type": "log", "content": "Mencoba klik tombol '发送' (Send)..."})
                    send_btn = page.locator('text="发送"').first
                
                    if await send_btn.is_visible(timeout=5000):
                        await send_btn.click()
                        await websocket.send_json({"type": "log", "content": "Tombol '发送' diklik! Memeriksa respon limit..."})
                    
                        # Cek apakah ada toast error dari server (Misal: Limit 20)
                        try:
                            toast = page.locator(".uni-toast")
                            if await toast.is_visible(timeout=2000):
                                toast_text = await toast.inner_text()
                                await websocket.send_json({"type": "log", "content": f"Pesan Server: {toast_text}"})
                                if "limit" in toast_text.lower() or "ip" in toast_text.lower() or "10" in toast_text or "20" in toast_text:
                                    await websocket.send_json({"type": "log", "content": "PROXY TERKENA LIMIT! Membuang proxy ini ke daftar hitam..."})
                                    if working_proxy:
                                        from app.proxy_handler import mark_proxy_used
                                        mark_proxy_used(working_proxy)
                                    await websocket.send_json({"type": "log", "content": "Bot dihentikan otomatis. Silakan klik Start lagi untuk mencoba IP Proxy lain."})
                                    return # Berhenti agar finally menutup browser
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            pass
                    
                        # 4. Tunggu OTP (Non-blocking loop)
                        otp_code = None
                        for attempt in range(15): # 75 detik
                            await websocket.send_json({"type": "log", "content": f"Cek inbox email (Attempt {attempt+1}/15)..."})
                            otp_code = await asyncio.to_thread(wait_for_otp, email_obj, 5)
                            if otp_code:
                                await websocket.send_json({"type": "log", "content": f"OTP DITERIMA: {otp_code}"})
                                break
                            await asyncio.sleep(1)

                        if otp_code:
                            # Isi OTP
                            await inputs.nth(1).fill(otp_code)
                            await websocket.send_json({"type": "log", "content": "OTP diinput."})
                        
                            # Klik checkbox policy
                            checkbox = page.locator('.cuIcon-round').first
                            if await checkbox.is_visible():
                                await websocket.send_json({"type": "log", "content": "Mencentang Privacy Policy..."})
                                await checkbox.click(timeout=5000)
                        
                            # Klik Sign Up
                            await websocket.send_json({"type": "log", "content": "Mencari tombol Sign up..."})
                            reg_btn = page.locator('.dlbutton', has_text="Sign up")
                            await reg_btn.click(timeout=10000)
                            await websocket.send_json({"type": "log", "content": "Tombol SIGN UP diklik!"})
                            await asyncio.sleep(5)
                        
                            # 5. Simpan Akun
                            os.makedirs("data", exist_ok=True)
                            with open("data/accounts.txt", "a") as f:
                                f.write(f"Email: {email_addr} | User: {username} | Pass: {password}\n")
                            await websocket.send_json({"type": "log", "content": f"Akun tersimpan di data/accounts.txt (User: {username})"})
                        
                            # Blacklist proxy agar tidak dipakai daftar lagi
                            if working_proxy:
                                from app.proxy_handler import mark_proxy_used
                                mark_proxy_used(working_proxy)
                        
                            # 6. Auto Login (Switch to Real IP)
                            await websocket.send_json({"type": "log", "content": "Registrasi Sukses! Mengganti IP Proxy kembali ke IP Asli agar koneksi super cepat..."})
                        
                            stop_visuals.set()
                            if 'visual_task' in locals():
                                await visual_task
                            
                        await browser.close()
            
            # --- START LOGIN AND AI VISION PHASE ---
            if True: # Always runs, either from login mode or after registration
                async with async_playwright() as p:
                    new_launch_options = {
                        "headless": True,
                        "args": [
                            '--no-sandbox', 
                            '--disable-setuid-sandbox',
                            '--autoplay-policy=no-user-gesture-required'
                        ]
                    }
                    browser = await p.chromium.launch(**new_launch_options)
                    new_device_config = p.devices['iPhone 15 Pro Max'].copy()
                    new_device_config['has_touch'] = False
                    new_device_config['is_mobile'] = False
                    new_device_config['ignore_https_errors'] = True
                    context = await browser.new_context(**new_device_config)
                    page = await context.new_page()
                    await Stealth().apply_stealth_async(page)
                    
                    stop_visuals.clear()
                    visual_task = asyncio.create_task(stream_visuals(page, websocket, stop_visuals))
                    
                    await websocket.send_json({"type": "log", "content": "Mencoba Login otomatis dengan IP Asli..."})
                    for attempt in range(3):
                        try:
                            await page.goto("https://www.hippocloudphone.com/index.html#/pages/login/login", wait_until="domcontentloaded", timeout=90000)
                            break
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            if attempt == 2:
                                raise e
                            await websocket.send_json({"type": "log", "content": f"Timeout login, mencoba ulang (Attempt {attempt+2}/3)..."})
                            await asyncio.sleep(3)
                    await asyncio.sleep(5)
                    
                    login_inputs = page.locator("input")
                    await login_inputs.nth(0).fill(email_addr)
                    await login_inputs.nth(1).fill(password)
                    
                    login_btn = page.locator('.dlbutton', has_text="Login")
                    await login_btn.click(timeout=10000)
                    
                    await websocket.send_json({"type": "log", "content": "Login berhasil disubmit!"})
                    await asyncio.sleep(5)
                    
                    # Masuk ke Grup Trial
                    await websocket.send_json({"type": "log", "content": f"URL Setelah Login: {page.url}"})
                    await websocket.send_json({"type": "log", "content": "Mencari Grup Trial (试用分组)... (Tunggu hingga 60 detik)"})
                    group_element = page.locator("text=试用分组").first
                    if await group_element.is_visible(timeout=60000):
                        await websocket.send_json({"type": "log", "content": "Grup Trial ditemukan, masuk ke grup..."})
                        await group_element.click()
                        
                        # Tunggu phone list termuat secara DINAMIS (realtime), gausah nunggu 15 detik!
                        await websocket.send_json({"type": "log", "content": "Menunggu daftar HP muncul di layar (realtime)..."})
                        
                        phone_card_visible = False
                        try:
                            # Cek ID: xxx, begitu muncul langsung sikat, max tunggu 30 detik
                            phone_id_el = page.locator("text=/ID:\\s*\\d+/").first
                            await phone_id_el.wait_for(state="visible", timeout=30000)
                            phone_card_visible = True
                            await websocket.send_json({"type": "log", "content": "Phone card terdeteksi! Melanjutkan klik..."})
                        except Exception:
                            await websocket.send_json({"type": "log", "content": "TIDAK ADA phone card aktif di grup ini. Akun mungkin expired. Bot dihentikan."})
                            return
                        
                        # Screenshot sebelum klik (debug)
                        await page.screenshot(path="before_click_phone.png")
                        
                        # BLIND CLICK langsung ke koordinat thumbnail phone
                        # Koordinat diambil dari config_coordinates.py
                        await websocket.send_json({"type": "log", "content": f"Klik koordinat Phone (X:{COORDS['PHONE_THUMBNAIL']['x']}, Y:{COORDS['PHONE_THUMBNAIL']['y']})..."})
                        await page.mouse.click(COORDS['PHONE_THUMBNAIL']['x'], COORDS['PHONE_THUMBNAIL']['y'])
                        clicked = True
                        await websocket.send_json({"type": "log", "content": "Phone diklik! Menunggu WebRTC iframe muncul (8 detik)..."})
                        
                        if clicked:
                            # Masuk ke dalam WebRTC Iframe secara dinamis
                            await websocket.send_json({"type": "log", "content": "Menunggu Iframe WebRTC muncul di DOM..."})
                            try:
                                await page.wait_for_selector("iframe", timeout=30000)
                                await asyncio.sleep(3) # Tunggu 3 detik agar elemen internal iframe siap (tombol play)
                                
                                await websocket.send_json({"type": "log", "content": f"Mengklik Tombol Play Iframe di (X:{COORDS['WEBRTC_IFRAME']['x']}, Y:{COORDS['WEBRTC_IFRAME']['y']})..."})
                                
                                # Cukup klik 2x cepat (double click)
                                await page.mouse.click(COORDS['WEBRTC_IFRAME']['x'], COORDS['WEBRTC_IFRAME']['y'])
                                await asyncio.sleep(0.5)
                                await page.mouse.click(COORDS['WEBRTC_IFRAME']['x'], COORDS['WEBRTC_IFRAME']['y'])
                                
                                await websocket.send_json({"type": "log", "content": "Iframe diklik! Menyerahkan ke AI Vision (Realtime Polling)..."})
                                
                                # Panggil AI Vision Autonomous State Machine LANGSUNG tanpa menunggu 15 detik!
                                await navigate_to_chrome(page, websocket)
                                
                                # Tunggu beberapa detik untuk persiapan eksekusi tugas utama (Proxy/Tiktok dll)
                                await asyncio.sleep(5)
                                
                                await websocket.send_json({"type": "log", "content": "🎉 Chrome Search Bar TERBUKA! Misi Selesai dengan AI Vision!"})
                                
                                # Simpan state berhasil
                                from config_state import save_state
                                await save_state(email_addr, {"status": "success", "chrome_ready": True})
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                await websocket.send_json({"type": "log", "content": f"Gagal klik iframe: {e}"})
                            
                        await websocket.send_json({"type": "log", "content": "Selesai mengeksplorasi dashboard. Menunggu 15 detik untuk preview..."})
                    else:
                        await websocket.send_json({"type": "log", "content": "Grup Trial (试用分组) tidak muncul di layar."})

        except asyncio.CancelledError:
            await websocket.send_json({"type": "log", "content": "Proses bot dihentikan secara paksa."})
        except Exception as e:
            await websocket.send_json({"type": "log", "content": f"Error: {str(e)}"})
        finally:
            stop_visuals.set()
            if 'visual_task' in locals(): await visual_task
            if 'browser' in locals(): await browser.close()
            await websocket.send_json({"type": "status", "content": "Idle"})
            await websocket.send_json({"type": "log", "content": "Bot Stopped."})
