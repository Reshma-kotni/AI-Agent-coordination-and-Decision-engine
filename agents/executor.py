class ExecutionAgent:
    def __init__(self):
        pass

    def execute(self, state):
        try:
            with open("final_report.txt", "w", encoding="utf-8") as f:
                f.write("=== Contract & Procurement Audit Report ===\n\n")
                f.write("Plan:\n")
                f.write(state.get("plan", "No plan generated.") + "\n\n")
                f.write("Retrieval:\n")
                f.write(state.get("retrieval", "No retrieval available.") + "\n\n")
                f.write("Analysis:\n")
                f.write(state.get("analysis", "No analysis available.") + "\n\n")
                f.write("Review Notes:\n")
                f.write(state.get("review_notes", "No review notes.") + "\n\n")
                f.write("Decision Output:\n")
                f.write(state.get("decision", "No decision available.") + "\n\n")
                if state.get("contract_dataframe_summary"):
                    f.write("Contract DataFrame Summary:\n")
                    f.write(state["contract_dataframe_summary"] + "\n\n")
                if state.get("contract_risk_clause_detection"):
                    f.write("Risk Clause Detection:\n")
                    f.write(state["contract_risk_clause_detection"] + "\n\n")
                if state.get("tool_error"):
                    f.write("Tool Error:\n")
                    f.write(state["tool_error"] + "\n\n")
                f.write("Report generated successfully by Execution Agent.\n")
            return "Report saved as final_report.txt"
        except Exception as e:
            return f"Execution failed: {e}"

    def run(self, state):
        result = self.execute(state)
        state["final_result"] = result
        state["report_path"] = "final_report.txt"
        state["executor_metadata"] = {
            "node": "executor",
            "tool": "file_writer",
        }
        return state
