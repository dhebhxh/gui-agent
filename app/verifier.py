import logging
from state import AgentState
from config import AgentConfig
from action_verifier import ActionVerifier

logger = logging.getLogger(__name__)

def build_verifier_node(cfg: AgentConfig):

    action_verifier = ActionVerifier()

    def verifier_node(state: AgentState) -> dict:

        logger.info(
            "node=verifier step=%d",
            state.get("step", 0)
        )

        result = action_verifier.verify(state)

        logger.info(
            "verification result | status=%s reason=%s",
            result["status"],
            result["reason"]
        )

        return {
            "last_verification_result": result
        }

    return verifier_node