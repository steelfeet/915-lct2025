import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np


# 0.0001 - 10 m
step = 0.001

# парсим Новозыбков 
left_x, top_y = 52.544, 31.903  # улица ОХ Волна Революции
right_x, bottom_y = 52.518, 31.949 # Жертвам Холокоста

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)



classes_list = []
class_n = 0
for lat in np.arange(right_x, left_x, step):
    for long in np.arange(top_y, bottom_y, step):
        class_n += 1
        formatted_lat = "%.3f" % lat
        formatted_long = "%.3f" % long

        class_item = {}
        class_item["class"] = class_n
        class_item["lat"] = formatted_lat
        class_item["long"] = formatted_long

        classes_list.append(class_item)

with open(os.path.join(BASE_DIR, 'classes.json'), "w") as f:
    json.dump(classes_list, f, indent=4)

