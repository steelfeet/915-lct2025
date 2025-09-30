import os, sys
from tqdm import tqdm
import time, shutil, json, random, string
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

import numpy as np # linear algebra

import torch

import requests, json
import secret





from os.path import dirname, abspath
#директории основных модулей
BASE_DIR = dirname(abspath(__file__))

cache_dir = os.path.join("d:\\", "_models", "huggingface.co")

GEMMA_DIR = os.path.join("d:\\", "_vault", "06-Gemma", "data")
os.makedirs(GEMMA_DIR, exist_ok=True)


from transliterate import translit



for class_n in tqdm(os.listdir(GEMMA_DIR)):
    gemma_class_dir = os.path.join(GEMMA_DIR, class_n)
    for filename in os.listdir(gemma_class_dir):
        txt_path = os.path.join(gemma_class_dir, filename)
        if "en" in filename:
            os.remove(txt_path)
            continue
        
        if filename.endswith(".txt"):
            txt_path = os.path.join(gemma_class_dir, filename)

            en_street_text = ""
            with open(txt_path, 'r', encoding='utf-8') as file:
                ru_street_text = file.read()
            
            ru_street_list = ru_street_text.split(";")
            for ru_street_item in ru_street_list:
                en_street_item = translit(ru_street_item, language_code='ru', reversed=True)
                en_street_text += f"{en_street_item};"

            en_filename = f"en-{filename}"
            txt_path = os.path.join(gemma_class_dir, en_filename)
            with open(txt_path, "w", encoding='utf-8') as file:
                file.write(en_street_text)        
        


