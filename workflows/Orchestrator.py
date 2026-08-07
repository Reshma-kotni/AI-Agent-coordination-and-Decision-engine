"""
Orchestrator.py
───────────────
Sprint 4: LangGraph StateGraph v4.0 — Workflow Automation & Decision Intelligence.

New additions vs v3.0:
  - EvaluatorAgent node (scores audit quality 0-100)
  - PipelineMetrics (per-node timing + persistent metrics log)
  - Conditional re-planning loop: if analysis is too thin (<300 chars),
    the graph loops back to research_agent (max 1 re-plan to avoid infinite loops)
  - Re-plan flag written to state for metrics tracking

Graph topology:
  memory_pre ──► planner ──► tool_router ──► [run_tools?] ──►
  research_agent ──► analyzer ──► [re_plan?] ──► review ──►
  [error_recovery?] ──► decision ──► executor ──► evaluator ──►
  memory_post ──► validator
"""

from __future__ import annotations

import json
import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import END, StateGraph

from agents.analyzer import AnalyzerAgent
from agents.decision import DecisionAgent
from agents.doc_parser import PDFContractParserTool
from agents.evaluator import EvaluatorAgent
from agents.executor import ExecutionAgent
from agents.memory_manager import MemoryManagerAgent
from agents.planner import PlannerAgent
from agents.prompt_templates import ERROR_RECOVERY_PROMPT, TOOL_ROUTER_PROMPT
from agents.research_agent import ResearchAgent
from agents.review import ReviewAgent
from agents.tools import PandasAuditTool
from agents.validator import ValidatorAgent
from agents.vendor_api import VendorRiskApiTool
from workflows.metrics import PipelineMetrics

load_dotenv()

# ── Shared State Schema ────────────────────────────────────────────────────────
class AuditState(TypedDict, total=False):
    task: str
    graph_name: str
    metadata: dict
    tools_summary: str
    contract_pdf_path: str
    contract_csv_path: str
    vendor_name: str
    conversation_history: list
    vendor_history: str
    known_risk_patterns_context: str
    memory_save_status: str
    plan: str
    plan_metadata: dict
    research_queries: list
    research_brief: str
    research_metadata: dict
    retrieval: str
    analysis: str
    analysis_metadata: dict
    review_notes: str
    review_metadata: dict
    decision: str
    decision_metadata: dict
    error_recovery_notes: str
    final_result: str
    report_path: str
    executor_metadata: dict
    pdf_tool_result: str
    pdf_contract_text: str
    pdf_contract_chunks: list
    pandas_tool_result: str
    contract_dataframe_summary: str
    contract_risk_clause_detection: str
    vendor_risk_report: str
    vendor_risk_data: dict
    vendor_risk_tool_result: str
    tools_to_invoke: list
    node_history: list
    conditional_path: str
    tool_errors: list
    validation_status: str
    validation_errors: list
    # Sprint 4 additions
    re_plan_triggered: bool
    audit_score: int
    audit_quality_band: str
    score_breakdown: dict
    pipeline_metrics: dict

# ── Tool Registry ──────────────────────────────────────────────────────────────
TOOL_REGISTRY = {
    PDFContractParserTool.name: PDFContractParserTool,
    PandasAuditTool.name: PandasAuditTool,
    VendorRiskApiTool.name: VendorRiskApiTool,
}

TOOLS_SUMMARY = "\n".join(
    f"- {cls.name}: {cls.description}"
    for cls in TOOL_REGISTRY.values()
)

# ── Orchestrator ───────────────────────────────────────────────────────────────
class Orchestrator:
    def __init__(self):
        self.memory_manager = MemoryManagerAgent()
        self.planner = PlannerAgent()
        self.research = ResearchAgent()
        self.analyzer = AnalyzerAgent()
        self.decision = DecisionAgent()
        self.review = ReviewAgent()
        self.executor = ExecutionAgent()
        self.evaluator = EvaluatorAgent()
        self.validator = ValidatorAgent()

        api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=api_key) if api_key else None
        self.graph = self._build_graph()

    # ── Graph Construction ─────────────────────────────────────────────────────
    def _build_graph(self) -> StateGraph:
        g = StateGraph(AuditState)

        g.add_node("memory_pre",      self._node_memory_pre)
        g.add_node("planner",         self._node_planner)
        g.add_node("tool_router",     self._node_tool_router)
        g.add_node("run_tools",       self._node_run_tools)
        g.add_node("research_agent",  self._node_research_agent)
        g.add_node("analyzer",        self._node_analyzer)
        g.add_node("re_planner",      self._node_re_planner)
        g.add_node("review",          self._node_review)
        g.add_node("error_recovery",  self._node_error_recovery)
        g.add_node("decision",        self._node_decision)
        g.add_node("executor",        self._node_executor)
        g.add_node("evaluator",       self._node_evaluator)
        g.add_node("memory_post",     self._node_memory_post)
        g.add_node("validator",       self._node_validator)

        g.set_entry_point("memory_pre")

        g.add_edge("memory_pre", "planner")
        g.add_edge("planner", "tool_router")

        g.add_conditional_edges(
            "tool_router",
            self._route_after_tool_router,
            {"run_tools": "run_tools", "research_agent": "research_agent"},
        )
        g.add_edge("run_tools", "research_agent")
        g.add_edge("research_agent", "analyzer")

        # ── Re-planning conditional edge ───────────────────────────────────────
        g.add_conditional_edges(
            "analyzer",
            self._route_after_analyzer,
            {"re_planner": "re_planner", "review": "review"},
        )
        g.add_edge("re_planner", "research_agent")   # loop back for deeper research

        g.add_conditional_edges(
            "review",
            self._route_after_review,
            {"error_recovery": "error_recovery", "decision": "decision"},
        )
        g.add_edge("error_recovery", "decision")
        g.add_edge("decision", "executor")
        g.add_edge("executor", "evaluator")
        g.add_edge("evaluator", "memory_post")
        g.add_edge("memory_post", "validator")
        g.add_edge("validator", END)

        return g.compile()

    # ── Node Implementations ───────────────────────────────────────────────────

    def _node_memory_pre(self, state: AuditState) -> AuditState:
        state["tools_summary"] = TOOLS_SUMMARY
        state["re_plan_triggered"] = False
        state = self.memory_manager.run_pre_audit(dict(state))
        self._metrics.end_node("memory_pre")
        return state

    def _node_planner(self, state: AuditState) -> AuditState:
        self._metrics.start_node("planner")
        state = {**state, **self.planner.run(dict(state))}
        state.setdefault("node_history", []).append("planner")
        self._metrics.end_node("planner")
        return state

    def _node_tool_router(self, state: AuditState) -> AuditState:
        self._metrics.start_node("tool_router")
        task = state.get("task", "")
        plan = state.get("plan", "")

        if not self.groq_client:
            state["tools_to_invoke"] = []
            state.setdefault("node_history", []).append("tool_router")
            self._metrics.end_node("tool_router")
            return state

        prompt = TOOL_ROUTER_PROMPT.format(
            task=task, plan=plan, tools_summary=TOOLS_SUMMARY
        )
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a tool-selection agent. Respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            tools_to_invoke = parsed.get("tools_to_invoke", [])
            for tool_call in tools_to_invoke:
                state.update(tool_call.get("args", {}))
            state["tools_to_invoke"] = tools_to_invoke
        except Exception as exc:
            state["tools_to_invoke"] = self._heuristic_tool_selection(state)
            state.setdefault("tool_errors", []).append(
                f"tool_router: LLM parse failed ({exc}). Used heuristic fallback."
            )

        state.setdefault("node_history", []).append("tool_router")
        self._metrics.end_node("tool_router")
        return state

    def _heuristic_tool_selection(self, state: AuditState) -> list:
        tools = []
        task_lower = state.get("task", "").lower()
        if state.get("contract_pdf_path") or ".pdf" in task_lower:
            tools.append({"tool": "pdf_contract_parser", "args": {}})
        if state.get("contract_csv_path") or any(k in task_lower for k in ["csv", "spreadsheet"]):
            tools.append({"tool": "pandas_contract_audit", "args": {}})
        if state.get("vendor_name") or "vendor" in task_lower:
            tools.append({"tool": "vendor_risk_api", "args": {}})
        return tools

    def _node_run_tools(self, state: AuditState) -> AuditState:
        self._metrics.start_node("run_tools")
        for tool_call in state.get("tools_to_invoke", []):
            tool_name = tool_call.get("tool")
            tool_class = TOOL_REGISTRY.get(tool_name)
            if not tool_class:
                state.setdefault("tool_errors", []).append(
                    f"run_tools: unknown tool '{tool_name}'."
                )
                continue
            print(f"\n  [Tool] Invoking: {tool_name}")
            state = tool_class.run(state)
        state.setdefault("node_history", []).append("run_tools")
        self._metrics.end_node("run_tools")
        return state

    def _node_research_agent(self, state: AuditState) -> AuditState:
        self._metrics.start_node("research_agent")
        state = {**state, **self.research.run(dict(state))}
        self._metrics.end_node("research_agent")
        return state

    def _node_analyzer(self, state: AuditState) -> AuditState:
        self._metrics.start_node("analyzer")
        state = {**state, **self.analyzer.run(dict(state))}
        state.setdefault("node_history", []).append("analyzer")
        self._metrics.end_node("analyzer")
        return state

    def _node_re_planner(self, state: AuditState) -> AuditState:
        """
        Re-planning node: triggered when analysis is too thin.
        Enriches the task description and re-runs research with a broader query.
        """
        self._metrics.start_node("re_planner")
        state["re_plan_triggered"] = True
        original_task = state.get("task", "")
        state["task"] = (
            f"{original_task} "
            "[ENRICHED: Expand research scope. Focus on regulatory compliance, "
            "vendor risk history, and industry benchmarks.]"
        )
        # Clear previous thin retrieval so research_agent runs fresh
        state.pop("retrieval", None)
        state.pop("research_brief", None)
        state.setdefault("node_history", []).append("re_planner")
        self._metrics.end_node("re_planner")
        return state

    def _node_review(self, state: AuditState) -> AuditState:
        self._metrics.start_node("review")
        state = {**state, **self.review.run(dict(state))}
        state.setdefault("node_history", []).append("review")
        self._metrics.end_node("review")
        return state

    def _node_error_recovery(self, state: AuditState) -> AuditState:
        self._metrics.start_node("error_recovery")
        tool_errors = state.get("tool_errors", [])
        if self.groq_client and tool_errors:
            prompt = ERROR_RECOVERY_PROMPT.format(
                tool_errors="\n".join(f"- {e}" for e in tool_errors),
                task=state.get("task", ""),
            )
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are an error recovery agent."},
                        {"role": "user", "content": prompt},
                    ],
                )
                state["error_recovery_notes"] = response.choices[0].message.content
            except Exception as exc:
                state["error_recovery_notes"] = f"Error recovery failed: {exc}"
        state.setdefault("node_history", []).append("error_recovery")
        self._metrics.end_node("error_recovery")
        return state

    def _node_decision(self, state: AuditState) -> AuditState:
        self._metrics.start_node("decision")
        state = {**state, **self.decision.run(dict(state))}
        state.setdefault("node_history", []).append("decision")
        self._metrics.end_node("decision")
        return state

    def _node_executor(self, state: AuditState) -> AuditState:
        self._metrics.start_node("executor")
        state = {**state, **self.executor.run(dict(state))}
        state.setdefault("node_history", []).append("executor")
        self._metrics.end_node("executor")
        return state

    def _node_evaluator(self, state: AuditState) -> AuditState:
        self._metrics.start_node("evaluator")
        state = {**state, **self.evaluator.run(dict(state))}
        state.setdefault("node_history", []).append("evaluator")
        self._metrics.end_node("evaluator")
        return state

    def _node_memory_post(self, state: AuditState) -> AuditState:
        self._metrics.start_node("memory_post")
        state = self.memory_manager.run_post_audit(dict(state))
        # Finalize and store metrics
        state["pipeline_metrics"] = self._metrics.finalize(state)
        self._metrics.end_node("memory_post")
        return state

    def _node_validator(self, state: AuditState) -> AuditState:
        self._metrics.start_node("validator")
        state = {**state, **self.validator.run(dict(state))}
        state.setdefault("node_history", []).append("validator")
        self._metrics.end_node("validator")
        return state

    # ── Conditional Edge Functions ─────────────────────────────────────────────

    def _route_after_tool_router(self, state: AuditState) -> str:
        return "run_tools" if state.get("tools_to_invoke") else "research_agent"

    def _route_after_analyzer(self, state: AuditState) -> str:
        """Re-plan if analysis is too thin AND we haven't re-planned yet."""
        analysis = state.get("analysis", "")
        already_replanned = state.get("re_plan_triggered", False)
        if len(analysis) < 300 and not already_replanned:
            print("\n  [Re-planner] Analysis too thin — triggering re-planning loop.")
            return "re_planner"
        return "review"

    def _route_after_review(self, state: AuditState) -> str:
        return "error_recovery" if state.get("tool_errors") else "decision"

    # ── Public Entry Point ─────────────────────────────────────────────────────

    def run(self, task: str, **kwargs) -> AuditState:
        """
        Execute the full audit pipeline via LangGraph StateGraph v4.0.

        Optional kwargs:
          contract_pdf_path, contract_csv_path, vendor_name
        """
        print("\n━━━ Orchestration Started (LangGraph v4.0 + Metrics) ━━━")

        self._metrics = PipelineMetrics()
        self._metrics.start_node("memory_pre")

        initial_state: AuditState = {
            "task": task,
            "graph_name": "vendor_contract_audit_v4",
            "node_history": [],
            "tool_errors": [],
            "conversation_history": [],
            "re_plan_triggered": False,
            "metadata": {"milestone": "4.0", "pipeline": "LangGraph + Memory + Metrics"},
            **kwargs,
        }

        final_state = self.graph.invoke(initial_state)

        metrics = final_state.get("pipeline_metrics", {})
        print("\n━━━ Orchestration Finished ━━━")
        print(f"  Nodes visited  : {final_state.get('node_history', [])}")
        print(f"  Audit Score    : {final_state.get('audit_score', 'N/A')}/100 ({final_state.get('audit_quality_band', 'N/A')})")
        print(f"  Duration       : {metrics.get('total_duration_s', 'N/A')}s")
        print(f"  Re-plan        : {final_state.get('re_plan_triggered', False)}")
        print(f"  Validation     : {final_state.get('validation_status', 'N/A')}")
        return final_state
