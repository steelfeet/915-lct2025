from datetime import datetime, timedelta
import os, json, sys, time, random
from bs4 import BeautifulSoup
from os.path import abspath, dirname
from typing import List

from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = abspath(dirname(dirname(dirname(dirname(dirname(__file__))))))
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault
from safe_request import get_url_html, get_url_content

PARSER_DIR = abspath(dirname((__file__)))
sys.path.append(PARSER_DIR)
sys.path.insert(0, PARSER_DIR)
    


# получение списка ссылок на новости с заданной страницы
def get_all_previews(page) -> List[str]:
    previews = []

    if page == 1:
        index_url = f"https://npedkol.ru/novosti/"
    else:
        index_url = f"https://npedkol.ru/novosti/page{page}/"

    index_html = get_url_html(index_url)
    
    soup = BeautifulSoup(index_html, "lxml")
    item_soups = soup.find_all('div', {'class': 'news_title'})

    for item_soup in item_soups:
        a_soup = item_soup.find('a')
        if a_soup != None:
            a_href = str(a_soup.get("href")).strip()
            previews.append(a_href)

    return previews


# запоминаем последнюю спарсенную страницу
last_page_path = os.path.join(PARSER_DIR, "npedkol_last_page.txt")
if os.path.isfile(last_page_path):
    with open(last_page_path, "r") as f:
        text = f.read()
    last_page = int(text)
else:
    last_page = 1



for page_delta in range(0, 20):
    current_page = last_page + page_delta
    print(f"Текущая страница: {current_page}")

     # все Previews
    all_previews = get_all_previews(current_page)
    print(f"Всего данных: {len(all_previews)}")


    for current_url in all_previews:
        print(f"current_url: {current_url}")
        # проверяем наличие такой сущности в таблице
        entity_item = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.donor_url==current_url).first()
        if entity_item == None:
            # html текущей сущности            
            entity_html = get_url_html(current_url)
            entity_soup = BeautifulSoup(entity_html, "lxml")
            entity_title = str(entity_soup.find('h1').getText()).strip()
            print(f"entity_title: {entity_title}")

            # добавляем новость
            entity_item = db.Monitor_Previews(
                donor="npedkol.ru", 
                donor_url=current_url, 
                donor_type="news",
                status=0,
                time=0,
                parse_time=int((datetime.now().timestamp())),
                title = entity_title,
                full_html = entity_html
            )
            db.session.add(entity_item)
            db.session.flush()
            db.session.refresh(entity_item)

            entity_id = entity_item.id
            print(f"entity_id: {entity_id}")



            # текст
            entity_text_soup = entity_soup.find('div', {'class': '_text'})
            entity_p_soups = entity_text_soup.find_all('p')
            for p_soup in entity_p_soups:
                p_text = str(p_soup.getText()).strip()
                print(p_text)
                # добавляем текст
                text_db_item = db.Monitor_Paragraphs(
                    monitor_id=entity_id, 
                    clear_text=p_text
                )
                db.session.add(text_db_item)



            # изображения 
            images_soup = entity_soup.find('div', {'class': '_images'})
            if images_soup != None:
                tr_soups = images_soup.find_all('a')
                if tr_soups != None:
                    for image_i, tr_soup in enumerate(tr_soups):
                        image_url = tr_soup["href"]
                        print(f"image_url: {image_url}")
                        
                        # скачиваем изображение
                        if image_url != None:
                            main_image_basename = vault.random_string(5) + "-" + os.path.basename(image_url)
                            image_dir, current_upload_dir = vault.get_vault_dirs("npedkol.ru")
                            full_file_path = os.path.join(image_dir, main_image_basename)
                            local_file_path = os.path.join(current_upload_dir, main_image_basename)
                            img_data = get_url_content(image_url)
                            if img_data != None:
                                with open(full_file_path, 'wb') as handler:
                                    handler.write(img_data)    

                                is_main = 0
                                if image_i == 0:
                                    is_main = 1

                                donor_db_image = db.Monitor_Images(
                                    monitor_id = entity_item.id,
                                    is_main = is_main,
                                    image_src = image_url,
                                    image_path = local_file_path,
                                    image_alt = "",
                                )
                                db.session.add(donor_db_image)
                                
            print()
            db.session.commit()
            


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    with open(last_page_path, "w") as f:
        text = f"{current_page}"
        f.write(text)
