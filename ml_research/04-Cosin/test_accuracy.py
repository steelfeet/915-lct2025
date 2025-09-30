
import os, random
import csv, json, shutil
import glob
import requests

from tqdm import tqdm


from sentence_transformers import SentenceTransformer
from scipy import spatial
from PIL import Image
import pandas as pd
import numpy as np
import copy
import os


from sentence_transformers import SentenceTransformer
from PIL import Image

model_name = 'clip-ViT-B-16'
st_model = SentenceTransformer(model_name)

CLASSES_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
RESULT_DIR = os.path.join("d:\\", "_vault", "04-Cosin")


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


CLASSES_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
RESULT_DIR = os.path.join("d:\\", "_vault", "04-Cosin")


# загружаем нашу базу эмббедингов
result_path = os.path.join(RESULT_DIR, "result.json")
with open(result_path, 'r') as file:
    images_db = json.load(file)


# очищаем config.UPLOAD_DIR
images_n = 0
accuracy_n = 0
for class_n in tqdm(os.listdir(CLASSES_DIR)):
    class_dir = os.path.join(CLASSES_DIR, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)
        sorted_list = found_similar_images(current_file_path, images_db, 2)

        images_n += 1
        similar_class = sorted_list[0]["class_n"]
        # отсекаем то-же самое изображение
        """
        if sorted_list[0]["filename"] == filename:
            similar_class = sorted_list[1]["class_n"]
        """
        if int(class_n) == int(similar_class):
            accuracy_n += 1

formatted_accuracy = accuracy_n/images_n
print(f"images_n: {images_n}; accuracy_n: {accuracy_n}, accuracy: {formatted_accuracy:.6f}")
