"""
planner.py
──────────
PlannerAgent — breaks incoming tasks into concrete audit steps and identifies
which enterprise tools will likely be needed.

Sprint 3: Planner now receives vendor_history from long-term memory so it can
tailor the audit plan based on past findings for the same vendor.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import PLANNER_PROMPT
from agents.memory_manager import MemoryManagerAgent

load_dotenv()


class PlannerAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)
        self.memory = MemoryManagerAgent()

    def plan(self, task: str, tools_summary: str = "", vendor_history: str = "") -> str:
        prompt = PLANNER_PROMPT.format(
            task=task,
            tools_summary=tools_summary or "No tools registered.",
            vendor_history=vendor_history or "No vendor history available.",
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a planner agent for contract audit workflows.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Planner failed: {exc}"

    def run(self, state: dict) -> dict:
        task = state.get("task", "")
        tools_summary = state.get("tools_summary", "")
        vendor_history = state.get("vendor_history", "")

        plan = self.plan(task, tools_summary, vendor_history)
        state["plan"] = plan

        # Log plan to short-term memory
        state = self.memory.add_to_short_term(
            state,
            role="planner",
            content=f"Plan generated: {plan[:200]}",
            node="planner",
        )

        state["plan_metadata"] = {
            "node": "planner",
            "prompt": "contract_audit_plan",
            "tool": None,
            "used_vendor_history": bool(vendor_history),
        }
        return state
