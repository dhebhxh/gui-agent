# cli.py
import logging
import typer
from agent import GUIAgent
from logging_config import setup_logging

app = typer.Typer()

logger = logging.getLogger(__name__)

@app.command()
def run(goal: str):
    setup_logging(logger.INFO)
    
    # 初始化 Agent
    agent = GUIAgent()

    try:
        # 跑 Agent 的流式输出
        for _ in agent.run_stream(goal):
            pass
    except Exception as e:
        logger.exception("Agent 运行崩溃")
    finally:
        logger.info("Agent 运行结束")

if __name__ == "__main__":
    app()