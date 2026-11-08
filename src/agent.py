import uuid
from typing import Generator

from config import AgentConfig
from graph import build_graph


class GUIAgent:
    def __init__(self, agent_config: AgentConfig = None):
        self.agent_cfg = agent_config or AgentConfig()
        self.agent = build_graph(self.agent_cfg)
        print(f"Agent created")

    def run_stream(
        self,
        goal: str,
        thread_id: str = None,
        stream_mode: str = "values",
    ) -> Generator[dict, None, None]:
        init_state = {
            "goal": goal,
            "raw_screenshot": None,
            "annotated_screenshot": None,
            "elements": [],
            "messages": [],
            "history": [],
            "last_action": None,
            "last_result": None,
            "step": 0,
            "finished": False,
        }

        run_config = {
            "configurable": {"thread_id": thread_id or str(uuid.uuid4())},
            "recursion_limit": self.agent_cfg.max_steps * 6 + 20,
        }

        last_printed_step = None
        
        for event in self.agent.stream(
            init_state, config=run_config, stream_mode=stream_mode
        ):

            state = event
            step = state.get("step", 0)

            if step != last_printed_step:
                last_printed_step = step
                print(
                    f"[step {step}]\n"
                    f"thought={state.get('messages')[-1].content if state.get('messages') else None}\n"
                    f"action={state.get('last_action')}\n"
                    f"result={state.get('last_result')}\n"
                    f"finished={state.get('finished')}"
                )

            yield state