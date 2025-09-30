import os, string, random
from datetime import datetime

def random_string(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

VAULT_DIR = os.path.join("d:\\", "_vault")
os.makedirs(VAULT_DIR, exist_ok=True)

def get_vault_dirs(donor):
   date = datetime.now()
   current_upload_dir = os.path.join(donor, str(date.year), str(date.month), str(date.day), str(date.hour))
   image_dir = os.path.join(VAULT_DIR, current_upload_dir)
   os.makedirs(image_dir, exist_ok=True)

   return image_dir, current_upload_dir
