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


device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
print("device: ", device)
print()

from transformers import M2M100ForConditionalGeneration, AutoTokenizer
# model_name_2 = 'utrobinmv/m2m_translate_en_ru_zh_large_4096'
model_name_2 = os.path.join(cache_dir, "m2m_translate_en_ru_zh_large_4096")
model_2 = M2M100ForConditionalGeneration.from_pretrained(model_name_2)
tokenizer_2 = AutoTokenizer.from_pretrained(model_name_2)

model_2.eval()
model_2.to(device)

def translate_2en(input_text) -> str:
    # translate Russian to English
    prefix = 'translate to en: '
    src_text = prefix + input_text

    input_ids = tokenizer_2(src_text, return_tensors="pt")
    generated_tokens = model_2.generate(**input_ids.to(device))

    result = tokenizer_2.batch_decode(generated_tokens, skip_special_tokens=True)

    return result[0]



import glob
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
                # переводим только без _
                if not "_" in ru_street_item:
                    en_street_item = translate_2en(ru_street_item).strip()
                    if len(en_street_item) > 3:
                        en_street_text += f"{en_street_item};"

            en_filename = f"en-{filename}"
            txt_path = os.path.join(gemma_class_dir, en_filename)
            with open(txt_path, "w", encoding='utf-8') as file:
                file.write(en_street_text)        
        


