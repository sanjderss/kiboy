import time
import requests
import os
import concurrent.futures
import random

PROXY_SOURCES = [
    # APIs
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc",
    "https://spys.me/proxy.txt",
    
    # Github Repositories
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/ErcinDedooglu/proxies/main/proxies/http.txt"
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
                # Cek kualitas IP menggunakan ip-api.com (filter hosting & proxy)
                ip = proxy.split(":")[0]
                check_r = requests.get(f"http://ip-api.com/json/{ip}?fields=hosting,proxy", timeout=3).json()
                if not check_r.get("hosting", True) and not check_r.get("proxy", False):
                    print(f"[Hunter] [+] Kualitas Tinggi (Residensial): {proxy}")
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
        futures = {executor.submit(test_proxy, p): p for p in candidates[:1000]} # Tes 1000 teratas tiap siklus
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
