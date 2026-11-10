import os
import json
import glob
import pickle
from io import BytesIO
from typing import List
from PIL import Image
import pyarrow.parquet as pq

from ..src.prompts import PLANNER_USER_TEMPLATE, SYSTEM_PROMPT
from common import UnifiedSample


def clean_mind2web_all(parquet_dir: str = "mind2web_raw") -> List[UnifiedSample]:
    print("开始处理数据集: Mind2Web (全量遍历)")

    unified_rows = []
    step_counters = {}

    stats = {
        "total_scanned": 0, "success": 0,
        "fail_missing_image": 0, "fail_image_load": 0,
        "fail_no_target": 0, "skip_select": 0, "fail_other": 0,
    }

    parquet_files = sorted(glob.glob(os.path.join(parquet_dir, "*.parquet")))
    print(f"共发现 {len(parquet_files)} 个数据分片，开始逐个读取...")

    for file_idx, target_file in enumerate(parquet_files):
        print(f"正在处理分片 [{file_idx + 1}/{len(parquet_files)}]: {os.path.basename(target_file)}")

        try:
            pf = pq.ParquetFile(target_file)
            for batch in pf.iter_batches(batch_size=50):
                rows = batch.to_pylist()

                for row in rows:
                    stats["total_scanned"] += 1

                    # 1. screenshot 缺失
                    if not row.get("screenshot"):
                        stats["fail_missing_image"] += 1
                        continue

                    # 2. 图片损坏
                    try:
                        image = Image.open(BytesIO(row["screenshot"])).convert("RGB")
                    except Exception:
                        stats["fail_image_load"] += 1
                        continue

                    # 3. 定位目标元素
                    target = None
                    for candidate in row["pos_candidates"]:
                        if candidate["is_original_target"]:
                            target = candidate
                            break
                    if target is None:
                        for candidate in row["pos_candidates"]:
                            if candidate["is_top_level_target"]:
                                target = candidate
                                break
                    if target is None:
                        stats["fail_no_target"] += 1
                        continue

                    # 4. 解析坐标
                    attrs = json.loads(target["attributes"])
                    rect = attrs["bounding_box_rect"]
                    x_str, y_str, w_str, h_str = rect.split(",")
                    x = float(x_str)
                    y = float(y_str)
                    w = float(w_str)
                    h = float(h_str)
                    cx = int(x + w / 2)
                    cy = int(y + h / 2)

                    # 5. 动作
                    op = row["operation"]["op"].upper()
                    value = row["operation"].get("value", "")

                    if op == "CLICK":
                        action = {"type": "left_click", "x": cx, "y": cy}
                    elif op == "TYPE":
                        action = {"type": "type_text", "x": cx, "y": cy, "text": value}
                    elif op == "SELECT":
                        stats["skip_select"] += 1
                        continue
                    else:
                        stats["fail_other"] += 1
                        continue

                    # 6. step
                    ann_id = row["annotation_id"]
                    step_counters[ann_id] = step_counters.get(ann_id, -1) + 1
                    step = step_counters[ann_id]

                    # 7. user_text
                    user_text = PLANNER_USER_TEMPLATE.format(
                        goal=row["confirmed_task"],
                        thought_history="This is the first step. Start by examining the current screen.",
                    )

                    # 8. 构造样本
                    unified_row = {
                        "prompt": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": [
                                {"type": "text", "text": user_text},
                                {"type": "image"},
                            ]},
                        ],
                        "completion": [
                            {"role": "assistant", "content": json.dumps(
                                {"thought": "", "action": action},
                                ensure_ascii=False,
                            )},
                        ],
                        "images": [image],
                        "goal_id": ann_id,
                        "step": step,
                        "source": "multimodal-mind2web",
                    }

                    unified_rows.append(unified_row)
                    stats["success"] += 1

        except Exception as e:
            print(f"读取分片 {target_file} 时发生异常: {e}")
            continue

    print("-" * 40)
    print("Mind2Web 全量清洗报告")
    print("-" * 40)
    print(f"共扫描样本数: {stats['total_scanned']}")
    print(f"成功处理数  : {stats['success']}")
    print(f"  缺失截图  : {stats['fail_missing_image']}")
    print(f"  图片损坏  : {stats['fail_image_load']}")
    print(f"  目标定位失败: {stats['fail_no_target']}")
    print(f"  跳过 SELECT : {stats['skip_select']}")
    print(f"  处理异常  : {stats['fail_other']}")
    print("-" * 40)

    return unified_rows


if __name__ == "__main__":
    unified_rows = clean_mind2web_all(parquet_dir="mind2web_raw")

    if unified_rows:
        with open("mind2web_full.pkl", "wb") as f:
            pickle.dump(unified_rows, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"全量数据已保存至: mind2web_full.pkl")
    else:
        print("警告: 未提取到任何样本。")