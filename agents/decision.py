import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import DECISION_PROMPT

load_dotenv()

class DecisionAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)

    def decide(self, analysis: str):
        prompt = DECISION_PROMPT.format(analysis_text=analysis)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a decision agent for procurement auditing."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Decision failed: {exc}"

    def run(self, state):
        analysis = state.get("analysis", "")
        state["decision"] = self.decide(analysis)
        state["decision_metadata"] = {
            "node": "decision",
            "prompt": "audit_action_recommendation",
            "tool": None,
        }
        return state
