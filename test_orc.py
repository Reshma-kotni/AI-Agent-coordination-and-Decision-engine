from workflows.Orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator()
    task = input("Enter your task: ")
    final_result = orchestrator.run(task)
    print("\nFinal Result:", final_result)
