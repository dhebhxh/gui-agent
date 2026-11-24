# test_screenparser.py

import csv
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from datasets import load_dataset
from tqdm import tqdm
from ultralytics import YOLO
from qwen_vl_utils.vision_process import smart_resize


# ==========================================
# 1. Configuration
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "screenparser" / "best.pt"
OUTPUT_DIR = BASE_DIR / "test_results" / "screenparser_resize"
VIS_DIR = OUTPUT_DIR / "visualizations"

DATASET_NAME = "docling-project/screenparse"
MAX_SAMPLES = 100

DEVICE = 0  # CPU 改为 "cpu"
CONF = 0.10
NMS_IOU = 0.10
EVAL_IOU = 0.50
IMGSZ = 1280

# 与 GUI Agent 正式使用的 smart_resize 参数保持一致
RESIZE_FACTOR = 28
MIN_PIXELS = 56 * 56
MAX_PIXELS = 14 * 14 * 4 * 1280

SAVE_VIS_COUNT = 10


# ==========================================
# 2. Image Resize
# ==========================================

def resize_image(image):
    """
    使用 Qwen smart_resize 计算目标尺寸，
    返回缩放后的 PIL 图片和缩放信息。
    """

    original_width, original_height = image.size

    resized_height, resized_width = smart_resize(
        original_height,
        original_width,
        factor=RESIZE_FACTOR,
        min_pixels=MIN_PIXELS,
        max_pixels=MAX_PIXELS
    )

    resized_image = image.resize(
        (resized_width, resized_height),
        Image.Resampling.LANCZOS
    )

    scale_x = resized_width / original_width
    scale_y = resized_height / original_height

    resize_info = {
        "original_width": original_width,
        "original_height": original_height,
        "resized_width": resized_width,
        "resized_height": resized_height,
        "resize_applied": (
            original_width != resized_width
            or original_height != resized_height
        ),
        "scale_x": scale_x,
        "scale_y": scale_y,
    }

    return resized_image, resize_info


# ==========================================
# 3. Ground Truth
# ==========================================

def get_ground_truth(sample, scale_x=1.0, scale_y=1.0):
    """
    Dataset bbox: [x, y, width, height]

    转换为:
    [x1, y1, x2, y2]
    """

    elements = []

    for bbox, label in zip(sample["bboxes"], sample["labels"]):
        x, y, w, h = bbox

        elements.append({
            "bbox": [
                x * scale_x,
                y * scale_y,
                (x + w) * scale_x,
                (y + h) * scale_y
            ],
            "label": str(label).strip()
        })

    return elements


# ==========================================
# 4. YOLO Prediction
# ==========================================

def predict(model, image):
    """
    PIL RGB -> OpenCV BGR -> YOLO
    """

    image_np = np.array(image.convert("RGB"))
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    start_time = time.perf_counter()

    results = model.predict(
        source=image_bgr,
        imgsz=IMGSZ,
        conf=CONF,
        iou=NMS_IOU,
        device=DEVICE,
        verbose=False
    )

    inference_time = time.perf_counter() - start_time

    elements = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()

            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())

            elements.append({
                "bbox": [x1, y1, x2, y2],
                "label": result.names[class_id],
                "confidence": confidence
            })

    return elements, inference_time


# ==========================================
# 5. IoU
# ==========================================

def calculate_iou(box_a, box_b):
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)

    intersection = inter_w * inter_h

    area_a = max(0, box_a[2] - box_a[0]) * max(
        0, box_a[3] - box_a[1]
    )

    area_b = max(0, box_b[2] - box_b[0]) * max(
        0, box_b[3] - box_b[1]
    )

    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


# ==========================================
# 6. Evaluation
# ==========================================

def evaluate(gt_elements, predictions):
    """
    Greedy matching:
    1. 类别必须一致
    2. IoU >= EVAL_IOU
    3. 一个 GT 只能匹配一个预测框
    """

    matched_gt = set()

    tp = 0
    fp = 0

    predictions = sorted(
        predictions,
        key=lambda x: x["confidence"],
        reverse=True
    )

    for pred in predictions:
        best_iou = 0
        best_index = None

        for index, gt in enumerate(gt_elements):
            if index in matched_gt:
                continue

            if pred["label"].strip().casefold() != gt["label"].strip().casefold():
                continue

            iou = calculate_iou(
                pred["bbox"],
                gt["bbox"]
            )

            if iou > best_iou:
                best_iou = iou
                best_index = index

        if best_index is not None and best_iou >= EVAL_IOU:
            tp += 1
            matched_gt.add(best_index)
        else:
            fp += 1

    fn = len(gt_elements) - len(matched_gt)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn
    }


def calculate_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ==========================================
# 7. Visualization
# ==========================================

def save_visualization(image, gt_elements, predictions, path):
    """
    Green: Ground Truth
    Red: YOLO Prediction
    """

    vis = image.convert("RGB").copy()
    draw = ImageDraw.Draw(vis)

    for elem in gt_elements:
        x1, y1, x2, y2 = elem["bbox"]

        draw.rectangle(
            [x1, y1, x2, y2],
            outline="green",
            width=2
        )

        draw.text(
            (x1, max(0, y1 - 12)),
            f"GT: {elem['label']}",
            fill="green"
        )

    for elem in predictions:
        x1, y1, x2, y2 = elem["bbox"]

        draw.rectangle(
            [x1, y1, x2, y2],
            outline="red",
            width=2
        )

        draw.text(
            (x1, y2 + 2),
            f"Pred: {elem['label']} {elem['confidence']:.2f}",
            fill="red"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    vis.save(path)


# ==========================================
# 8. Main
# ==========================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VIS_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    print("Loading ScreenParser...")
    model = YOLO(str(MODEL_PATH))

    print("Loading ScreenParse dataset (streaming)...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
        streaming=True
    )

    csv_rows = []

    # 分别累计原图和缩放图的 TP / FP / FN
    totals = {
        "original": {"tp": 0, "fp": 0, "fn": 0},
        "resized": {"tp": 0, "fp": 0, "fn": 0}
    }

    resize_count = 0
    processed = 0

    progress = tqdm(
        total=MAX_SAMPLES,
        desc="ScreenParser Evaluation"
    )

    for sample in dataset:

        if processed >= MAX_SAMPLES:
            break

        image = sample["image"].convert("RGB")
        image_id = sample["id"]

        original_width, original_height = image.size

        # ----------------------------------
        # A. Original image inference
        # ----------------------------------

        original_gt = get_ground_truth(sample)

        original_preds, original_time = predict(
            model,
            image
        )

        original_stats = evaluate(
            original_gt,
            original_preds
        )

        # ----------------------------------
        # B. Resize image
        # ----------------------------------

        resized_image, resize_info = resize_image(image)

        scale_x = resize_info["scale_x"]
        scale_y = resize_info["scale_y"]

        if resize_info["resize_applied"]:
            resize_count += 1

        resized_gt = get_ground_truth(
            sample,
            scale_x,
            scale_y
        )

        # ----------------------------------
        # C. Resized image inference
        # ----------------------------------

        resized_preds, resized_time = predict(
            model,
            resized_image
        )

        resized_stats = evaluate(
            resized_gt,
            resized_preds
        )

        # ----------------------------------
        # D. Aggregate statistics
        # ----------------------------------

        totals["original"]["tp"] += original_stats["tp"]
        totals["original"]["fp"] += original_stats["fp"]
        totals["original"]["fn"] += original_stats["fn"]

        totals["resized"]["tp"] += resized_stats["tp"]
        totals["resized"]["fp"] += resized_stats["fp"]
        totals["resized"]["fn"] += resized_stats["fn"]

        original_metrics = calculate_metrics(
            **original_stats
        )

        resized_metrics = calculate_metrics(
            **resized_stats
        )

        # ----------------------------------
        # E. Save CSV rows
        # ----------------------------------

        common = {
            "image_id": image_id,
            "original_width": original_width,
            "original_height": original_height,
            "resized_width": resize_info["resized_width"],
            "resized_height": resize_info["resized_height"],
            "resize_applied": resize_info["resize_applied"],
            "scale_x": scale_x,
            "scale_y": scale_y,
        }

        for mode, stats, metrics, preds, inference_time in [
            (
                "original",
                original_stats,
                original_metrics,
                original_preds,
                original_time
            ),
            (
                "resized",
                resized_stats,
                resized_metrics,
                resized_preds,
                resized_time
            )
        ]:
            csv_rows.append({
                **common,
                "mode": mode,
                "gt_count": len(original_gt),
                "pred_count": len(preds),
                **stats,
                **metrics,
                "inference_time": inference_time
            })

        # ----------------------------------
        # F. Save visualizations
        # ----------------------------------

        if processed < SAVE_VIS_COUNT:

            save_visualization(
                resized_image,
                resized_gt,
                resized_preds,
                VIS_DIR / f"{image_id}_resized.jpg"
            )

        processed += 1

        progress.update(1)

        progress.set_postfix({
            "resize": resize_info["resize_applied"],
            "GT": len(original_gt),
            "Pred": len(resized_preds),
            "F1": f"{resized_metrics['f1']:.3f}"
        })

    progress.close()

    # ======================================
    # 9. Save CSV
    # ======================================

    csv_path = OUTPUT_DIR / "results.csv"

    if csv_rows:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=csv_rows[0].keys()
            )
            writer.writeheader()
            writer.writerows(csv_rows)

    # ======================================
    # 10. Summary
    # ======================================

    summary = {
        "dataset": DATASET_NAME,
        "model": str(MODEL_PATH),
        "processed_images": processed,
        "resize_count": resize_count,
        "resize_ratio": resize_count / processed if processed else 0,
        "eval_iou_threshold": EVAL_IOU,
        "results": {}
    }

    for mode, stats in totals.items():

        metrics = calculate_metrics(**stats)

        summary["results"][mode] = {
            **stats,
            **metrics
        }

    summary["difference"] = {
        key: (
            summary["results"]["resized"][key]
            - summary["results"]["original"][key]
        )
        for key in ["precision", "recall", "f1"]
    }

    json_path = OUTPUT_DIR / "summary.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            summary,
            f,
            indent=4,
            ensure_ascii=False
        )

    # ======================================
    # 11. Print report
    # ======================================

    print("\n" + "=" * 55)
    print("ScreenParser Resize Evaluation Report")
    print("=" * 55)

    print(f"Processed images: {processed}")
    print(f"Resized images: {resize_count}")

    for mode, stats in summary["results"].items():

        print(f"\n[{mode.upper()}]")

        print(f"TP: {stats['tp']}")
        print(f"FP: {stats['fp']}")
        print(f"FN: {stats['fn']}")

        print(f"Precision: {stats['precision']:.4f}")
        print(f"Recall:    {stats['recall']:.4f}")
        print(f"F1:        {stats['f1']:.4f}")

    print("\n[RESIZE - ORIGINAL]")

    for key, value in summary["difference"].items():
        print(f"{key}: {value:+.4f}")

    print("\nSaved:")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Visualizations: {VIS_DIR}")

    print("=" * 55)


if __name__ == "__main__":
    main()
