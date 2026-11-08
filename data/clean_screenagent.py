import os
import json
import pickle
from pathlib import Path
from typing import List, Optional
from io import BytesIO
from PIL import Image

from common import UnifiedSample

# ==========================================
# 核心解析工具
# ==========================================
def _first_present(d: dict, keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def _resolve_image_path(session_dir: Path, img_name: str) -> Optional[Path]:
    """尝试寻找图片路径"""
    if not img_name:
        return None
    p = Path(img_name)
    if p.is_absolute() and p.exists():
        return p
    candidates = [
        session_dir / img_name,
        session_dir / "images" / Path(img_name).name,
        session_dir / "screenshots" / Path(img_name).name,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def _extract_and_map_screenagent(raw_act: dict):
    """精准解析 ScreenAgent 的嵌套结构"""
    if not raw_act:
        return None
        
    action_type = raw_act.get("action_type", "")
    
    # 过滤掉无效动作（计划、任务评估等）
    if action_type not in ("MouseAction", "KeyboardAction"):
        return None
        
    # 1. 处理鼠标点击
    if action_type == "MouseAction" and raw_act.get("mouse_action_type") == "click":
        pos = raw_act.get("mouse_position", {})
        x = int(pos.get("width", 0))
        y = int(pos.get("height", 0))
        return {
            "thought": "Click on the target coordinate.",
            "type": "left_click",
            "x": x,
            "y": y
        }
        
    # 2. 处理键盘输入/按键
    if action_type == "KeyboardAction":
        kb_type = raw_act.get("keyboard_action_type")
        
        if kb_type == "text":
            text = raw_act.get("keyboard_text", "")
            return {
                "thought": f"Type the text '{text}' into the focused area.",
                "type": "type_text",
                "x": 0,
                "y": 0,
                "text": text
            }
            
        elif kb_type == "press":
            raw_key = raw_act.get("keyboard_key", "")
            
            # 修复点：兼容字符串和列表两种类型
            if isinstance(raw_key, list):
                # 如果是组合键列表，比如 ["Control", "c"]，转小写后用加号拼接
                key = "+".join([str(k).lower() for k in raw_key])
            else:
                # 如果是普通字符串，比如 "Return"
                key = str(raw_key).lower()
                
            return {
                "thought": f"Press the '{key}' key.",
                "type": "key_press",
                "x": 0,
                "y": 0,
                "key": key
            }
            
    return None

# ==========================================
# 主处理流程 (全量遍历)
# ==========================================
def clean_screenagent_all(data_dir: str = "screenagent_raw", split: str = "train") -> List[UnifiedSample]:
    print("开始处理数据集: ScreenAgent (全量遍历)")
    
    root = Path(data_dir) / split
    if not root.exists():
        print(f"错误: 找不到目录 {root}")
        return []

    unified_samples = []
    stats = {
        "total_sessions": 0, 
        "total_jsons": 0, 
        "success": 0,
        "fail_missing_img": 0, 
        "fail_json": 0, 
        "fail_invalid_action": 0, 
        "fail_other": 0
    }

    session_dirs = [d for d in sorted(root.iterdir()) if d.is_dir()]
    stats["total_sessions"] = len(session_dirs)
    print(f"共发现 {stats['total_sessions']} 个 Session 文件夹，开始逐个扫描...")
    
    task_step_counters = {}

    for session_idx, session_dir in enumerate(session_dirs):
        json_files = sorted(session_dir.glob("*.json"))
        stats["total_jsons"] += len(json_files)
        
        goal_instruction = ""
        goal_id = session_dir.name

        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                stats["fail_json"] += 1
                continue

            # 每个 session 的 instruction 是一样的，拿一次就行
            if not goal_instruction:
                goal_instruction = _first_present(meta, ("task_prompt_en", "task_prompt", "instruction"), "")

            img_name = meta.get("saved_image_name", "")
            img_path = _resolve_image_path(session_dir, img_name)

            if not img_path or not img_path.exists():
                stats["fail_missing_img"] += 1
                continue
            
            try:
                img_bytes = img_path.read_bytes()
                Image.open(BytesIO(img_bytes)).verify() # 验证图片完整性
            except Exception:
                stats["fail_missing_img"] += 1
                continue

            raw_actions = meta.get("actions", [])
            if not isinstance(raw_actions, list):
                raw_actions = [raw_actions] if isinstance(raw_actions, dict) else []

            for act in raw_actions:
                if not isinstance(act, dict):
                    continue

                mapped_action = _extract_and_map_screenagent(act)
                
                # 跳过所有 PlanAction 或无法解析的动作
                if mapped_action is None:
                    stats["fail_invalid_action"] += 1
                    continue

                try:
                    step = task_step_counters.get(goal_id, 0)
                    task_step_counters[goal_id] = step + 1

                    sample = UnifiedSample(
                        goal_id=goal_id,
                        goal_desc=goal_instruction,
                        image_bytes=img_bytes,
                        step=step,
                        action=mapped_action,
                        source="screenagent_local",
                        metadata={"json_file": jf.name, "image_path": str(img_path)}
                    )
                    unified_samples.append(sample)
                    stats["success"] += 1
                    
                    # 打印进度 (每成功 500 条提示一次)
                    if stats["success"] % 500 == 0:
                        print(f"  当前已成功提取: {stats['success']} 条...")

                except Exception:
                    stats["fail_other"] += 1
                    continue

        # 打印 Session 级别进度 (每 20 个 Session 提示一次)
        if (session_idx + 1) % 20 == 0:
            print(f"  已扫描 {session_idx + 1} / {stats['total_sessions']} 个 Session...")

    # 打印最终统计报告
    print("-" * 40)
    print("ScreenAgent 全量清洗报告")
    print("-" * 40)
    print(f"遍历 Session 数 : {stats['total_sessions']}")
    print(f"解析 JSON 文件数: {stats['total_jsons']}")
    print(f"成功提取有效样本: {stats['success']}")
    print(f"失败/跳过总计   : {stats['fail_missing_img'] + stats['fail_json'] + stats['fail_invalid_action'] + stats['fail_other']}")
    print(f"  - 缺失/损坏图片 : {stats['fail_missing_img']}")
    print(f"  - JSON 解析失败 : {stats['fail_json']}")
    print(f"  - 无效动作(跳过): {stats['fail_invalid_action']}")
    print(f"  - 处理异常      : {stats['fail_other']}")
    print("-" * 40)

    return unified_samples

if __name__ == "__main__":
    samples = clean_screenagent_all(data_dir="screenagent_raw", split="train")
    
    if samples:
        with open("screenagent_full.pkl", "wb") as f:
            pickle.dump(samples, f, protocol=pickle.HIGHEST_PROTOCOL)
        print("全量数据已保存至: screenagent_full.pkl")
    else:
        print("警告: 未提取到任何样本，跳过保存。")