
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from state import AgentState
from config import AgentConfig
from schema import AgentOutputSchema, ActionType
from prompts import SYSTEM_PROMPT, PLANNER_USER_TEMPLATE

import base64
import json
import logging
import time

logger = logging.getLogger(__name__)


def _dump_llm_input(llm_input) -> str:
    lines = []

    for message in llm_input:
        role = message.get("role")
        content = message.get("content")

        lines.append("[role] " + str(role))

        if isinstance(content, str):
            lines.append("[content] " + content)

        elif isinstance(content, list):
            for block in content:
                block_type = block.get("type")

                if block_type == "text":
                    lines.append("[text] " + str(block.get("text")))

                elif block_type == "image_url":
                    image_url = block.get("image_url", {})
                    url = image_url.get("url", "")
                    lines.append("[image] <" + str(len(url)) + " chars>")

                else:
                    lines.append("[block] type=" + str(block_type))

        lines.append("")

    return "\n".join(lines)


def _format_ai_messages(messages, max_n=5) -> str:
    """Extract recent planner thoughts from conversation history."""

    ai_messages = []

    for msg in (messages or []):
        if isinstance(msg, AIMessage):
            ai_messages.append(msg.content)

    if not ai_messages:
        return "1. This is the first step. Start by examining the current screen."

    recent = ai_messages[-max_n:]

    return "\n".join(
        f"{i}. {content}"
        for i, content in enumerate(recent, start=1)
    )


def _format_context(value) -> str:
    """Format state information for the planner prompt."""

    if value is None:
        return "None"

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str
        )

    return str(value)


def build_planner_node(cfg: AgentConfig):

    # Initialize chat model
    llm = ChatOpenAI(
        model=cfg.model_name,
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )

    # Structured output
    llm_with_structure = llm.with_structured_output(AgentOutputSchema)

    def planner_node(state: AgentState) -> dict:

        logger.info(
            "node=planner step=%d",
            state.get("step")
        )

        start = time.time()

        # 1. Prepare previous action context
        last_action = _format_context(
            state.get("last_action")
        )

        execution_result = _format_context(
            state.get("last_execution_result")
        )

        verification_result = _format_context(
            state.get("last_verification_result")
        )

        expected_result = _format_context(
            state.get("expected_result")
        )

        thought_history = _format_ai_messages(
            state.get("messages") or []
        )

        # 2. Build planner prompt
        user_text = PLANNER_USER_TEMPLATE.format(
            goal=state["goal"],
            last_action=last_action,
            execution_result=execution_result,
            verification_result=verification_result,
            expected_result=expected_result,
            thought_history=thought_history
        )

        # 3. Prepare screenshot
        user_image = state.get("raw_screenshot")

        if isinstance(user_image, bytes):
            b64_str = base64.b64encode(user_image).decode("utf-8")
        else:
            b64_str = user_image

        llm_input = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64_str}"
                        }
                    },
                ]
            },
        ]

        # 4. Log full LLM input
        logger.debug(
            "llm input | step=%d\n%s",
            state.get("step"),
            _dump_llm_input(llm_input)
        )

        # 5. Call LLM
        logger.info("llm call start")

        llm_start = time.time()

        llm_output: AgentOutputSchema = llm_with_structure.invoke(
            llm_input
        )

        logger.info(
            "llm call end | latency=%.2fs",
            time.time() - llm_start
        )

        # 6. Extract structured output
        thought = llm_output.thought
        action = llm_output.action.model_dump(exclude_none=True)
        expected_result = llm_output.expected_result

        logger.info(
            "llm output | step=%d\n%s",
            state.get("step"),
            llm_output.model_dump_json(indent=2)
        )

        logger.info(
            "planner done | step=%d action=%s total_time=%.2fs",
            state.get("step"),
            action.get("type"),
            time.time() - start
        )

        # 7. Update agent state
        return {
            "finished": (
                llm_output.action.type == ActionType.FINISH
            ),
            "last_action": action,
            "expected_result": expected_result,
            "messages": [
                HumanMessage(content=user_text),
                AIMessage(content=thought or ""),
            ]
        }

    return planner_node
