import os, sys, random
import csv, json, shutil
import requests, time
from tqdm import tqdm

import numpy as np

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

model_id = "IDEA-Research/grounding-dino-base"
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

processor = AutoProcessor.from_pretrained(model_id, cache_dir=MODEL_PATH)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=MODEL_PATH).to(DEVICE)
print("device: ", DEVICE)
print()

full_prompt = "building . tree . clouds . grasses . sky . hill . monument . road . path . bench . bush . pole . lantern . signpost . pointer . sign"

labels_list = full_prompt.split(".")
print(f"labels count: {len(labels_list)}")
detected_n = 0
min_detected_n = sys.maxsize
max_detected_n = 0
average_detected_n = 0
class_stat_dict = {}
for label_text in labels_list:
    class_stat_dict[label_text] = 0

CLASSES_DIR = os.path.join("d:\\", "_vault", "03-YaMap", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

for class_n in tqdm(os.listdir(CLASSES_DIR)):
    class_dir = os.path.join(CLASSES_DIR, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)

        img_pil = Image.open(current_file_path)
        detected_n += 1
        current_detected_n = 0
        for label_text in labels_list:

            inputs = processor(images=img_pil, text=f"{label_text} .", return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)

            bbox_info = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                # box_threshold=0.4,
                text_threshold=0.3,
                target_sizes=[img_pil.size[::-1]]
            )

            bbox_info[0]['boxes'] = bbox_info[0]['boxes'].cpu().numpy()
            bbox_info[0]['scores'] = bbox_info[0]['scores'].cpu().numpy()
            

            if len(bbox_info[0]['boxes']) > 0:
                current_detected_n += 1
                class_stat_dict[label_text] += len(bbox_info[0]['boxes'])

        average_detected_n += current_detected_n

        if current_detected_n > max_detected_n:
            max_detected_n = current_detected_n

        if current_detected_n < min_detected_n:
            min_detected_n = current_detected_n

    average_detected = average_detected_n / detected_n
    print()    
    print(f"average_detected: {average_detected}; max_detected_n: {max_detected_n}; min_detected_n: {min_detected_n}")

average_detected = average_detected_n / detected_n
print()    
print(f"average_detected: {average_detected}; max_detected_n: {max_detected_n}; min_detected_n: {min_detected_n}")
print(class_stat_dict)
