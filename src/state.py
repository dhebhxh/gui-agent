from typing import TypedDict, Annotated, List, Optional, Literal
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

# ---------- Action Schema (for LLM structured output) ----------
class ActionSchema(BaseModel):
    """Action structure the LLM must output; fields align with the dispatcher."""
    type: Literal[
        "left_click", "right_click", "left_double_click", "mouse_move",
        "scroll", "left_click_drag", "type_text", "key_press",
        "key_down", "key_up", "wait", "finish"
    ] = Field(..., description="Action type")
    x: Optional[int] = Field(None, description="Target x coordinate; required for click/move")
    y: Optional[int] = Field(None, description="Target y coordinate")
    text: Optional[str] = Field(None, description="Text to type for type_text")
    key: Optional[str] = Field(None, description="Key name")
    direction: Optional[Literal["up", "down", "left", "right"]] = None
    amount: Optional[float] = None
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    element_id: Optional[int] = Field(None, description="Perceived element id to reference, if any")
    reasoning: str = Field(..., description="Why this action was chosen (for trajectory logging)")

# ---------- LangGraph shared state ----------
class AgentState(TypedDict):
    goal: str                                   # User task goal
    messages: Annotated[list, add_messages]     # Conversation / reasoning history
    step: int                                   # Current step count
    screenshot: Optional[bytes]                 # Current screenshot (PNG bytes)
    elements: List[dict]                        # List of perceived elements
    vis_image: Optional[bytes]                  # Visualization/debug image
    last_action: Optional[dict]                 # Previous action
    last_result: Optional[dict]                 # Previous execution result {"type": "ok"/"error", ...}
    history: List[dict]                         # Full trajectory [{step, action, result, ...}]
    finished: bool                              # Whether the task is finished
    error: Optional[str]                        # Error message