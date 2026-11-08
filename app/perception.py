import base64
import time, os
from screen_element_extractor import ScreenElementExtractor   # 你已有的
from state import AgentState
import cv2, numpy as np
import requests

LOCAL_SERVER_URL = ""

def build_perception_node():
    extractor = ScreenElementExtractor()

    def perception_node(state: AgentState) -> dict:
        print("-" * 80)
        print(f"Processing perception node")
        print("-" * 80)

        try:
            resp = requests.get(f"{LOCAL_SERVER_URL}/screenshot")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error fetching data from server: {e}")
            return {"last_result": {"type": "error", "data": str(e)}}

        if data.get("status") != "success":
            raise ValueError(f"Server failed to take screenshot")

        img_base64 = data.get("image_base64")
        png = base64.b64decode(img_base64)

        print(f"Received screenshot data: {len(png)} bytes")

        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int(time.time() * 1000) % 1000
        raw_path = os.path.join("screenshot", f"raw_{ts}_{ms:03d}.png")
        with open(raw_path, "wb") as f:
            f.write(png)

        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        output, annotated_img = extractor.process_cv_image(img)
        _, annotated_buf = cv2.imencode(".png", annotated_img)

        print(f"Generated annotated screenshot")

        return {
            "raw_screenshot": png,
            "annotated_screenshot": annotated_buf.tobytes(),
            "elements": output["elements"],
        }

    return perception_node