import pytesseract
from PIL import Image
import sys

img = Image.open(sys.argv[1])
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if len(text) > 2:
        print(f"'{text}' at ({data['left'][i]}, {data['top'][i]}) w={data['width'][i]} h={data['height'][i]} conf={data['conf'][i]}")
