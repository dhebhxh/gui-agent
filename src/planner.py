from langchain_openai import ChatOpenAI
from state import AgentState
from config import AgentConfig
from schema import AgentOutputSchema, ActionType
from prompts import SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
import base64
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def _build_multimodal_message(text: str, image_data) -> HumanMessage:

    if isinstance(image_data, bytes):
        b64_str = base64.b64encode(image_data).decode("utf-8")
    else:
        b64_str = image_data

    content = [
        {
            "type": "text",
            "text": text
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64_str}"}
        }
    ]

    return HumanMessage(content = content)
    
def _format_history(history:list, max_n=10):
    formatted_history = []
    for entry in history[:max_n]:
        step = entry.get("step")
        action = entry.get("action")
        result = entry.get("result")

        formatted_entry = f"Step {step}:\nAction: {action}\nResult: {result}\n"
        formatted_history.append(formatted_entry)

    return "\n".join(formatted_history)

def build_planner_node(cfg: AgentConfig):
    # initialize chat model
    llm = ChatOpenAI(
        model=cfg.model_name,
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )

    # structure output
    llm_with_structure = llm.with_structured_output(AgentOutputSchema)
    
    def planner_node(state: AgentState) -> dict:
        print("-" * 80)
        print(f"Processing planner node")
        print("-" * 80)

        user_text = PLANNER_USER_TEMPLATE.format(
            goal=state["goal"],
            history=_format_history(state.get("history", [])),
            last_action=state.get("last_action", "None"),
            last_result=state.get("last_result", "None"),
        )

        user_image = state.get("raw_screenshot") or state.get("raw_screenshot")

        user_msg = _build_multimodal_message(user_text, user_image)

        sys_msg = SystemMessage(content=SYSTEM_PROMPT)

        llm_input = [sys_msg, user_msg]

        print(f"...reasoning start...")
        llm_output: AgentOutputSchema = llm_with_structure.invoke(llm_input)
        print(f"...reasoning complete...")

        action = llm_output.action
        action_dict = action.model_dump()

        thought = action_dict.pop("thought", None)
        
        clear_action = action_dict

        ai_msg = AIMessage(content=thought or "")

        return {
            "step": state.get("step") + 1,
            "finished": (llm_output.action.type == ActionType.FINISH),
            "last_action": clear_action,
            "messages": [user_msg, ai_msg]
        }
    
    return planner_node
        