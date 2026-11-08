import os
import json
import glob
import pickle
from io import BytesIO
from typing import List
from PIL import Image, ImageDraw
import pyarrow.parquet as pq

from common import UnifiedSample

# ==========================================
# 核心工具：生成占位图
# ==========================================
def create_placeholder_image(text: str) -> bytes:
    """
    因为 WebArena 没有真实截图，生成一张黑底白字的占位图
    """
    img = Image.new('RGB', (1280, 720), color='black')
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), f"WebArena Task:\n{text[:100]}...", fill="white")
    
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 主处理流程 (全量遍历)
# ==========================================
def clean_webarena_all(parquet_dir: str = "webarena_raw") -> List[UnifiedSample]:
    print("开始处理数据集: WebArena (全量遍历)")
    
    unified_samples = []
    
    stats = {
        "total_scanned": 0,
        "success": 0,
        "fail_other": 0
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
            
            # 按批次流式读取
            for batch in pf.iter_batches(batch_size=50):
                rows = batch.to_pylist()
                
                for row in rows:
                    stats["total_scanned"] += 1
                    
                    task_id = str(row.get("task_id", ""))
                    intent = row.get("intent", "Unknown Task")
                    start_urls = row.get("start_urls", [])
                    
                    try:
                        # 1. 生成占位图
                        image_bytes = create_placeholder_image(intent)
                        
                        # 2. 构造初始占位动作
                        action = {
                            "thought": f"At the start URL. Need to execute the task: {intent}",
                            "type": "left_click",
                            "x": 640,
                            "y": 360
                        }
                        
                        # 3. 提取 URL
                        url = start_urls[0] if start_urls else ""
                        
                        sample = UnifiedSample(
                            goal_id=task_id,
                            goal_desc=intent,
                            image_bytes=image_bytes,
                            step=0,
                            action=action,
                            source="webarena_verified",
                            metadata={
                                "url": url,
                                "eval": row.get("eval", ""),
                                "intent_template": row.get("intent_template", "")
                            }
                        )
                        
                        unified_samples.append(sample)
                        stats["success"] += 1

                        # 打印进度 (每成功 500 条提示一次)
                        if stats["success"] % 500 == 0:
                            print(f"  当前已成功提取: {stats['success']} 条...")

                    except Exception:
                        stats["fail_other"] += 1
                        continue

        except Exception as e:
            print(f"读取分片 {target_file} 时发生异常: {e}")
            continue

    # 打印最终统计报告
    print("-" * 40)
    print("WebArena 全量清洗报告")
    print("-" * 40)
    print(f"共扫描样本数: {stats['total_scanned']}")
    print(f"成功处理数  : {stats['success']}")
    print(f"失败总计    : {stats['total_scanned'] - stats['success']}")
    print(f"  处理异常  : {stats['fail_other']}")
    print("-" * 40)

    return unified_samples

if __name__ == "__main__":
    samples = clean_webarena_all(parquet_dir="webarena_raw")
    
    if samples:
        with open("webarena_full.pkl", "wb") as f:
            pickle.dump(samples, f, protocol=pickle.HIGHEST_PROTOCOL)
        print("全量数据已保存至: webarena_full.pkl")
    else:
        print("警告: 未提取到任何样本，跳过保存。")