"""
validator.py
────────────
ValidatorAgent — validates that all pipeline stages completed successfully.

Sprint 3: Also checks that long-term memory was saved and short-term
conversation history was populated.
"""


class ValidatorAgent:
    def run(self, state: dict) -> dict:
        errors = []

        # Core pipeline checks
        if not state.get("plan"):
            errors.append("Missing audit plan.")
        if not state.get("analysis"):
            errors.append("Missing analysis.")
        if not state.get("decision"):
            errors.append("Missing decision output.")
        if not state.get("final_result"):
            errors.append("Execution did not complete.")

        # Sprint 3: Memory checks
        if not state.get("conversation_history"):
            errors.append("Short-term memory not populated.")
        if state.get("memory_save_status", "").startswith("Memory save failed"):
            errors.append(f"Long-term memory error: {state['memory_save_status']}")

        # Tool error flag (non-blocking — just reported)
        tool_errors = state.get("tool_errors", [])
        if tool_errors:
            errors.append(f"{len(tool_errors)} tool error(s) occurred — see report for details.")

        state["validation_errors"] = errors
        state["validation_status"] = "PASS" if not errors else "FAIL"
        return state
