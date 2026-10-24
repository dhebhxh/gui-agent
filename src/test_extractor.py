import os
import cv2
import numpy as np
import time
from datasets import load_dataset
from screen_element_extractor import ScreenElementExtractor

def run_first_round_test(num_samples=100, output_dir="test_results"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("初始化模型...")
    extractor = ScreenElementExtractor(use_gpu=False)
    
    print(f"流式加载数据集前 {num_samples} 张图...")
    dataset = load_dataset("docling-project/screenparse", split="train", streaming=True)
    
    total_pred = 0
    total_gt = 0
    start_time = time.time()
    
    for i, sample in enumerate(dataset):
        if i >= num_samples:
            break
            
        # 1. 极速转换：PIL -> NumPy -> OpenCV BGR
        # 这一步在内存里瞬间完成，不需要存硬盘
        pil_image = sample["image"]
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        gt_count = len(sample["bboxes"])
        
        # 2. 直接调用你刚添加的 process_cv_image 方法
        result, vis_image = extractor.process_cv_image(cv_image)
        pred_count = result["element_count"]
        
        total_gt += gt_count
        total_pred += pred_count
        
        # 3. 只保存可视化结果图（方便你看效果）
        out_img_path = os.path.join(output_dir, f"result_{i:03d}.png")
        cv2.imwrite(out_img_path, vis_image)
        
        print(f"[{i+1:03d}/{num_samples}] 预测: {pred_count:2d} 个 | 真实: {gt_count:2d} 个")

    end_time = time.time()
    
    print("\n" + "="*40)
    print(f"测试完成！共处理 {num_samples} 张图")
    print(f"总耗时: {end_time - start_time:.2f} 秒 (平均 {((end_time - start_time)/num_samples):.2f} 秒/张)")
    print(f"真实标注总数: {total_gt} 个")
    print(f"模型预测总数: {total_pred} 个")
    print("="*40)

if __name__ == "__main__":
    run_first_round_test(num_samples=100, output_dir="test_results")