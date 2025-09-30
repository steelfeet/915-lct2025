import torch

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image
# https://imageomics.github.io/pybioclip/python-tutorial/

import torch
from unsloth import FastModel


from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'


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



# Добавляем обработку
processing_title = "Gemma 3n E4B it #1"
processing_desc = "Определение наличия и описания вида санитарного повреждения дерева. Запрос на русском языке. Только деревья"

processing_item = db.session.query(db.Monitor_Image_Processing_Types).filter(db.Monitor_Image_Processing_Types.title==processing_title).first()
if processing_item == None:
    # добавляем тип обработки
    processing_item = db.Monitor_Image_Processing_Types(
        title=processing_title, 
        desc=processing_desc 
    )
    db.session.add(processing_item)
    db.session.flush()
    db.session.refresh(processing_item)
    db.session.commit()


processing_id = processing_item.id
print(f"processing_id: {processing_id}") #9



image_items = db.session.query(db.Monitor_Images).all()
for image_item in tqdm(image_items):
    # обрабатывали ли изображение этим процессингом
    image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==processing_id)).first()            
    if image_status_item == None:
        full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
        img_main_clear = Image.open(full_image_path)

        detected_items = db.session.query(db.Monitor_Objects).filter(db.Monitor_Objects.image_id==image_item.id).all()   
        for detected_item in detected_items:
            if ("tree" in detected_item.label):
                left = detected_item.left
                right = detected_item.right
                top = detected_item.top
                bottom = detected_item.bottom
                copy_bbox = (left, top, right, bottom)

                img_region = img_main_clear.crop(copy_bbox)
                img_region.save(os.path.join(BASE_DIR, "temp.jpg"))
            
                messages =[
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": "Ты специалист по болезням и повреждением деревьев - дендролог."}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "url": os.path.join(BASE_DIR, "temp.jpg")},
                            {"type": "text", "text": """Какие повреждения есть на дереве? Выберите из списка ниже. В качестве ответа дай только число. Если повреждений нет, напиши 0. Список возможных повреждений:
                            1. Комлевая гниль в сильной степени
                            2. Стволовая гниль в сильной степени
                            3. Обширное дупло
                            4. Сухостой
                            5. Механические повреждения ствола и ветвей
                            6. Плодовые тела древесных грибов
                            7. Повереждено вредителями
                            8. Сухие ветви более 75 %
                            9. Отслоение коры
                            """},
                        ]
                    },
                ]

                output = do_gemma_3n_inference(model, messages, max_new_tokens = 256)
                text = tokenizer.decode(output[0], skip_special_tokens=True)
                t, text_number = str(text).split("model")
                text_number = text_number.strip()

                # добавляем статус изображению
                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="class_n",
                    value=text_number
                )
                db.session.add(image_status_item)




                messages =[
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": "Ты специалист по болезням и повреждением деревьев - дендролог."}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "url": os.path.join(BASE_DIR, "temp.jpg")},
                            {"type": "text", "text": """Какие повреждения есть на дереве? Выбери из списка ниже. Ответ подробно обоснуй. Список возможных повреждений:
                            1. Комлевая гниль в сильной степени
                            2. Стволовая гниль в сильной степени
                            3. Обширное дупло
                            4. Сухостой
                            5. Механические повреждения ствола и ветвей
                            6. Плодовые тела древесных грибов
                            7. Повереждено вредителями
                            8. Сухие ветви более 75 %
                            9. Отслоение коры
                            """},
                        ]
                    },
                ]

                output = do_gemma_3n_inference(model, messages, max_new_tokens = 256)
                text = tokenizer.decode(output[0], skip_special_tokens=True)
                t, text_number = str(text).split("model")
                text_number = text_number.strip()

                # добавляем статус изображению
                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="detailed",
                    value=text_number
                )
                db.session.add(image_status_item)




    db.session.commit()


print(f"success")