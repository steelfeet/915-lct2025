import os, sys, random
import csv, json, shutil
import requests, time
from urllib.parse import urlparse

import numpy as np

import shutil



n = 0
CLASSES_DIR = os.path.join("d:\\", "_vault", "03-YaMap", "data")
os.makedirs(CLASSES_DIR, exist_ok=True)

for class_n in os.listdir(CLASSES_DIR):
    print(class_n)
    class_dir = os.path.join(CLASSES_DIR, class_n)
    for filename in os.listdir(class_dir):
        current_file_path = os.path.join(class_dir, filename)
        print(filename)
        """
        new_file_name = f"v0-{filename}"
        new_file_path = os.path.join(class_dir, new_file_name)

        os.rename(current_file_path, new_file_path)
        """

        
        shutil.copyfile(current_file_path, os.path.join("d:\\", "_vault", "02-ClearDS", "good", filename))
        n += 1
        print(n)
        if n == 1000:
            print("sucess")
            exit()