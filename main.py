from workflows.Orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator()
    task = "Audit the latest vendor contract for procurement risk and summarize required review steps."
    state = orchestrator.run(task)
    print("Final Audit State:", state)
