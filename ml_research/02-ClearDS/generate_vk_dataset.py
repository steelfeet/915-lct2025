import os, sys, random
import csv, json, shutil
import requests, time
from tqdm import tqdm
from urllib.parse import urlparse

import numpy as np

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection


DB_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(DB_DIR)
import geo_db, safe_request

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
import get_class


CLASSES_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

model_id = "IDEA-Research/grounding-dino-base"
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

processor = AutoProcessor.from_pretrained(model_id, cache_dir=MODEL_PATH)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=MODEL_PATH).to(DEVICE)
print("device: ", DEVICE)

full_prompt = "building . tree ."

labels_list = full_prompt.split(".")
print(f"labels count: {len(labels_list)}")

with open(os.path.join(BASE_DIR, 'classes.json'), 'r') as file:
    classes_list = json.load(file)



# список уже скачанных файлов, чтобы не скачивать заново (а в какой класс мы его сохранили - неизвестно)
CLASSES_DIR_1 = os.path.join("d:\\", "_vault", "01-GeoGuessr", "data")
files_dict = {}
for class_n in os.listdir(CLASSES_DIR_1):
    class_dir = os.path.join(CLASSES_DIR_1, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)
        files_dict[os.path.basename(current_file_path)] = current_file_path

detected_n = 0
db_images_all = geo_db.session.query(geo_db.DonorsDataGeo).filter(geo_db.DonorsDataGeo.donor_domain == "vk.ru").all()
print(f"images count: {len(db_images_all)}")
for current_image in tqdm(db_images_all):
    class_n = get_class.check_class(classes_list, current_image.lat , current_image.long)
   
    orig_photo_filename = os.path.basename(urlparse(current_image.image_url).path)
    if os.path.basename(orig_photo_filename) in files_dict.keys():
        orig_photo_local_path = files_dict[os.path.basename(orig_photo_filename)]
        
        img_pil = Image.open(orig_photo_local_path)
        current_detected_n = 0
        for label_text in labels_list:

            inputs = processor(images=img_pil, text=f"{label_text} .", return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)

            bbox_info = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                # box_threshold=0.4,
                text_threshold=0.3,
                target_sizes=[img_pil.size[::-1]]
            )

            bbox_info[0]['boxes'] = bbox_info[0]['boxes'].cpu().numpy()
            bbox_info[0]['scores'] = bbox_info[0]['scores'].cpu().numpy()
            

            if len(bbox_info[0]['boxes']) > 0:
                current_detected_n += 1


        if current_detected_n == 2:
            detected_n += 1
            orig_photo_local_dir = os.path.join(CLASSES_DIR, str(class_n))
            os.makedirs(orig_photo_local_dir, exist_ok=True)
            orig_photo_local_path = os.path.join(orig_photo_local_dir, orig_photo_filename)
            img_pil.save(orig_photo_local_path)
        else:
            img_pil.save(os.path.join(BASE_DIR, "temp", orig_photo_filename))

    # print()    
    # print(f"current_detected_n: {current_detected_n}; detected_n: {detected_n}; average_detected: {detected_n / len(db_images_all)}; ")


print()    
print(f"detected_n: {detected_n}; average_detected: {detected_n / len(db_images_all)}; ")
