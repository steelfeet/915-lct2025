# https://www.kaggle.com/code/danielhanchen/gemma-3n-4b-multimodal-finetuning-inference
# https://www.kaggle.com/code/danielhanchen/gemma-3n-4b-vision-finetuning

import os, sys
from unsloth import FastModel # FastLanguageModel for LLMs
import torch

import torch._dynamo
torch._dynamo.config.suppress_errors = True
from transformers import TextStreamer

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







# dataset 
def format_data_for_trl(image_path, text_content):
    loaded_image = Image.open(image_path).convert("RGB").resize(TARGET, resample=Image.BILINEAR)
    content_parts = []
    content_parts.append({"type":"text","text":system_message})
    content_parts.append({"type":"image", "image": loaded_image})
    trl_messages = [{"role":"user","content":content_parts}]  # FIXED: was tuple, now list

    content_parts = []
    content_parts.append({"type":"text", "text": text_content})
    trl_messages.append({"role": "assistant", "content": content_parts})
    return {"messages": trl_messages}


train_dataset = []
for class_n in os.listdir(GEMMA_DIR):
    gemma_class_dir = os.path.join(GEMMA_DIR, class_n)
    for filename in os.listdir(gemma_class_dir):
        if (filename.endswith(".txt")) and (not "en" in filename):
            txt_path = os.path.join(gemma_class_dir, filename)
            with open(txt_path, 'r', encoding='utf-8') as file:
                ru_street_text = file.read()
            
            jpg_filename = filename.replace("txt", "jpg")
            jpg_path = os.path.join(gemma_class_dir, jpg_filename)

            ru_street_list = ru_street_text.split(";")
            for ru_street_item in ru_street_list:
                if not "_" in ru_street_item:
                    ru_street_item = f"город Новозыбков, {ru_street_item}"
                    trl_message = format_data_for_trl(jpg_path, ru_street_item)
                    train_dataset.append(trl_message)



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


















model, processor = FastModel.from_pretrained(
    model_name = "unsloth/gemma-3-27b-it", # Or "unsloth/gemma-3n-E2B-it"
    dtype = None, # None for auto detection
    max_seq_length = 1024, # Choose any for long context!
    load_in_4bit = False,  # 4 bit quantization to reduce memory
    full_finetuning = False, # [NEW!] We have full finetuning now!
    # token = "hf_...", # use one if using gated models
    cache_dir = cache_dir
)


model = FastModel.get_peft_model(
    model,
    finetune_vision_layers     = True, # False if not finetuning vision layers
    finetune_language_layers   = True, # False if not finetuning language layers
    finetune_attention_modules = True, # False if not finetuning attention layers
    finetune_mlp_modules       = True, # False if not finetuning MLP layers

    r = 32,                           # The larger, the higher the accuracy, but might overfit
    lora_alpha = 32,                  # Recommended alpha == r at least
    lora_dropout = 0,
    bias = "none",
    random_state = 3407,
    use_rslora = False,               # We support rank stabilized LoRA
    loftq_config = None,              # And LoftQ
    target_modules = "all-linear",    # Optional now! Can specify a list if needed
)



from unsloth import get_chat_template
processor = get_chat_template(
    processor,
    "gemma-3"
)






sloth_path = os.path.join(BASE_DIR, "v0-52.522000-52.522000-0.jpg")
# You might have to wait 1 minute for Unsloth's auto compiler
do_gemma_3n_inference(sloth_path)






from unsloth.trainer import UnslothVisionDataCollator
from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    processing_class=processor.tokenizer,
    data_collator=UnslothVisionDataCollator(model, processor),
    args = SFTConfig(
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 4,
        max_grad_norm = 0.3,            # max gradient norm based on QLoRA paper
        warmup_ratio = 0.03,
        max_steps = 200,
        #num_train_epochs = 2,          # Set this instead of max_steps for full training runs
        learning_rate = 2e-4,
        logging_steps = 1,
        save_strategy="steps",
        optim = "adamw_torch_fused",
        weight_decay = 0.01,
        lr_scheduler_type = "cosine",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none",             # For Weights and Biases

        # You MUST put the below items for vision finetuning:
        remove_unused_columns = False,
        dataset_text_field = "",
        dataset_kwargs = {"skip_prepare_dataset": True},
        max_length = 2048,
    )
)




gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
print(f"{start_gpu_memory} GB of memory reserved.")

trainer_stats = trainer.train()

used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
used_percentage = round(used_memory / max_memory * 100, 3)
lora_percentage = round(used_memory_for_lora / max_memory * 100, 3)
print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
print(
    f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training."
)
print(f"Peak reserved memory = {used_memory} GB.")
print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
print(f"Peak reserved memory % of max memory = {used_percentage} %.")
print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")







print("После обучения")
sloth_path = os.path.join(BASE_DIR, "v0-52.522000-52.522000-0.jpg")
# You might have to wait 1 minute for Unsloth's auto compiler
do_gemma_3n_inference(sloth_path)

model.save_pretrained(os.path.join(cache_dir, "gemma3n_27B_ru_1"))  # Local saving
processor.save_pretrained(os.path.join(cache_dir, "gemma3n_27B_ru_1"))


model, processor = FastModel.from_pretrained(
    model_name=os.path.join(cache_dir, "gemma3n_27B_ru_1"),  # YOUR MODEL YOU USED FOR TRAINING
    load_in_4bit=True,  # Set to False for 16bit LoRA
    cache_dir = cache_dir
)
FastModel.for_inference(model)  # Enable for inference!