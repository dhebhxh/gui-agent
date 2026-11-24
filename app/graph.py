from state import AgentState
from langgraph.graph import StateGraph, END
from perception import build_perception_node
from planner import build_planner_node
from executor import build_executor_node
from verifier import build_verifier_node

def build_graph(cfg):

    g = StateGraph(AgentState)

    g.add_node("perception", build_perception_node(cfg))
    g.add_node("verifier", build_verifier_node(cfg))
    g.add_node("planner",    build_planner_node(cfg))
    g.add_node("executor",   build_executor_node(cfg))

    g.set_entry_point("perception")

    g.add_edge("perception", "verifier")
    g.add_edge("verifier", "planner")
    g.add_edge("executor", "perception")

    def should_continue(state: AgentState) -> str:
        if state.get("finished"):
            return "end"
        if state.get("step") >= cfg.max_steps:
            return "end"
        
        return "continue"

    g.add_conditional_edges(
        "planner",
        should_continue,
        {"continue": "executor", "end": END},
    )

    return g.compile()