from state import AgentState
from config import AgentConfig
from llm import build_vl_llm, build_multimodal_message
from prompts import REFLECT_PROMPT

def build_feedback_node(cfg: AgentConfig):
    llm = build_vl_llm(cfg)

    def feedback_node(state: AgentState) -> dict:
        # 规则层：动作失败 → 直接标记需重规划（planner 下一轮会看到 error）
        if state.get("last_result", {}).get("type") == "error":
            return {"error": state["last_result"]["error"]}

        # 语义层（可选）：让 VL 模型看一眼执行后画面，给一句评价
        # 这里不强制，避免每步多一次 LLM 调用；可按需开启
        msg = build_multimodal_message(
            REFLECT_PROMPT.format(result=state["last_result"]),
            state["screenshot"],
        )
        reflect = llm.invoke([msg])
        # 把反思写进 messages，供下一轮 planner 参考
        return {"messages": [reflect]}

    return feedback_node