class ReviewAgent:
    def __init__(self):
        pass

    def run(self, state):
        analysis = state.get("analysis", "")
        if not analysis:
            state["review_notes"] = "No analysis available for review."
            return state

        if any(keyword in analysis.lower() for keyword in [
            "risk",
            "non-compliance",
            "breach",
            "penalty",
            "liability",
        ]):
            state["review_notes"] = (
                "High-risk clauses detected. Recommend immediate contract review by legal and procurement teams, "
                "with special focus on termination, indemnity, and scope-of-work alignment."
            )
        else:
            state["review_notes"] = (
                "No high-risk contract language detected in the current analysis summary. "
                "Proceed with standard procurement audit checks and stakeholder signoff."
            )

        state["review_metadata"] = {
            "node": "review",
            "prompt": "risk_review_routing",
            "tool": None,
        }
        return state
