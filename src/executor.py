from dispatcher import ActionDispatcher
from state import AgentState
from config import AgentConfig

def build_executor_node(cfg: AgentConfig):
    dispatcher = ActionDispatcher()

    def _resolve_coords(action: dict, elements: list) -> dict:
        """若给 element_id 而没给 x/y，从 elements 取 center 补上"""
        if action.get("element_id") and action.get("x") is None:
            for e in elements:
                if e["element_id"] == action["element_id"]:
                    action["x"], action["y"] = e["center"]
                    break
        return action

    def executor_node(state: AgentState) -> dict:
        action = dict(state["last_action"])

        if action["type"] == "finish":
            return {"finished": True, "last_result": {"type": "ok", "data": "finished"}}

        action = {k: v for k, v in action.items() if v is not None and k != "reasoning"}
        action = _resolve_coords(action, state["elements"])

        try:
            result = dispatcher.dispatch(action)
            error = None
        except Exception as e:
            result = {"type": "error", "error": str(e)}
            error = str(e)

        record = {"step": state["step"], "action": action, "result": result, "error": error}
        history = state.get("history", []) + [record]

        return {"last_result": result, "history": history, "error": error}

    return executor_node