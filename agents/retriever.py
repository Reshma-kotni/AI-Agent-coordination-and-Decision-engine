from ddgs import DDGS

class RetrieverAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def retrieve(self, plan: str):
        query = plan.split("\n")[0].strip() if plan else "vendor contract procurement audit"
        results = list(self.ddgs.text(query, max_results=3))
        if results:
            snippets = [r["body"] for r in results]
            return f"Top results for '{query}':\n" + "\n".join(snippets)
        return f"No results found for '{query}'"

    def run(self, state):
        plan = state.get("plan", "")
        state["retrieval"] = self.retrieve(plan)
        state["retrieval_metadata"] = {
            "node": "retriever",
            "prompt": "contract_retrieval_query",
            "tool": "duckduckgo_search",
        }
        return state
