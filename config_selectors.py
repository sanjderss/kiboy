# Daftar selector untuk elemen-elemen di Hippo Cloud Phone
HIPPO_SELECTORS = {
    # Selector untuk kontainer utama/grup
    "group_trial": "text=试用分组",
    
    # Menggunakan selector lama yang sudah terbukti WORK
    # Jika sesekali salah menekan chat, usahakan memakai nth(0) atau first() di bot_engine
    "device_primary": ".device-item, .phone-item, .device-list .item",
    "device_fallback_preview": "text=预览, text=Preview, text=Enter",
    "device_fallback_box": "uni-image, img, .item, .box" 
}
