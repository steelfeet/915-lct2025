import os, sys, shutil, random, json, time
from app import app
from flask import render_template, request, redirect, Blueprint, make_response

from os.path import dirname

from sqlalchemy import and_

from PIL import Image, ImageDraw, ImageFont

import markdown


# директория основных файлов
BASE_DIR = os.path.abspath(dirname(dirname(dirname(dirname(__file__)))))
sys.path.append(BASE_DIR)
import db, vault

# директория файла
APP_DIR = os.path.abspath((dirname(__file__)))

# функция сортировки 
def order_of_left_item(item):
    return int(item.left)



def get_sanitarka_html(image_id):
    detected_html = ""
    static_temp_dir = os.path.join(APP_DIR, "static", "temp")

    sanitar_classes = {}
    sanitar_classes[0] = "Санитарных повреждений нет"
    sanitar_classes[1] = "Комлевая гниль в сильной степени"
    sanitar_classes[2] = "Стволовая гниль в сильной степени"
    sanitar_classes[3] = "Обширное дупло"
    sanitar_classes[4] = "Сухостой"
    sanitar_classes[5] = "Механические повреждения ствола и ветвей"
    sanitar_classes[6] = "Плодовые тела древесных грибов"
    sanitar_classes[7] = "Повереждено вредителями"
    sanitar_classes[8] = "Сухие ветви более 75 %"
    sanitar_classes[9] = "Отслоение коры"


    image_item = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.id==image_id).first()
    detected_items = db.session.query(db.Monitor_Objects).filter(db.Monitor_Objects.image_id==image_id).all()

    if detected_items != None:
        detected_html += "<table border=0 cellspacing=5 align=center width=90% class='detected_bg'>"

        full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
        img_main_clear = Image.open(full_image_path)


        for det_i, detected_item in enumerate(detected_items):
            if ("tree" in detected_item.label) or ("bush" in detected_item.label):
                left = detected_item.left
                right = detected_item.right
                top = detected_item.top
                bottom = detected_item.bottom
                copy_bbox = (left, top, right, bottom)

                width = right-left
                td_width = ""
                if width > 300:
                    td_width = " width=300"


                description_item = db.session.query(db.Monitor_Objects_Description).filter(and_(db.Monitor_Objects_Description.objects_id==detected_item.id), (db.Monitor_Objects_Description.processing_version==9)).first()

                if description_item != None:
                    img_region = img_main_clear.crop(copy_bbox)
                    detected_image_path = os.path.join(static_temp_dir, f"desc_image-{image_id}-{det_i}.jpg")
                    img_region.save(detected_image_path)

                    html_output = markdown.markdown(description_item.desc)
                    sanitar_class = sanitar_classes[description_item.class_n]

                    if (det_i % 2) == 0:
                        detected_html += f"<tr align=center valign=top><td align=center><img src='static/temp/desc_image-{image_id}-{det_i}.jpg' {td_width}></td><td align=left><b>Определенный класс:</b> {description_item.class_n} // {sanitar_class}<p>{html_output}</td>"
                    else:
                        detected_html += f"<td align=center><img src='static/temp/desc_image-{image_id}-{det_i}.jpg' {td_width}></td><td align=left><b>Определенный класс:</b> {description_item.class_n} // {sanitar_class}<p>{html_output}</td></tr>"




    detected_html += "</table>"
    return detected_html