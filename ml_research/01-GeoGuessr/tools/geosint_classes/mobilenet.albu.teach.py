"""
https://www.kaggle.com/sharansmenon/herbarium-pytorch

"""
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision.utils import save_image
import torch.optim.lr_scheduler as lr_scheduler

import albumentations as A
from albumentations.pytorch import ToTensorV2

import os, sys
import json
import pathlib, cv2
from tqdm import tqdm

from PIL import Image







BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join("d:\\", "coins-ds", "ds429.gen1")
MODEL_DIR = os.path.join("d:\\", "coins-ds", "a0", "models-27")

STEP = 2

STAT_DIR = os.path.join(BASE_DIR, "stat", f"step_{STEP}")

# mobilenet
BATCH = 3
EPOCHS = 100
total_iters = 30 # lr_scheduler
LR = 0.001
IM_SIZE = 512

# сбрасывать ли последний слой (при смене и объединении классов)
RESET_LINEAR = False

# текущая (промежуточного сохранения)
MODEL_NAME = "a027"


# стартовая (теперь можно, трейн отдельно от валидации)
START_MODEL_NAME = "s0_best"
START_NUM_CL = 382

# лучшая
BEST_MODEL_NAME = f"{MODEL_NAME}_best"

# история обучения
training_history_path = os.path.join(STAT_DIR, f"training_history_{MODEL_NAME}_s{STEP}.json")
validation_history_path = os.path.join(STAT_DIR, f"validation_history_{MODEL_NAME}_s{STEP}.json")
train_items_loss_path = os.path.join(STAT_DIR, f"train_items_{MODEL_NAME}_loss_s{STEP}.json")
valid_items_loss_path = os.path.join(STAT_DIR, f"valid_items_{MODEL_NAME}_loss_s{STEP}.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(STAT_DIR, exist_ok=True)




class GetData(Dataset):
    """
    Аналог ImageFolder, но в качестве меток отдает не порядок папок (иначе путает 1, 10 (который становится 2), 100 (становится 3)), а имя самой папки в int
    ds_type - папка с данными внутри DATA_DIR, например train, valid или test
    """
    def __init__(self, ds_type, Transform):
        ds_dir = os.path.join(DATA_DIR, ds_type)
        subfolders = [ f.path for f in os.scandir(ds_dir) if f.is_dir() ]

        DSList = []
        for sn_path in subfolders:
            sn_id = int(os.path.basename(sn_path))
            images_paths = [ f.path for f in os.scandir(sn_path) ]
            for image_path in images_paths:
                item = {}
                item["src"] = image_path
                item["id"] = int(os.path.basename(image_path).split('.')[0])
                item["y"] = sn_id
                DSList.append(item)

        self.fnames = DSList
        self.transform = Transform
        
    def __len__(self):
        return len(self.fnames)

    def __getitem__(self, index):       
        item = self.fnames[index]
        src = item["src"]
        image = cv2.imread(src)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.transform(image=image)["image"]

        # temp_path = os.path.join("d:\\", "0d", "temp", os.path.basename(item["src"]))
        #save_image(image, temp_path)

        y = item["y"]
        id = item["id"]
        return image, y, id




if __name__ == '__main__':
    
    ds_dir = os.path.join(DATA_DIR, "train")
    subfolders_n = [ int(os.path.basename(f)) for f in os.scandir(ds_dir) if f.is_dir() ]
    NUM_CL = max(subfolders_n) + 1
    print(f"NUM_CL = {NUM_CL}")

    #Загружаем изображения
    from PIL import Image

    TrainTransform = A.Compose(
    [
        A.Resize(IM_SIZE,IM_SIZE),
        A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.05, rotate_limit=15, p=0.5),
        # A.RGBShift(r_shift_limit=15, g_shift_limit=15, b_shift_limit=15, p=0.5),
        # A.MultiplicativeNoise(multiplier=[0.5, 1.5], elementwise=True, per_channel=True, p=0.5),
        # A.CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), always_apply=False, p=0.5), - перестановки, хз зачем вообще
        A.CoarseDropout(max_holes=10, max_height=20, max_width=20, fill_value=255, p=0.5),
        A.Blur(blur_limit=(1, 1), p=0.5),
        A.RandomBrightnessContrast(p=0.5),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]
)

    ValidTransform = A.Compose([
        A.Resize(IM_SIZE,IM_SIZE),
        A.CenterCrop(IM_SIZE,IM_SIZE),
        A.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ToTensorV2()])


    train_set = GetData("train", TrainTransform)    
    valid_set = GetData("valid", ValidTransform)    

    trainloader = DataLoader(train_set, batch_size=BATCH, shuffle=True, num_workers=6)
    validloader = DataLoader(valid_set, batch_size=BATCH, shuffle=True, num_workers=6)

    print("trainloader shape: ")
    print(next(iter(trainloader))[0].shape)
    print()


    model = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1)

    #перенастраиваем модель под наши классы
    for param in model.parameters():
        param.requires_grad = False

    n_inputs = model.classifier[0].in_features
    last_layer = nn.Linear(n_inputs, NUM_CL)
    model.classifier = last_layer


    # если есть - загружаем
    MODEL_PATH = pathlib.Path(MODEL_DIR, f"{MODEL_NAME}.pth")
    BEST_MODEL_PATH = pathlib.Path(MODEL_DIR, f"{MODEL_NAME}_best.pth")
    START_MODEL_PATH = pathlib.Path(MODEL_DIR, f"{START_MODEL_NAME}.pth")

    BEST_LOSS_PATH = pathlib.Path(STAT_DIR, f"{MODEL_NAME}_best_loss.txt")
    START_LOSS_PATH = pathlib.Path(STAT_DIR, f"{START_MODEL_NAME}_loss.txt")


    min_valid_loss = np.inf

    if START_MODEL_PATH.is_file():
        print("start file exist, load")
        
        """
        #перенастраиваем модель под наши классы
        for param in model.parameters():
            param.requires_grad = False

        n_inputs = model.classifier.in_features
        last_layer = nn.Linear(n_inputs, START_NUM_CL)
        model.classifier = last_layer

        model.load_state_dict(torch.load(START_MODEL_PATH))
        last_layer = nn.Linear(n_inputs, NUM_CL)
        model.classifier = last_layer
        """

        model.load_state_dict(torch.load(START_MODEL_PATH))

        try:
            # лучший и для старотовой - лучший
            with open(START_LOSS_PATH) as my_file:
                min_valid_loss = float(my_file.read())
        except:
            min_valid_loss = min_valid_loss
    else:
        print("no start model")

    if BEST_MODEL_PATH.is_file():
        print("best file exist, load")
        model.load_state_dict(torch.load(BEST_MODEL_PATH))
        try:
            with open(BEST_LOSS_PATH) as my_file:
                min_valid_loss = float(my_file.read())
        except:
            min_valid_loss = min_valid_loss
    else:
        print("no best model")
        

    if MODEL_PATH.is_file():
        print("current file exist, load")
        model.load_state_dict(torch.load(MODEL_PATH))
        try:
            with open(BEST_LOSS_PATH) as my_file:
                min_valid_loss = float(my_file.read())
        except:
            min_valid_loss = min_valid_loss
    else:
        print("no current model")


    model.eval()
    print(f"min_valid_loss: {min_valid_loss}")
    print()

    if RESET_LINEAR:
        n_inputs = model.classifier.in_features
        last_layer = nn.Linear(n_inputs, NUM_CL)
        model.classifier = last_layer
        model.eval()
        print(f"RESET LINEAR")
        print()


    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    torch.cuda.empty_cache()
    print("device: ", device)
    print()


    #настройки обучения
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=LR)
    scheduler = lr_scheduler.LinearLR(optimizer, start_factor=1.0, end_factor=0.1, total_iters=total_iters)

    if os.path.isfile(training_history_path):
        with open(training_history_path) as fp:
            training_history = json.load(fp)
        with open(validation_history_path) as fp:
            validation_history = json.load(fp)
    else:
        training_history = {'accuracy':[],'loss':[]}
        validation_history = {'accuracy':[],'loss':[]}

    
    
    # потери для каждого объекта по отдельности
    prev_valid_loss = 0
    prev_train_loss = 0
    
    if os.path.isfile(train_items_loss_path):
        with open(train_items_loss_path) as fp:
            train_items_losses = json.load(fp)
    else:
        train_items_losses = {}
    if os.path.isfile(valid_items_loss_path):
        with open(valid_items_loss_path) as fp:
            valid_items_losses = json.load(fp)
    else:
        valid_items_losses = {}
    
    
    
    
    
    
    # Training with Validation
    for e in range(EPOCHS):
        train_acc = 0.0
        train_loss = 0.0
        for data, labels, ids in tqdm(trainloader):
            # Transfer Data to GPU if available
            # if torch.cuda.is_available():
                #data, labels = data.cuda(), labels.cuda()
            data, labels = data.to(device), labels.to(device)

            # Clear the gradients
            optimizer.zero_grad()
            # Forward Pass
            target = model(data)
            # Find the Loss
            loss = criterion(target,labels)
            # Calculate gradients
            loss.backward()
            # Update Weights
            optimizer.step()

            # Calculate Loss
            train_loss += loss.item()

            # Calculate Items Loss
            if (prev_train_loss>0):
                for id in ids:
                    try:
                        train_items_losses[int(id)] += float(loss.item() / BATCH / prev_train_loss)
                    except:
                        train_items_losses[int(id)] = float(loss.item() / BATCH / prev_train_loss)


            # Calculate Accuracy
            acc = ((target.argmax(dim=1) == labels).float().mean())
            train_acc += acc

        train_acc = train_acc / len(trainloader) * 100
        prev_train_loss = train_loss
        train_loss = train_loss / len(trainloader)        
        training_history['accuracy'].append(float(train_acc))
        training_history['loss'].append(float(train_loss))

        # Saving State Dict
        torch.save(model.state_dict(), MODEL_PATH)
        torch.cuda.empty_cache()

        before_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()
        after_lr = optimizer.param_groups[0]["lr"]


        valid_acc = 0.0
        valid_loss = 0.0
        model.eval()     # Optional when not using Model Specific layer
        for data, labels, ids in tqdm(validloader):
            # Transfer Data to GPU if available
            data, labels = data.to(device), labels.to(device)        
            # Forward Pass
            target = model(data)
            # Find the Loss
            loss = criterion(target,labels)
            # Calculate Loss
            valid_loss += loss.item()
            # Calculate Accuracy
            acc = ((target.argmax(dim=1) == labels).float().mean())
            valid_acc += acc

            # Calculate Items Loss
            if prev_valid_loss > 0:
                for id in ids:
                    try:
                        valid_items_losses[int(id)] += float(loss.item() / BATCH / prev_valid_loss)
                    except:
                        valid_items_losses[int(id)] = float(loss.item() / BATCH / prev_valid_loss)

        valid_acc = valid_acc / len(validloader) * 100
        prev_valid_loss = valid_loss
        valid_loss = valid_loss / len(validloader)
        validation_history['accuracy'].append(float(valid_acc))
        validation_history['loss'].append(float(valid_loss))

        print(f'Epoch {e+1} | Train Acc: {train_acc:.6f} | Train Loss: {train_loss:.6f} | Valid Acc: {valid_acc:.6f} | Valid Loss: {valid_loss:.6f}')
        print(f"before_lr: {before_lr:.4f} -> {after_lr:.4f}")
        
        if min_valid_loss > valid_loss:
            print(f'Validation Loss Decreased({min_valid_loss:.6f}--->{valid_loss:.6f}) \t Saving The Model')
            min_valid_loss = valid_loss
            
            # Saving State Dict
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            with open(BEST_LOSS_PATH, "w+") as my_file:
                my_file.write(str(valid_loss))


        with open(training_history_path, 'w+', encoding='utf-8') as f:
            json.dump(training_history, f, ensure_ascii=False, indent=4)
            f.close()
        with open(validation_history_path, 'w+', encoding='utf-8') as f:
            json.dump(validation_history, f, ensure_ascii=False, indent=4)
            f.close()

        with open(train_items_loss_path, 'w+', encoding='utf-8') as f:
            json.dump(train_items_losses, f, ensure_ascii=False, indent=4)
            f.close()
        with open(valid_items_loss_path, 'w+', encoding='utf-8') as f:
            json.dump(valid_items_losses, f, ensure_ascii=False, indent=4)
            f.close()



        print()

    print()
    print("success")
    print()
