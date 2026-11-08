import json
from pathlib import Path
from collections import Counter

def inspect_dataset(root_dir="screenagent_raw/train", max_files=5):
    root = Path(root_dir)
    if not root.exists():
        print(f"❌ 找不到目录: {root.absolute()}")
        return

    session_dirs = [d for d in root.iterdir() if d.is_dir()]
    print(f"共发现 {len(session_dirs)} 个 Session 文件夹。\n")

    json_count = 0
    action_types = Counter()
    
    for session_dir in session_dirs[:3]: # 只看前3个session
        print(f"📂 正在检查文件夹: {session_dir.name}")
        json_files = sorted(session_dir.glob("*.json"))
        
        for jf in json_files:
            if json_count >= max_files:
                break
                
            print(f"  📄 文件: {jf.name}")
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception as e:
                print(f"    ❌ 解析失败: {e}")
                continue
                
            # 打印所有顶层字段
            print(f"    🔑 顶层字段: {list(meta.keys())}")
            
            # 专门看看 actions 字段长什么样
            actions = meta.get("actions", [])
            if isinstance(actions, list):
                for act in actions:
                    if isinstance(act, dict):
                        # 收集所有的 action_type
                        atype = act.get("action_type", act.get("type", "UNKNOWN"))
                        action_types[atype] += 1
                        print(f"      👉 动作原始字典: {act}")
            elif isinstance(actions, dict):
                print(f"      👉 动作是字典(不是列表): {actions}")
            else:
                print(f"      👉 动作字段为空或未知类型")
                
            json_count += 1
            print("-" * 40)
            
        if json_count >= max_files:
            break

    print("\n" + "="*40)
    print("📊 发现的动作类型统计 (前5个文件):")
    for k, v in action_types.most_common():
        print(f"  - {k}: {v} 次")
    print("="*40)

if __name__ == "__main__":
    inspect_dataset()