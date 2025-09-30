import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np



from PIL import Image, ImageDraw, ImageFont

os.environ["HF_TOKEN"] = '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'
print(os.environ["HF_TOKEN"])

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

DETECTED_DIR = "X:\\_vault\\олимпиады\\915-lct2025\\07-Monitor\\Характеристики"


cache_dir="D:\\_models\\huggingface.co"


# https://huggingface.co/unsloth/gemma-3-12b-it-unsloth-bnb-4bit?library=transformers
# Load model directly
from transformers import pipeline

pipe = pipeline("image-text-to-text", model="unsloth/gemma-3-12b-it-unsloth-bnb-4bit")
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/p-blog/candy.JPG"},
            {"type": "text", "text": "What animal is on the candy?"}
        ]
    },
]
pipe(text=messages)