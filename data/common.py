from typing import TypedDict, Optional, Any


class UnifiedSample(TypedDict):
    """Unified sample format shared by all dataset adapters."""
    goal_id: str
    goal_desc: str
    image_bytes: Optional[bytes]
    step: int
    action: dict
    source: str
    metadata: Optional[dict]