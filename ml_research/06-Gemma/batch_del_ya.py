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


for class_n in tqdm(os.listdir(GEMMA_DIR)):
    gemma_class_dir = os.path.join(GEMMA_DIR, class_n)
    
    for filename in os.listdir(gemma_class_dir):
        res_path = os.path.join(gemma_class_dir, filename)
        if filename.endswith(".jpg"):
            im_res = Image.open(res_path)
            im_copy = im_res.copy()
            draw = ImageDraw.Draw(im_copy)

            street_box = (20, 10), (250, 60)
            draw.rectangle((street_box), fill='green', outline='red')
            copy_path = os.path.join(BASE_DIR, filename)
            im_copy.save(res_path)


        


