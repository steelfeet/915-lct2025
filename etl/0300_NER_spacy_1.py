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

processing_title = "spacy_ru_core_news_sm_1"
processing_desc = "Используется модель spacy ru_core_news_sm без предобработки текста"




nlp = spacy.load("ru_core_news_sm")
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



paragraph_items = db.session.query(db.Monitor_Paragraphs).all()
for paragraph_item in tqdm(paragraph_items):
    # проверяем параграф на обработку этой версией
    para_status_item = db.session.query(db.Monitor_Paragraphs_Statuses).filter(and_
    (db.Monitor_Paragraphs_Statuses.paragraph_id==paragraph_item.id), 
    (db.Monitor_Paragraphs_Statuses.processing_version==processing_id)
    ).first()
    if para_status_item == None:
        # на вход NLP подаем текст целиком для учета контекста
        doc = nlp(paragraph_item.clear_text)
        for token in doc:
            # print(token.text, token.pos_, token.dep_)
            # добавляем токен
            word_item = db.Monitor_Paragraph_Words(
                paragraph_id=paragraph_item.id, 
                word=token.text
            )
            db.session.add(word_item)
            db.session.flush()
            db.session.refresh(word_item)

            # добавляем статус токену
            word_status_item = db.Monitor_Words_Statuses(
                word_id=word_item.id, 
                processing_version=processing_id,
                ner_type=token.pos_,
                ner_subtype=token.dep_
            )
            db.session.add(word_status_item)

        # добавляем статус параграфу
        para_status_item = db.Monitor_Paragraphs_Statuses(
            paragraph_id=paragraph_item.id, 
            processing_version=processing_id
        )
        db.session.add(para_status_item)

    db.session.commit()

