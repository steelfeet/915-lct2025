# https://www.kaggle.com/code/danielhanchen/gemma-3n-4b-multimodal-finetuning-inference
# https://www.kaggle.com/code/danielhanchen/gemma-3n-4b-vision-finetuning

import os, sys
from unsloth import FastModel

from transformers import TextStreamer
import torch
import torch._dynamo
torch._dynamo.config.suppress_errors = True

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEMMA_DIR = os.path.join("d:\\", "_vault", "06-Gemma", "data")

TARGET = (512, 512)
system_message = "You are a helpful AI assistant specialized in determining the name of a place, street, alley, building from its image. Provide concise and accurate information."
system_message = "Опиши, что ты видишь на русском языке"
system_message = "Вы — полезный ИИ-помощник, который специализируется на определении названия места, улицы, переулка или здания по изображению. Предоставляйте краткую и точную информацию."

cache_dir = os.path.join("d:\\", "_models", "huggingface.co")

os.environ['HF_HOME'] = cache_dir
os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir





model, processor = FastModel.from_pretrained(
    model_name=os.path.join(cache_dir, "gemma3n_ru_1"),  # YOUR MODEL YOU USED FOR TRAINING
    load_in_4bit=True,  # Set to False for 16bit LoRA
    cache_dir = cache_dir
)
FastModel.for_inference(model)  # Enable for inference!


# Helper function for inference
def do_gemma_3n_inference(image_path):
    FastModel.for_inference(model)
    
    loaded_image = Image.open(image_path).convert("RGB").resize(TARGET, resample=Image.BILINEAR)
    messages = [
        {
            "role": "user",
            "content": [{"type": "image"}, {"type": "text", "text": system_message}],
        }
    ]
    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(
        loaded_image,
        input_text,
        add_special_tokens=False,
        return_tensors="pt",
    ).to("cuda")

    text_streamer = TextStreamer(processor, skip_prompt=True)
    result = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128,
                            use_cache=True, temperature = 1.0, top_p = 0.95, top_k = 6)



sloth_path = os.path.join(BASE_DIR, "v0-52.524000-52.524000-0.jpg")

# You might have to wait 1 minute for Unsloth's auto compiler
do_gemma_3n_inference(sloth_path)


