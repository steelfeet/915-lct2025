import os, sys, shutil, random, json, time
from app import app
from flask import render_template, request, redirect, Blueprint, make_response

from os.path import dirname

from sqlalchemy import and_

from PIL import Image, ImageDraw, ImageFont



# директория основных файлов
BASE_DIR = os.path.abspath(dirname(dirname(dirname(dirname(__file__)))))
sys.path.append(BASE_DIR)
import db, vault

# директория файла
APP_DIR = os.path.abspath((dirname(__file__)))

# функция сортировки 
def order_of_left_item(item):
    return int(item.left)

# https://gist.github.com/meyerjo/dd3533edc97c81258898f60d8978eddc
def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = abs(max((xB - xA, 0)) * max((yB - yA), 0))
    if interArea == 0:
        return 0
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = abs((boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = abs((boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou



def get_detected_html(preview_id):
    detected_html = ""
    static_temp_dir = os.path.join(APP_DIR, "static", "temp")


    image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_id).order_by(db.Monitor_Images.id).all()
    for i, image_item in enumerate(image_items[:5]):
        detected_items = db.session.query(db.Monitor_Objects).filter(db.Monitor_Objects.image_id==image_item.id).all()
        if detected_items != None:
            detected_html += "<table border=0 cellspacing=5 align=center width=90% class='detected_bg'><tr align=center><td>"

            color_classes = []
            color_classes.append("red")
            color_classes.append("green")
            color_classes.append("blue")
            color_classes.append("magenta")
            color_classes.append("cyan")
            color_classes.append("lime")
            color_classes.append("black")
            color_classes.append("aqua")
            color_classes.append("orange")
            color_classes.append("darkred")

            # изображение, на которое выводим
            img_background_width = 1200
            img_background_height = 800
            # отступы выводимых обектов по сторонам
            padding_left = 20
            padding_bottom = 50 # надо место для подписи
            padding_top = 20
            
            img_background = Image.new('RGB', (img_background_width, img_background_height), color = (255, 255, 255))
            draw_background = ImageDraw.Draw(img_background)
            draw_font = ImageFont.truetype("arial.ttf", 14)
            

            # выводим по часовой стрелке
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            img_main = Image.open(full_image_path)
            draw_main = ImageDraw.Draw(img_main)
            img_main_clear = Image.open(full_image_path)
            width_main, height_main = img_main.size
            if width_main > height_main:
                # размещаем посередине внизу,
                new_main_width = int(img_background_width / 2)
                k_main = new_main_width / width_main
                new_main_height = int(height_main * k_main)

                # отбираем только вертикальные и только с деревьями и кустарниками, с несовпадающими координатами
                tree_detected_items = []
                for detected_item in detected_items:
                    if ("tree" in detected_item.label) or ("bush" in detected_item.label):
                        left = detected_item.left
                        right = detected_item.right
                        top = detected_item.top
                        bottom = detected_item.bottom

                        width = right - left
                        height = bottom - top
                        # вертикальные
                        if (width + width / 5) < height:
                            # непересекающиеся
                            if len(tree_detected_items) == 0:
                                tree_detected_items.append(detected_item)
                            else:
                                boxA = [left, top, right, bottom]
                                max_iou = 0
                                for tree_detected_item in tree_detected_items:
                                    boxB = [tree_detected_item.left, tree_detected_item.top, tree_detected_item.right, tree_detected_item.bottom]

                                    iou = bb_intersection_over_union(boxA, boxB)
                                    if iou > max_iou:
                                        max_iou = iou
                                
                                if max_iou < 0.3:
                                    tree_detected_items.append(detected_item)



                sorted_detected_items = sorted(tree_detected_items[:6], key=order_of_left_item, reverse=False)
                
                
                # рисуем найденные объекты
                for det_i, detected_item in enumerate(sorted_detected_items):
                    left = detected_item.left
                    right = detected_item.right
                    top = detected_item.top
                    bottom = detected_item.bottom
                    copy_bbox = (left, top, right, bottom)
                    draw_main.rectangle((copy_bbox), outline=color_classes[det_i], width=3)

                resized_img = img_main.resize((new_main_width, new_main_height))
                paste_position = (int(img_background_width / 4), img_background_height-new_main_height)
                img_background.paste(resized_img, paste_position)


                # рисуем отдельные объекты вокруг
                for det_i, detected_item in enumerate(sorted_detected_items):
                    left = detected_item.left
                    right = detected_item.right
                    top = detected_item.top
                    bottom = detected_item.bottom
                    copy_bbox = (left, top, right, bottom)

                    label = detected_item.label
                    score = detected_item.score

                    img_region = img_main_clear.crop(copy_bbox)
                    width_region, height_region = img_region.size
                    new_height_region = int((img_background_height - new_main_height) - padding_bottom - padding_top)
                    k = new_height_region / height_region
                    new_width_region = int(width_region * k)
                    
                    img_region_resized = img_region.resize((new_width_region, new_height_region), Image.Resampling.BILINEAR)
                    draw_region_resized = ImageDraw.Draw(img_region_resized)
                    draw_region_resized.rectangle((0, 0, new_width_region-2, new_height_region-2), outline=color_classes[det_i], width=3)

                    if det_i == 0:
                        paste_position = (padding_left, int(height_main/2) + padding_top)
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (padding_left+3, int(height_main/2) + padding_top + new_height_region + 3)
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = padding_left + new_width_region
                        left_line_y = height_main/2 + padding_top + 50

                        right_line_x = left * k_main + img_background_width / 4
                        # смещение относительно оригинального: top * k_main 
                        # смещение относительно основы: (img_background_height - new_main_height)
                        right_line_y = int((img_background_height - new_main_height) + top * k_main + (bottom-top) * k_main / 5)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


                    if det_i == 1:
                        paste_position = (padding_left, padding_top)
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (padding_left+3, padding_top+new_height_region+3)
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = padding_left + new_width_region
                        left_line_y = padding_top + new_height_region - new_height_region / 5

                        right_line_x = left * k_main + img_background_width / 4
                        right_line_y = int((img_background_height - new_main_height) + top * k_main + (bottom-top) * k_main / 5)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


                    if det_i == 2:
                        paste_position = (int(padding_left + width_main / 4), padding_top)
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (int(padding_left + width_main / 4)+3, padding_top+new_height_region+3)
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = int(padding_left + width_main / 4 + new_width_region / 2)
                        left_line_y = padding_top + new_height_region

                        right_line_x = left * k_main +(right-left) * k_main / 2 + img_background_width / 4
                        right_line_y = int((img_background_height - new_main_height) + top * k_main)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


                    if det_i == 3:
                        paste_position = (int(padding_left + width_main / 2), padding_top)
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (int(padding_left + width_main / 2)+3, padding_top+new_height_region+3)
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = int(padding_left + width_main / 2 + new_width_region / 2)
                        left_line_y = padding_top + new_height_region

                        right_line_x = left * k_main +(right-left) * k_main / 2 + img_background_width / 4
                        right_line_y = int((img_background_height - new_main_height) + top * k_main)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


                    if det_i == 4:
                        paste_position = (int(2*padding_left + 3 * width_main / 4), padding_top)
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (int(padding_left + 3*width_main / 4)+3, padding_top+new_height_region+3)
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = int(2*padding_left + 3 * width_main / 4 )
                        left_line_y = int(padding_top + new_height_region - 50)

                        right_line_x = int(left * k_main +(right-left) * k_main + img_background_width / 4)
                        right_line_y = int((img_background_height - new_main_height) + top * k_main + (bottom-top) * k_main / 5)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


                    if det_i == 5:
                        paste_position = (int(2*padding_left + 3 * width_main / 4), int(padding_top + height_main / 2))
                        img_background.paste(img_region_resized, paste_position)

                        text_to_draw = f"label: {label}; score: {score:.3f}"
                        text_position = (int(2*padding_left + 3 * width_main / 4 + 3), int(padding_top + height_main / 2 + new_height_region + 3))
                        draw_background.text(text_position, text_to_draw, fill=color_classes[det_i], font=draw_font)

                        # координаты соединяющей линии
                        left_line_x = int(2*padding_left + 3 * width_main / 4)
                        left_line_y = int(padding_top + height_main / 2 + 50)

                        right_line_x = int(left * k_main +(right-left) * k_main + img_background_width / 4)
                        right_line_y = int((img_background_height - new_main_height) + top * k_main + (bottom-top) * k_main / 5)
                        coordinates = [(left_line_x, left_line_y), (right_line_x, right_line_y)]
                        draw_background.line(coordinates, fill=(color_classes[det_i]), width=3)


            
            
            
            
            
            
            detected_image_path = os.path.join(static_temp_dir, f"detected_image-{i}.jpg")
            img_background.save(detected_image_path)

            detected_html += f"<img src='static/temp/detected_image-{i}.jpg' width={img_background_width}>"



    detected_html += "</td></tr></table>"
    return detected_html