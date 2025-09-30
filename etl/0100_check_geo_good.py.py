import numpy as np # linear algebra

import torch
import torch.nn as nn
import torchvision
from torch.utils.data import Dataset, DataLoader, random_split
import torch.optim.lr_scheduler as lr_scheduler

import albumentations as A
from albumentations.pytorch import ToTensorV2

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image


from sqlalchemy import and_
from sqlalchemy.sql.expression import func, select

# директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print(f"BASE_DIR: {BASE_DIR}")
sys.path.append(BASE_DIR)
sys.path.insert(0, BASE_DIR)
import db, vault

DATA_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "good-bad")
MODEL_DIR = os.path.join("d:\\", "_vault", "02-ClearDS", "models")
# текущая (промежуточного сохранения)
MODEL_NAME = "mnet_good-bad"
# лучшая
BEST_MODEL_NAME = f"{MODEL_NAME}_best"
IM_SIZE = 512




processing_title = "Mnet3 GeoGood #1"
processing_desc = "Первый вариант MobileNet v3 на основе вручную отобранных изображений из vk. 02-ClearDS/geo_2.mobilenet.good-bad.teach.py"




processing_item = db.session.query(db.Monitor_Image_Processing_Types).filter(db.Monitor_Image_Processing_Types.title==processing_title).first()
if processing_item == None:
    # добавляем тип обработки
    processing_item = db.Monitor_Image_Processing_Types(
        title=processing_title, 
        desc=processing_desc 
    )
    db.session.add(processing_item)
    db.session.flush()
    db.session.refresh(processing_item)
    db.session.commit()


processing_id = processing_item.id
print(f"processing_id: {processing_id}")


ValidTransform = A.Compose([
    A.Resize(IM_SIZE,IM_SIZE),
    A.CenterCrop(IM_SIZE,IM_SIZE),
    A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ToTensorV2()])


if __name__ == '__main__':

    model = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1)

    #перенастраиваем модель под наши классы
    for param in model.parameters():
        param.requires_grad = False
    n_inputs = model.classifier[0].in_features
    last_layer = nn.Linear(n_inputs, 3)
    model.classifier = last_layer

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


    pred_0 = 0
    pred_1 = 1
    preview_items = db.session.query(db.Monitor_Previews).filter(db.Monitor_Previews.status==0).all()
    print(f"Новостей в статусе '0': {len(preview_items)}")
    for preview_item in tqdm(preview_items):
        image_items = db.session.query(db.Monitor_Images).filter(db.Monitor_Images.monitor_id==preview_item.id).all()
        for image_item in image_items:
            full_image_path = os.path.join(vault.VAULT_DIR, image_item.image_path)

            im_new = Image.open(full_image_path)
            try:
                image_array = np.array(im_new.getdata()).reshape(im_new.size[0], im_new.size[1], 3).astype(np.float32)
                # image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)


                input = ValidTransform(image=image_array)
                # unsqueeze batch dimension, in case you are dealing with a single image
                input = input["image"].unsqueeze(0)
                input = input.to(device)
                # Get prediction
                with torch.no_grad():
                    logits = model(input)
                top_class = logits.argmax(dim=1)
                predicted_class = int(top_class.cpu()[0])

                if predicted_class == 0:
                    pred_0 += 1
                    cv2.imwrite("saved_image.png", im_new)
                else:
                    pred_1 += 1
                    image_item.is_geo_good = 1

                # добавляем статус изображению
                image_status_item = db.Monitor_Image_Statuses(
                    image_id=image_item.id, 
                    processing_version=processing_id,
                    key="is_geo_good",
                    value=predicted_class
                )
                db.session.add(image_status_item)

            except:
                pass
        preview_item.status = 1
        db.session.commit()


print(f"stat: pred_0: {pred_0}; pred_1: {pred_1}")