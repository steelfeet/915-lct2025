import os, sys
from tqdm import tqdm
import time, shutil, json, random, string
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

import numpy as np # linear algebra



import requests, json
import secret





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

            prompt = {
            "modelUri": f"gpt://{secret.service_acc}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.9,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Дан результат распознования OCR названия улиц и переулков г. Новозыбков. Исправь неправильно распознанные названия. В ответе используй только название"
                },
                {
                    "role": "user",
                    "text": "Попевая упица"
                },
                {
                    "role": "assistant",
                    "text": """
                    Полевая улица
                    """
                },
                {
                    "role": "user",
                    "text": f""" {street_text} 
                    
                    """
                }]
            }


            url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {secret.api_key}"
            }



            response = requests.post(url, headers=headers, json=prompt)
            result_dict = json.loads(response.text)
            try:
                clear_street_text = result_dict["result"]["alternatives"][0]["message"]["text"]
            except:
                referat = "Error"    
                print(result_dict)


        except:
            pass
        clear_street_text = clear_street_text.strip()
        gemma_text = f"{clear_street_text}; "


        for i in range(len(x_list)):
            left = x_list[i]-10
            top = y_list[i]+3
            right = x_list[i]+40
            bottom = y_list[i]+25
            box = (left, top), (right, bottom)
            draw.rectangle((box), fill='green', outline='red')

            img_cropped = im_res.crop((left, top, right, bottom))
            enhancer = ImageEnhance.Contrast(img_cropped)
            # 3. Измените контраст
            # Значение > 1 увеличивает контраст, < 1 уменьшает
            contrast_factor = 1.5
            img_contrasted = enhancer.enhance(contrast_factor)
            grayscale_img = img_contrasted.convert('L')
            inverted_image = ImageOps.invert(grayscale_img)

            inverted_image.save(os.path.join(BASE_DIR, f"copy_{i}.jpg"))

            page_text = reader.readtext(os.path.join(BASE_DIR, f"copy_{i}.jpg"))
            try:
                print(page_text[0][1])
                gemma_text += f"{clear_street_text} {page_text[0][1]}; "
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
        


