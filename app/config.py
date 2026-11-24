import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AgentConfig:
    model_name: str = "mind2web"
    base_url: str = "http://127.0.0.1:8000/v1"
    api_key: str = "EMPTY"
    temperature: float = 0.1
    max_tokens: int = 2048

    max_steps: int = 10
    max_elements_in_prompt: int = 60

    local_server_url: str = "http://127.0.0.1:8001/"

    # image resize config
    factor: int = 28
    min_pixels: int = 256 * 28 * 28
    max_pixels: int = 1280 * 28 * 28