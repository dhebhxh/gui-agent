from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    goal: str

    old_resized_screenshot: bytes
    old_elements: List

    orig_screenshot: bytes
    resized_screenshot: bytes
    resize_info: dict
    elements: List

    messages: Annotated[list, add_messages]
    history: List[dict]

    expected_result: str

    last_action: dict
    # last action execution result
    last_execution_result: dict
    # last action visual verification result
    last_verification_result: dict

    step: int
    finished: bool