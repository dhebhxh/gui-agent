# cli.py

import typer
from agent import GUIAgent

app = typer.Typer()

@app.command()
def run(goal: str):
    print("=" * 80)
    print(f"Initialize GUI Agent with goal: {goal}")
    print("=" * 80)
    
    # 初始化 Agent
    agent = GUIAgent()

    print("=" * 80)
    print(f"Start running agent")
    print("=" * 80)

    try:
        # 跑 Agent 的流式输出
        for _ in agent.run_stream(goal):
            pass
    except Exception as e:
        print(f"\n[Error] Agent 运行崩溃: {e}")
    finally:
        print("\n" + "=" * 80)
        print("Agent 运行结束。")
        print("=" * 80)

if __name__ == "__main__":
    app()