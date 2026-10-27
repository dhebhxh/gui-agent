from typing import TypedDict, Optional, Any


class UnifiedSample(TypedDict):
    """Unified sample format shared by all dataset adapters."""
    image_bytes: Optional[bytes]
    image_path: Optional[str]
    instruction: str
    action: dict
    source: str
    metadata: dict


# ---- Mind2Web operation -> our ActionSchema ----
_MIND2WEB_OP_MAP = {
    "CLICK": "left_click",
    "TYPE": "type_text",
    "SELECT": "left_click",   # TODO: SELECT needs dropdown handling
}


def normalize_action(raw: dict, source: str) -> dict:
    """Map a raw dataset action into our ActionSchema-shaped dict."""
    if source == "mind2web":
        op = str(raw.get("type", "")).upper()
        action_type = _MIND2WEB_OP_MAP.get(op, "left_click")
        result = {"type": action_type}
        if action_type == "type_text":
            result["text"] = raw.get("value", "")
        return result

    if source == "screenagent":
        # ScreenAgent actions are already structured; pass through known keys.
        act_type = (
            raw.get("action_type")
            or raw.get("type")
            or raw.get("action")
            or ""
        )
        act_type = str(act_type).lower()

        # Normalize common aliases to our ActionSchema names.
        alias = {
            "click": "left_click",
            "leftclick": "left_click",
            "left_click": "left_click",
            "double_click": "left_double_click",
            "doubleclick": "left_double_click",
            "rightclick": "right_click",
            "right_click": "right_click",
            "type": "type_text",
            "typetext": "type_text",
            "type_text": "type_text",
            "press": "key_press",
            "keypress": "key_press",
            "key_press": "key_press",
            "scroll": "scroll",
            "move": "mouse_move",
            "mousemove": "mouse_move",
            "drag": "left_click_drag",
            "wait": "wait",
        }
        action_type = alias.get(act_type, act_type or "left_click")

        result = {"type": action_type}
        for k in ("x", "y", "text", "key", "direction", "amount",
                  "end_x", "end_y"):
            if k in raw and raw[k] is not None:
                result[k] = raw[k]
        return result

    return dict(raw)