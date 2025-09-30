import numpy as np # linear algebra

import os, sys
import json

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

# директория файла
APP_DIR = os.path.join(os.path.abspath((os.path.dirname(__file__))), "app")

# тестируем на 
# http://127.0.0.1:3000/show_pipeline?preview_id=3&show_status=all
monitor_id = 3

classes_lat = {}
classes_long = {}
with open(os.path.join(APP_DIR, 'classes.json'), 'r') as file:
    classes_list = json.load(file)
for classes_item in classes_list:
    classes_lat[str(classes_item["class"])]= classes_item["lat"]
    classes_long[str(classes_item["class"])]= classes_item["long"]


image_classes_list = []

image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==monitor_id).all()
for image_item in image_items:
    # обрабатывали ли изображение Mnet3 GeoGuessr #1
    image_status_item = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==3), (db.Monitor_Image_Statuses.key=="geo_class")).first()            
    if image_status_item != None:
        image_class_item = {}
        image_class_item["id"] = image_status_item.id
        image_class_item["class"] = image_status_item.value
        image_classes_list.append(image_class_item)

    # обрабатывали ли изображение GeoGuessr ViT-Cos #1
    image_status_items = db.session.query(db.Monitor_Image_Statuses).filter(and_(db.Monitor_Image_Statuses.image_id==image_item.id), (db.Monitor_Image_Statuses.processing_version==4), (db.Monitor_Image_Statuses.key=="class_n")).all()            
    if image_status_items != None:
        for image_status_item in image_status_items:
            image_class_item = {}
            image_class_item["id"] = image_status_item.id
            image_class_item["class"] = image_status_item.value
            image_classes_list.append(image_class_item)


# ищем среднюю точку
sum_lat = 0
average_lat = 0
sum_long = 0
average_long = 0
for image_class_item in image_classes_list:
    lat = float(classes_lat[image_class_item["class"]])
    long = float(classes_long[image_class_item["class"]])

    sum_lat += lat
    sum_long += long

average_lat = sum_lat / len(image_classes_list)
average_long = sum_long / len(image_classes_list)
print(f"average_lat: {average_lat}; average_long: {average_long}")


# ищем расстояния между изображением и средней точкой
delta_classes_list = []
delta_list = []
for image_class_item in image_classes_list:
    lat = float(classes_lat[image_class_item["class"]])
    long = float(classes_long[image_class_item["class"]])

    delta = (average_lat - lat) * (average_lat - lat) + (average_long - long) * (average_long - long)
    image_class_item["delta"] = delta * 10000
    delta_classes_list.append(image_class_item)
    t = []
    t.append(lat)
    t.append(long)
    delta_list.append(t)

print(delta_list)

# определение лучшего разбиения на кластеры
# https://ru.stackoverflow.com/questions/1356798/%D0%BF%D0%BE%D1%81%D0%BE%D0%B2%D0%B5%D1%82%D1%83%D0%B9%D1%82%D0%B5-%D0%BA%D0%B0%D0%BA-%D1%81%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C-%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8E-%D0%BE%D0%B4%D0%BD%D0%BE%D0%BC%D0%B5%D1%80%D0%BD%D0%BE%D0%B3%D0%BE-%D1%81%D0%BF%D0%B8%D1%81%D0%BA%D0%B0-%D1%86%D0%B5%D0%BB%D1%8B%D1%85-%D1%87%D0%B8%D1%81%D0%B5%D0%BB-%D0%B1%D0%B5%D0%B7-%D0%B7%D0%B0%D0%B4%D0%B0%D0%BD
clusters = list(range(2, 5))
scores = []
clusters_centers = []
for k in clusters:
    kmeans = KMeans(n_clusters=k, n_init=10).fit(delta_list)
    preds = kmeans.predict(delta_list)
    clusters_centers.append(kmeans.cluster_centers_)
    scores.append(silhouette_score(delta_list, preds))

s, k = max(zip(scores, clusters))
print(s, k)