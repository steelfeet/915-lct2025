# https://habr.com/ru/articles/826820/
# https://habr.com/ru/articles/531940/
import os, sys
from tqdm import tqdm

from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import func, select

import spacy


# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

processing_title = "Ручная разметка NER"
processing_desc = "Ручная разметка текста на именованные сущности: Geo / FIO"


processing_item = db.session.query(db.Monitor_Processing_Types).filter(db.Monitor_Processing_Types.title==processing_title).first()
if processing_item == None:
    # добавляем тип обработки
    processing_item = db.Monitor_Processing_Types(
        title=processing_title, 
        desc=processing_desc 
    )
    db.session.add(processing_item)
    db.session.flush()
    db.session.refresh(processing_item)
    db.session.commit()


processing_id = processing_item.id
print(f"processing_id: {processing_id}")



processing_title = "Ручная разметка GeoGood"
processing_desc = "Ручная разметка изображений на пригодность к GeoOSINT"


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
print(f"image processing_id: {processing_id}")
