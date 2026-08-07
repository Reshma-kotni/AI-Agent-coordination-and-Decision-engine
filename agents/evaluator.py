"""
evaluator.py
────────────
EvaluatorAgent — scores the quality of a completed audit run across
four dimensions and produces an overall audit confidence score.

Scoring Dimensions (each 0–25 points):
  1. Completeness   — were all required pipeline stages executed?
  2. Risk Coverage  — did the analysis identify specific risk categories?
  3. Tool Coverage  — were appropriate tools invoked without errors?
  4. Decision Quality — does the decision contain actionable next steps?

Total score 0–100. Bands:
  90–100 → EXCELLENT
  70–89  → GOOD
  50–69  → ADEQUATE
  0–49   → POOR

Sprint 4: Module 4 — Workflow Automation & Decision Intelligence
"""

from __future__ import annotations

import re


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _score_completeness(state: dict) -> tuple[int, list[str]]:
    """Check all required pipeline stages produced output."""
    required = {
        "plan": "Audit plan",
        "analysis": "Risk analysis",
        "decision": "Decision recommendation",
        "final_result": "Execution / report",
        "validation_status": "Validation",
    }
    missing = [label for key, label in required.items() if not state.get(key)]
    score = max(0, 25 - len(missing) * 5)
    notes = [f"Missing: {m}" for m in missing] if missing else ["All required stages completed."]
    return score, notes


def _score_risk_coverage(state: dict) -> tuple[int, list[str]]:
    """Check whether the analysis identified multiple risk categories."""
    analysis = (state.get("analysis") or "").lower()
    risk_categories = {
        "compliance": ["compliance", "regulatory", "gdpr", "ccpa"],
        "financial": ["financial", "cost", "payment", "pricing"],
        "operational": ["operational", "delivery", "performance", "sla"],
        "legal": ["legal", "liability", "indemnity", "breach", "termination"],
    }
    found = []
    for category, keywords in risk_categories.items():
        if any(kw in analysis for kw in keywords):
            found.append(category)

    score = min(25, len(found) * 7)
    notes = (
        [f"Risk categories identified: {', '.join(found)}"]
        if found
        else ["No specific risk categories detected in analysis."]
    )
    if len(found) == len(risk_categories):
        notes.append("Full risk coverage achieved.")
    return score, notes


def _score_tool_coverage(state: dict) -> tuple[int, list[str]]:
    """Score based on tools invoked and errors encountered."""
    tools_invoked = state.get("tools_to_invoke") or []
    tool_errors = state.get("tool_errors") or []

    base = min(15, len(tools_invoked) * 5)
    penalty = min(base, len(tool_errors) * 3)
    score = max(0, base - penalty)

    # Bonus for using vendor risk API (important for procurement audit)
    if any(t.get("tool") == "vendor_risk_api" for t in tools_invoked):
        score = min(25, score + 5)

    # If no tools but task was purely text-based, give partial credit
    if not tools_invoked:
        score = 10

    notes = [
        f"Tools invoked: {len(tools_invoked)}",
        f"Tool errors: {len(tool_errors)}",
    ]
    if tool_errors:
        notes.append(f"Errors: {'; '.join(tool_errors[:2])}")
    return score, notes


def _score_decision_quality(state: dict) -> tuple[int, list[str]]:
    """Check whether the decision contains actionable language."""
    decision = (state.get("decision") or "").lower()
    action_signals = [
        "recommend", "escalate", "review", "notify", "request",
        "verify", "update", "contact", "schedule", "conduct",
    ]
    deadline_signals = ["within", "days", "weeks", "immediately", "asap", "by"]
    owner_signals = ["legal", "procurement", "team", "manager", "officer", "cfo", "cto"]

    action_count = sum(1 for s in action_signals if s in decision)
    has_deadline = any(s in decision for s in deadline_signals)
    has_owner = any(s in decision for s in owner_signals)

    score = min(25, action_count * 3 + (5 if has_deadline else 0) + (5 if has_owner else 0))
    notes = [
        f"Action verbs found: {action_count}",
        f"Deadline mentioned: {'Yes' if has_deadline else 'No'}",
        f"Owner/team referenced: {'Yes' if has_owner else 'No'}",
    ]
    return score, notes


# ── EvaluatorAgent ─────────────────────────────────────────────────────────────

class EvaluatorAgent:
    """
    Scores the completed audit pipeline on four dimensions and produces
    an overall audit confidence score and quality band.
    """

    name: str = "evaluator"

    @staticmethod
    def _band(score: int) -> str:
        if score >= 90:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "ADEQUATE"
        return "POOR"

    def evaluate(self, state: dict) -> dict:
        comp_score, comp_notes = _score_completeness(state)
        risk_score, risk_notes = _score_risk_coverage(state)
        tool_score, tool_notes = _score_tool_coverage(state)
        dec_score, dec_notes = _score_decision_quality(state)

        total = comp_score + risk_score + tool_score + dec_score
        band = self._band(total)

        return {
            "audit_score": total,
            "audit_quality_band": band,
            "score_breakdown": {
                "completeness": {"score": comp_score, "max": 25, "notes": comp_notes},
                "risk_coverage": {"score": risk_score, "max": 25, "notes": risk_notes},
                "tool_coverage": {"score": tool_score, "max": 25, "notes": tool_notes},
                "decision_quality": {"score": dec_score, "max": 25, "notes": dec_notes},
            },
        }

    def run(self, state: dict) -> dict:
        evaluation = self.evaluate(state)
        state.update(evaluation)
        state["evaluator_metadata"] = {"node": "evaluator"}
        return state
