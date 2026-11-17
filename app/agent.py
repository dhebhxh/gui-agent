import uuid
from typing import Generator
import logging
import time
from config import AgentConfig
from graph import build_graph

logger = logging.getLogger(__name__)

class GUIAgent:
    def __init__(self, agent_config: AgentConfig = None):
        self.agent_cfg = agent_config or AgentConfig()
        self.agent = build_graph(self.agent_cfg)
        logger.info(
            "Agent created | model=%s base_url=%s max_steps=%d",
            self.agent_cfg.model_name,
            self.agent_cfg.base_url,
            self.agent_cfg.max_steps,
        )

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

        logger.info(
            "run start | thread_id=%s goal=%r",
            thread_id,
            goal,
        )

        last_printed_step = 0
        loop_start = time.time()

        for event in self.agent.stream(
            init_state, config=run_config, stream_mode=stream_mode
        ):

            state = event
            step = state.get("step")

            if step != last_printed_step:

                logger.info(
                    "loop done | step=%d loop_time=%.2fs",
                    last_printed_step,
                    time.time() - loop_start,
                )

                last_printed_step = step
                loop_start = time.time()

            yield state