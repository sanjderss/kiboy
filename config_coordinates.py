"""
Konfigurasi Koordinat (X, Y) untuk navigasi UI WebRTC Cloud Phone.
Ubah nilai X dan Y di sini jika ada perubahan posisi UI pada layar Cloud Phone.
"""

COORDS = {
    # == DASHBOARD ==
    "PHONE_THUMBNAIL": {"x": 92, "y": 222}, # Koordinat klik gambar thumbnail phone list
    "WEBRTC_IFRAME": {"x": 215, "y": 465},  # Tombol '▶ 开始操作' - diukur dari screenshot nyata (Y:460-470)

    # == DALAM CLOUD PHONE (WEBRTC) ==
    "APP_STORE_ICON": {"x": 75, "y": 540},  # Koordinat Icon App Store di Home Screen (Diperbarui via OCR/Layout)
    "TAB_COMMON_APPS": {"x": 178, "y": 49}, # Koordinat Tab 'CommonApps' di dalam App Store
    "INSTALL_CHROME": {"x": 77, "y": 457},  # Koordinat tombol Download/Install Chrome
    "POPUP_INSTALL": {"x": 361, "y": 667},  # Koordinat tombol Install pada popup Android
    "OPEN_CHROME": {"x": 77, "y": 457},     # Koordinat tombol Open (setelah Chrome terinstall)
    "HOME_BUTTON": {"x": 104, "y": 906}     # Tombol Home navigasi bawah Android (X:104 Y:906)
}
