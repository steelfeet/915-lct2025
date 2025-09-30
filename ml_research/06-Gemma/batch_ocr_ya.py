import os, sys
from tqdm import tqdm
import time, shutil, json, random, string
from PIL import Image, ImageDraw, ImageFont

import numpy as np # linear algebra



import language_tool_python
tool = language_tool_python.LanguageTool('ru-RU')


from os.path import dirname, abspath
#директории основных модулей
BASE_DIR = dirname(abspath(__file__))

CLASSES_DIR = os.path.join("d:\\", "_vault", "03-YaMap", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

GEMMA_DIR = os.path.join("d:\\", "_vault", "06-Gemma", "data")
os.makedirs(GEMMA_DIR, exist_ok=True)


import easyocr
reader = easyocr.Reader(['ru','en']) # this needs to run only once to load the model into memory

sample_path = os.path.join(BASE_DIR, "sample-3.png")
im_sample = Image.open(sample_path)


for class_n in tqdm(os.listdir(CLASSES_DIR)):
    class_dir = os.path.join(CLASSES_DIR, class_n)
    gemma_class_dir = os.path.join(GEMMA_DIR, class_n)
    os.makedirs(gemma_class_dir, exist_ok=True)
    
    for filename in os.listdir(class_dir):
        delta_colors = []
        x_list = []
        y_list = []

        res_path = os.path.join(class_dir, filename)
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
            tokens = street_text.split(" ")
            clear_street_text = ""
            for token in tokens:
                matches = tool.check(token)
                if len(matches) > 0:
                    match = matches[0]
                    clear_street_text += f"{match.replacements[0]} "
                else:
                    clear_street_text += f"{token} "
        except:
            pass
        clear_street_text = clear_street_text.strip()
        gemma_text = f"{clear_street_text}; "


        for i in range(len(x_list)):
            box = (x_list[i]-20, y_list[i]-3), (x_list[i]+40, y_list[i]+30)
            draw.rectangle((box), fill='green', outline='red')

            img_cropped = im_res.crop((x_list[i]-20, y_list[i]-3, x_list[i]+40, y_list[i]+30))
            img_cropped.save(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
            page_text = reader.readtext(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
            try:
                print(page_text[0][1])
                gemma_text += f"{street_text} {page_text[0][1]}; "
            except:
                pass

            
        copy_path = os.path.join(gemma_class_dir, filename)
        im_copy.save(copy_path)


        txt_filename = filename.replace("jpg", "txt")
        txt_path = os.path.join(gemma_class_dir, txt_filename)
        gemma_text = gemma_text.strip()
        gemma_text += gemma_text.replace(" ", "_")
        with open(txt_path, "w", encoding='utf-8') as file:
            file.write(gemma_text)        
        


