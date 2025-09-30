import os, sys
from tqdm import tqdm
import time, shutil, json, random, string
from PIL import Image, ImageDraw, ImageFont

import numpy as np # linear algebra


from os.path import dirname, abspath
#директории основных модулей
APP_DIR = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.insert(1, APP_DIR)
APP_DIR = dirname(APP_DIR)
sys.path.append(APP_DIR)


BASE_DIR = dirname(abspath(__file__))


def random_string(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))


"""
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

for i in range(4):
    img_cropped = Image.open(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
    # img_cropped = Image.open(os.path.join(BASE_DIR, "0.png"))
    page_text = pytesseract.image_to_string(img_cropped, lang='rus')
    print(page_text)
exit()
"""

import easyocr
reader = easyocr.Reader(['ru','en']) # this needs to run only once to load the model into memory



delta_colors = []
x_list = []
y_list = []

start_time = time.time()
sample_path = os.path.join(BASE_DIR, "sample-3.png")
im_sample = Image.open(sample_path)

res_path = os.path.join(BASE_DIR, "v0-52.518000-52.518000-180.jpg")
im_res = Image.open(res_path)
for x in range(im_res.width- im_sample.width):
    for y in range(im_res.height - im_sample.height):
        # верхние пиксели
        delta_color_1 = 0
        y_sam = 0
        for x_sam in range(im_sample.width):
            r_sam, g_sam, b_sam = im_sample.getpixel((x_sam, y_sam))
            r_res, g_res, b_res = im_res.getpixel((x+x_sam, y+y_sam))
            delta_color_1 += (r_sam-r_res)**2 + (g_sam-g_res)**2 + (b_sam-b_res)**2
        
        # перебираем вертикальные пиксели
        delta_color = 0
        if delta_color_1 < 300:
            for x_sam in range(im_sample.width):
                for y_sam in range(im_sample.height):
                    r_sam, g_sam, b_sam = im_sample.getpixel((x_sam, y_sam))
                    r_res, g_res, b_res = im_res.getpixel((x+x_sam, y+y_sam))
                    delta_color += (r_sam-r_res)**2 + (g_sam-g_res)**2 + (b_sam-b_res)**2

            if delta_color < 4000:
                # расстояние с уже найденными точками
                if len(x_list) > 0:
                    min_delta_l = 1000000000000
                    delta_l = 0
                    for i in range(len(x_list)):
                        delta_l = (x_list[i]-x)**2 + (y_list[i]-y)
                        if delta_l < min_delta_l:
                            min_delta_l = delta_l

                    if min_delta_l > 1000:
                        x_list.append(x)
                        y_list.append(y)
                else:
                    x_list.append(x)
                    y_list.append(y)

im_copy = im_res.copy()
draw = ImageDraw.Draw(im_copy)

street_box = (800, 5), (1100, 60)
draw.rectangle((street_box), fill='green', outline='red')
img_cropped = im_res.crop((800, 5, 1100, 60))
img_cropped.save(os.path.join(BASE_DIR, f"copy_s.jpg"))
page_text = reader.readtext(os.path.join(BASE_DIR, f"copy_s.jpg"))
try:
    street_text = page_text[0][1]
except:
    pass
street_text = str(street_text).replace("упица", "улица")


for i in range(len(x_list)):
    box = (x_list[i]-20, y_list[i]-3), (x_list[i]+40, y_list[i]+30)
    draw.rectangle((box), fill='green', outline='red')

    img_cropped = im_res.crop((x_list[i]-20, y_list[i]-3, x_list[i]+40, y_list[i]+30))
    img_cropped.save(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
    page_text = reader.readtext(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
    try:
        print(page_text[0][1])
    except:
        pass


copy_path = os.path.join(BASE_DIR, "copy.png")
im_copy.save(copy_path)

end_time = time.time()

print(f"time: {end_time - start_time} с.")
print(f"images: {len(x_list)}")
print(x_list)
print(y_list)
