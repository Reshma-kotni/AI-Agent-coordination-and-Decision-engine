class ValidatorAgent:
    def run(self, state):
        errors = []
        if not state.get("plan"):
            errors.append("Missing audit plan.")
        if not state.get("analysis"):
            errors.append("Missing analysis.")
        if not state.get("decision"):
            errors.append("Missing decision output.")
        if not state.get("final_result"):
            errors.append("Execution did not complete.")

        state["validation_errors"] = errors
        state["validation_status"] = "PASS" if not errors else "FAIL"
        return state
