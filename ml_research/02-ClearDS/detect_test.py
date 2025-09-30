import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

orig_photo_filename = "bH5MvSpoiDWocL0zSB936x7Hl_CIaKs7cEuTFqohb2Sxf8HmeGhj1sA6fNwdtxwbE9QKZp78RFCW8sRW79-d5n58.jpg"

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

DETECTED_DIR = os.path.join(BASE_DIR, "detected")
os.makedirs(DETECTED_DIR, exist_ok=True)

sample_images_dir = os.path.join(BASE_DIR, "temp")




model_id = "IDEA-Research/grounding-dino-base"
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

processor = AutoProcessor.from_pretrained(model_id, cache_dir=MODEL_PATH)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=MODEL_PATH).to(DEVICE)
print("device: ", DEVICE)
print()

orig_photo_local_path = os.path.join(sample_images_dir, orig_photo_filename)




# функция рисования bbox
def draw_boxes_on_image(img_pil, bbox_info):
    font_list = ["red", "blue", "green", "lime", "magenta", "white", "black"]
    img_pil = img_pil.copy()
    draw = ImageDraw.Draw(img_pil)
    
    for bbox_item in bbox_info:
        boxes = bbox_item['boxes']
        labels = bbox_item['labels']
        scores = bbox_item['scores']

        font = ImageFont.truetype("arial.ttf", 40)

        for box, label, score in zip(boxes, labels, scores):
            rand_color = random.choice(font_list)

            x1, y1, x2, y2 = box
            draw.rectangle([x1, y1, x2, y2], outline=rand_color, width=2)
            text = f"{label}: {score:.2f}"
            text_left, text_top, text_right, text_bottom = draw.textbbox((0,0), text, font=font)
            text_width, text_height = (text_right - text_left, text_bottom - text_top)
            draw.text((x1, y1 - text_height - 2), text, fill=rand_color, font=font)

    return img_pil


full_prompt = "building . tree . clouds . bush "

img_pil = Image.open(orig_photo_local_path)

# проверяем детекцию на промте из всех меток вместе
inputs = processor(images=img_pil, text=full_prompt, return_tensors="pt").to(DEVICE)
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
print(f"Детектировано: {len(bbox_info[0]['boxes'])}; score: {bbox_info[0]['scores']}")

"""
for box, score, text_labels in zip(bbox_info[0]["boxes"], bbox_info[0]["scores"], bbox_info[0]["text_labels"]):
    box = [round(x, 2) for x in box.tolist()]
    print(f"Detected {text_labels} with confidence {round(score.item(), 3)} at location {box}")

# postprocess / рисуем bbox
detect_img = draw_boxes_on_image(img_pil, bbox_info)
detect_photo_local_path = os.path.join(DETECTED_DIR, orig_photo_filename)
detect_img.save(detect_photo_local_path)
"""

# проверяем детекцию на каждой метке по отдельности
print()
print("Проверяем детекцию на каждой метке по отдельности")
labels_list = full_prompt.split(".")
print(f"labels count: {len(labels_list)}")
detected_n = 0

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
    
    detected_n += len(bbox_info[0]['boxes'])
    print(f"Детектировано: {len(bbox_info[0]['boxes'])}; score: {bbox_info[0]['scores']}")


print(f"Всего детектировано: {detected_n};")


