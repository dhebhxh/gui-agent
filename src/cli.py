# cli.py

import typer
import ctypes
import sys
from agent import GUIAgent

app = typer.Typer()

# 定义 Windows API 常量
SW_HIDE = 0       # 隐藏窗口
SW_RESTORE = 9    # 恢复窗口
SW_SHOWMINIMIZED = 2  # 最小化 (备用)

def get_console_hwnd():
    """获取当前控制台窗口的句柄"""
    try:
        kernel32 = ctypes.windll.kernel32
        return kernel32.GetConsoleWindow()
    except Exception:
        return None

def hide_console():
    """彻底隐藏控制台窗口 (不占任务栏，无白条)"""
    if sys.platform != "win32":
        return
    hwnd = get_console_hwnd()
    if hwnd:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, SW_HIDE)

def restore_console():
    """恢复控制台窗口"""
    if sys.platform != "win32":
        return
    hwnd = get_console_hwnd()
    if hwnd:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, SW_RESTORE)

@app.command()
def run(goal: str):

    hide_console() 
    print("=" * 80)
    print(f"initialize gui agent with goal")
    print("=" * 80)
    
    # 初始化 Agent（如果这里很慢，可以让用户看到进度）
    agent = GUIAgent()

    print("=" * 80)
    print(f"start running agent")
    print("=" * 80)

    try:
        for _ in agent.run_stream(goal):
            pass
    finally:
        # 程序跑完（无论成功还是报错），恢复窗口，方便查看最终结果
        restore_console()
        print("\n" + "=" * 80)
        print("Agent 运行结束，窗口已恢复。")
        print("=" * 80)

if __name__ == "__main__":
    app()