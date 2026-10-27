import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    # ---- LLM (ModelScope / Qwen2.5-VL) ----
    model_name: str = os.getenv("VLM_MODEL_ID", "Qwen/Qwen2.5-VL-7B-Instruct")
    base_url: str = "https://api-inference.modelscope.cn/v1/"
    api_key: str = os.getenv("MODELSCOPE_API_KEY", "")
    temperature: float = 0.1
    max_tokens: int = 2048

    # ---- Perception ----
    ocr_langs: tuple = ("ch_sim", "en")
    iou_threshold: float = 0.3
    use_gpu: bool = False
    max_elements_in_prompt: int = 60               # Truncate/summarize when too many elements

    # ---- Loop control ----
    max_steps: int = 15                            # Maximum loop iterations
    max_retries_per_step: int = 2                  # Retries allowed per step on action failure
    screenshot_dir: str = "./runs"

    # ---- Allowed actions (aligned with dispatcher) ----
    allowed_actions: list = field(default_factory=lambda: [
        "mouse_move", "left_click", "right_click", "left_double_click",
        "scroll", "left_click_drag", "type_text", "key_press",
        "key_down", "key_up", "wait"
    ])