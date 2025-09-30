import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import func, select

from selenium import webdriver
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
import secrets

DB_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(DB_DIR)
import geo_db


CLASSES_DIR = os.path.join("d:\\", "_vault", "03-YaMap", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)


# парсим Новозыбков 
left_x, top_y = 52.544, 31.903  # улица ОХ Волна Революции
# right_x, bottom_y = 52.518, 31.949 # Жертвам Холокоста
right_x, bottom_y = 52.518, 32.5 # правее, к Индуктору, Замишево


try:
    with open(os.path.join(BASE_DIR, 'data.json'), 'r') as file:
        data = json.load(file)
        last_lat = data["last_lat"]
        last_long = data["last_long"]
        class_n = data["class_n"]
except:
    data = {}
    last_lat = right_x
    last_long = top_y
    class_n = 0


with open(os.path.join(BASE_DIR, 'tpl.html'), "r") as f:
    tpl = f.read()


opts = Options()
opts.add_experimental_option('excludeSwitches', ['enable-automation'])
opts.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=opts)            
driver.maximize_window()

api_count = 0
# 0.0005 - 50 m
for lat in np.arange(last_lat, left_x, 0.0005):
    for long in np.arange(last_long, bottom_y, 0.0005):
        if api_count > 900:
            exit()

        # округляем до 6 значащих цифр после запятой
        formatted_lat = "%.6f" % lat
        formatted_long = "%.6f" % long
        direction = 0
        print(f"lat: {formatted_lat}, {formatted_long}; direction: {direction}; api_count: {api_count}")

        tpl_2_save = tpl.replace("{lat}", str(formatted_lat))
        tpl_2_save = tpl_2_save.replace("{long}", str(formatted_long))
        tpl_2_save = tpl_2_save.replace("{direct}", str(direction))


        with open(os.path.join(BASE_DIR, 'temp.html'), "w") as f:
            f.write(tpl_2_save)

        html_file_path = Path(BASE_DIR, 'temp.html')
        driver.get(html_file_path.as_uri())
        api_count += 1

        # Alternatively, wait for the document.readyState to be 'complete' using JavaScript
        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(5)

        driver.save_screenshot(Path(BASE_DIR, 'screen.png'))
        img = Image.open(Path(BASE_DIR, 'screen.png'))
        pixel = img.getpixel((50, 50))
        
        if pixel == (50, 243, 162):
            print("панорамы нет")
        else:
            orig_photo_local_dir = os.path.join(CLASSES_DIR, str(class_n))
            os.makedirs(orig_photo_local_dir, exist_ok=True)
            orig_photo_filename = f"v0-{formatted_lat}-{formatted_lat}-{direction}.jpg"
            orig_photo_local_path = os.path.join(orig_photo_local_dir, orig_photo_filename)
            img.save(orig_photo_local_path, "jpeg")

            for direction in range(90, 360, 90):
                # округляем до 6 значащих цифр после запятой
                formatted_lat = "%.6f" % lat
                formatted_long = "%.6f" % long
                print(f"lat: {formatted_lat}, {formatted_long}; direction: {direction}; api_count: {api_count}")

                tpl_2_save = tpl.replace("{lat}", str(formatted_lat))
                tpl_2_save = tpl_2_save.replace("{long}", str(formatted_long))
                tpl_2_save = tpl_2_save.replace("{direct}", str(direction))
                
                with open(os.path.join(BASE_DIR, 'temp.html'), "w") as f:
                    f.write(tpl_2_save)

                html_file_path = Path(BASE_DIR, 'temp.html')
                driver.get(html_file_path.as_uri())
                api_count += 1

                # Alternatively, wait for the document.readyState to be 'complete' using JavaScript
                WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(5)

                driver.save_screenshot(Path(BASE_DIR, 'screen.png'))
                img = Image.open(Path(BASE_DIR, 'screen.png'))
                pixel = img.getpixel((50, 50))
                
                if pixel == (50, 243, 162):
                    print("панорамы нет")
                else:
                    orig_photo_local_dir = os.path.join(CLASSES_DIR, str(class_n))
                    os.makedirs(orig_photo_local_dir, exist_ok=True)
                    orig_photo_filename = f"v0-{formatted_lat}-{formatted_lat}-{direction}.jpg"
                    orig_photo_local_path = os.path.join(orig_photo_local_dir, orig_photo_filename)
                    img.save(orig_photo_local_path, "jpeg")
            
            




        # приводим к структуре классов из 01-GeoGuessr (квадрат со стороной 100 м.)
        # class_n += 1
        if (int(lat*10000) % 10 == 0) and (int(long*10000) % 10 == 9):
            class_n += 1

        data["last_lat"] = lat
        data["last_long"] = long
        data["class_n"] = class_n
        with open(os.path.join(BASE_DIR, 'data.json'), "w") as f:
            json.dump(data, f, indent=4)



        # geo_db.session.commit()
# geo_db.session.close()




print("all")







