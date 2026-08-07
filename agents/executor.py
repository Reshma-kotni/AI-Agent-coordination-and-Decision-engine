"""
executor.py
───────────
ExecutionAgent — compiles all agent outputs, tool results, evaluation
scores, and pipeline metrics into the final audit report.

Sprint 4: Report now includes audit quality score, score breakdown,
re-planning flag, and pipeline timing metrics.
"""


class ExecutionAgent:
    def __init__(self):
        pass

    def execute(self, state: dict) -> str:
        try:
            with open("final_report.txt", "w", encoding="utf-8") as f:
                f.write("=== Contract & Procurement Audit Report ===\n\n")

                # ── Core agent outputs ─────────────────────────────────────
                f.write("Plan:\n")
                f.write(state.get("plan", "No plan generated.") + "\n\n")

                f.write("Research Brief:\n")
                queries = state.get("research_queries", [])
                if queries:
                    f.write(f"  Queries executed: {', '.join(queries)}\n")
                f.write(state.get("retrieval", "No retrieval available.") + "\n\n")

                f.write("Analysis:\n")
                f.write(state.get("analysis", "No analysis available.") + "\n\n")

                f.write("Review Notes:\n")
                f.write(state.get("review_notes", "No review notes.") + "\n\n")

                f.write("Decision Output:\n")
                f.write(state.get("decision", "No decision available.") + "\n\n")

                # ── Tool Outputs ───────────────────────────────────────────
                if state.get("pdf_tool_result"):
                    f.write("PDF Contract Parser Result:\n")
                    f.write(state["pdf_tool_result"] + "\n\n")

                if state.get("pdf_contract_text"):
                    preview = state["pdf_contract_text"][:1000]
                    f.write("PDF Contract Text Preview (first 1000 chars):\n")
                    f.write(preview + "\n\n")

                if state.get("vendor_risk_report"):
                    f.write("Vendor Risk API Report:\n")
                    f.write(state["vendor_risk_report"] + "\n\n")

                if state.get("contract_dataframe_summary"):
                    f.write("Contract CSV DataFrame Summary:\n")
                    f.write(state["contract_dataframe_summary"] + "\n\n")

                if state.get("contract_risk_clause_detection"):
                    f.write("CSV Risk Clause Detection:\n")
                    f.write(state["contract_risk_clause_detection"] + "\n\n")

                # ── Sprint 4: Audit Quality Score ──────────────────────────
                score = state.get("audit_score")
                band = state.get("audit_quality_band")
                if score is not None:
                    f.write(f"Audit Quality Score: {score}/100 ({band})\n")
                    breakdown = state.get("score_breakdown", {})
                    for dim, data in breakdown.items():
                        f.write(f"  {dim.replace('_', ' ').title()}: "
                                f"{data['score']}/{data['max']} — "
                                f"{'; '.join(data['notes'])}\n")
                    f.write("\n")

                if state.get("re_plan_triggered"):
                    f.write("Note: Re-planning was triggered during this audit run "
                            "(initial analysis was insufficient).\n\n")

                # ── Error Traceability ─────────────────────────────────────
                tool_errors = state.get("tool_errors", [])
                if tool_errors:
                    f.write("Tool Errors Encountered:\n")
                    for err in tool_errors:
                        f.write(f"  - {err}\n")
                    f.write("\n")

                # ── Pipeline Metadata ──────────────────────────────────────
                metrics = state.get("pipeline_metrics", {})
                f.write("Pipeline Metadata:\n")
                f.write(f"  Node History      : {state.get('node_history', [])}\n")
                f.write(f"  Conditional Path  : {state.get('conditional_path', 'N/A')}\n")
                f.write(f"  Validation Status : {state.get('validation_status', 'N/A')}\n")
                f.write(f"  Total Duration    : {metrics.get('total_duration_s', 'N/A')}s\n")
                f.write(f"  Milestone         : {state.get('metadata', {}).get('milestone', 'N/A')}\n")
                f.write("\n")

                f.write("Report generated successfully by Execution Agent.\n")

            return "Report saved as final_report.txt"
        except Exception as e:
            return f"Execution failed: {e}"

    def run(self, state: dict) -> dict:
        result = self.execute(state)
        state["final_result"] = result
        state["report_path"] = "final_report.txt"
        state["executor_metadata"] = {
            "node": "executor",
            "tool": "file_writer",
        }
        return state
