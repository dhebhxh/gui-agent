from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    goal: str

    orig_screenshot: bytes
    resized_screenshot: bytes
    resize_info: dict
    elements: List

    messages: Annotated[list, add_messages]
    history: List[dict]
    
    last_action: dict
    last_result: dict

    step: int
    finished: bool