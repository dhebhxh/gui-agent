import os
import torch

if not hasattr(torch.compiler, 'is_compiling'):
    torch.compiler.is_compiling = lambda: False
    
# 设置显存碎片优化（建议在导入 torch 之前或紧随其后）
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from datasets import load_from_disk, concatenate_datasets
from transformers import (
    AutoProcessor, 
    AutoModelForImageTextToText, 
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

MODEL_PATH = "/root/autodl-tmp/Qwen2.5-VL-7B-Instruct"
DATASET_DIR = "/root/autodl-tmp/mind2web_sft"
OUTPUT_DIR = "/root/autodl-tmp/mind2web_qwen25vl_sft"

# ============================================================
# 1. 加载所有分片
# ============================================================
part_dirs = sorted([
    os.path.join(DATASET_DIR, name)
    for name in os.listdir(DATASET_DIR)
    if name.startswith("part_")
    and os.path.isdir(os.path.join(DATASET_DIR, name))
])

datasets_list = [load_from_disk(path) for path in part_dirs]
train_dataset = concatenate_datasets(datasets_list)

print(train_dataset)
print(train_dataset.features)

# ============================================================
# 2. 加载 Processor 和 4-bit 量化模型
# ============================================================
processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    min_pixels=256 * 28 * 28,
    max_pixels=1280 * 28 * 28
)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",           # 修复了引号
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16           # 修复了 bfloat16
)

model.gradient_checkpointing_enable()
model = prepare_model_for_kbit_training(model)

# ============================================================
# 3. 配置 LoRA
# ============================================================
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

model.enable_input_require_grads() 
# ============================================================
# 4. SFT 配置
# ============================================================
training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=2,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    learning_rate=2e-4,                  # 改为 2e-4，LoRA 需要更大的学习率
    logging_steps=10,
    save_steps=500,
    save_total_limit=3,
    bf16=True,
    gradient_checkpointing=True,
    max_length=None,                     # 如果后续 OOM，改成 2048 试试
    completion_only_loss=True,
    packing=False,
    report_to="none",
)

# ============================================================
# 5. 创建 Trainer
# ============================================================
trainer = SFTTrainer(
    model=model,                         # 传入已经包装好的 model 对象
    args=training_args,
    train_dataset=train_dataset,
    processing_class=processor,
)

# ============================================================
# 6. 开始训练
# ============================================================
trainer.train()

# ============================================================
# 7. 保存模型
# ============================================================
trainer.save_model(OUTPUT_DIR)
processor.save_pretrained(OUTPUT_DIR)