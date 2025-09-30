import numpy as np # linear algebra

import torch
import torch.nn as nn
import torchvision
from torch.utils.data import Dataset, DataLoader, random_split
import torch.optim.lr_scheduler as lr_scheduler

import albumentations as A
from albumentations.pytorch import ToTensorV2

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image
from sentence_transformers import SentenceTransformer
from scipy import spatial


from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")

processing_title = "GeoGuessr ViT-Cos #1"
processing_desc = "Определение класса местности по минимальному косинусному расстоянию"

processing_item = db.session.query(db.Monitor_Image_Processing_Types).filter(db.Monitor_Image_Processing_Types.title==processing_title).first()
if processing_item == None:
    # добавляем тип обработки
    processing_item = db.Monitor_Image_Processing_Types(
        title=processing_title, 
        desc=processing_desc 
    )
    db.session.add(processing_item)
    db.session.flush()
    db.session.refresh(processing_item)
    db.session.commit()


processing_id = processing_item.id
print(f"processing_id: {processing_id}") #4







RESULT_DIR = os.path.join("d:\\", "_vault", "04-Cosin")
os.makedirs(RESULT_DIR, exist_ok=True)
model_name = 'clip-ViT-B-16'

st_model = SentenceTransformer(model_name)


# функция сортировки 
def order_of_item(item):
    return float(item["cos_dist"])


def calculate_cos_dist(emb_a: np.array, emb_b: np.array) -> float:
    result_distance = spatial.distance.cosine(emb_a, emb_b)
    return result_distance


def found_similar_images(input_img_path: str, images_db, n: int=2):
    similar_classes = []
    emb_b = vectorize_img(input_img_path)

    for result_item in images_db:
        emb_a = np.array(result_item["emb"])
        cos_dist = calculate_cos_dist(emb_a, emb_b)
        similar_item = {}
        similar_item["class_n"] = result_item["class_n"]
        similar_item["cos_dist"] = cos_dist
        similar_item["filename"] = result_item["filename"]

        similar_classes.append(similar_item)

    # сортируем
    sorted_list = sorted(similar_classes, key=order_of_item)

    return sorted_list[:n]


def vectorize_img(img_path, model=st_model):
    img = Image.open(img_path)
    return model.encode(img)














# загружаем нашу базу эмббедингов
result_path = os.path.join(RESULT_DIR, "result.json")
with open(result_path, 'r') as file:
    images_db = json.load(file)


preview_items = db.session.query(db.Monitor_Previews).all()
for preview_item in tqdm(preview_items):
    image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_item.id).all()
    for image_item in image_items:
        # обрабатывали ли изображение этим процессингом
        image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==processing_id)).first()            
        if image_status_item == None:
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            sorted_list = found_similar_images(full_image_path, images_db, 5)

            # добавляем статусы изображению
            for similar_item in sorted_list:
                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="class_n",
                    value=str(similar_item["class_n"])
                )
                db.session.add(image_status_item)

                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="cos_dist",
                    value=str(similar_item["cos_dist"])
                )
                db.session.add(image_status_item)

                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="filename",
                    value=similar_item["filename"]
                )
                db.session.add(image_status_item)


    db.session.commit()


print(f"success")