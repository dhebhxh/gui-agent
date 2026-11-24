import time
from state import AgentState
import requests
import logging
from config import AgentConfig

logger = logging.getLogger(__name__)

def _convert_action_coordinates(action: dict, resize_info: dict) -> dict:
    action = dict(action)
    coordinate_keys = (
        "x", "y",
        "start_x", "start_y",
        "end_x", "end_y",
    )

    if not any(key in action for key in coordinate_keys):
        return action
    if not resize_info:
        raise ValueError("Missing resize_info for coordinate conversion.")

    scale_x = resize_info.get("scale_x")
    scale_y = resize_info.get("scale_y")

    if not scale_x or not scale_y or scale_x <= 0 or scale_y <= 0:
        raise ValueError(f"Invalid resize_info: {resize_info}")

    for key in coordinate_keys:
        if key not in action:
            continue
        scale = scale_x if key.endswith("x") else scale_y
        action[key] = int(round(action[key] / scale))

    return action

def build_executor_node(cfg: AgentConfig):
    local_server_url = cfg.local_server_url.rstrip("/")
    
    def executor_node(state: AgentState) -> dict:
        logger.info("node executer | step=%d", state.get("step"))
        
        original_action = dict(state.get("last_action") or {})
        action_type = original_action["type"]

        # task finish
        if action_type == "finish":
            logger.info("executor | task finished")
            return {
                "finished": True,
                "last_execution_result": {
                    "type": "ok",
                    "data": "finished"
                }
            }

        try:
            resize_info = state.get("resize_info")
            action = _convert_action_coordinates(
                original_action,
                resize_info
            )

            logger.debug(
                "coordinate conversion | origina%s executed=%s",
                original_action,
                action
            )

        except Exception as e:
            logger.exception("coordinate conversion failed")
            return {
                "last_execution_result": {
                    "type": "error",
                    "data": str(e)
                }
            }
        
        # other action
        req_start = time.time()
        try:
            payload = {"action": action}
            resp = requests.post(f"{local_server_url}/execute", json=payload, timeout=10)
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
                "last_execution_result": {
                    "type": "error",
                    "data": str(e)
                }
            }
        except Exception as e:
            logger.exception(
                "http request failed | POST /execute action=%s latency=%.3fs",
                action_type, time.time() - req_start,
            )
            return {
                "last_execution_result": {
                    "type": "error",
                    "data": str(e)
                },
            }

        time.sleep(2) # wait for the screen to update after the action is performed

        # if screenshot
        if action_type == "screenshot":
            safe_result = {"type": "image", "data": "<image>"}
        else:
            safe_result = result

        history_entry = {
            "step": state.get("step", 0),
            "action": original_action,
            "executed_action": action,
            "execution_result": safe_result
        }

        logger.debug("executor done")
        
        return {
            "step": state.get("step") + 1,
            "last_execution_result": safe_result,
            "history": list(state.get("history") or []) + [history_entry]
        }

    return executor_node
        
