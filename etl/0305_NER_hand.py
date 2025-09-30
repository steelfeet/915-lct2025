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


nlp = spacy.load("ru_core_news_lg")
processing_item = db.session.query(db.Monitor_Processing_Types).filter(db.Monitor_Processing_Types.title==processing_title).first()
processing_id = processing_item.id
print(f"processing_id: {processing_id}")



paragraph_items = db.session.query(db.Monitor_Paragraphs).all()
for paragraph_item in tqdm(paragraph_items):
    # проверяем параграф на обработку этой версией
    para_status_item = db.session.query(db.Monitor_Paragraphs_Statuses).filter(and_
        (db.Monitor_Paragraphs_Statuses.paragraph_id==paragraph_item.id), 
        (db.Monitor_Paragraphs_Statuses.processing_version==processing_id)
    ).first()
    if para_status_item == None:
        # просто разбиваем по пробелам
        words = str(paragraph_item.clear_text).split(" ")
        for word in words:
            word_status_item = db.Monitor_Paragraph_Words(
                paragraph_id=paragraph_item.id, 
                processing_version=processing_id,
                text=word,
                ner_type="",
                ner_subtype=""
            )
            db.session.add(word_status_item)

        # добавляем статус параграфу
        para_status_item = db.Monitor_Paragraphs_Statuses(
            paragraph_id=paragraph_item.id, 
            processing_version=processing_id
        )
        db.session.add(para_status_item)

    db.session.commit()

