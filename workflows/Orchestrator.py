from agents.planner import PlannerAgent
from agents.retriever import RetrieverAgent
from agents.analyzer import AnalyzerAgent
from agents.decision import DecisionAgent
from agents.executor import ExecutionAgent
from agents.review import ReviewAgent
from agents.tools import PandasAuditTool
from agents.validator import ValidatorAgent


class AuditState(dict):
    """Shared graph state passed between agent nodes."""
    pass


class Orchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent()
        self.analyzer = AnalyzerAgent()
        self.decision = DecisionAgent()
        self.review = ReviewAgent()
        self.executor = ExecutionAgent()
        self.validator = ValidatorAgent()
        self.tools = {
            "pandas_contract_audit": PandasAuditTool,
        }

    def _build_initial_state(self, task: str) -> AuditState:
        return AuditState(
            task=task,
            graph_name="vendor_contract_audit",
            node_history=[],
            tools=list(self.tools.keys()),
            metadata={"milestone": "1.0", "pipeline": "LangGraph-style audit"},
        )

    def _bind_node(self, state: AuditState, node_name: str) -> AuditState:
        state.setdefault("node_history", []).append(node_name)
        return state

    def _requires_risk_review(self, state: AuditState) -> bool:
        analysis = state.get("analysis", "").lower()
        return any(keyword in analysis for keyword in [
            "risk",
            "issue",
            "non-compliance",
            "liability",
            "breach",
        ])

    def call_tool(self, state: AuditState, tool_name: str) -> AuditState:
        tool_class = self.tools.get(tool_name)
        if not tool_class:
            state["tool_error"] = f"Tool {tool_name} not registered."
            return state
        try:
            return tool_class.run(state)
        except Exception as exc:
            state["tool_error"] = f"{tool_name} invocation failed: {exc}"
            return state

    def select_tool_from_analysis(self, analysis: str):
        if not analysis:
            return None
        if "csv" in analysis.lower() or "spreadsheet" in analysis.lower():
            return "pandas_contract_audit"
        return None

    def run(self, task: str) -> AuditState:
        print("\n--- Orchestration Started ---")
        state = self._build_initial_state(task)

        state = self.planner.run(state)
        print("\n[Planner Output]\n", state.get("plan"))
        state = self._bind_node(state, "planner")

        state = self.retriever.run(state)
        print("\n[Retriever Output]\n", state.get("retrieval"))
        state = self._bind_node(state, "retriever")

        state = self.analyzer.run(state)
        print("\n[Analyzer Output]\n", state.get("analysis"))
        state = self._bind_node(state, "analyzer")

        selected_tool = self.select_tool_from_analysis(state.get("analysis", ""))
        if selected_tool:
            state = self.call_tool(state, selected_tool)
            print("\n[Tool Output]\n", state.get("pandas_tool_result"))
            state = self._bind_node(state, "pandas_tool")

        if self._requires_risk_review(state):
            state = self.review.run(state)
            print("\n[Review Output]\n", state.get("review_notes"))
            state = self._bind_node(state, "review")
            state["conditional_path"] = "high_risk_review"
        else:
            state["conditional_path"] = "standard_audit"

        state = self.decision.run(state)
        print("\n[Decision Output]\n", state.get("decision"))
        state = self._bind_node(state, "decision")

        state = self.executor.run(state)
        print("\n[Executor Output]\n", state.get("final_result"))
        state = self._bind_node(state, "executor")

        state = self.validator.run(state)
        print("\n[Validation Output]\n", state.get("validation_status"), state.get("validation_errors"))
        state = self._bind_node(state, "validator")

        print("\n--- Orchestration Finished ---")
        return state

