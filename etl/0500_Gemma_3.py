import numpy as np # linear algebra

from unsloth import FastModel
from PIL import Image

from transformers import TextStreamer
import torch
import torch._dynamo
torch._dynamo.config.suppress_errors = True

import os, sys
from tqdm import tqdm

from sqlalchemy import and_


# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")

processing_title = "Gemma 3 Get NER #1"
processing_desc = "Генерация GeoNER-описания снимка "

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
print(f"processing_id: {processing_id}")












GEMMA_DIR = os.path.join("d:\\", "_vault", "06-Gemma", "data")

TARGET = (512, 512)
system_message = "You are a helpful AI assistant specialized in determining the name of a place, street, alley, building from its image. Provide concise and accurate information."
system_message = "Опиши, что ты видишь на русском языке"
system_message = "Вы — полезный ИИ-помощник, который специализируется на определении названия географического места: церкви, стадиона, памятника, улицы, переулка или здания по изображению. Предоставляйте информацию через запятую: улица, номер дома / домов, достопримечательности, рассуждение о причинах выбора"
system_message = "Вы — полезный ИИ-помощник, который специализируется на определении названия географического места: организации, церкви, стадиона, памятника, улицы, переулка или здания по изображению. Предоставляйте краткую и точную информацию"


cache_dir = os.path.join("d:\\", "_models", "huggingface.co")

os.environ['HF_HOME'] = cache_dir
os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir



model, processor = FastModel.from_pretrained(
    # model_name=os.path.join(cache_dir, "gemma3n_ru_1"),  # YOUR MODEL YOU USED FOR TRAINING
    model_name = "unsloth/gemma-3n-E4B-it",
    load_in_4bit=True,  # Set to False for 16bit LoRA
    cache_dir = cache_dir
)
FastModel.for_inference(model)  # Enable for inference!


# Helper function for inference
def do_gemma_3n_inference(image_path):
    FastModel.for_inference(model)
    
    loaded_image = Image.open(image_path).convert("RGB").resize(TARGET, resample=Image.BILINEAR)
    messages = [
        {
            "role": "user",
            "content": [{"type": "image"}, {"type": "text", "text": system_message}],
        }
    ]
    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(
        loaded_image,
        input_text,
        add_special_tokens=False,
        return_tensors="pt",
    ).to("cuda")

    text_streamer = TextStreamer(processor, skip_prompt=True)
    result = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128,
                            use_cache=True, temperature = 0.5, top_p = 0.95, top_k = 6)
    
    text = processor.decode(result[0], skip_special_tokens=True)
    text_list = str(text).split("\n")
    clear_text = text_list[len(text_list)-1]
    return clear_text


preview_items = db.session.query(db.Monitor_Previews).all()
for preview_item in tqdm(preview_items):
    image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_item.id).all()
    for image_item in image_items:
        # обрабатывали ли изображение этим процессингом
        image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==processing_id)).first()            
        if image_status_item == None:
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            text_2_db = do_gemma_3n_inference(full_image_path)
            
            """
            print(f"text_2_db: {text_2_db}")
            input("Next...")
            """


            image_status_item = db.Monitor_Image_Statuses(
                image_id=image_item.id, 
                processing_version=processing_id,
                key="text",
                value=text_2_db
            )
            db.session.add(image_status_item)


    db.session.commit()


print(f"success")