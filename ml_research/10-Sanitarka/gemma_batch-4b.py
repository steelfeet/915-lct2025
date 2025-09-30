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


result_list = []

# https://huggingface.co/docs/transformers/en/model_doc/gemma3

for filename in os.listdir(DATA_DIR):
    if ".jpg" in filename.lower():
        result_item = {}
        result_item['filename'] = filename
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
                    {"type": "image", "url": os.path.join(DATA_DIR, filename)},
                    # {"type": "image", "url": url_cat},
                    {"type": "text", "text": """What damage is there on the tree? Select from the list below. Give me only the number as an answer.
                    1. Severe butt rot
                    2. severe stem rot
                    4. Dead wood
                    3. hollow on wood
                    5. Mechanical damage to wood
                    6. Fruiting bodies of wood mushrooms
                    7. Damaged by wood pests
                    8. Dry branches more than 75%
                    9. wood bark peeling


                    """},
                ]
            },
        ]

        output = do_gemma_3n_inference(model, messages, max_new_tokens = 256)
        text = tokenizer.decode(output[0], skip_special_tokens=True)
        t, text_number = str(text).split("model")
        print(f"text_number: {text_number}")
        result_item['number'] = text_number



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
                    {"type": "image", "url": os.path.join(DATA_DIR, filename)},
                    # {"type": "image", "url": url_cat},
                    {"type": "text", "text": """What damage is there on the tree? Select from the list below. give a detailed answer.
                    1. Severe butt rot
                    2. severe stem rot
                    4. Dead wood
                    3. hollow on wood
                    5. Mechanical damage to wood
                    6. Fruiting bodies of wood mushrooms
                    7. Damaged by wood pests
                    8. Dry branches more than 75%
                    9. wood bark peeling


                    """},
                ]
            },
        ]

        output = do_gemma_3n_inference(model, messages, max_new_tokens = 256)
        text = tokenizer.decode(output[0], skip_special_tokens=True)
        t, text_detailed = str(text).split("model")
        print(f"text_detailed: {text_detailed}")
        result_item['detailed'] = text_detailed

        result_list.append(result_item)

        with open(os.path.join(BASE_DIR, "gemma-4.json"), 'w', encoding="utf-8") as fp:
            json.dump(result_list, fp)