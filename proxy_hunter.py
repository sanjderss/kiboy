import time
import requests
import os
import concurrent.futures
import random

PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt"
]

ACTIVE_PROXIES_FILE = "data/active_proxies.txt"
USED_PROXIES_FILE = "data/used_proxies.txt"
TARGET_POOL_SIZE = 10

def ensure_dirs():
    os.makedirs("data", exist_ok=True)
    for f in [ACTIVE_PROXIES_FILE, USED_PROXIES_FILE]:
        if not os.path.exists(f):
            open(f, 'w').close()

def get_used_proxies():
    with open(USED_PROXIES_FILE, "r") as f:
        return set(f.read().splitlines())

def get_active_proxies():
    with open(ACTIVE_PROXIES_FILE, "r") as f:
        return set(f.read().splitlines())

def save_active_proxies(proxies_set):
    with open(ACTIVE_PROXIES_FILE, "w") as f:
        f.write("\n".join(proxies_set) + "\n")

def scrape_raw_proxies():
    all_proxies = set()
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                proxies = [p.strip() for p in r.text.split('\n') if p.strip()]
                all_proxies.update(proxies)
        except Exception as e:
            print(f"[Hunter] Gagal scrape {url}: {e}")
    return list(all_proxies)

def test_proxy(proxy):
    try:
        start = time.time()
        # Test lebih ketat, timeout pendek
        r = requests.get("https://www.hippocloudphone.com/index.html", proxies={"http": proxy, "https": proxy}, timeout=3)
        if r.status_code == 200 and len(r.content) > 500:
            if (time.time() - start) < 2.5:
                return proxy
    except:
        pass
    return None

def hunt_proxies():
    print("[Hunter] Memulai siklus perburuan proxy...")
    ensure_dirs()
    
    active = get_active_proxies()
    
    if len(active) >= TARGET_POOL_SIZE:
        print(f"[Hunter] Kolam proxy penuh ({len(active)}/{TARGET_POOL_SIZE}). Tidur 10 detik.")
        time.sleep(10)
        return
        
    print(f"[Hunter] Kolam kurang ({len(active)}/{TARGET_POOL_SIZE}). Mencari mangsa...")
    used = get_used_proxies()
    raw_proxies = scrape_raw_proxies()
    
    # Filter out used and already active
    candidates = [p for p in raw_proxies if p not in used and p not in active]
    random.shuffle(candidates)
    
    print(f"[Hunter] Mengetes {len(candidates)} kandidat dengan 30 Pekerja...")
    
    needed = TARGET_POOL_SIZE - len(active)
    found = set()
    
    # Gunakan thread pool untuk mengetes massal
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(test_proxy, p): p for p in candidates[:200]} # Tes 200 teratas saja tiap siklus
        for future in concurrent.futures.as_completed(futures):
            p = future.result()
            if p:
                found.add(p)
                print(f"[Hunter] [+] Proxy Lolos Uji: {p}")
                if len(found) >= needed:
                    # Cancel sisa pekerjaan
                    break 
                    
    if found:
        # Update file
        current_active = get_active_proxies()
        current_active.update(found)
        save_active_proxies(current_active)
        print(f"[Hunter] Berhasil menambahkan {len(found)} proxy ke kolam.")
    else:
        print("[Hunter] Gagal menemukan proxy yang cukup cepat di siklus ini.")

if __name__ == "__main__":
    print("=== [ HUNTER PROXY AKTIF ] ===")
    while True:
        try:
            hunt_proxies()
        except Exception as e:
            print(f"[Hunter] Error: {e}")
        time.sleep(3)
