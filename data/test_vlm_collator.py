
import torch

from PIL import Image
from transformers import AutoProcessor

from trl.trainer.sft_trainer import (
    DataCollatorForVisionLanguageModeling
)

MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

processor = AutoProcessor.from_pretrained(MODEL_NAME)

collator = DataCollatorForVisionLanguageModeling(
    processor=processor,
    max_length=None,
    completion_only_loss=True,
)

image = Image.new(
    "RGB",
    (640, 480),
    color="white"
)

examples = [
    {
        "prompt": [
            {
                "role": "system",
                "content": "You are a GUI agent."
            },
            {
                "role": "user",
                "content": "Click the button on the screenshot."
            }
        ],
        "completion": [
            {
                "role": "assistant",
                "content": '{"thought":"","action":{"type":"left_click","x":100,"y":200}}'
            }
        ],
        "images": [image],
    }
]

batch = collator(examples)

print("\n========== BATCH ==========")

for key, value in batch.items():

    if isinstance(value, torch.Tensor):
        print(
            key,
            value.shape,
            value.dtype
        )
    else:
        print(key, type(value))

assert "input_ids" in batch
assert "attention_mask" in batch
assert "pixel_values" in batch
assert "labels" in batch

assert batch["pixel_values"].numel() > 0

# 验证 prompt 部分被 mask
labels = batch["labels"]

assert (labels == -100).any()

# 验证 completion 部分存在训练标签
assert (labels != -100).any()

print("\n✅ Qwen2.5-VL multimodal collator test passed!")
