"""
metrics.py
──────────
Pipeline metrics tracker for the audit engine.

Tracks:
  - Per-node execution timing
  - Overall pipeline duration
  - Risk level progression
  - Tool invocation statistics
  - Audit quality scores over time (persisted to metrics_log.json)

Sprint 4: Module 4 — Workflow Automation & Decision Intelligence
"""

from __future__ import annotations

import json
import time
import datetime
from pathlib import Path

METRICS_FILE = Path(__file__).parent.parent / "memory" / "metrics_log.json"


def _load_metrics() -> list:
    try:
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_metrics(records: list) -> None:
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


class PipelineMetrics:
    """
    Lightweight metrics tracker. One instance per audit run.
    Call start_node() / end_node() around each graph node,
    then call finalize() at the end to produce the metrics summary.
    """

    def __init__(self):
        self._run_start = time.perf_counter()
        self._node_timings: dict[str, float] = {}
        self._node_start_times: dict[str, float] = {}

    def start_node(self, node_name: str) -> None:
        self._node_start_times[node_name] = time.perf_counter()

    def end_node(self, node_name: str) -> float:
        start = self._node_start_times.pop(node_name, None)
        if start is None:
            return 0.0
        elapsed = round(time.perf_counter() - start, 4)
        self._node_timings[node_name] = elapsed
        return elapsed

    def finalize(self, state: dict) -> dict:
        total_duration = round(time.perf_counter() - self._run_start, 4)
        tools_invoked = state.get("tools_to_invoke") or []
        tool_errors = state.get("tool_errors") or []

        metrics = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task": state.get("task", "")[:120],
            "vendor_name": state.get("vendor_name", ""),
            "total_duration_s": total_duration,
            "node_timings_s": self._node_timings,
            "nodes_visited": state.get("node_history", []),
            "tools_invoked": [t.get("tool") for t in tools_invoked],
            "tool_error_count": len(tool_errors),
            "validation_status": state.get("validation_status", "UNKNOWN"),
            "audit_score": state.get("audit_score"),
            "audit_quality_band": state.get("audit_quality_band"),
            "risk_level": state.get("vendor_risk_data", {}).get("compliance_status", "Unknown"),
            "conditional_path": state.get("conditional_path", "standard_audit"),
            "re_plan_triggered": state.get("re_plan_triggered", False),
            "research_queries_run": state.get("research_metadata", {}).get("queries_run", 0),
        }

        # Persist to log
        try:
            records = _load_metrics()
            records.append(metrics)
            _save_metrics(records)
            metrics["metrics_saved"] = True
        except Exception as exc:
            metrics["metrics_save_error"] = str(exc)

        return metrics


def load_all_metrics() -> list[dict]:
    """Return all persisted pipeline metrics records."""
    return _load_metrics()


def get_metrics_summary() -> dict:
    """Return aggregate statistics across all audit runs."""
    records = _load_metrics()
    if not records:
        return {"total_runs": 0}

    scores = [r["audit_score"] for r in records if r.get("audit_score") is not None]
    durations = [r["total_duration_s"] for r in records if r.get("total_duration_s")]
    pass_count = sum(1 for r in records if r.get("validation_status") == "PASS")

    return {
        "total_runs": len(records),
        "pass_rate_pct": round(pass_count / len(records) * 100, 1),
        "avg_audit_score": round(sum(scores) / len(scores), 1) if scores else None,
        "avg_duration_s": round(sum(durations) / len(durations), 2) if durations else None,
        "fastest_run_s": min(durations) if durations else None,
        "slowest_run_s": max(durations) if durations else None,
        "quality_distribution": {
            band: sum(1 for r in records if r.get("audit_quality_band") == band)
            for band in ["EXCELLENT", "GOOD", "ADEQUATE", "POOR"]
        },
    }
