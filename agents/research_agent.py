"""
research_agent.py
─────────────────
ResearchAgent — a specialized agent that performs deep, multi-angle retrieval
to support the Analyzer with richer context than a single DuckDuckGo search.

How it works:
  1. Uses the LLM (Planner output + task) to generate 2–3 targeted search queries
     covering different angles: compliance, vendor background, industry benchmarks.
  2. Runs each query through DuckDuckGo and collects the top snippets.
  3. Deduplicates and merges results into a structured research brief.
  4. Adds each query + finding to the short-term conversation memory.

Sprint 3: Milestone 3 — Agent Coordination & Memory Systems
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS
from agents.memory_manager import MemoryManagerAgent

load_dotenv()

# ── Prompt used to generate focused search queries ─────────────────────────────
RESEARCH_QUERY_GEN_PROMPT = """You are a research strategist for a contract audit team.
Given the task and audit plan, generate {n} short, targeted web search queries
that would help an auditor understand:
  1. Regulatory/compliance context relevant to this vendor and contract type.
  2. Background information about the vendor (news, reputation, risk incidents).
  3. Industry benchmarks or standards for this type of procurement.

Task: {task}

Audit Plan (excerpt):
{plan_excerpt}

Known Vendor History:
{vendor_history}

Output ONLY a numbered list of search queries, one per line. No explanations."""


class ResearchAgent:
    """
    Specialized research agent that replaces the basic RetrieverAgent.
    Performs multi-query deep retrieval with memory integration.
    """

    name: str = "research_agent"
    description: str = (
        "Deep research agent: generates multiple targeted search queries, "
        "retrieves web results from each, and compiles a structured research brief."
    )

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)
        self.ddgs = DDGS()
        self.memory = MemoryManagerAgent()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _generate_queries(
        self,
        task: str,
        plan: str,
        vendor_history: str,
        n: int = 3,
    ) -> list[str]:
        """Ask the LLM to generate n targeted search queries."""
        prompt = RESEARCH_QUERY_GEN_PROMPT.format(
            n=n,
            task=task,
            plan_excerpt=plan[:500] if plan else "No plan available.",
            vendor_history=vendor_history[:300] if vendor_history else "None.",
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a research strategist. Output only the list."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()
            # Parse numbered list: "1. query", "2. query" → ["query", ...]
            queries = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Strip leading "1." / "1)" / "-" / "*"
                for prefix in ["1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)", "-", "*"]:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                        break
                if line:
                    queries.append(line)
            return queries[:n]
        except Exception as exc:
            # Fallback: single query from task
            return [task[:120]]

    def _search(self, query: str, max_results: int = 3) -> list[str]:
        """Run a DuckDuckGo search and return a list of result snippets."""
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            return [r.get("body", "") for r in results if r.get("body")]
        except Exception:
            return [f"Search failed for query: '{query}'"]

    def _compile_research_brief(
        self,
        queries: list[str],
        results_map: dict[str, list[str]],
    ) -> str:
        """Merge multi-query results into a structured research brief."""
        sections = ["=== Research Brief ===\n"]
        for i, query in enumerate(queries, start=1):
            snippets = results_map.get(query, [])
            sections.append(f"Query {i}: {query}")
            if snippets:
                for j, snippet in enumerate(snippets, start=1):
                    sections.append(f"  [{j}] {snippet[:400]}")
            else:
                sections.append("  No results found.")
            sections.append("")
        return "\n".join(sections)

    # ── Main node ──────────────────────────────────────────────────────────────

    def run(self, state: dict) -> dict:
        """
        Performs deep multi-query research and writes results to state.
        Skips web retrieval if PDF contract text is already available.
        """
        # If PDF was already parsed, skip web retrieval (PDF is the source of truth)
        if state.get("pdf_contract_text"):
            state.setdefault("node_history", []).append("research_agent_skipped")
            state = self.memory.add_to_short_term(
                state,
                role="research_agent",
                content="Skipped web retrieval — PDF contract text is available.",
                node="research_agent",
            )
            return state

        task = state.get("task", "")
        plan = state.get("plan", "")
        vendor_history = state.get("vendor_history", "")

        # 1. Generate targeted queries
        queries = self._generate_queries(task, plan, vendor_history)
        state["research_queries"] = queries

        # 2. Execute each search
        results_map: dict[str, list[str]] = {}
        for query in queries:
            snippets = self._search(query)
            results_map[query] = snippets

            # Log each query to short-term memory
            state = self.memory.add_to_short_term(
                state,
                role="research_agent",
                content=f"Searched: '{query}' → {len(snippets)} result(s) found.",
                node="research_agent",
            )

        # 3. Compile research brief and store in state
        brief = self._compile_research_brief(queries, results_map)
        state["retrieval"] = brief
        state["research_brief"] = brief
        state["research_metadata"] = {
            "node": "research_agent",
            "queries_run": len(queries),
            "queries": queries,
        }

        # 4. Log completion
        state = self.memory.add_to_short_term(
            state,
            role="research_agent",
            content=f"Research complete. {len(queries)} queries executed.",
            node="research_agent",
        )

        state.setdefault("node_history", []).append("research_agent")
        return state
