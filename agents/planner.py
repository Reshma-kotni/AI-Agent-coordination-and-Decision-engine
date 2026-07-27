import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import PLANNER_PROMPT

load_dotenv()

class PlannerAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)

    def plan(self, task: str):
        prompt = PLANNER_PROMPT.format(task=task)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a planner agent for contract audit workflows."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Planner failed: {exc}"

    def run(self, state):
        task = state.get("task", "")
        state["plan"] = self.plan(task)
        state["plan_metadata"] = {
            "node": "planner",
            "prompt": "contract_audit_plan",
            "tool": None,
        }
        return state
