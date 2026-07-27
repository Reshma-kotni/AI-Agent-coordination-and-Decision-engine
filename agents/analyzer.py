import os
from dotenv import load_dotenv
from groq import Groq
from agents.prompt_templates import ANALYZER_PROMPT

load_dotenv()

class AnalyzerAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)

    def analyze(self, data: str):
        prompt = ANALYZER_PROMPT.format(retrieval_text=data)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an analyzer agent for vendor contracts."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Analyzer failed: {exc}"

    def run(self, state):
        retrieval = state.get("retrieval", "")
        state["analysis"] = self.analyze(retrieval)
        state["analysis_metadata"] = {
            "node": "analyzer",
            "prompt": "risk_and_compliance_analysis",
            "tool": None,
        }
        return state
