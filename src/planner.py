from langchain_core.messages import SystemMessage
from state import AgentState, ActionSchema
from llm import build_vl_llm, build_multimodal_message
from prompts import SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
from config import AgentConfig

def _format_elements(elements, max_n=60):
    lines = []
    for e in elements[:max_n]:
        cx, cy = e["center"]
        txt = e.get("text", "")[:20]
        lines.append(f"#{e['element_id']} [{e['type']}] center=({cx},{cy}) text={txt!r}")
    return "\n".join(lines)

def _format_history(history, last_n=6):
    return "\n".join(
        f"step{h['step']}: {h['action'].get('type')} -> {h['result'].get('type')}"
        for h in history[-last_n:]
    )

def build_planner_node(cfg: AgentConfig):
    llm = build_vl_llm(cfg)
    structured_llm = llm.with_structured_output(ActionSchema)

    def planner_node(state: AgentState) -> dict:
        user_text = PLANNER_USER_TEMPLATE.format(
            goal=state["goal"],
            step=state["step"] + 1,
            max_steps=cfg.max_steps,
            n=len(state["elements"]),
            elements_desc=_format_elements(state["elements"], cfg.max_elements_in_prompt),
            last_action=state.get("last_action"),
            last_result=state.get("last_result"),
            history_summary=_format_history(state.get("history", [])),
        )

        # 多模态消息：文本 + 可视化图（或原始截图）
        msg = build_multimodal_message(user_text, state["vis_image"] or state["screenshot"])
        messages = [SystemMessage(content=SYSTEM_PROMPT), msg]

        action: ActionSchema = structured_llm.invoke(messages)
        return {
            "last_action": action.model_dump(),
            "step": state["step"] + 1,
            "messages": [msg],   # 可选：记录到 messages 历史
        }

    return planner_node