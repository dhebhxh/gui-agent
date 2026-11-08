import pickle
import json
import os

def view_webarena_sample():
    pkl_path = "webarena_10.pkl"
    
    try:
        with open(pkl_path, "rb") as f:
            samples = pickle.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {pkl_path}，请确认你在 data 目录下运行。")
        return
        
    if not samples:
        print("❌ 里面没有数据！")
        return
        
    print(f"🎉 成功加载了 {len(samples)} 条 WebArena 数据。\n")
    
    sample = samples[0]
    
    print("="*40)
    print("📌 基础信息")
    print("="*40)
    print(f"Goal ID   : {sample.get('goal_id')}")
    print(f"Goal Desc : {sample.get('goal_desc')}")
    print(f"Step      : {sample.get('step')}")
    print(f"Source    : {sample.get('source')}")
    
    print("\n" + "="*40)
    print("🌐 WebArena 专属元数据")
    print("="*40)
    # 打印 URL 和 评估标准
    meta = sample.get("metadata", {})
    print(f"Target URL: {meta.get('url')}")
    print(f"Eval规则  : {str(meta.get('eval'))[:200]}...") # 评估规则通常很长，截断显示
    
    print("\n" + "="*40)
    print("🤖 动作指令 (注意: 这是占位动作)")
    print("="*40)
    print(json.dumps(sample.get("action"), indent=4, ensure_ascii=False))
    
    # 保存图片
    img_bytes = sample.get("image_bytes")
    if img_bytes:
        output_img_path = "preview_webarena.png"
        with open(output_img_path, "wb") as f:
            f.write(img_bytes)
        print(f"\n✅ 占位图片已保存为: {output_img_path}")
        print("👉 请去左侧文件目录双击打开看看那张黑底白字的图！")

if __name__ == "__main__":
    view_webarena_sample()