# screen_parser_detector.py
from ultralytics import YOLO
from pathlib import Path
from huggingface_hub import hf_hub_download

class ScreenParserDetector:
    def __init__(
        self,
        device=None,
        conf=0.10,
        iou=0.10,
        imgsz=1280
    ):
        base_dir = Path(__file__).resolve().parent
        model_dir = base_dir / "models" / "screenparser"
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / "best.pt"

        if not model_path.exists():
            downloaded_path = hf_hub_download(
                repo_id="docling-project/ScreenParser",
                filename="best.pt",
                local_dir=str(model_dir)
            )
        
        self.model = YOLO(str(model_path))
        self.device = device
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz

    def process_image(self, image):
        results = self.model.predict(
            source=image,
            imgsz=self.imgsz,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False
        )

        elements = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()

                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                label = result.names[class_id]

                elements.append({
                    "bbox": [round(x1), round(y1), round(x2), round(y2)],
                    "text": "",
                    "type": label,
                    "confidence": round(confidence, 4),
                    "source": "screenparser"
                })

        return {"elements": elements}


