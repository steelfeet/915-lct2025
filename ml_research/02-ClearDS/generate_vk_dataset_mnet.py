import os, sys, cv2
import csv, json, shutil
import requests, time
from tqdm import tqdm
from urllib.parse import urlparse

import numpy as np

import torch
from PIL import Image, ImageDraw, ImageFont

import torch
import torch.nn as nn
import torchvision

import albumentations as A
from albumentations.pytorch import ToTensorV2



IM_SIZE = 512

DB_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(DB_DIR)
import geo_db, safe_request

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
import get_class

MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")
MODEL_NAME = "mnet_good-bad"
BEST_MODEL_NAME = f"{MODEL_NAME}_best.pth"
BEST_MODEL_PATH = os.path.join(MODEL_DIR, BEST_MODEL_NAME)

CLASSES_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)



ValidTransform = A.Compose([
    A.Resize(IM_SIZE,IM_SIZE),
    A.CenterCrop(IM_SIZE,IM_SIZE),
    A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ToTensorV2()])



model = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1)

#перенастраиваем модель под наши классы
for param in model.parameters():
    param.requires_grad = False

n_inputs = model.classifier[0].in_features
last_layer = nn.Linear(n_inputs, 3)
model.classifier = last_layer
model.load_state_dict(torch.load(BEST_MODEL_PATH))
model.eval()

device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
model = model.to(device)
torch.cuda.empty_cache()
print("device: ", device)
print()

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

        try:
            img_pil = Image.open(orig_photo_local_path)
            im_new = cv2.imread(orig_photo_local_path)
        
            input = ValidTransform(image=im_new)
            # unsqueeze batch dimension, in case you are dealing with a single image
            input = input["image"].unsqueeze(0)
            input = input.to(device)
            # Get prediction
            with torch.no_grad():
                logits = model(input)
            """
            ps = torch.exp(logits)        
            _, top_class = ps.topk(1, dim=1)
            """
            top_class = logits.argmax(dim=1)
            predicted_class = int(top_class.cpu()[0])


            if predicted_class == 1:
                detected_n += 1
                orig_photo_local_dir = os.path.join(CLASSES_DIR, str(class_n))
                os.makedirs(orig_photo_local_dir, exist_ok=True)
                orig_photo_local_path = os.path.join(orig_photo_local_dir, orig_photo_filename)
                img_pil.save(orig_photo_local_path)
            #else:
                #img_pil.save(os.path.join(BASE_DIR, "temp", orig_photo_filename))
        except:
            pass
    # print()    
    # print(f"current_detected_n: {current_detected_n}; detected_n: {detected_n}; average_detected: {detected_n / len(db_images_all)}; ")


print()    
print(f"detected_n: {detected_n}; average_detected: {detected_n / len(db_images_all)}; ")
