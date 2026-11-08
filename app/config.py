import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AgentConfig:
    model_name: str = os.getenv("VLM_MODEL_ID")
    base_url: str = "http://127.0.0.1:11434/v1"
    api_key: str = os.getenv("MODELSCOPE_API_KEY", "")
    temperature: float = 0.1
    max_tokens: int = 2048

    max_steps: int = 10
    max_elements_in_prompt: int = 60