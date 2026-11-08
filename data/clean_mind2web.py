import os
import json
import glob
import pickle
from io import BytesIO
from typing import List, Tuple
from PIL import Image, ImageDraw
import pyarrow.parquet as pq

from common import UnifiedSample

# ==========================================
# 核心解析工具
# ==========================================
def draw_target_element(image: Image.Image, target_info: dict) -> Tuple[Image.Image, dict]:
    attrs_str = target_info.get("attributes", "{}")
    try:
        attrs = json.loads(attrs_str)
    except Exception:
        return image, {}
        
    rect_str = attrs.get("bounding_box_rect")
    if not rect_str:
        return image, {}
        
    try:
        x, y, w, h = map(float, rect_str.split(","))
        center = [int(x + w/2), int(y + h/2)]
    except Exception:
        return image, {}
        
    element = {
        "element_id": 1,
        "type": target_info.get("tag", "unknown"),
        "text": attrs.get("aria_label", "")[:30],
        "center": center,
        "bbox": [x, y, w, h],
        "backend_node_id": target_info.get("backend_node_id")
    }
    
    draw = ImageDraw.Draw(image)
    draw.rectangle([x, y, x + w, y + h], outline="red", width=3)
    draw.text((x, max(0, y - 12)), "#1", fill="red")
    
    return image, element

def map_action(raw_op: str, center_x: int, center_y: int) -> dict:
    try:
        op = json.loads(raw_op)
    except Exception:
        op = {}
        
    op_type = str(op.get("op", "CLICK")).upper()
    value = str(op.get("value", ""))
    
    if op_type == "TYPE":
        return {"type": "type_text", "x": center_x, "y": center_y, "text": value}
    else:
        return {"type": "left_click", "x": center_x, "y": center_y}


# ==========================================
# 主处理流程 (遍历所有分片，处理全量数据)
# ==========================================
def clean_mind2web_all(parquet_dir: str = "mind2web_raw") -> List[UnifiedSample]:
    print("开始处理数据集: Mind2Web (全量遍历)")
    
    unified_samples = []
    task_step_counters = {}
    
    stats = {
        "total_scanned": 0, "success": 0,
        "fail_missing_image": 0, "fail_image_load": 0,
        "fail_no_target": 0, "fail_other": 0
    }

    # 获取所有 parquet 文件并排序
    parquet_files = sorted(glob.glob(os.path.join(parquet_dir, "*.parquet")))
    if not parquet_files:
        print(f"错误: 在 {parquet_dir} 找不到 Parquet 文件。")
        return []
    
    print(f"共发现 {len(parquet_files)} 个数据分片，开始逐个读取...")

    for file_idx, target_file in enumerate(parquet_files):
        print(f"正在处理分片 [{file_idx + 1}/{len(parquet_files)}]: {os.path.basename(target_file)}")
        
        try:
            pf = pq.ParquetFile(target_file)
            # 按批次流式读取，防止内存溢出
            for batch in pf.iter_batches(batch_size=50):
                rows = batch.to_pylist()
                
                for row in rows:
                    stats["total_scanned"] += 1
                    goal_id = str(row.get("annotation_id", ""))
                    goal_desc = row.get("confirmed_task", "")

                    # 1. 处理图像数据
                    raw_image = row.get("screenshot")
                    if not raw_image:
                        stats["fail_missing_image"] += 1
                        continue
                    try:
                        if isinstance(raw_image, dict) and "bytes" in raw_image:
                            raw_image = Image.open(BytesIO(raw_image["bytes"]))
                        elif isinstance(raw_image, bytes):
                            raw_image = Image.open(BytesIO(raw_image))
                    except Exception:
                        stats["fail_image_load"] += 1
                        continue

                    # 2. 获取目标元素坐标信息
                    pos_candidates_raw = row.get("pos_candidates", "[]")
                    try:
                        candidates = json.loads(pos_candidates_raw) if isinstance(pos_candidates_raw, str) else pos_candidates_raw
                        if not candidates:
                            stats["fail_no_target"] += 1
                            continue
                        
                        target_info = candidates[0]
                        if isinstance(target_info, str):
                            target_info = json.loads(target_info)
                    except Exception:
                        stats["fail_no_target"] += 1
                        continue

                    # 3. 画图并解析动作
                    try:
                        annotated_image, target_element = draw_target_element(raw_image.copy(), target_info)
                        if not target_element:
                            stats["fail_no_target"] += 1
                            continue
                            
                        cx, cy = target_element["center"]
                        operation = row.get("operation", "")
                        action = map_action(operation, cx, cy)

                        step = task_step_counters.get(goal_id, 0)
                        task_step_counters[goal_id] = step + 1
                            
                        img_byte_arr = BytesIO()
                        annotated_image.save(img_byte_arr, format='PNG')
                            
                        sample = UnifiedSample(
                            goal_id=goal_id,
                            goal_desc=goal_desc,
                            image_bytes=img_byte_arr.getvalue(),
                            step=step,
                            action=action,
                            source="multimodal_mind2web_local",
                            metadata={"url": row.get("website", "")}
                        )
                            
                        unified_samples.append(sample)
                        stats["success"] += 1

                        # 打印进度 (每处理 100 条刷新一次)
                        if stats["success"] % 100 == 0:
                            print(f"  当前已成功提取: {stats['success']} 条...")

                    except Exception:
                        stats["fail_other"] += 1
                        continue

        except Exception as e:
            print(f"读取分片 {target_file} 时发生异常: {e}")
            continue

    # 打印最终统计报告
    print("-" * 40)
    print("Mind2Web 全量清洗报告")
    print("-" * 40)
    print(f"共扫描样本数: {stats['total_scanned']}")
    print(f"成功处理数  : {stats['success']}")
    print(f"失败总计    : {stats['total_scanned'] - stats['success']}")
    print(f"  缺失截图  : {stats['fail_missing_image']}")
    print(f"  图片损坏  : {stats['fail_image_load']}")
    print(f"  目标定位失败: {stats['fail_no_target']}")
    print(f"  处理异常  : {stats['fail_other']}")
    print("-" * 40)
    
    return unified_samples

if __name__ == "__main__":
    samples = clean_mind2web_all(parquet_dir="mind2web_raw")
    
    if samples:
        # 全量数据可能很大，用最高的协议版本保存
        with open("mind2web_full.pkl", "wb") as f:
            pickle.dump(samples, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"全量数据已保存至: mind2web_full.pkl")
    else:
        print("警告: 未提取到任何样本。")