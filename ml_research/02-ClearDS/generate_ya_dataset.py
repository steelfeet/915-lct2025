import os, sys, random
import csv, json, shutil
import requests, time
from tqdm import tqdm
from urllib.parse import urlparse


import shutil
from pathlib import Path


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
import get_class

with open(os.path.join(BASE_DIR, 'classes.json'), 'r') as file:
    classes_list = json.load(file)

CLASSES_DIR = os.path.join("d:\\", "_vault", "03-YaMap", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

for class_n in os.listdir(CLASSES_DIR):
    class_dir = os.path.join(CLASSES_DIR, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)
        file_path = Path(current_file_path)
        filename_without_extension = file_path.stem

        t, lat, long, direction = filename_without_extension.split("-")
        class_n = get_class.check_class(classes_list, lat , long)
        print(class_n)
        class_path = os.path.join("d:\\", "_vault", "02-ClearDS", "data", str(class_n))
        os.makedirs(class_path, exist_ok=True)
        shutil.copyfile(current_file_path, os.path.join(class_path, filename))