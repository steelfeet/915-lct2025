import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np


# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)


with open(os.path.join(BASE_DIR, 'classes.json'), 'r') as file:
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

