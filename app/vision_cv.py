import cv2
import numpy as np
import io
import os
from PIL import Image

def find_image_on_screen(screenshot_bytes, template_path, threshold=0.8):
    """
    Menggunakan OpenCV Template Matching untuk mencari sebuah gambar di dalam screenshot.
    Mengembalikan (x, y) koordinat TENGAH dari gambar jika ditemukan, atau None jika gagal.
    """
    if not os.path.exists(template_path):
        print(f"[OpenCV] Error: Template gambar tidak ditemukan: {template_path}")
        return None

    # Load screenshot dari bytes
    nparr = np.frombuffer(screenshot_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Load template
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"[OpenCV] Error: Gagal membaca template: {template_path}")
        return None

    # Template matching
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    
    # Ambil nilai probabilitas kecocokan terbesar
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        # max_loc adalah sudut kiri atas gambar. Kita cari titik tengahnya untuk diklik
        template_h, template_w = template.shape[:2]
        center_x = max_loc[0] + (template_w // 2)
        center_y = max_loc[1] + (template_h // 2)
        print(f"[OpenCV] FOUND {template_path} at X:{center_x} Y:{center_y} (Confidence: {max_val:.2f})")
        return {"x": center_x, "y": center_y}
    else:
        print(f"[OpenCV] NOT FOUND {template_path} (Confidence: {max_val:.2f} < {threshold})")
        return None
