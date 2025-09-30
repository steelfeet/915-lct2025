import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

import torch
from unsloth import FastModel


from PIL import Image, ImageDraw, ImageFont

os.environ["HF_TOKEN"] = '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'
print(os.environ["HF_TOKEN"])

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

DETECTED_DIR = "X:\\_vault\\олимпиады\\915-lct2025\\07-Monitor\\Характеристики"
DATA_DIR = "X:\\_vault\\олимпиады\\915-lct2025\\07-Monitor\\Санитарка"

DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'
print("device: ", DEVICE)
print()



cache_dir="D:\\_models\\huggingface.co"

model, tokenizer = FastModel.from_pretrained(
    # model_name = "unsloth/gemma-3-27b-it-unsloth-bnb-4bit", # Or "unsloth/gemma-3n-E2B-it"
    model_name = "unsloth/gemma-3n-E4B-it",
    dtype = None, # None for auto detection
    max_seq_length = 1024, # Choose any for long context!
    load_in_4bit = True,  # 4 bit quantization to reduce memory
    full_finetuning = False, # [NEW!] We have full finetuning now!
    cache_dir="D:\\_models\\huggingface.co"
)


from transformers import TextStreamer
# Helper function for inference
def do_gemma_3n_inference(model, messages, max_new_tokens = 128):
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt = True, # Must add for generation
        tokenize = True,
        return_dict = True,
        return_tensors = "pt",
    ).to("cuda")
    output = model.generate(
        **inputs,
        max_new_tokens = max_new_tokens,
        temperature = 1.0, top_p = 0.95, top_k = 64,
        streamer = TextStreamer(tokenizer, skip_prompt = True),
    )

    return output




# https://huggingface.co/docs/transformers/en/model_doc/gemma3
url_cow = "https://media.istockphoto.com/id/1192867753/photo/cow-in-berchida-beach-siniscola.jpg?s=612x612&w=0&k=20&c=v0hjjniwsMNfJSuKWZuIn8pssmD5h5bSN1peBd1CmH4="
url_cat = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"

messages =[
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "You are a helpful assistant."}
        ]
    },
    {
        "role": "user",
        "content": [
            {"type": "image", "url": os.path.join(DATA_DIR, "0cWwTCAiBaE.jpg")},
            {"type": "text", "text": "What damage is there on the tree only in the first photo? Сhoose from the list of examples below. Give me only the number as an answer."},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "1.jpg")},
            {"type": "text", "text": "1. Severe butt rot"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "2.jpg")},
            {"type": "text", "text": "2. severe stem rot"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "3.jpg")},
            {"type": "text", "text": "3. Mechanical damage to wood"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "4.jpg")},
            {"type": "text", "text": "4. Fruiting bodies of wood mushrooms"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "5.jpg")},
            {"type": "text", "text": "5. wood bark peeling"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "6.jpg")},
            {"type": "text", "text": "6. Dry branches more than 75%"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "7.jpg")},
            {"type": "text", "text": "7. Dead wood of the current year"},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "8.jpg")},
            {"type": "text", "text": "8. Dry branches more than 75% "},

            {"type": "image", "url": os.path.join(DETECTED_DIR, "9.jpg")},
            {"type": "text", "text": "9. wood bark peeling; 2. severe stem rot"},


        ]
    },
]

"""
            1. Severe butt rot //Комлевая гниль в сильной степени
            2. severe stem rot // стволовая гниль в сильной степени
            3. Dead wood // Сухостой
            4. hollow // обширное дупло
            5. Mechanical damage to wood // Механические повреждения
            6. Fruiting bodies of wood mushrooms // Плодовые тела
            7. Damaged by wood pests // Повереждено вредителями
            8. Dry branches more than 75% // Сухие ветви более 75 %
            9. wood bark peeling // Отслоение коры

"""

output = do_gemma_3n_inference(model, messages, max_new_tokens = 256)
print(tokenizer.decode(output[0], skip_special_tokens=True))