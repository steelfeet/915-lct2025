import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import func, select

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
import secrets
import safe_request

DB_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(DB_DIR)
import geo_db


CLASSES_DIR = os.path.join("d:\\", "_vault", "01-GeoGuessr", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)


# парсим Новозыбков 
left_x, top_y = 52.544, 31.903  # улица ОХ Волна Революции
right_x, bottom_y = 52.518, 31.949 # Жертвам Холокоста

# 0.0001 - 10 m
class_n = 0
for lat in np.arange(right_x, left_x, 0.0005):
    for long in np.arange(top_y, bottom_y, 0.0005):
        class_n += 1
print(class_n)        
exit()        

# парсим Новозыбков 
left_x, top_y = 52.544, 31.903  # улица ОХ Волна Революции
right_x, bottom_y = 52.518, 31.949 # Жертвам Холокоста

# 0.001 - 100 m
class_n = 0
for lat in np.arange(right_x, left_x, 0.001):
    for long in np.arange(top_y, bottom_y, 0.001):
        # округляем до 6 значащих цифр после запятой
        formatted_lat = "%.6f" % lat
        formatted_long = "%.6f" % long
        print(f"lat: {formatted_lat}; long: {formatted_long};")

        # формируем запрос к VK
        params = {
            'lat': formatted_lat,
            'long': formatted_long,
            'start_time': "",
            'end_time': "",
            'radius': 100,
            'sort': 0,
            'count': 1000,
            'access_token': secrets.vk_token,
            'v': "5.199"
        }
        r = requests.get('https://api.vk.com/method/photos.search', params=params).json()

        if "response" in r.keys():
            count = r['response']['count']
            print(f"Всего: {count}")


            # скачиваем оригинальное изображение
            for item in r['response']['items']:
                if "orig_photo" in item.keys():
                    orig_photo = item["orig_photo"]["url"]
                    # проверяем наличие изображения в БД
                    items_n = geo_db.session.query(geo_db.DonorsDataGeo).filter(geo_db.DonorsDataGeo.image_url==orig_photo).count()
                    if items_n > 0:
                        print(f"Есть в БД")
                    else:
                        print(f"Добавляем в DonorsDataGeo")
                        new_item = geo_db.DonorsDataGeo(donor_domain = "vk.ru", 
                                                image_url = orig_photo,
                                                lat = formatted_lat,
                                                long = formatted_long,
                                                radius = 100,
                                                user_id = "",
                                                parse_time = int(time.time()),
                                                text = ""
                                                )
                        geo_db.session.add(new_item)
                        geo_db.session.flush()
                        geo_db.session.refresh(new_item)
                        donor_data_id = new_item.id
                    
                        # сохраняем оригинал
                        orig_photo_filename = os.path.basename(urlparse(orig_photo).path)
                    
                        orig_photo_local_dir = os.path.join(CLASSES_DIR, str(class_n))
                        os.makedirs(orig_photo_local_dir, exist_ok=True)
                        orig_photo_local_path = os.path.join(orig_photo_local_dir, orig_photo_filename)
                        print(f"orig_photo_local_path: {orig_photo_local_path}")

                        post_content = safe_request.get_url_content(orig_photo)
                        with open(orig_photo_local_path, "wb") as f:
                            f.write(post_content)

            

        else:
            print(f"no response key")
        
        
        class_n += 1   
        geo_db.session.commit()
geo_db.session.close()












