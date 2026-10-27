import uuid
from config import AgentConfig
from graph import build_graph

class GUIAgent:
    def __init__(self, cfg: AgentConfig = None):
        self.cfg = cfg or AgentConfig()
        self.app = build_graph(self.cfg)

    def run(self, goal: str, thread_id: str = None) -> dict:
        init_state = {
            "goal": goal,
            "messages": [],
            "step": 0,
            "screenshot": None,
            "elements": [],
            "vis_image": None,
            "last_action": None,
            "last_result": None,
            "history": [],
            "finished": False,
            "error": None,
        }
        config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())},
                  "recursion_limit": self.cfg.max_steps * 6}
        final = self.app.invoke(init_state, config=config)
        return {
            "finished": final["finished"],
            "steps": final["step"],
            "history": final["history"],
            "error": final["error"],
        }