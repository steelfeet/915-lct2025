import torch

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

MODEL_PATH = os.path.join("D:\\", "_models", "huggingface.co")

model_id = "IDEA-Research/grounding-dino-base"
DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

processor = AutoProcessor.from_pretrained(model_id, cache_dir=MODEL_PATH)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, cache_dir=MODEL_PATH).to(DEVICE)
print("device: ", DEVICE)
print()

full_prompt = "tree . bush . grass . plant . animal . bird . insect"
labels_list = full_prompt.split(".")




processing_title = "Detect Objects #1"
processing_desc = "grounding-dino-base: Детектирование требуемых объектов: деревьев, травы, кустарников, животных, насекомых, птиц"

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
print(f"processing_id: {processing_id}") #7







preview_items = db.session.query(db.Monitor_Previews).all()
for preview_item in tqdm(preview_items):
    image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_item.id).all()
    for image_item in image_items:
        # обрабатывали ли изображение этим процессингом
        image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==processing_id)).first()            
        if image_status_item == None:
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            img_pil = Image.open(full_image_path)

            for label_text in labels_list:
                is_detect = None
                try:
                    inputs = processor(images=img_pil, text=f"{label_text} .", return_tensors="pt").to(DEVICE)
                    with torch.no_grad():
                        outputs = model(**inputs)
                    is_detect = True
                except:
                    is_detect = None

                if is_detect:
                    bbox_info = processor.post_process_grounded_object_detection(
                        outputs,
                        inputs.input_ids,
                        # box_threshold=0.4,
                        text_threshold=0.3,
                        target_sizes=[img_pil.size[::-1]]
                    )

                    bbox_boxes = bbox_info[0]['boxes'].cpu().numpy()
                    bbox_scores = bbox_info[0]['scores'].cpu().numpy()
                    
                    for box, score in zip(bbox_boxes, bbox_scores):
                        x1, y1, x2, y2 = box
                    
                        monitor_objects_item = db.Monitor_Objects(
                            image_id=image_item.id, 
                            version=processing_id,
                            label = label_text,
                            score=float(score),
                            left = int(x1),
                            right = int(x2),
                            top = int(y1),
                            bottom = int(y2)
                        )
                        db.session.add(monitor_objects_item)

            # добавляем статус изображению
            image_status_item = db.Monitor_Image_Statuses(
                image_id=image_item.id, 
                processing_version=processing_id,
                key="detected",
                value="1"
            )
            db.session.add(image_status_item)



    db.session.commit()


print(f"success")