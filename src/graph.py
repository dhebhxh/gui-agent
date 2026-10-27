from langgraph.graph import StateGraph, END
from state import AgentState
from perception import build_perception_node
from planner import build_planner_node
from executor import build_executor_node
from feedback import build_feedback_node
from config import AgentConfig

def build_graph(cfg: AgentConfig):
    g = StateGraph(AgentState)

    g.add_node("perception", build_perception_node(cfg))
    g.add_node("planner",    build_planner_node(cfg))
    g.add_node("executor",   build_executor_node(cfg))
    g.add_node("feedback",   build_feedback_node(cfg))

    g.set_entry_point("perception")

    g.add_edge("perception", "planner")
    g.add_edge("planner",    "executor")
    g.add_edge("executor",   "feedback")

    def should_continue(state: AgentState) -> str:
        if state.get("finished"):
            return "end"
        if state["step"] >= cfg.max_steps:
            return "end"
        if state.get("error") and state["step"] >= cfg.max_steps:
            return "end"
        return "continue"

    g.add_conditional_edges(
        "feedback",
        should_continue,
        {"continue": "perception", "end": END},
    )

    return g.compile()