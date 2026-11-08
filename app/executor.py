import time
from state import AgentState
import requests

LOCAL_SERVER_URL = ""

def build_executor_node():

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
            payload = {"action": action}
            resp = requests.post(f"{LOCAL_SERVER_URL}/execute", json=payload, timeout=10)
            resp.raise_for_status()
            response_data = resp.json()
            result = response_data.get("result", {})
        except requests.exceptions.HTTPError as e:
            return {
                "last_result": {"type": "error", "data": str(e)}
            }
        except Exception as e:
            return {
                "last_result": {"type": "error", "data": str(e)},
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
        
