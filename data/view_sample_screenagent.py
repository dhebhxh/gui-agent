import pickle
import json

def view_first_sample():
    # 1. 修改为读取 ScreenAgent 的数据
    pkl_path = "screenagent_10.pkl" 
    
    try:
        with open(pkl_path, "rb") as f:
            samples = pickle.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {pkl_path}，请确认你在正确的目录下运行，或者 pkl 文件是否已生成。")
        return
        
    if not samples:
        print("❌ 里面没有数据！")
        return
        
    print(f"🎉 成功加载了 {len(samples)} 条数据。下面为你展示第一条的完整信息：\n")
    
    # 2. 提取第一条数据
    sample = samples[0]
    
    # 3. 打印基本信息
    print("="*40)
    print("📌 基础信息 (Metadata)")
    print("="*40)
    print(f"Goal ID   : {sample.get('goal_id')}")
    print(f"Goal Desc : {sample.get('goal_desc')}")
    print(f"Step      : {sample.get('step')} (当前是任务的第几步)")
    print(f"Source    : {sample.get('source')}")
    
    # 4. 打印动作 (Action) - 格式化 JSON 显示
    print("\n" + "="*40)
    print("🤖 动作指令 (Action Schema)")
    print("="*40)
    print(json.dumps(sample.get("action"), indent=4, ensure_ascii=False))
    
    # 5. 打印附加信息 (Metadata)
    print("\n" + "="*40)
    print("📦 附加信息 (Meta)")
    print("="*40)
    print(json.dumps(sample.get("metadata"), indent=4, ensure_ascii=False))
    
    # 6. 检查图片并保存到本地让你看
    img_bytes = sample.get("image_bytes")
    if img_bytes:
        print("\n" + "="*40)
        print("🖼️ 图像信息 (Image)")
        print("="*40)
        print(f"图片大小: {len(img_bytes) / 1024:.2f} KB")
        
        # 保存到本地，方便你双击打开看
        output_img_path = "preview_screenagent.png"
        with open(output_img_path, "wb") as f:
            f.write(img_bytes)
        print(f"✅ 图片已提取并保存为: {output_img_path}")
        print("👉 请去左侧文件目录双击打开 preview_screenagent.png 看看原图！")
    else:
        print("❌ 没有图片数据！")

if __name__ == "__main__":
    view_first_sample()