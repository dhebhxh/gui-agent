import time
from dispatcher import ActionDispatcher
from state import AgentState

def build_executor_node():
    d = ActionDispatcher()

    def executor_node(state: AgentState) -> dict:

        print("-" * 80)
        print(f"Processing executor node")
        print("-" * 80)
        
        action = dict(state.get("last_action"))

        action_type = action["type"]

        # task finish
        if action_type == "finish":
            return {
                "finished": True,
                "last_result": {"type": "ok", "data": "finished"}
            }

        # other action
        try:
            result = d.dispatch(action)
        except Exception as e:
            err_msg = f"type(d).__name__: {e}"
            return {
                "last_result": {"type": "error", "data": err_msg},
            }

        time.sleep(2) # wait for the screen to update after the action is performed
        # if screenshot
        if action_type == "screenshot":
            safe_result = {"type": "image", "data": "<image>"}
        else:
            safe_result = result

        history_entry = {
            "step": state.get("step", 0),
            "action": {k: v for k, v in action.items()},
            "result": safe_result
        }

        return {
            "last_result": safe_result,
            "history": list(state.get("history") or []) + [history_entry]
        }

    return executor_node
        
