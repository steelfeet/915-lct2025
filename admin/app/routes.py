import os, sys, shutil, random, json, time
from app import app
from flask import render_template, request, redirect, Blueprint, make_response

from os.path import dirname

from sqlalchemy import and_




# директория основных файлов
BASE_DIR = os.path.abspath(dirname(dirname(dirname(dirname(__file__)))))
sys.path.append(BASE_DIR)
import db, vault

# директория файла
APP_DIR = os.path.abspath((dirname(__file__)))
sys.path.append(APP_DIR)
import detected_0600 as detected



# добавляем headers в запрос
@app.after_request
def apply_caching(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# загрузка списка классов с координатами
with open(os.path.join(APP_DIR, 'classes.json'), 'r') as file:
    classes_list = json.load(file)

# находим ближайший класс по евклидову расстоянию
def check_class(classes_list, lat, long):
    delta_d = sys.maxsize
    class_n = 0

    for class_item in classes_list:
        current_delta = (float(class_item["lat"]) - float(lat)) ** 2 + (float(class_item["long"]) - float(long)) ** 2
        if current_delta < delta_d:
            delta_d = current_delta
            class_n = class_item["class"]
    
    return class_n














########### Views:
@app.route('/', methods=['post', 'get'])
def main_page():
    # Выводим список новостей
    title = "Мониторинг открытых источников г.Новозыбков"
    breadcrumbs = ">> Новости"

    static_temp_dir = os.path.join(APP_DIR, "static", "temp")
    if os.path.isdir(static_temp_dir):
        time.sleep(1)
        shutil.rmtree(static_temp_dir)
    os.makedirs(static_temp_dir, exist_ok=True)
    
    # показываем все новости определенного статуса
    show_status = str(request.args.get("show_status"))
    settings_list_html = "Показывать новости:<br>"

    if (show_status == "all"):
        preview_items = db.session.query(db.Monitor_Previews).all()
        settings_list_html += f"""
        <b>Все [{len(preview_items)}]</b><br>
        <a href=/?show_status=0>Новые</a><br>
        <a href=/?show_status=1>Верифицированные</a><br>
        <a href=/?show_status=2>Не подходят</a><br>
        """
    elif (show_status == "0") or (show_status == "None"):
        preview_items = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.status==0).all()
        settings_list_html += f"""
        <a href=/?show_status=all>Все</a><br>
        <b>Новые [{len(preview_items)}]</b><br>
        <a href=/?show_status=1>Верифицированные</a><br>
        <a href=/?show_status=2>Не подходят</a><br>
        """
    elif (show_status == "1"):
        preview_items = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.status==1).all()
        settings_list_html += f"""
        <a href=/?show_status=all>Все</a><br>
        <a href=/?show_status=0>Новые</a><br>
        <b>Верифицированные</b> [{len(preview_items)}]<br>
        <a href=/?show_status=2>Не подходят</a><br>
        """
    elif (show_status == "2"):
        preview_items = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.status==2).all()
        settings_list_html += f"""
        <a href=/?show_status=all>Все</a><br>
        <a href=/?show_status=0>Новые</a><br>
        <a href=/?show_status=1>Верифицированные</a><br>
        <b>Не подходят</b> [{len(preview_items)}]<br>
        """


    previews_list_html = "Страницы: "
    # пагинация
    page = str(request.args.get("page"))
    if page == "None":
        page = 1
    else:
        page = int(page)
    
    for page_i in range(1, len(preview_items)//10+2):
        if page_i == page:
            previews_list_html += f"<b>[ {page_i} ]</b> ~ "
        else:
            previews_list_html += f" <a href='/?page={page_i}&show_status={show_status}'>{page_i}</a> ~ "
    previews_list_html += "<p>"

    for preview_item in preview_items[(page-1)*10:page*10]:
        image_item = db.session.query(db.Monitor_Images).filter(and_(db.Monitor_Images.monitor_id==preview_item.id, db.Monitor_Images.is_main==1)).first()
        full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
        image_basename = str(os.path.basename(image_item.image_path))
        temp_image_path = os.path.join(static_temp_dir, image_basename)
        try:
            shutil.copy(full_image_path, temp_image_path)
        except:
            pass

        paragraph_item = db.session.query(db.Monitor_Paragraphs).filter(db.Monitor_Paragraphs.monitor_id==preview_item.id).first()
        
        
        if paragraph_item != None:
            previews_list_html += f"<p><table border=0><tr valign=top><td rowspan=2><img src='static/temp/{image_basename}' width=300></td>"
            previews_list_html += f"<td><h3><a href='show_pipeline?preview_id={preview_item.id}&show_status={show_status}'>{preview_item.title}</a></h3></td></tr>"
            previews_list_html += f"<tr valign=top><td>{paragraph_item.clear_text}</td></tr></table>"
        else:
            previews_list_html += f"<p><table border=0><tr valign=top><td rowspan=2><img src='static/temp/{image_basename}' width=300></td>"
            previews_list_html += f"<td><h3><a href='show_pipeline?preview_id={preview_item.id}&show_status={show_status}'>{preview_item.title}</a></h3></td></tr>"
            previews_list_html += f"</table>"



    return render_template('form1.html', title=title, breadcrumbs=breadcrumbs, previews_list_html=previews_list_html, settings_list_html=settings_list_html)






















@app.route('/show_pipeline', methods=['post', 'get'])
def show_pipeline():
    show_status = str(request.args.get("show_status"))

    preview_id = int(request.args.get("preview_id"))
    preview_item = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.id==preview_id).first()

    # Выводим пайплайн новости
    title = f"{preview_item.title} &mdash; Мониторинг открытых источников г.Новозыбков"
    
    # подтверждение ручной обработки
    if preview_item.status == 0:
        is_hand_html = f"""
        <b>Новая</b> ~ 
        <a href=/change_status?preview_id={preview_id}&status=1>Верифицировано</a> ~ 
        <a href=/change_status?preview_id={preview_id}&status=2>Не подходит</a>
        """
    elif preview_item.status == 1:
        is_hand_html = f"""
        <a href=/change_status?preview_id={preview_id}&status=0>Новая</a></a> ~ 
        <b>Верифицировано</b> ~ 
        <a href=/change_status?preview_id={preview_id}&status=2>Не подходит</a>
        """
    elif preview_item.status == 2:
        is_hand_html = f"""
        <a href=/change_status?preview_id={preview_id}&status=0>Новая</a> ~ 
        <a href=/change_status?preview_id={preview_id}&status=1>Верифицировано</a> ~ 
        <b>Не подходит</b>
        """
    
    breadcrumbs = f">> <a href='/?show_status={show_status}'>Новости</a> ->  {is_hand_html}" 
    h4 = f"{preview_item.title}"

    static_temp_dir = os.path.join(APP_DIR, "static", "temp")
    time.sleep(1) # PermissionError: [WinError 32] Процесс не может получить доступ к файлу, так как этот файл занят другим процессом:
    if os.path.isdir(static_temp_dir):
        shutil.rmtree(static_temp_dir)
    os.makedirs(static_temp_dir, exist_ok=True)
    




    """
     ██████    ███████    ██████     ██████     ██████     ██████    █████     
    ██         ██        ██    ██   ██         ██    ██   ██    ██   ██   ██   
    ██   ██    █████     ██    ██   ██   ██    ██    ██   ██    ██   ██   ██   
    ██    ██   ██        ██    ██   ██    ██   ██    ██   ██    ██   ██   ██   
    ██████     ███████    ██████    ██████      ██████     ██████    █████     
    """
    pipeline_html = ""
    # Подходят-ли изображения для геодетекции
    pipeline_html += f"""
    <h4>Шаги #100 &mdash; #200+. Подходят-ли изображения для геодетекции</h4>
    <table width=100% border=0><tr align=center bgcolor='#ffffff'>
    """

    # все виды обработки изображений на GeoGood
    try:
        img_proc_id = int(request.args.get("img_proc_id"))
    except:
        img_proc_id = 1

    max_td = 3
    pipeline_html += f"<table width=100% border=0><tr class=tab_text align=center bgcolor='#ffffff'><td class=unactive_tab>Модели GeoGood:</td>"
    # вывод типов обработки
    processing_desc = ""
    # типы процессинга, которые показываем
    processing_types_2show = ['Ручная разметка GeoGood', 'Mnet3 GeoGood #1']
    processing_items = db.session.query(db.Monitor_Image_Processing_Types).filter(db.Monitor_Image_Processing_Types.title.in_(processing_types_2show)).all()
    for processing_item in processing_items:
        if processing_item.id == img_proc_id:
            pipeline_html += f"<td width=35% class=active_tab><b>{processing_item.title}</b></td>"
            processing_desc = processing_item.desc
        else:
            pipeline_html += f"<td width=35% class=unactive_tab><a href='show_pipeline?preview_id={preview_id}&img_proc_id={processing_item.id}'>{processing_item.title}</a></td>"

    # дополняем таблицу ячейками справа, чтобы основные были слева
    for i in range(0, max_td-len(processing_items)-1):
        pipeline_html += f"<td width=35% class=unactive_tab></td>"
    
    pipeline_html += f"</tr><tr align=left><td colspan={max_td}>{processing_desc}</td></tr>"


    # выводим изображения
    pipeline_html += f"<tr><td colspan={max_td}><table width=100% border=0><tr align=center>"
    image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_id).order_by(db.Monitor_Images.id).all()
    for image_item in image_items[:5]:
        # копируем изображение в static/temp
        full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
        image_basename = str(os.path.basename(image_item.image_path))
        temp_image_path = os.path.join(static_temp_dir, image_basename)
        try:
            shutil.copy(full_image_path, temp_image_path)
        except:
            pass
        
        # выводим изображение
        status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==img_proc_id), (db.Monitor_Image_Statuses.key=="is_geo_good")).first()

        pipeline_html += f"<td width=300>"
        img_css_class = ""
        change_geo_str = ""
        if status_item != None:
            if status_item.value == "1":
                img_css_class = "geogood"
                change_geo_str = f"""
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=0>Плохое</a> ~ 
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=2>В помещении</a> ~ 
                <b>Хорошее</b> 
                """
            elif status_item.value == "2":
                img_css_class = "geointernal"
                change_geo_str = f"""
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=0>Плохое</a> ~ 
                <b>В помещении</b> ~ 
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=1>Хорошее</a>
                """
            else:
                img_css_class = "geobad"
                change_geo_str = f"""
                <b>Плохое</b> ~ 
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=2>В помещении</a> ~ 
                <a href=/change_geo_status?image_id={image_item.id}&preview_id={preview_id}&img_proc_id=1&geo_value=1>Хорошее</a>    
                """    
        # ручная разметка на GeoGood
        if img_proc_id == 1:
            pipeline_html += f"<img src='static/temp/{image_basename}' width=220 class={img_css_class}><br>{change_geo_str}"
        else:
            pipeline_html += f"<img src='static/temp/{image_basename}' width=220 class={img_css_class}><br>class: {status_item.value}</td>"



    pipeline_html += f"</tr></table></td></tr></table>"













    """
     ██████    ███████    ██████    ███     ██   ███████   ███████    
    ██         ██        ██    ██   ██ ██   ██   ██        ██    ██   
    ██   ██    █████     ██    ██   ██  ██  ██   █████     ███████    
    ██    ██   ██        ██    ██   ██   ██ ██   ██        ██  ██     
    ██████     ███████    ██████    ██     ███   ███████   ██    ██   
    """


    # Выделение GeoNER из текста новости
    pipeline_html += f"""
    <p>&nbsp;<p>&nbsp;<h4>Шаг #300+. Выделение GeoNER из текста новости</h4>
    """
    # все виды обработки текста
    try:
        process_id = int(request.args.get("process_id"))
    except:
        process_id = 1

    max_td = 6
    pipeline_html += f"<table width=100% border=0><tr class=tab_text align=center bgcolor='#ffffff'><td class=unactive_tab>Модели:</td>"
    # вывод типов обработки
    processing_desc = ""
    # типы процессинга, которые показываем
    processing_types_2show = ['Ручная разметка NER', 'spacy_ru_core_news_lg_2']
    processing_items = db.session.query(db.Monitor_Processing_Types).filter(db.Monitor_Processing_Types.title.in_(processing_types_2show)).all()
    for processing_item in processing_items:
        if processing_item.id == process_id:
            pipeline_html += f"<td width=25% class=active_tab><b>{processing_item.title}</b></td>"
            processing_desc = processing_item.desc
        else:
            pipeline_html += f"<td width=25% class=unactive_tab><a href='show_pipeline?preview_id={preview_id}&process_id={processing_item.id}'>{processing_item.title}</a></td>"
    # дополняем таблицу ячейками справа, чтобы основные были слева
    for i in range(0, max_td-len(processing_items)-1):
        pipeline_html += f"<td width=25% class=unactive_tab></td>"
    pipeline_html += f"</tr><tr align=left><td colspan={max_td}>{processing_desc}</td></tr>"


    pipeline_html += f"</tr><tr align=left><td colspan={max_td}>"
    # вывод токенов
    paragraphs_items = db.session.query(db.Monitor_Paragraphs).filter(db.Monitor_Paragraphs.monitor_id==preview_id).all()
    for paragraph_item in paragraphs_items:
        pipeline_html += f"<p>"
        words_items = db.session.query(db.Monitor_Paragraph_Words).filter(and_(db.Monitor_Paragraph_Words.paragraph_id==paragraph_item.id), (db.Monitor_Paragraph_Words.processing_version==process_id)).order_by(db.Monitor_Paragraph_Words.id).all()
        for word_item in words_items:
            if word_item.ner_type == "PERSON": 
                span_text = "<span class=ner_name>"
            elif word_item.ner_type in ["GPE", "LOC", "ORG"]: 
                span_text = "<span class=ner_loc>"
            else:
                span_text = "<span>"

            # ручная обработка
            if process_id==1:
                pipeline_html += f"<a href='/change_ner?preview_id={preview_id}&process_id={process_id}&word_id={word_item.id}'>{span_text}{word_item.text}</span></a> "
            else:
                pipeline_html += f"<li>{span_text}{word_item.text} &mdash; {word_item.ner_type}</span> "

    pipeline_html += f"</tr></table>"
















    """
    ███    ███   ███     ██   ███████   ████████    ██████    ███████    ██████    
    ██ █  █ ██   ██ ██   ██   ██           ██      ██         ██        ██    ██   
    ██  ██  ██   ██  ██  ██   █████        ██      ██   ██    █████     ██    ██   
    ██      ██   ██   ██ ██   ██           ██      ██    ██   ██        ██    ██   
    ██      ██   ██     ███   ███████      ██      ██████     ███████    ██████    
    """


    # Шаг #400+. Определение координат по фотографии места. Mnet3 GeoGuessr #1
    pipeline_html += f"""
    <p>&nbsp;<p>&nbsp;<h4>Шаг #400+. Определение координат по фотографии места.</h4>
    """

    try:
        # показываем панораму этого класса
        show_geo_class = int(request.args.get("show_geo_class"))
    except:
        # не показываем ничего
        show_geo_class = None

    if show_geo_class != None:
        with open(os.path.join(APP_DIR, 'classes.json'), 'r') as file:
            classes_list = json.load(file)

        selected_lat = None
        selected_long = None
        for class_item in classes_list:
            if class_item["class"] == show_geo_class:
                selected_lat = class_item["lat"]
                selected_long = class_item["long"]
                break

        if (selected_lat != None) and (selected_long != None):
            # показываем панораму
            with open(os.path.join(APP_DIR, 'tpl.html'), "r") as f:
                tpl = f.read()
            tpl_2_save = tpl.replace("{lat}", str(selected_lat))
            tpl_2_save = tpl_2_save.replace("{long}", str(selected_long))
            tpl_2_save = tpl_2_save.replace("{direct}", "90")

            pipeline_html += tpl_2_save




    try:
        img_geo_1 = int(request.args.get("img_geo_1"))
    except:
        img_geo_1 = 3 # id Mnet3 GeoGuessr #1 с ручной разметкой

    max_td = 6
    pipeline_html += f"<p><table width=100% border=0><tr class=tab_text align=center bgcolor='#ffffff'><td class=unactive_tab>Модели GeoOSINT:</td>"
    # вывод типов обработки
    processing_desc = ""
    # типы процессинга, которые показываем
    processing_types_2show = ['Mnet3 GeoGuessr #1', 'GeoGuessr ViT-Cos #1', 'K-Means #1']
    processing_items = db.session.query(db.Monitor_Image_Processing_Types).filter(db.Monitor_Image_Processing_Types.title.in_(processing_types_2show)).all()
    for processing_item in processing_items:
        if processing_item.id == img_geo_1:
            pipeline_html += f"<td width=35% class=active_tab><b>{processing_item.title}</b></td>"
            processing_desc = processing_item.desc
        else:
            pipeline_html += f"<td width=35% class=unactive_tab><a href='show_pipeline?preview_id={preview_id}&img_geo_1={processing_item.id}'>{processing_item.title}</a></td>"



    # дополняем таблицу ячейками справа, чтобы основные были слева
    for i in range(0, max_td-len(processing_items)-1):
        pipeline_html += f"<td width=35% class=unactive_tab></td>"
    
    pipeline_html += f"</tr><tr align=left><td colspan={max_td}>{processing_desc}</td></tr>"

    
    # Mnet3 GeoGuessr #1
    if img_geo_1 == 3:
        # выводим само изображение, его класс и другие изображения этого класса
        image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_id).order_by(db.Monitor_Images.id).all()
        for image_item in image_items[:5]:
            # копируем изображение в static/temp
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            image_basename = str(os.path.basename(image_item.image_path))
            temp_image_path = os.path.join(static_temp_dir, image_basename)
            try:
                shutil.copy(full_image_path, temp_image_path)
            except:
                pass
            
            # выводим изображение
            # выводим только подходящие для GeoGood
            status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==1), (db.Monitor_Image_Statuses.key=="is_geo_good")).first()
            if status_item != None: # изображение еще не обработано на GeoGood
                if status_item.value == "1":
                    status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==img_geo_1), (db.Monitor_Image_Statuses.key=="geo_class")).first()
                    if status_item != None:
                        geo_class = status_item.value

                        pipeline_html += f"""<tr align=right>
                        <td colspan=2 rowspan=2><img src='static/temp/{image_basename}' width=400 class={img_css_class}>
                        <h3>MNet ГеоКласс: {geo_class}</h3>
                        <a href=/show_pipeline?preview_id={preview_id}&img_geo_1={img_geo_1}&show_geo_class={geo_class}>Показать на панораме</a>; </td>
                        <td colspan=4 align=center valign=middle><h3>Другие фотографии этого предсказанного ГеоКласса</h3>
                        </td></tr>
                        <tr>                    
                        """
                        
                        # Вывод случайных изображений из этого MNet класса
                        DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
                        class_dir = os.path.join(DATA_DIR, str(geo_class))
                        class_images = os.listdir(class_dir)
                        random_class_images = random.choices(class_images, k=4)
                        for image_basename in random_class_images:
                            # копируем изображение в static/temp
                            full_image_path = os.path.join(class_dir, image_basename)
                            temp_image_path = os.path.join(static_temp_dir, image_basename)
                            try:
                                shutil.copy(full_image_path, temp_image_path)
                            except:
                                pass
                            pipeline_html += f"<td valign=bottom><img src='static/temp/{image_basename}' width=200></td>"
                        pipeline_html += f"</tr>"

                    
                    # класс, выбранный вручную
                    status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==7), (db.Monitor_Image_Statuses.key=="geo_class")).first()

                    if status_item != None:
                        hand_geo_class = status_item.value

                        pipeline_html += f"""<tr align=right>
                        <td colspan=2 rowspan=2>
                        <h3>Верифицированный ГеоКласс: {hand_geo_class}</h3>
                        <a href=/show_hand_map?preview_id={preview_id}&image_id={image_item.id}>Выбрать на карте</a>; </td>
                        <td colspan=4 align=center valign=middle><h3>Другие фотографии этого верифицированного ГеоКласса</h3>
                        </td></tr>
                        <tr>                    
                        """

                        # Вывод случайных изображений из этого Hand класса
                        DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
                        class_dir = os.path.join(DATA_DIR, str(hand_geo_class))
                        if os.path.isdir(class_dir):
                            class_images = os.listdir(class_dir)
                            random_class_images = random.choices(class_images, k=4)
                            for image_basename in random_class_images:
                                # копируем изображение в static/temp
                                full_image_path = os.path.join(class_dir, image_basename)
                                temp_image_path = os.path.join(static_temp_dir, image_basename)
                                try:
                                    shutil.copy(full_image_path, temp_image_path)
                                except:
                                    pass
                                pipeline_html += f"<td valign=bottom><img src='static/temp/{image_basename}' width=200></td>"
                            pipeline_html += f"</tr>"

                    else:
                        pipeline_html += f"""<tr align=right>
                        <td colspan=2>
                        <h3>Верифицированный ГеоКласс: Отсутств.</h3>
                        <a href=/show_hand_map?preview_id={preview_id}&image_id={image_item.id}>Выбрать на карте</a>; </td>
                        <td colspan=4 align=center valign=middle>
                        </td></tr>
                        <tr>                    
                        """






    """
     █████     ██████     ██████     ██   ███     ██   
    ██   ██   ██    ██   ██               ██ ██   ██   
    ██        ██    ██    █████      ██   ██  ██  ██   
    ██   ██   ██    ██        ██     ██   ██   ██ ██   
     █████     ██████    ██████      ██   ██     ███   
    """


    if img_geo_1 == 4:
        # выводим само изображение, его класс и другие изображения этого класса
        image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_id).order_by(db.Monitor_Images.id).all()
        for image_item in image_items[:5]:
            # копируем изображение в static/temp
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
            image_basename = str(os.path.basename(image_item.image_path))
            temp_image_path = os.path.join(static_temp_dir, image_basename)
            try:
                shutil.copy(full_image_path, temp_image_path)
            except:
                pass
            
            # выводим изображение
            # выводим только подходящие для GeoGood
            status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==1), (db.Monitor_Image_Statuses.key=="is_geo_good")).first()
            if status_item != None: # изображение еще не обработано на GeoGood
                if status_item.value == "1":

                    status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==3), (db.Monitor_Image_Statuses.key=="is_hand")).first()

                    if status_item == None:
                        img_css_class = "geobad"
                    else:
                        img_css_class = "geogood"


                    pipeline_html += f"""<tr align=right valign=top><td colspan=2 rowspan=2><img src='static/temp/{image_basename}' width=400 class={img_css_class}></td>
                    <td align=center colspan=4><h3>Похожие фотографии</h3></td>
                    </tr><tr>
                    """

                    # Вывод выбранных похожих
                    DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
                    status_list = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==4)).order_by(db.Monitor_Image_Statuses.id.desc()).all()

                    geo_class = None
                    cos_dist = None
                    image_basename = None

                    if status_list != None: # изображение еще не обработано на GeoGood
                        for status_item in status_list[:12]:
                            if status_item.key == "class_n":
                                geo_class = status_item.value
                                class_dir = os.path.join(DATA_DIR, str(geo_class))
                            
                            if status_item.key == "cos_dist":
                                cos_dist = status_item.value

                            if status_item.key == "filename":
                                image_basename = status_item.value

                            if (image_basename != None) and (cos_dist != None) and (geo_class != None):

                                full_image_path = os.path.join(class_dir, image_basename)
                                temp_image_path = os.path.join(static_temp_dir, image_basename)
                                try:
                                    shutil.copy(full_image_path, temp_image_path)
                                except:
                                    pass
                                pipeline_html += f"""<td valign=bottom align=center><img src='static/temp/{image_basename}' width=200><br>Класс: {geo_class}<br>cos_dist: {cos_dist}<br>
                                <a href=/show_pipeline?preview_id={preview_id}&img_geo_1={img_geo_1}&show_geo_class={geo_class}>Показать на панораме</a>;                                
                                
                                </td>"""

                                geo_class = None
                                cos_dist = None
                                image_basename = None

                    pipeline_html += f"</tr>"














    """
    ██    ██          ███    ███   ███████    █████    ███     ██    ██████   
    ██  ██            ██ █  █ ██   ██        ██   ██   ██ ██   ██   ██        
    ████      ██████  ██  ██  ██   █████     ███████   ██  ██  ██    █████    
    ██  ██            ██      ██   ██        ██   ██   ██   ██ ██        ██   
    ██    ██          ██      ██   ███████   ██   ██   ██     ███   ██████    

    """

    if img_geo_1 == 6:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        # загрузка списка классов с координатами
        with open(os.path.join(APP_DIR, 'classes.json'), 'r') as file:
            classes_list = json.load(file)

        classes_lat = {}
        classes_long = {}
        for classes_item in classes_list:
            classes_lat[str(classes_item["class"])]= classes_item["lat"]
            classes_long[str(classes_item["class"])]= classes_item["long"]


        # список подходящих классов, найденных предыдущими методами
        image_classes_list = []
        # список с координатами классов
        coords_list = []

        image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_id).all()
        for image_item in image_items:
            # обрабатывали ли изображение Mnet3 GeoGuessr #1
            image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==3), (db.Monitor_Image_Statuses.key=="geo_class")).first()            
            if image_status_item != None:
                image_class_item = {}
                image_class_item["id"] = image_status_item.id
                image_class_item["class"] = image_status_item.value
                image_classes_list.append(image_class_item)
                
                lat = float(classes_lat[image_status_item.value])
                long = float(classes_long[image_status_item.value])
                t = []
                t.append(lat)
                t.append(long)
                coords_list.append(t)

            # обрабатывали ли изображение GeoGuessr ViT-Cos #1
            image_status_items = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==4), (db.Monitor_Image_Statuses.key=="class_n")).all()            
            if image_status_items != None:
                for image_status_item in image_status_items:
                    image_class_item = {}
                    image_class_item["id"] = image_status_item.id
                    image_class_item["class"] = image_status_item.value
                    image_classes_list.append(image_class_item)

                    lat = float(classes_lat[image_status_item.value])
                    long = float(classes_long[image_status_item.value])
                    t = []
                    t.append(lat)
                    t.append(long)
                    coords_list.append(t)


        # определение лучшего разбиения на кластеры
        # https://ru.stackoverflow.com/questions/1356798/%D0%BF%D0%BE%D1%81%D0%BE%D0%B2%D0%B5%D1%82%D1%83%D0%B9%D1%82%D0%B5-%D0%BA%D0%B0%D0%BA-%D1%81%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C-%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8E-%D0%BE%D0%B4%D0%BD%D0%BE%D0%BC%D0%B5%D1%80%D0%BD%D0%BE%D0%B3%D0%BE-%D1%81%D0%BF%D0%B8%D1%81%D0%BA%D0%B0-%D1%86%D0%B5%D0%BB%D1%8B%D1%85-%D1%87%D0%B8%D1%81%D0%B5%D0%BB-%D0%B1%D0%B5%D0%B7-%D0%B7%D0%B0%D0%B4%D0%B0%D0%BD
        clusters = list(range(2, 5))
        scores = []
        clusters_centers = []
        for k in clusters:
            kmeans = KMeans(n_clusters=k, n_init=10).fit(coords_list)
            preds = kmeans.predict(coords_list)
            clusters_centers.append(kmeans.cluster_centers_)
            scores.append(silhouette_score(coords_list, preds))

        s, k = max(zip(scores, clusters))
        kmeans = KMeans(n_clusters=k, n_init=10).fit(coords_list)
        preds = kmeans.predict(coords_list)
        
        # кластер с наибольшим числом точек - правильный
        from statistics import mode
        most_frequent_claster = mode(preds)
        center_claster = kmeans.cluster_centers_[most_frequent_claster]
        
        claster_colors = []
        claster_colors.append("#f00")
        claster_colors.append("#00f")
        claster_colors.append("#0ff")
        claster_colors.append("#ff0")
        claster_colors.append("#f0f")
        claster_colors.append("#fff")
        # выводим метки
        geoObjects = "myMap.geoObjects"
        for i, point in enumerate(coords_list):
            current_class = check_class(classes_list, point[0], point[1])

            if (preds[i] == most_frequent_claster):
                geoObjects += f"""
                .add(new ymaps.Placemark([{point[0]}, {point[1]}], {{iconContent: "{current_class}"}},
                {{
                    preset: 'islands#StretchyIcon',
                    iconColor: '#00ff00'
                }}))
                """
            else:
                geoObjects += f"""
                .add(new ymaps.Placemark([{point[0]}, {point[1]}], {{iconContent: "{current_class}"}},
                {{
                    preset: "islands#StretchyIcon",
                    iconColor: '{claster_colors[preds[i]]}'
                }}))
                """

        geoObjects += ";"

        
        # выводим на карту
        pipeline_html += f"""<tr align=right valign=top><td colspan={max_td}>

            <div class="container"><div class="row">
                <div style="float: left;">
                    <div id="map" style="width: 800px; height: 600px"></div>
                </div>


            <script src="https://api-maps.yandex.ru/2.1/?apikey=e6b34264-72ad-4e9b-9c46-548063340836&lang=ru_RU" type="text/javascript"></script>

            <script>
                var myMap;

            // Дождёмся загрузки API и готовности DOM.
            ymaps.ready(init);

            function init () {{
                // Создание экземпляра карты и его привязка к контейнеру с
                // заданным id ("map").
                myMap = new ymaps.Map('map', {{
                    // При инициализации карты обязательно нужно указать
                    // её центр и коэффициент масштабирования.
                    center: [{center_claster[0]}, {center_claster[1]}], // ГАПОУ НППК
                    zoom: 15
                }}, {{
                    searchControlProvider: 'yandex#search'
                }});
                {geoObjects}
            }}

            window.myMap=myMap;
            </script>

    """
    pipeline_html += f"</tr></table>"
        







    # Шаг #600+. Показ детектированных объектов
    pipeline_html += f"""
    <p>&nbsp;<p>&nbsp;<h4>Шаги #700-800+. Показ детектированных и классифицированных объектов</h4>
    """
    pipeline_html += detected.get_detected_html(preview_id)







    return render_template('form2.html', title=title, breadcrumbs=breadcrumbs, h4=h4, pipeline_html=pipeline_html)



























@app.route('/show_hand_map', methods=['post', 'get'])
def show_hand_map():
    preview_id = int(request.args.get("preview_id"))
    image_id = int(request.args.get("image_id"))

    preview_item = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.id==preview_id).first()

    # Выводим пайплайн новости
    title = f"{preview_item.title} &mdash; Мониторинг открытых источников г.Новозыбков"
    
    breadcrumbs = f">> <a href='/'>Новости</a> ->  <a href=/show_pipeline?preview_id={preview_id}&img_geo_1=3>{preview_item.title}</a>"


    # выбранное изображение
    static_temp_dir = os.path.join(APP_DIR, "static", "temp")
    if os.path.isdir(static_temp_dir):
        shutil.rmtree(static_temp_dir)
    os.makedirs(static_temp_dir, exist_ok=True)

    image_item = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.id==image_id).first()
    # копируем изображение в static/temp
    full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)
    image_basename = str(os.path.basename(image_item.image_path))
    temp_image_path = os.path.join(static_temp_dir, image_basename)
    try:
        shutil.copy(full_image_path, temp_image_path)
    except:
        pass

    image_html = f"<img src='static/temp/{image_basename}' width=400>"

    return render_template('select_class_test.html', title=title, breadcrumbs=breadcrumbs, image_id=image_id, image_html=image_html)











@app.route('/change_geo_status', methods=['post', 'get'])
def change_geo_status():
    preview_id = int(request.args.get("preview_id"))
    image_id = int(request.args.get("image_id"))
    img_proc_id = 1
    geo_value = str(request.args.get("geo_value"))
    
   
    image_item = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.id==image_id).first()
    status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==img_proc_id), (db.Monitor_Image_Statuses.key=="is_geo_good")).first()

    if status_item != None: # изображение еще не обработано на GeoGood
        status_item.value = geo_value
        
    else:
        # добавляем статус изображению
        image_status_item = db.Monitor_Image_Statuses(
            image_id=image_item.id, 
            processing_version=1,
            key="is_geo_good",
            value=geo_value
        )
        db.session.add(image_status_item)


    db.session.commit()

    return redirect(f"/show_pipeline?preview_id={preview_id}&img_proc_id={img_proc_id}", code=302)
    







@app.route('/change_geo_class', methods=['post', 'get'])
def confirm_geo_class():
    image_id = int(request.args.get("image_id"))
    lat = float(request.args.get("lat"))
    long = float(request.args.get("long"))

    img_geo_1 = 7 #0390_GeoGuessr_Hand_1.py 

    geo_class = str(check_class(classes_list, lat, long))
    
    status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_id), (db.Monitor_Image_Statuses.processing_version==img_geo_1), (db.Monitor_Image_Statuses.key=="geo_class")).first()

    if status_item == None:
        # добавляем статус изображению
        image_status_item = db.Monitor_Image_Statuses(
            image_id=image_id, 
            processing_version=img_geo_1,
            key="geo_class",
            value=geo_class
        )
        db.session.add(image_status_item)
    else:
        status_item.value=geo_class

    db.session.commit()

    response = make_response(f"{geo_class}", 200)
    response.mimetype = "text/plain"
    return response








@app.route('/change_ner', methods=['post', 'get'])
def change_ner():
    preview_id = int(request.args.get("preview_id"))
    process_id = int(request.args.get("process_id"))
    word_id = int(request.args.get("word_id"))

    word_item = db.session.query(db.Monitor_Paragraph_Words).filter(and_(db.Monitor_Paragraph_Words.id==word_id)).first()

    if word_item.ner_type == "LOC":
        word_item.ner_type = ""
    else:
        word_item.ner_type = "LOC"

    db.session.commit()

    return redirect(f"/show_pipeline?preview_id={preview_id}&process_id={process_id}", code=302)



@app.route('/change_status', methods=['post', 'get'])
def change_status():
    preview_id = int(request.args.get("preview_id"))
    status = int(request.args.get("status"))

    preview_item = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.id==preview_id).first()

    preview_item.status = status

    return redirect(f"/show_pipeline?preview_id={preview_id}", code=302)
