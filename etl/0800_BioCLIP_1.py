import torch

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image
# https://imageomics.github.io/pybioclip/python-tutorial/
from bioclip import TreeOfLifeClassifier, Rank

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

classifier = TreeOfLifeClassifier()


# Добавляем обработку
processing_title = "BioClip #1"
processing_desc = "Определитель требуемых объектов: деревьев, травы, кустарников, животных, насекомых, птиц"

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
print(f"processing_id: {processing_id}") #8



image_items = db.session.query(db.Monitor_Images).all()
for image_item in tqdm(image_items):
    # обрабатывали ли изображение этим процессингом
    image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==processing_id)).first()            
    if image_status_item == None:
        full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
        img_main_clear = Image.open(full_image_path)

        detected_items = db.session.query(db.Monitor_Objects).filter(db.Monitor_Objects.image_id==image_item.id).all()   
        for detected_item in detected_items:
            left = detected_item.left
            right = detected_item.right
            top = detected_item.top
            bottom = detected_item.bottom
            copy_bbox = (left, top, right, bottom)

            img_region = img_main_clear.crop(copy_bbox)
            img_region.save(os.path.join(BASE_DIR, "temp.jpg"))
        
            # предсказываем
            predictions = classifier.predict(os.path.join(BASE_DIR, "temp.jpg"), Rank.SPECIES)
            for prediction in predictions:
                monitor_objects_classified_item = db.Monitor_Objects_Classified(
                    objects_id=detected_item.id, 
                    version=processing_id,
                    score=float(prediction["score"]),
                    name_en=prediction["species"],
                    common_name=prediction["common_name"],
                )
                db.session.add(monitor_objects_classified_item)

    # добавляем статус изображению
    image_status_item = db.Monitor_Image_Statuses(
        image_id=image_item.id, 
        processing_version=processing_id,
        key="classified",
        value="1"
    )
    db.session.add(image_status_item)

    db.session.commit()


print(f"success")