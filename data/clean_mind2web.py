
import os
import sys
import json
import glob
import argparse
from io import BytesIO

import pyarrow.parquet as pq
from PIL import Image, ImageFile

from datasets import (
    Dataset,
    Features,
    Value,
    Image as HFImage,
    List
)

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from src.prompts import PLANNER_USER_TEMPLATE, SYSTEM_PROMPT


# ============================================================
# 1. 全局配置
# ============================================================

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

PARQUET_DIR = "/root/autodl-tmp/mind2web_raw/data"
OUT_DIR = "/root/autodl-tmp/mind2web_sft"

BATCH_SIZE = 32

NEEDED_COLS = [
    "screenshot",
    "operation",
    "pos_candidates",
    "annotation_id",
    "confirmed_task",
]

# ============================================================
# Hugging Face Dataset Features
# ============================================================

CONTENT_FEATURE = List({
    "type": Value("string"),
    "text": Value("string"),
})

MESSAGE_FEATURE = {
    "role": Value("string"),
    "content": CONTENT_FEATURE,
}

DATASET_FEATURES = Features({
    "prompt": List(MESSAGE_FEATURE),

    "completion": List(MESSAGE_FEATURE),

    "images": List(HFImage()),

    "goal_id": Value("string"),

    "source": Value("string"),
})


# ============================================================
# 3. 数据解析函数
# ============================================================

def parse_json(value):
    """兼容 JSON 字符串和已经解析的字典。"""

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        return json.loads(value)

    raise ValueError("Unsupported JSON value")


def get_screenshot(row):
    """读取 Parquet 中的截图并转换为 RGB PIL Image。"""

    screenshot = row.get("screenshot")

    if not screenshot:
        return None

    if isinstance(screenshot, dict):
        img_bytes = screenshot.get("bytes")
    else:
        img_bytes = None

    if not img_bytes:
        return None

    try:
        with Image.open(BytesIO(img_bytes)) as img:
            img.load()
            image = img.convert("RGB")

        return image

    except Exception:
        return None


def parse_action(row):
    """
    将 Mind2Web operation 转换为模型动作。

    支持:
        CLICK -> left_click
        TYPE  -> type_text

    SELECT 暂时跳过。
    """

    try:
        operation = parse_json(row["operation"])

        op = operation.get("op", "").upper()
        value = operation.get("value", "")

    except Exception:
        return None

    if op == "CLICK":

        action = {
            "type": "left_click"
        }

    elif op == "TYPE":

        if value is None:
            value = ""

        action = {
            "type": "type_text",
            "text": str(value)
        }

    else:
        return None

    return action


def get_target_coordinates(row, image):
    """
    优先使用 original_target。
    如果没有，则使用 top_level_target。

    返回目标框中心坐标。
    """

    candidates = row.get("pos_candidates")

    if not candidates:
        return None

    parsed_candidates = []

    try:
        for item in candidates:

            candidate = parse_json(item)

            parsed_candidates.append(candidate)

    except Exception:
        return None

    target = None

    # 优先寻找原始目标
    for candidate in parsed_candidates:

        if candidate.get("is_original_target"):
            target = candidate
            break

    # 其次寻找顶层目标
    if target is None:

        for candidate in parsed_candidates:

            if candidate.get("is_top_level_target"):
                target = candidate
                break

    if target is None:
        return None

    try:
        attrs = parse_json(target["attributes"])

        rect = attrs["bounding_box_rect"]

        x_str, y_str, w_str, h_str = rect.split(",")

        x = float(x_str) + float(w_str) / 2
        y = float(y_str) + float(h_str) / 2

        # 坐标合法性检查
        if not (
            0 <= x < image.width
            and 0 <= y < image.height
        ):
            return None

        return int(x), int(y)

    except Exception:
        return None


# ============================================================
# 4. 构造训练样本
# ============================================================

def build_sample(row):

    # --------------------------
    # 4.1 图片
    # --------------------------

    image = get_screenshot(row)

    if image is None:
        return None

    # --------------------------
    # 4.2 动作
    # --------------------------

    action = parse_action(row)

    if action is None:
        return None

    # --------------------------
    # 4.3 坐标
    # --------------------------

    coordinates = get_target_coordinates(row, image)

    if coordinates is None:
        return None

    action["x"], action["y"] = coordinates

    # --------------------------
    # 4.4 User Prompt
    # --------------------------

    goal = row.get("confirmed_task")

    if not goal:
        return None

    user_text = PLANNER_USER_TEMPLATE.format(
        goal=str(goal),
        thought_history=(
            "This is the first step. "
            "Start by examining the current screen."
        ),
    )

    # --------------------------
    # 4.5 Completion
    # --------------------------

    completion_text = json.dumps(
        {
            "thought": "",
            "action": action
        },
        ensure_ascii=False
    )

    # --------------------------
    # 4.6 Prompt
    # --------------------------

    prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text
                },
                {
                    "type": "image",
                    "text": None
                }
            ]
        }
    ]

    # --------------------------
    # 4.7 Completion
    # --------------------------

    completion = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": completion_text
                }
            ]
        }
    ]

    # --------------------------
    # 4.8 最终样本
    # --------------------------

    return {
        "prompt": prompt,
        "completion": completion,

        # 图片与 prompt 中的 image placeholder 对应
        "images": [image],

        "goal_id": str(row["annotation_id"]),
        "source": "multimodal-mind2web",
    }


# ============================================================
# 5. 处理单个 Parquet 分片
# ============================================================

def process_single_file(target_file, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    filename = os.path.basename(target_file)

    part_name = filename.replace(
        "train-", ""
    ).replace(
        ".parquet", ""
    )

    save_path = os.path.join(
        out_dir,
        f"part_{part_name}"
    )

    if os.path.exists(save_path):

        print(f"⏭️ {save_path} 已经存在，跳过。")
        return

    print(f"\n开始处理: {filename}")

    stats = {
        "scanned": 0,
        "success": 0,
        "skip": 0,
    }

    part_rows = []

    pf = pq.ParquetFile(target_file)

    # 按 batch 读取，避免一次性读取整个 Parquet
    for batch in pf.iter_batches(
        batch_size=BATCH_SIZE,
        columns=NEEDED_COLS
    ):

        rows = batch.to_pylist()

        for row in rows:

            stats["scanned"] += 1

            try:

                sample = build_sample(row)

                if sample is None:

                    stats["skip"] += 1
                    continue

                part_rows.append(sample)

                stats["success"] += 1

            except Exception as e:

                stats["skip"] += 1

                # 不打印每条异常，避免日志过多
                if stats["skip"] <= 5:
                    print(f"⚠️ 样本处理异常: {e}")

        print(
            f"\r已扫描: {stats['scanned']} | "
            f"成功: {stats['success']} | "
            f"跳过: {stats['skip']}",
            end="",
            flush=True
        )

    print()

    # ========================================================
    # 6. 保存 Dataset
    # ========================================================

    if not part_rows:

        print("⚠️ 当前分片没有有效数据。")
        return

    print(
        f"💾 正在保存 {len(part_rows)} 条样本..."
    )

    ds = Dataset.from_list(
        part_rows,
        features=DATASET_FEATURES
    )

    ds.save_to_disk(save_path)

    # 保存统计信息
    stats_path = os.path.join(
        out_dir,
        f"part_{part_name}_stats.json"
    )

    with open(
        stats_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            stats,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"✅ 保存成功: {save_path}")

    print(
        f"统计: {json.dumps(stats, ensure_ascii=False)}"
    )

    # 释放分片数据
    del ds
    del part_rows


# ============================================================
# 7. 主函数
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--index",
        type=int,
        required=True,
        help="要处理的分片序号"
    )

    args = parser.parse_args()

    all_files = sorted(
        glob.glob(
            os.path.join(
                PARQUET_DIR,
                "train-*.parquet"
            )
        )
    )

    if not all_files:

        raise RuntimeError(
            f"没有找到 Parquet 文件: {PARQUET_DIR}"
        )

    if 0 <= args.index < len(all_files):

        target_file = all_files[args.index]

        process_single_file(
            target_file,
            OUT_DIR
        )

    else:

        print(
            f"错误: index 必须在 0 到 "
            f"{len(all_files)-1} 之间"
        )
