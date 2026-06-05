# 🧠 AI Logic — Cara Mikir Bot (IF / THEN State Machine)

## Konsep Dasar
Bot menggunakan **State Machine** berbasis **OCR Vision**. Setiap detik, bot:
1. Ambil screenshot layar
2. Baca semua teks dengan OCR (Tesseract)
3. Cocokkan teks dengan **Rules** di bawah
4. Tentukan **STATE** (posisi bot sekarang)
5. Eksekusi **ACTION** berdasarkan state

---

## 🔀 Flow Decision Tree

```
[Bot Mulai]
    │
    ▼
┌─────────────────────────┐
│ SCREENSHOT + OCR SCAN   │ ◄──── Loop setiap 1 detik
└───────────┬─────────────┘
            │
            ▼
    ┌───────────────────┐
    │ Teks apa di layar?│
    └───────┬───────────┘
            │
    ┌───────┼──────────────────────────────────┐
    │       │       │       │       │          │
    ▼       ▼       ▼       ▼       ▼          ▼
  HOME   APP_STORE  INSTALL  DOWNLOADING  CHROME   UNKNOWN
```

---

## 📋 Rules Table (config_vision.py)

| # | STATE              | IF (Teks di Layar)                        | THEN (Aksi)                          |
|---|--------------------|--------------------------------------------|--------------------------------------|
| 1 | `HOME_SCREEN`      | "virtual" AND "location"                   | Cari & klik "App Store" / "RPA"      |
| 2 | `APP_STORE`        | "commonapps" OR "tools" OR "store"         | Klik tab "CommonApps" → Install Chrome |
| 3 | `INSTALL_POPUP`    | "application?" OR "install this"           | Klik tombol "Install" di popup       |
| 4 | `APP_STORE_DOWNLOADING` | "installing" OR "downloading" OR "cancel" | Tunggu sampai selesai (jangan klik)  |
| 5 | `OS_INSTALLING`    | (dari config, installing tanpa commonapps) | Tunggu APK terpasang                 |
| 6 | `CHROME_FRE`       | "accept" AND "continue"                    | Klik "Accept & Continue"             |
| 7 | `CHROME_SYNC`      | "no" AND "thanks"                          | Klik "No Thanks" → SELESAI!          |
| 8 | `CHROME_MAIN`      | "search" OR "google"                       | 🎉 GOAL TERCAPAI!                   |
| 9 | `UNKNOWN`          | (tidak cocok semua di atas)                | Coba OCR pasif, tunggu loading       |

---

## 🔁 Detail IF/THEN per State

### STATE: HOME_SCREEN
```
JIKA halaman = Home Screen (ada teks "virtual location"):
    MAKA:
        1. Cari teks "store" / "app" / "rpa" dengan OCR
        2. JIKA ketemu → Klik teks tersebut (offset Y -30 ke atas untuk klik icon)
        3. JIKA tidak ketemu → Fallback klik koordinat APP_STORE_ICON (X:93, Y:520)
        4. Tunggu 5 detik
```

### STATE: APP_STORE
```
JIKA halaman = App Store (ada teks "commonapps" / "tools" / "store"):
    MAKA:
        1. Cek apakah ada teks "open" di layar
        2. JIKA ada "open" → Chrome sudah terinstall, klik "Open"
        3. JIKA tidak ada "open":
            a. Klik tab "CommonApps" (OCR atau fallback X:178, Y:49)
            b. Cari tombol "Install" / "Download"
            c. Klik untuk mulai download Chrome
```

### STATE: INSTALL_POPUP
```
JIKA muncul popup install (ada teks "application?" / "install this"):
    MAKA:
        1. Klik tombol Install di popup (koordinat X:361, Y:667)
        2. Tunggu 3 detik
```

### STATE: APP_STORE_DOWNLOADING / OS_INSTALLING
```
JIKA sedang download/install (ada teks "installing" / "downloading" / "cancel"):
    MAKA:
        1. JANGAN KLIK APA-APA
        2. Tunggu 2 detik
        3. Loop kembali ke scan OCR
```

### STATE: CHROME_FRE (First Run Experience)
```
JIKA Chrome baru pertama kali dibuka (ada teks "accept" + "continue"):
    MAKA:
        1. Cari teks "Accept" dengan OCR
        2. Klik tombol Accept
        3. Tunggu 3 detik
```

### STATE: CHROME_SYNC
```
JIKA Chrome minta sync (ada teks "no" + "thanks"):
    MAKA:
        1. Cari teks "No" dengan OCR
        2. Klik "No Thanks"
        3. Tunggu 3 detik
        4. RETURN TRUE → Misi selesai!
```

### STATE: CHROME_MAIN
```
JIKA sudah di halaman utama Chrome (ada teks "search" / "google"):
    MAKA:
        1. Log: "GOAL TERCAPAI!"
        2. RETURN TRUE → Chrome siap digunakan
```

### STATE: UNKNOWN
```
JIKA tidak ada teks yang cocok dengan semua rules di atas:
    MAKA:
        1. Coba OCR pasif: cari "store" / "app" / "rpa" 
        2. JIKA ketemu → Klik (artinya ini Home Screen tapi belum sempurna ter-detect)
        3. JIKA tidak ketemu → Tunggu 2 detik (kemungkinan masih loading/booting)
        4. Loop kembali
```

---

## 🎯 Prioritas Deteksi

Rules di-evaluate **dari atas ke bawah** (urutan di `VISION_CONFIG_RULES`). 
Yang pertama cocok akan dipakai. Urutan penting!

1. `CHROME_FRE` ← Paling spesifik (accept + continue)
2. `CHROME_SYNC` ← Spesifik (no + thanks)  
3. `INSTALL_POPUP` ← Popup sistem
4. `APP_STORE_DOWNLOADING` ← Status download
5. `APP_STORE` ← Halaman store
6. `HOME_SCREEN` ← Halaman utama
7. `CHROME_MAIN` ← Chrome sudah buka

---

## 🔧 Cara Menambah Rule Baru

Edit file `config_vision.py`, tambahkan entry baru ke `VISION_CONFIG_RULES`:

```python
{
    "state_name": "NAMA_STATE_BARU",
    "keywords": [["kata1", "kata2"], ["kata_alternatif"]],
    "action_log": "Deskripsi aksi yang dilakukan..."
}
```

Lalu tambahkan handler di `vision_navigator.py` → fungsi `navigate_to_chrome()`:

```python
elif state == "NAMA_STATE_BARU":
    # Aksi yang dilakukan
    await click_by_ocr(page, websocket, ["target"], "Nama Aksi", delay_after=3)
```

---

## 📐 Koordinat Klik (config_coordinates.py)

| Elemen              | X   | Y   | Keterangan                    |
|---------------------|-----|-----|-------------------------------|
| PHONE_THUMBNAIL     | 92  | 222 | Klik thumbnail di phone list  |
| WEBRTC_IFRAME       | 215 | 465 | Tombol Play ▶ 开始操作         |
| APP_STORE_ICON      | 93  | 520 | Icon App Store di Home Screen |
| TAB_COMMON_APPS     | 178 | 49  | Tab CommonApps di App Store   |
| INSTALL_CHROME      | 77  | 457 | Tombol Install Chrome         |
| POPUP_INSTALL       | 361 | 667 | Konfirmasi Install popup      |
| OPEN_CHROME         | 77  | 457 | Tombol Open Chrome            |
| HOME_BUTTON         | 104 | 906 | Tombol Home navigasi bawah    |

---

## ⚡ Metode Klik

1. **OCR Click** (Prioritas): Baca teks → temukan posisi → klik tengah teks (offset Y -30)
2. **Hardcoded Click** (Fallback): Pakai koordinat tetap dari `config_coordinates.py`
3. **Sweep Click**: Klik berkali-kali di area (untuk tombol yang susah di-target)
