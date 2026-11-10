from langchain_openai import ChatOpenAI
from state import AgentState
from config import AgentConfig
from schema import AgentOutputSchema, ActionType
from prompts import SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
import base64
    
def _format_ai_messages(messages, max_n=5) -> str:
    ai_messages = []
    for msg in (messages or []):
        if msg.get("role") != "assistant":
            continue

        content = msg.get("content")
        if content and isinstance(content, str) and content.strip():
            ai_messages.append(content)

    if not ai_messages:
        return "This is the first step. Start by examining the current screen."

    recent = list(reversed(ai_messages[-max_n:]))
    lines = [f"{i}. {text}" for i, text in enumerate(recent, start=1)]
    return "\n".join(lines)

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
            thought_history=_format_ai_messages(state.get("messages") or [])
        )

        user_image = state.get("raw_screenshot")
        if isinstance(user_image, bytes):
            b64_str = base64.b64encode(user_image).decode("utf-8")
        else:
            b64_str = user_image
        
        llm_input = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_str}"}},
            ]},
        ]

        print(f"...reasoning start...")
        llm_output: AgentOutputSchema = llm_with_structure.invoke(llm_input)
        print(f"...reasoning complete...")

        thought = llm_output.thought
        action = llm_output.action.model_dump(exclude_none=True)

        ai_msg = {
            "role": "assistant",
            "content": thought or ""
        }

        return {
            "step": state.get("step") + 1,
            "finished": (llm_output.action.type == ActionType.FINISH),
            "last_action": action,
            "messages": [
                {"role": "user", "content": user_text},
                ai_msg
            ]
        }
    
    return planner_node
        