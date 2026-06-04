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
                        
                        # Tunggu phone list termuat dulu sepenuhnya
                        await websocket.send_json({"type": "log", "content": "Menunggu daftar HP termuat (15 detik)..."})
                        await asyncio.sleep(15)
                        
                        # CEK apakah ada phone card sebelum klik
                        # Cari text 'ID:' yang pasti ada di setiap phone card
                        phone_card_visible = False
                        try:
                            phone_id_el = page.locator("text=/ID:\\s*\\d+/").first
                            await phone_id_el.wait_for(state="visible", timeout=5000)
                            phone_card_visible = True
                            await websocket.send_json({"type": "log", "content": "Phone card terdeteksi! Melanjutkan klik..."})
                        except Exception:
                            await websocket.send_json({"type": "log", "content": "TIDAK ADA phone card aktif di grup ini. Akun mungkin expired. Bot dihentikan."})
                            return
                        
                        # Screenshot sebelum klik (debug)
                        await page.screenshot(path="before_click_phone.png")
                        
                        # BLIND CLICK langsung ke koordinat thumbnail phone
                        # Koordinat dari debug bounding_box: IMG x:31,y:112,w:123,h:220 → center X:92,Y:222
                        await websocket.send_json({"type": "log", "content": "Klik koordinat Phone (X:92, Y:222)..."})
                        await page.mouse.click(92, 222)
                        clicked = True
                        await websocket.send_json({"type": "log", "content": "Phone diklik! Menunggu WebRTC iframe muncul (8 detik)..."})
                        
                        if clicked:
                            await asyncio.sleep(8)
                            # Masuk ke dalam WebRTC Iframe
                            await websocket.send_json({"type": "log", "content": "Menunggu 10 detik untuk memuat Iframe WebRTC..."})
                            await websocket.send_json({"type": "log", "content": "Menembus iframe WebRTC..."})
                            try:
                                await websocket.send_json({"type": "log", "content": "Memulai SPAM KLIK Koordinat Iframe (X:215, Y:400) secara brutal..."})
                                
                                # SPAM KLIK Loop 10x selama 10 detik agar tombol play di iframe pasti kena
                                for i in range(10):
                                    await page.mouse.click(215, 400)
                                    await page.mouse.click(215, 420)
                                    await asyncio.sleep(1)
                                    
                                await websocket.send_json({"type": "log", "content": "Spam klik selesai! OS Android seharusnya mulai dimuat..."})
                                # Panggil AI Vision Autonomous State Machine
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
