import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import AgentConfig


def build_vl_llm(cfg: AgentConfig) -> ChatOpenAI:
    """
    Qwen2.5-VL is compatible with the OpenAI Chat Completions protocol.
    Reuse ChatOpenAI directly; just swap out model/base_url.
    """
    return ChatOpenAI(
        model=cfg.model_name,
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        # Key point: multimodal input
    )


def encode_image_to_data_url(png_bytes: bytes) -> str:
    """Encode screenshot bytes into a data URL for use in a HumanMessage."""
    b64 = base64.b64encode(png_bytes).decode()
    return f"data:image/png;base64,{b64}"


def build_multimodal_message(text: str, png_bytes: bytes) -> HumanMessage:
    """Build a HumanMessage containing both text and an image."""
    return HumanMessage(content=[
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": {"url": encode_image_to_data_url(png_bytes)}},
    ])