from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):

    goal: str

    raw_screenshot: bytes
    annotated_screenshot: bytes

    messages: Annotated[list, add_messages]
    history: List[dict]
    
    last_action: dict
    last_result: dict

    step: int
    finished: bool