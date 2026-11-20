import base64
import time, os
from screen_element_extractor import ScreenElementExtractor   # 你已有的
from state import AgentState
import cv2, numpy as np
import requests
import logging
from config import AgentConfig

logger = logging.getLogger(__name__)

LOCAL_SERVER_URL = ""

def build_perception_node(cfg: AgentConfig):
    extractor = ScreenElementExtractor()
    local_server_url = cfg.local_server_url.rstrip("/")
    
    def perception_node(state: AgentState) -> dict:
        logger.info(
            "node=perception step=%d",
            state.get("step")
        )

        start = time.time()

        # request screenshot
        req_start = time.time()
        try:
            resp = requests.get(f"{local_server_url}/screenshot", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "http request | GET /screenshot status=%d latency=%.3fs size=%d",
                resp.status_code,
                time.time() - req_start,
                len(resp.content)
            )
        except Exception as e:
            logger.error(
                "http request | GET /screenshot latency=%.3fs error=%s",
                time.time() - req_start,
                e
            )
            return {"last_result": {"type": "error", "data": str(e)}}

        if data.get("status") != "success":
            logger.error("server failed to take screenshot | response=%s", data)
            raise ValueError(f"Server failed to take screenshot")

        img_base64 = data.get("image_base64")
        png = base64.b64decode(img_base64)
        logger.debug("screenshot decoded | %d bytes", len(png))

        # save raw screenshot
        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int(time.time() * 1000) % 1000
        raw_path = os.path.join("screenshot", f"raw_{ts}_{ms:03d}.png")
        with open(raw_path, "wb") as f:
            f.write(png)
        logger.debug("raw screenshot saved | path=%s", raw_path)

        # extract element
        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        output, annotated_img = extractor.process_cv_image(img)
        _, annotated_buf = cv2.imencode(".png", annotated_img)
        annotated_bytes = annotated_buf.tobytes()

        logger.debug(
            "perception done | total_time=%.2fs",
            time.time() - start
        )

        return {
            "raw_screenshot": png,
            "annotated_screenshot": annotated_bytes,
            "elements": output["elements"],
        }

    return perception_node