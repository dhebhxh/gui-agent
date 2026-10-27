from typing import Callable
from screen_element_extractor import ScreenElementExtractor   # 你已有的
from dispatcher import ActionDispatcher                        # 你已有的
from state import AgentState
from config import AgentConfig
import cv2, numpy as np

def build_perception_node(cfg: AgentConfig):
    extractor = ScreenElementExtractor(
        ocr_langs=cfg.ocr_langs,
        iou_threshold=cfg.iou_threshold,
        use_gpu=cfg.use_gpu,
    )
    dispatcher = ActionDispatcher()

    def perception_node(state: AgentState) -> dict:
        # 1) 截图（复用 dispatcher 的 screenshot action，保证与执行层一致）
        shot = dispatcher.dispatch({"type": "screenshot"})   # {"type":"image","data":png}
        png = shot["data"]

        # 2) bytes -> cv2 image
        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        # 3) 元素提取
        output, vis = extractor.process_cv_image(img)

        # 4) 可视化图也编码成 png 存进 state（方便 debug / 给 LLM 看标注图）
        _, vis_buf = cv2.imencode(".png", vis)

        return {
            "screenshot": png,
            "elements": output["elements"],
            "vis_image": vis_buf.tobytes(),
        }

    return perception_node