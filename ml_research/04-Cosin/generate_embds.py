# -*- encoding: utf-8 -*-
# 
import os, urllib, sys
from os.path import dirname, abspath

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import random, time
from datetime import datetime
import requests
from requests.exceptions import ProxyError

import time
import json

from sentence_transformers import SentenceTransformer
from PIL import Image



BASE_DIR = dirname(abspath(__file__))
sys.path.insert(1, BASE_DIR)
APP_DIR = dirname(BASE_DIR)
sys.path.append(APP_DIR)



CLASSES_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
RESULT_DIR = os.path.join("d:\\", "_vault", "04-Cosin")
os.makedirs(RESULT_DIR, exist_ok=True)
model_name = 'clip-ViT-B-16'


st_model = SentenceTransformer(model_name)
def vectorize_img(img_path, model=st_model):
    img = Image.open(img_path)
    return st_model.encode(img)


# функция построения эмбеддингов
def create_images_db(image_path, model=st_model):
    if os.path.isfile(image_path):
        emb = vectorize_img(image_path, model)
    return emb


result_list = []
for class_n in tqdm(os.listdir(CLASSES_DIR)):
    class_dir = os.path.join(CLASSES_DIR, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)
        emb = create_images_db(current_file_path)
        result_item = {}
        result_item["class_n"] = class_n
        result_item["filename"] = filename
        result_item["emb"] = emb.tolist()

        result_list.append(result_item)



result_path = os.path.join(RESULT_DIR, "result.json")
with open(result_path, "w") as f:
    json.dump(result_list, f, indent=4)
