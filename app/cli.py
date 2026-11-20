# cli.py
import logging
import typer
from agent import GUIAgent
from logging_config import setup_logging

app = typer.Typer()

logger = logging.getLogger(__name__)

@app.command()
def run(goal: str):
    # 配置日志
    setup_logging("INFO", "agent_run.log")
    
    # 初始化 Agent
    agent = GUIAgent()
    
        # 跑 Agent 的流式输出
    for _ in agent.run_stream(goal):
        pass

if __name__ == "__main__":
    app()