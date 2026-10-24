import cv2
import numpy as np
import easyocr

class ScreenElementExtractor:
    def __init__(self, ocr_langs=('ch_sim', 'en'), iou_threshold=0.3, use_gpu=False):
        self.ocr = easyocr.Reader(list(ocr_langs), gpu=use_gpu)
        self.iou_threshold = iou_threshold
        self._next_id = 1

    @staticmethod
    def _poly_to_bbox(poly):
        pts = np.array(poly, dtype=np.int32)
        x1, y1 = pts[:, 0].min(), pts[:, 1].min()
        x2, y2 = pts[:, 0].max(), pts[:, 1].max()
        return [int(x1), int(y1), int(x2), int(y2)]

    @staticmethod
    def _iou(box_a, box_b):
        xa1, ya1, xa2, ya2 = box_a
        xb1, yb1, xb2, yb2 = box_b
        inter_x1 = max(xa1, xb1)
        inter_y1 = max(ya1, yb1)
        inter_x2 = min(xa2, xb2)
        inter_y2 = min(ya2, yb2)
        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_a = (xa2 - xa1) * (ya2 - ya1)
        area_b = (xb2 - xb1) * (yb2 - yb1)
        union = area_a + area_b - inter_area
        return inter_area / union if union > 0 else 0.0

    @staticmethod
    def _center(bbox):
        x1, y1, x2, y2 = bbox
        return [(x1 + x2) // 2, (y1 + y2) // 2]

    def _run_ocr(self, image):
        results = self.ocr.readtext(image)
        ocr_elements = []
        for poly, text, conf in results:
            if conf < 0.3:
                continue
            bbox = self._poly_to_bbox(poly)
            ocr_elements.append({
                "bbox": bbox,
                "text": text,
                "confidence": round(float(conf), 4),
                "source": "ocr",
            })
        return ocr_elements

    def _run_visual_detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 5
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = image.shape[:2]
        visual_elements = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            if area < 200 or area > 0.5 * w * h or bw < 10 or bh < 8:
                continue
            aspect = bw / bh if bh > 0 else 0
            if aspect > 15 or aspect < 0.05:
                continue
            if x <= 1 and y <= 1 and bw >= w - 2 and bh >= h - 2:
                continue
            visual_elements.append({
                "bbox": [x, y, x + bw, y + bh],
                "text": "",
                "confidence": 1.0,
                "source": "contour",
            })
        return visual_elements

    def _merge(self, ocr_elements, visual_elements):
        merged = []
        for elem in ocr_elements:
            elem["element_id"] = self._next_id
            elem["type"] = self._infer_type(elem)
            self._next_id += 1
            merged.append(elem)

        for ve in visual_elements:
            dominated = False
            for me in merged:
                if self._iou(ve["bbox"], me["bbox"]) >= self.iou_threshold:
                    dominated = True
                    break
            if not dominated:
                ve["element_id"] = self._next_id
                ve["type"] = self._infer_type(ve)
                self._next_id += 1
                merged.append(ve)
        return merged

    @staticmethod
    def _infer_type(elem):
        text = elem.get("text", "")
        bbox = elem["bbox"]
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if text and len(text) <= 6 and h < 50:
            return "button"
        if text:
            return "text"
        if 30 < w < 300 and 20 < h < 60:
            return "input"
        return "icon"

    def _draw(self, image, elements):
        vis = image.copy()
        for elem in elements:
            x1, y1, x2, y2 = elem["bbox"]
            etype = elem["type"]
            color = {
                "button": (0, 200, 0),
                "text": (200, 150, 0),
                "input": (0, 165, 255),
                "icon": (255, 0, 200),
            }.get(etype, (0, 255, 255))

            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            label = f"#{elem['element_id']}"
            if elem["text"]:
                label += f" {elem['text'][:10]}"

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(vis, (x1, max(y1 - th - 6, 0)), (x1 + tw + 4, y1), color, -1)
            cv2.putText(vis, label, (x1 + 2, max(y1 - 4, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        return vis

    # ==========================================
    # 新增：专用于批量测试的极速接口 (不读写文件)
    # ==========================================
    def process_cv_image(self, image):
        """直接接收 OpenCV BGR 图像，返回 elements 和可视化图像"""
        self._next_id = 1  # 每次处理新图重置 ID，保证每张图都从 #1 开始
        
        h, w = image.shape[:2]
        ocr_elems = self._run_ocr(image)
        visual_elems = self._run_visual_detect(image)
        elements = self._merge(ocr_elems, visual_elems)

        for elem in elements:
            elem["center"] = self._center(elem["bbox"])

        vis = self._draw(image, elements)
        
        output = {
            "screenshot_size": [w, h],
            "element_count": len(elements),
            "elements": elements,
        }
        return output, vis