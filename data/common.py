from typing import TypedDict, Literal
from PIL import Image

class TextBlock(TypedDict):
    type: Literal["text"]
    text: str

class ImageBlock(TypedDict):
    type: Literal["image"]

ContentBlock = TextBlock | ImageBlock

class Message(TypedDict):
    role: str
    content: list[ContentBlock]

class VisionDataset(TypedDict):
    # format: conversional
    # type: prompt-completion
    prompt: list[Message]
    completion: list[Message]
    images: list[Image.Image]

    