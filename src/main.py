from agent import GUIAgent   # replace with your actual module name


def main():
    agent = GUIAgent()
    goal = "Open the browser and search for today's weather"  # put your real task here

    print(f"Starting task: {goal}\n")
    
    final = None
    for state in agent.run_stream(goal):
        final = state

    if final and final.get("finished"):
        print(f"\nDone. Total steps: {final.get('step')}")
        for i, h in enumerate(final.get("history", []), 1):
            print(f"  {i}. {h}")
    else:
        print("\nTask not completed.")


if __name__ == "__main__":
    main()