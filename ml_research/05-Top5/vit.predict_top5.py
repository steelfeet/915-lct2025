import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader, random_split

import os, sys
import json, random
import pathlib, cv2
from tqdm import tqdm

from sqlalchemy import and_


from PIL import Image, ImageDraw

import albumentations as A
from albumentations.pytorch import ToTensorV2


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "data")
MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")

IM_SIZE = 512

# сбрасывать ли последний слой (при смене и объединении классов)
RESET_LINEAR = False

# текущая (промежуточного сохранения)
MODEL_NAME = "vit_l_32_224"

TOP_CLASSES = 10

IM_SIZE = 224
# текущая (промежуточного сохранения)
# лучшая
BEST_MODEL_NAME = f"{MODEL_NAME}_best"



full_predicted = 0
full_n = 0
full_stat_dict = {}


ValidTransform = A.Compose([
    A.Resize(IM_SIZE,IM_SIZE),
    A.CenterCrop(IM_SIZE,IM_SIZE),
    A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ToTensorV2()])

if __name__ == '__main__':

    ds_dir = DATA_DIR
    subfolders_n = [ int(os.path.basename(f)) for f in os.scandir(ds_dir) if f.is_dir() ]
    NUM_CL = max(subfolders_n) + 1
    print(f"NUM_CL = {NUM_CL}")

    model = torchvision.models.vit_l_32(weights=torchvision.models.ViT_L_32_Weights.IMAGENET1K_V1)

    #перенастраиваем модель под наши классы
    for param in model.parameters():
        param.requires_grad = False

    n_inputs = model.heads.head.in_features
    last_layer = nn.Linear(n_inputs, NUM_CL)
    model.heads.head = last_layer

    # если есть - загружаем
    BEST_MODEL_PATH = pathlib.Path(MODEL_DIR, f"{BEST_MODEL_NAME}.pth")
    print(BEST_MODEL_PATH)
    if BEST_MODEL_PATH.is_file():
        print("best file exist, load")
        model.load_state_dict(torch.load(BEST_MODEL_PATH))
    else:
        print("no best model")
    model.eval()



    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    torch.cuda.empty_cache()
    print("device: ", device)
    print()

    for class_id in tqdm(os.listdir(DATA_DIR)):
        class_dir = os.path.join(DATA_DIR, class_id)
        for filename in os.listdir(class_dir):
            current_file_path = os.path.join(class_dir, filename)

            im_new = Image.open(current_file_path)
            image_array = np.array(im_new.getdata()).reshape(im_new.size[0], im_new.size[1], 3).astype(np.float32)
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            
            
            input_img = ValidTransform(image=image_array)
            # unsqueeze batch dimension, in case you are dealing with a single image
            input_img = input_img["image"].unsqueeze(0)
            input_img = input_img.to(device)
            # Get prediction
            with torch.no_grad():
                logits = model(input_img)
            """
            ps = torch.exp(logits)        
            _, top_class = ps.topk(1, dim=1)
            """
            top_classes = []
            top_classes = np.argsort(logits.cpu(), axis=1)[0].tolist()
            top_classes.reverse()
            """
            print()
            print(f"{class_id}")
            print(top_classes[:TOP_CLASSES])
            """

            data_item = {}
            if int(class_id) in top_classes[:TOP_CLASSES]: 
                full_predicted += 1

            full_n += 1



print(f"top {TOP_CLASSES} session accuracy: {full_predicted} / {full_n} = {(full_predicted / full_n * 100):.6f}%")
print("success")