import os, sys, asyncio
from tqdm import tqdm
import pathlib, shutil, json, random, string
from PIL import Image, ImageDraw, ImageFont, ImageOps

import numpy as np # linear algebra

from sqlalchemy import and_, or_
from sqlalchemy.sql import func as sql_func

from os.path import dirname, abspath
#директории основных модулей
APP_DIR = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.insert(1, APP_DIR)
APP_DIR = dirname(APP_DIR)
sys.path.append(APP_DIR)

from app import app
import func, db

BASE_DIR = dirname(abspath(__file__))
DATA_DIR = os.path.join("d:\\", "coins-ds", "ds446_types.diff.small.fon")
FON_DIR = os.path.join("d:\\", "coins-ds", "fon")
os.makedirs(DATA_DIR, exist_ok=True)

IMAGE_SIZE = 512
IMAGES_PER_CLASS = 250



def a_path_2_r(a_path):
    a_file_name = os.path.basename(a_path)
    a_dir_name = os.path.dirname(a_path)
    r_file_name = str(a_file_name).replace("a-", "r-")
    r_dir_name = str(a_dir_name).replace("avers", "revers")
    r_path = os.path.join(r_dir_name, r_file_name)

    return r_path


def random_string(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))


def get_random_attributes(img):
    font_size = random.randint(8, 70) 
    r = random.randint(8, 250) 
    g = random.randint(8, 250) 
    b = random.randint(8, 250) 
    font_color=(r,g,b)

    width, height = img.size
    random_x = random.randint(20, width-20) 
    random_y = random.randint(20, height-20) 

    letters_count = random.randint(1, 3) 
    text = random_string(letters_count)

    return font_size, random_x, random_y, text, font_color


# генерация на основе только одного изображения
def generate_train_image(a_path, r_path):
        fon_filename = random.choice(fon_list)
        fon_path = os.path.join(FON_DIR, fon_filename)
        im_fon = Image.open(fon_path)
        fon_w, fon_h = im_fon.size
        if fon_w < fon_h:
            # обрезаем по высоте
            crop_size = random.randint(0, fon_h-fon_w) # плавающий отступ
            fon_crop = im_fon.crop((0, crop_size, fon_w, crop_size + fon_w))
        else:
            # обрезаем по ширине
            crop_size = random.randint(0, fon_w-fon_h)
            fon_crop = im_fon.crop((crop_size, 0, crop_size + fon_h, fon_h))
        
        fon_crop.thumbnail((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
        
       
        #аугментация
        min_y = int(IMAGE_SIZE * 0.35)
        max_y = int(IMAGE_SIZE * 0.8)


        # аверс 1
        im = Image.open(a_path)
        im_copy = im.copy()
        current_y = random.randint(min_y, max_y)
        im_res = im_copy.resize((int(IMAGE_SIZE/2), int(current_y)), resample=Image.Resampling.BICUBIC)
        for x in range(im_res.width):
            for y in range(im_res.height):
                # входит ли точка внутрь эллипса
                a = im_res.width / 2 - 10 # 10 - уменьшаем диаметр эллипса, которым вырезаем, т.к. фото обычно меньше изображения
                b = im_res.height / 2 - 10
                x_norm = x - im_res.width / 2
                y_norm = y - im_res.height / 2
                if (x_norm*x_norm/(a * a) + y_norm*y_norm/(b*b)) < 1:
                    r, g, b = im_res.getpixel((x, y))
                    new_x = int(x)
                    new_y = int(y+10)
                    try:
                        fon_crop.putpixel((new_x, new_y), (r, g, b, 255))
                    except:
                        pass

        # реверс 1
        im = Image.open(r_path)
        im_copy = im.copy()
        current_y = random.randint(min_y, max_y)
        im_res = im_copy.resize((int(IMAGE_SIZE/2), int(current_y)), resample=Image.Resampling.BICUBIC)
        for x in range(im_res.width):
            for y in range(im_res.height):
                # входит ли точка внутрь эллипса
                a = im_res.width / 2 - 10 # 10 - уменьшаем диаметр эллипса, которым вырезаем, т.к. фото обычно меньше изображения
                b = im_res.height / 2 - 10
                x_norm = x - im_res.width / 2
                y_norm = y - im_res.height / 2
                if (x_norm*x_norm/(a * a) + y_norm*y_norm/(b*b)) < 1:
                    r, g, b = im_res.getpixel((x, y))
                    new_x = int(IMAGE_SIZE/2 + x)
                    new_y = int(y+10)
                    try:
                        fon_crop.putpixel((new_x, new_y), (r, g, b, 255))
                    except:
                        pass

        return fon_crop





"""
████████   ███████     █████       ██   ███     ██   
   ██      ██    ██   ██   ██           ██ ██   ██   
   ██      ███████    ███████      ██   ██  ██  ██   
   ██      ██  ██     ██   ██      ██   ██   ██ ██   
   ██      ██    ██   ██   ██      ██   ██     ███   
"""

fon_list = os.listdir(FON_DIR)


types_list = db.session.query(db.Types).all()
for type_item in tqdm(types_list):
    class_id = type_item.id
    if class_id > 322:
        #Е1 рубль и полтина
        if class_id==192:
            class_id=194
        #Е2 рубль и полтина
        if class_id==146:
            class_id=147
        #П1 рубль и полтина, 25
        if class_id==242:
            class_id=246
        if class_id==243:
            class_id=246

        train_dir = os.path.join(DATA_DIR, "train", str(class_id))
        os.makedirs(train_dir, exist_ok=True)
        valid_dir = os.path.join(DATA_DIR, "valid", str(class_id))
        os.makedirs(valid_dir, exist_ok=True)


        images_n = 0
        try_n = 0
        while (images_n < IMAGES_PER_CLASS) and (try_n < IMAGES_PER_CLASS*10):

            coin_items = db.session.query(db.Coins).filter(and_(db.Coins.type_id==type_item.id, db.Coins.is_hand==1, or_(db.Coins.ml_type=="train", db.Coins.ml_type=="test"))).all()
            if len(coin_items) < 2:
                print(f"no items: {class_id}")
                images_n = IMAGES_PER_CLASS + 1

            # ограничиваем число попыток
            try_n += 1

            coin_item_a = db.session.query(db.Coins).filter(and_(db.Coins.type_id==type_item.id, db.Coins.is_hand==1, or_(db.Coins.ml_type=="train", db.Coins.ml_type=="test"))).order_by(sql_func.random()).first()
            if coin_item_a != None:
                a_item = db.session.query(db.Coin_Avers_Images).filter(db.Coin_Avers_Images.coin_id==coin_item_a.id).first()
            
                coin_item_r = db.session.query(db.Coins).filter(and_(db.Coins.type_id==type_item.id, db.Coins.is_hand==1, or_(db.Coins.ml_type=="train", db.Coins.ml_type=="test"))).order_by(sql_func.random()).first()
                if coin_item_r != None:
                    r_item = db.session.query(db.Coin_Revers_Images).filter(db.Coin_Revers_Images.coin_id==coin_item_r.id).first()
                    
                    if (a_item != None) and (r_item != None):
                        a_path = a_item.link
                        r_path = r_item.link
                        if (os.path.isfile(a_path)) and (os.path.isfile(r_path)):
                            images_n += 1
                            im_new = generate_train_image(a_path, r_path)

                            random_filename = f"{coin_item_a.id}-{coin_item_r.id}-{random_string(5)}"
                            target_path = os.path.join(DATA_DIR, "train", str(class_id), random_filename+".jpg")

                            rgb_im = im_new.convert('RGB')
                            rgb_im.save(target_path)
