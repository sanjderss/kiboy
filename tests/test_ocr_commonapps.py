import pytesseract
from PIL import Image

def find_text_coordinates(image_path, target_text):
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if target_text.lower() in text.lower():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            center_x = x + w // 2
            center_y = y + h // 2
            print(f"Found '{text}' at X={center_x}, Y={center_y} (Box: {x},{y},{w},{h})")
            return center_x, center_y
            
    print(f"Text '{target_text}' not found.")
    return None

print("Searching for 'CommonApps'...")
find_text_coordinates('/home/codespace/.gemini/antigravity-cli/brain/4acaa28c-19c7-4065-a223-427ee91cae51/scratch/appstore.png', 'Common')
