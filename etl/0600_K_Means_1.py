import os, sys

from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")

processing_title = "K-Means #1"
processing_desc = "Выделяем кластеры по географическому расположению"

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
print(f"processing_id: {processing_id}") #6





