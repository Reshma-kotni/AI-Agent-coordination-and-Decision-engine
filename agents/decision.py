"""
decision.py
───────────
DecisionAgent — recommends the next audit action using the full analysis,
vendor history from long-term memory, matched risk patterns, and tool errors.

Sprint 3: Decision prompt now includes vendor_history and known_risk_patterns
so the LLM can escalate recommendations for repeat offenders.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import DECISION_PROMPT
from agents.memory_manager import MemoryManagerAgent

load_dotenv()


class DecisionAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)
        self.memory = MemoryManagerAgent()

    def decide(
        self,
        analysis: str,
        vendor_history: str = "",
        known_risk_patterns: str = "",
        tool_errors: list[str] | None = None,
    ) -> str:
        errors_str = (
            "\n".join(f"- {e}" for e in tool_errors) if tool_errors else "None"
        )
        prompt = DECISION_PROMPT.format(
            analysis_text=analysis or "No analysis available.",
            vendor_history=vendor_history or "No vendor history available.",
            known_risk_patterns=known_risk_patterns or "No known risk patterns.",
            tool_errors=errors_str,
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a decision agent for procurement auditing.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Decision failed: {exc}"

    def run(self, state: dict) -> dict:
        analysis = state.get("analysis", "")
        vendor_history = state.get("vendor_history", "")
        known_risk_patterns = state.get("known_risk_patterns_context", "")
        tool_errors = state.get("tool_errors", [])

        decision = self.decide(analysis, vendor_history, known_risk_patterns, tool_errors)
        state["decision"] = decision

        # Log decision to short-term memory
        state = self.memory.add_to_short_term(
            state,
            role="decision_agent",
            content=f"Decision: {decision[:200]}",
            node="decision",
        )

        state["decision_metadata"] = {
            "node": "decision",
            "prompt": "audit_action_recommendation",
            "tool": None,
            "tool_errors_present": bool(tool_errors),
            "used_vendor_history": bool(vendor_history),
        }
        return state
