"""
analyzer.py
───────────
AnalyzerAgent — extracts risk signals, compliance issues, and contract summary
details using retrieved text, vendor risk reports, and long-term memory context.

Sprint 3: Analyzer now receives vendor_history, known_risk_patterns, and
conversation_history from the shared state for context-aware analysis.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import ANALYZER_PROMPT
from agents.memory_manager import MemoryManagerAgent

load_dotenv()


class AnalyzerAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)
        self.memory = MemoryManagerAgent()

    def analyze(
        self,
        retrieval_text: str,
        vendor_risk_report: str = "",
        vendor_history: str = "",
        known_risk_patterns: str = "",
        conversation_history: str = "",
    ) -> str:
        prompt = ANALYZER_PROMPT.format(
            retrieval_text=retrieval_text or "No retrieval data available.",
            vendor_risk_report=vendor_risk_report or "No vendor risk report available.",
            vendor_history=vendor_history or "No vendor history available.",
            known_risk_patterns=known_risk_patterns or "No known risk patterns available.",
            conversation_history=conversation_history or "No conversation history.",
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an analyzer agent for vendor contracts.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Analyzer failed: {exc}"

    def run(self, state: dict) -> dict:
        retrieval = state.get("retrieval", "")
        vendor_risk_report = state.get("vendor_risk_report", "")
        vendor_history = state.get("vendor_history", "")
        known_risk_patterns = state.get("known_risk_patterns_context", "")
        conversation_history = MemoryManagerAgent.get_short_term_summary(state)

        analysis = self.analyze(
            retrieval,
            vendor_risk_report,
            vendor_history,
            known_risk_patterns,
            conversation_history,
        )
        state["analysis"] = analysis

        # Log analysis to short-term memory
        state = self.memory.add_to_short_term(
            state,
            role="analyzer",
            content=f"Analysis complete: {analysis[:200]}",
            node="analyzer",
        )

        state["analysis_metadata"] = {
            "node": "analyzer",
            "prompt": "risk_and_compliance_analysis",
            "tool": None,
            "used_vendor_risk": bool(vendor_risk_report),
            "used_vendor_history": bool(vendor_history),
            "used_risk_patterns": bool(known_risk_patterns),
        }
        return state
