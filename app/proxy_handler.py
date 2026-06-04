import os
import random

ACTIVE_PROXIES_FILE = "data/active_proxies.txt"
USED_PROXIES_FILE = "data/used_proxies.txt"

def get_working_proxy():
    """Mengambil satu proxy dari kolam (pool) yang sudah disiapkan oleh proxy_hunter."""
    if not os.path.exists(ACTIVE_PROXIES_FILE):
        return None
        
    with open(ACTIVE_PROXIES_FILE, "r") as f:
        active = f.read().splitlines()
        
    if not active:
        return None
        
    # Ambil 1 proxy teratas (atau random)
    chosen_proxy = active[0]
    
    # Hapus dari active pool karena akan kita pakai sekarang
    active.remove(chosen_proxy)
    with open(ACTIVE_PROXIES_FILE, "w") as f:
        f.write("\n".join(active) + ("\n" if active else ""))
        
    print(f"[Bot] Mengkonsumsi proxy dari kolam: {chosen_proxy}")
    return chosen_proxy

def mark_proxy_used(proxy):
    """Menandai proxy agar tidak pernah dicari/dipakai lagi oleh hunter."""
    os.makedirs("data", exist_ok=True)
    with open(USED_PROXIES_FILE, "a") as f:
        f.write(f"{proxy}\n")
    print(f"[Bot] Proxy {proxy} telah dimasukkan ke daftar hitam (sekali pakai).")
