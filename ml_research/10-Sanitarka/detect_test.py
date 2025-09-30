import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection


# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
os.makedirs(MODEL_PATH, exist_ok=True)

DETECTED_DIR = "X:\\_vault\\олимпиады\\915-lct2025\\07-Monitor\\Характеристики"





model_id = "IDEA-Research/grounding-dino-base"
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

processor = AutoProcessor.from_pretrained(model_id, cache_dir=MODEL_PATH)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=MODEL_PATH).to(DEVICE)
print("device: ", DEVICE)
print()





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

""
full_prompt = "butt rot"

for basename in os.listdir(DETECTED_DIR):
    if "jpg" in basename:
        orig_photo_local_path = os.path.join(DETECTED_DIR, basename)

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
        print(f"{basename}. Детектировано: {len(bbox_info[0]['boxes'])}; score: {bbox_info[0]['scores']}")

        if len(bbox_info[0]['boxes']) > 0:
            img_pil = draw_boxes_on_image(img_pil, bbox_info)
            img_pil_path = os.path.join(BASE_DIR, basename)
            img_pil.save(img_pil_path)



"""
гнилое дерево
full_prompt = "rotten wood"
12.jpg. Детектировано: 1; score: [0.31043774]
14.jpg. Детектировано: 1; score: [0.2667541]
2..jpg. Детектировано: 1; score: [0.25071952]
4.jpg. Детектировано: 1; score: [0.26872635]
5..jpg. Детектировано: 1; score: [0.25836912]
9.jpg. Детектировано: 1; score: [0.25315472]

сломанная ветка
full_prompt = "broken branch"
1.jpg. Детектировано: 1; score: [0.2807509]
12.jpg. Детектировано: 1; score: [0.31650573]
14.jpg. Детектировано: 1; score: [0.28058666]
2..jpg. Детектировано: 1; score: [0.28370923]
4.jpg. Детектировано: 1; score: [0.2640228]
5..jpg. Детектировано: 1; score: [0.25150058]

засохшая ветка
full_prompt = "dried branch"
1.jpg. Детектировано: 1; score: [0.25966826]
12.jpg. Детектировано: 1; score: [0.3132565]
14.jpg. Детектировано: 1; score: [0.2863202]
2..jpg. Детектировано: 1; score: [0.29693735]
4.jpg. Детектировано: 1; score: [0.26331657]

дупло в дереве
full_prompt = "a hollow in a tree"
1.jpg. Детектировано: 2; score: [0.4261424  0.26756337]
10.jpg. Детектировано: 1; score: [0.26085678]
12.jpg. Детектировано: 3; score: [0.3626657  0.33698285 0.28720522]
13.jpg. Детектировано: 1; score: [0.2546228]
14.jpg. Детектировано: 2; score: [0.2601794  0.27673706]
15.jpg. Детектировано: 1; score: [0.25426105]
16.jpg. Детектировано: 1; score: [0.3123355]
2..jpg. Детектировано: 1; score: [0.30909896]
3.jpg. Детектировано: 1; score: [0.27480122]
4.jpg. Детектировано: 2; score: [0.34105834 0.304719  ]
5..jpg. Детектировано: 1; score: [0.33912417]
6.jpg. Детектировано: 2; score: [0.271633   0.26596358]
7.jpg. Детектировано: 1; score: [0.27506152]
8.jpg. Детектировано: 1; score: [0.29696313]
9.jpg. Детектировано: 2; score: [0.2991992 0.263217 ]


full_prompt = "severe butt rot"


"""

