import os
from workflows.Orchestrator import Orchestrator


def test_orchestrator_runs_through():
    os.environ["GROQ_API_KEY"] = "test-key"
    orchestrator = Orchestrator()
    task = "Audit the latest vendor contract for procurement risk and summarize required review steps."
    state = orchestrator.run(task)

    assert "final_result" in state
    assert state["report_path"] == "final_report.txt"
    assert state["validation_status"] in {"PASS", "FAIL"}
