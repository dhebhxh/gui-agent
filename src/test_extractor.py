import cv2
from screen_element_extractor import ScreenElementExtractor

extractor = ScreenElementExtractor(
    ocr_langs=('ch_sim', 'en'),
    iou_threshold=0.3,
    use_gpu=False,
)

result, vis_image = extractor.process(
    image_path="screenshot.png",
    output_image_path="output_annotated.png",
    output_json_path="output_elements.json",
)

print("=" * 50)
print(f"截图尺寸: {result['screenshot_size']}")
print(f"检测到元素总数: {result['element_count']}")

# 按类型统计，快速看检测分布
from collections import Counter
type_count = Counter(e["type"] for e in result["elements"])
print(f"类型分布: {dict(type_count)}")

# 打印前10个元素
print("\n前10个元素:")
for e in result["elements"][:10]:
    print(f"  #{e['element_id']} [{e['type']}] "
          f"text='{e['text']}' bbox={e['bbox']} "
          f"source={e['source']}")