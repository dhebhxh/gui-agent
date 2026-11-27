import base64
import time, os
from screen_parser_detector import ScreenParserDetector
from state import AgentState
import cv2, numpy as np
import requests
import logging
from config import AgentConfig
from PIL import Image
from io import BytesIO
from qwen_vl_utils.vision_process import smart_resize


logger = logging.getLogger(__name__)

def resize_screenshot(orig_png: bytes, factor: int, min_pixels: int, max_pixels: int):
    image = Image.open(BytesIO(orig_png)).convert("RGB")
    orig_w, orig_h = image.size

    new_h, new_w = smart_resize(
        orig_h,
        orig_w,
        factor=factor,
        min_pixels=min_pixels,
        max_pixels=max_pixels
    )

    scale_x = new_w / orig_w
    scale_y = new_h / orig_h

    if (new_w, new_h) != (orig_w, orig_h):
        resized_image = image.resize(
            (new_w, new_h),
            Image.Resampling.BICUBIC
        )
    else:
        resized_image = image

    buffer = BytesIO()
    resized_image.save(buffer, format="PNG")
    resized_png = buffer.getvalue()
    resize_info = {
        "original_width": orig_w,
        "original_height": orig_h,
        "resized_width": new_w,
        "resized_height": new_h,
        "scale_x": scale_x,
        "scale_y": scale_y
    }

    return resized_png, resize_info

def build_perception_node(cfg: AgentConfig):
    detector = ScreenParserDetector(
        device=0,
        conf=0.10,
        iou=0.10,
        imgsz=1280
    )

    local_server_url = cfg.local_server_url.rstrip("/")
    factor = cfg.factor
    min_pixels = cfg.min_pixels
    max_pixels = cfg.max_pixels

    def perception_node(state: AgentState) -> dict:
        logger.info(
            "node=perception step=%d",
            state.get("step")
        )

        start = time.time()

        old_resized_screenshot = state.get("resized_screenshot")
        old_elements = state.get("elements", [])

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
        orig_png = base64.b64decode(img_base64)
        logger.debug("screenshot decoded | %d bytes", len(orig_png))

        # save original screenshot
        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int(time.time() * 1000) % 1000
        orig_path = os.path.join("screenshot", f"orig_{ts}_{ms:03d}.png")
        with open(orig_path, "wb") as f:
            f.write(orig_png)
        logger.debug("original screenshot saved | path=%s", orig_path)

        # 将原始截图进行缩放调整，并且存储缩放后的图片
        resized_png, resize_info = resize_screenshot(orig_png, factor, min_pixels, max_pixels)
        resized_path = os.path.join(
            "screenshot",
            f"resized_{ts}_{ms:03d}.png"
        )
        with open(resized_path, "wb") as f:
            f.write(resized_png)

        logger.info(
            "Screenshot resized | "
            "%dx%d -> %dx%d | scale_x=%.4f scale_y=%.4f",
            resize_info["original_width"],
            resize_info["original_height"],
            resize_info["resized_width"],
            resize_info["resized_height"],
            resize_info["scale_x"],
            resize_info["scale_y"],
        )

        # extract element
        arr = np.frombuffer(resized_png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        output = detector.process_image(img)

        logger.debug(
            "perception done | total_time=%.2fs",
            time.time() - start
        )

        return {
            "old_resized_screenshot": old_resized_screenshot,
            "old_elements": old_elements,
            
            "orig_screenshot": orig_png,
            "resized_screenshot": resized_png,
            "resize_info": resize_info,
            "elements": output["elements"],
        }

    return perception_node