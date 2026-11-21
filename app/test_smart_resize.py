import os
import math
from PIL import Image

from qwen_vl_utils.vision_process import smart_resize
from transformers import AutoProcessor

MODEL_PATH = "/root/autodl-tmp/Qwen2.5-VL-7B-Instruct-clean"
IMG_PATH = "/root/gui-agent/app/screenshot/raw_20261120_212150_741.png"

FACTOR = 28
MIN_PIXELS = 256 * 28 * 28
MAX_PIXELS = 1280 * 28 * 28


def get_processor_actual_size(processor, image):
    """
    用 processor 处理图片，返回 processor 实际采用的尺寸。
    优先从 image_grid_thw 推算，兼容不同 transformers 版本。
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": "describe this image"},
            ],
        }
    ]
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )

    grid = inputs.get("image_grid_thw", None)
    if grid is None:
        raise RuntimeError("processor output has no image_grid_thw, cannot infer size")

    # image_grid_thw: [t, h, w]，h/w 是 patch 网格数
    # Qwen2.5-VL 的 patch 尺寸为 14，故实际输入尺寸 = grid * 14
    t, h, w = grid[0].tolist()
    actual_h = int(h) * 14
    actual_w = int(w) * 14
    return actual_h, actual_w, inputs


def main():
    if not os.path.exists(IMG_PATH):
        raise FileNotFoundError(IMG_PATH)

    img = Image.open(IMG_PATH).convert("RGB")
    orig_w, orig_h = img.size
    print(f"原图尺寸: {orig_w} x {orig_h}, 总像素={orig_w * orig_h}")

    # 1) 用官方库做预缩放
    new_h, new_w = smart_resize(
        orig_h, orig_w,
        factor=FACTOR,
        min_pixels=MIN_PIXELS,
        max_pixels=MAX_PIXELS,
    )
    print(f"smart_resize 目标尺寸: {new_w} x {new_h}, 总像素={new_w * new_h}")

    resized_img = img.resize((new_w, new_h), Image.BICUBIC)
    print(f"预缩放后图片尺寸: {resized_img.size[0]} x {resized_img.size[1]}")

    # 2) 加载 processor，参数与训练脚本一致
    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        min_pixels=MIN_PIXELS,
        max_pixels=MAX_PIXELS,
        use_fast=False,
    )

    # 3) 让 processor 处理预缩放后的图片
    actual_h, actual_w, inputs = get_processor_actual_size(processor, resized_img)
    print(f"processor 实际使用尺寸: {actual_w} x {actual_h}")

    # 4) 对比
    if (actual_w, actual_h) == (new_w, new_h):
        print("✅ processor 没有二次缩放：预缩放尺寸与 processor 实际尺寸一致")
    else:
        print("❌ processor 发生了二次缩放")
        print(f"   预缩放: {new_w} x {new_h}")
        print(f"   processor: {actual_w} x {actual_h}")
        print(f"   偏差: dx={actual_w - new_w}, dy={actual_h - new_h}")

    # 5) 额外验证：对预缩放图再跑一次 smart_resize，应返回自身
    check_h, check_w = smart_resize(
        resized_img.height, resized_img.width,
        factor=FACTOR,
        min_pixels=MIN_PIXELS,
        max_pixels=MAX_PIXELS,
    )
    print(f"对预缩放图再次 smart_resize: {check_w} x {check_h}")
    if (check_w, check_h) == (new_w, new_h):
        print("✅ 预缩放图落在 [min_pixels, max_pixels] 且已对齐 28，smart_resize 不再改变尺寸")
    else:
        print("⚠️ 预缩放图再次 smart_resize 尺寸发生变化，说明缩放逻辑或参数有偏差")


if __name__ == "__main__":
    main()