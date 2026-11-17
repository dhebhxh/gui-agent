import time
from state import AgentState
import requests
import logging

logger = logging.getLogger(__name__)

LOCAL_SERVER_URL = ""

def build_executor_node():

    def executor_node(state: AgentState) -> dict:
        logger.info("node executer | step=%d", state.get("step"))
        
        action = dict(state.get("last_action"))
        action_type = action["type"]

        # task finish
        if action_type == "finish":
            logger.info("executor | task finished")
            return {
                "finished": True,
                "last_result": {"type": "ok", "data": "finished"}
            }

        # other action
        req_start = time.time()
        try:
            payload = {"action": action}
            resp = requests.post(f"{LOCAL_SERVER_URL}/execute", json=payload, timeout=10)
            resp.raise_for_status()
            response_data = resp.json()
            result = response_data.get("result", {})
            logger.info(
                "http request | POST /execute action=%s status=%d latency=%.3fs",
                action_type,
                resp.status_code,
                time.time() - req_start
            )
        except requests.exceptions.HTTPError as e:
            logger.error(
                "http request failed | POST /execute action=%s status=%s latency=%.3fs error=%s",
                action_type,
                getattr(e.response, "status_code", None),
                time.time() - req_start,
                e,
            )
            return {
                "last_result": {"type": "error", "data": str(e)}
            }
        except Exception as e:
            logger.exception(
                "http request failed | POST /execute action=%s latency=%.3fs",
                action_type, time.time() - req_start,
            )
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

        logger.debug("executor done")
        
        return {
            "step": state.get("step") + 1,
            "last_result": safe_result,
            "history": list(state.get("history") or []) + [history_entry]
        }

    return executor_node
        
