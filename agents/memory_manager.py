"""
memory_manager.py
─────────────────
MemoryManagerAgent — manages both short-term conversational memory and
long-term persistent audit knowledge for the multi-agent pipeline.

Short-term Memory
─────────────────
Stored in the shared AuditState under "conversation_history" as a list
of {"role": ..., "content": ..., "node": ...} entries. It acts like a
rolling conversation buffer between agents within a single audit run.
Max window: last SHORT_TERM_WINDOW entries.

Long-term Memory
────────────────
Persisted in `memory/audit_memory.json`. Three sub-stores:
  1. audit_records   — one record per completed audit run (task, summary, risks)
  2. vendor_profiles — accumulated findings about specific vendors across runs
  3. known_risk_patterns — pre-seeded and expanding library of clause patterns

Sprint 3: Milestone 3 — Agent Coordination & Memory Systems
"""

from __future__ import annotations

import json
import os
import datetime
from pathlib import Path
from typing import Any

# ── Configuration ──────────────────────────────────────────────────────────────
MEMORY_FILE = Path(__file__).parent.parent / "memory" / "audit_memory.json"
SHORT_TERM_WINDOW = 10   # max entries kept in conversational buffer per run


# ── Persistence helpers ────────────────────────────────────────────────────────

def _load_memory() -> dict:
    """Load the long-term memory JSON file. Returns empty structure on error."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"audit_records": [], "vendor_profiles": {}, "known_risk_patterns": []}


def _save_memory(data: dict) -> None:
    """Persist the long-term memory back to disk."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── MemoryManagerAgent ─────────────────────────────────────────────────────────

class MemoryManagerAgent:
    """
    Manages short-term and long-term memory for the audit pipeline.

    Node responsibilities:
      pre_audit  — load relevant long-term context into state before audit begins
      post_audit — save audit results and update vendor profiles after completion
    """

    name: str = "memory_manager"

    # ── Short-term helpers ─────────────────────────────────────────────────────

    @staticmethod
    def add_to_short_term(state: dict, role: str, content: str, node: str = "") -> dict:
        """
        Append a message to the in-state conversation buffer.
        Trims to SHORT_TERM_WINDOW most recent entries.
        """
        history: list = state.get("conversation_history", [])
        history.append({
            "role": role,
            "content": content,
            "node": node,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        state["conversation_history"] = history[-SHORT_TERM_WINDOW:]
        return state

    @staticmethod
    def get_short_term_summary(state: dict) -> str:
        """Return a formatted string of the short-term conversation buffer."""
        history = state.get("conversation_history", [])
        if not history:
            return "No conversation history yet."
        lines = [
            f"[{h['node'].upper() or h['role']}]: {h['content'][:300]}"
            for h in history
        ]
        return "\n".join(lines)

    # ── Long-term helpers ──────────────────────────────────────────────────────

    @staticmethod
    def get_vendor_history(vendor_name: str) -> str:
        """
        Retrieve past audit findings for a specific vendor from long-term memory.
        Returns a formatted string or 'No history found.'
        """
        if not vendor_name:
            return "No vendor name provided."
        memory = _load_memory()
        profiles = memory.get("vendor_profiles", {})
        key = vendor_name.strip().lower()
        profile = profiles.get(key)

        if not profile:
            return f"No previous audit history found for vendor '{vendor_name}'."

        audits = profile.get("past_audits", [])
        lines = [f"Vendor: {vendor_name} — {len(audits)} previous audit(s) on record."]
        for a in audits[-3:]:   # show last 3 audits
            lines.append(
                f"  [{a.get('date', 'N/A')}] Risk Level: {a.get('risk_level', 'Unknown')} | "
                f"Summary: {a.get('summary', '')[:200]}"
            )
        return "\n".join(lines)

    @staticmethod
    def get_relevant_risk_patterns(analysis_text: str) -> str:
        """
        Match the current analysis against the pre-seeded known_risk_patterns
        library and return matching patterns with mitigations.
        """
        memory = _load_memory()
        patterns = memory.get("known_risk_patterns", [])
        text_lower = analysis_text.lower()
        matches = []

        for p in patterns:
            if any(kw in text_lower for kw in p.get("keywords", [])):
                matches.append(
                    f"⚠ [{p['severity']}] {p['pattern']}: {p['mitigation']}"
                )

        if not matches:
            return "No known risk patterns matched the current analysis."
        return "Matched risk patterns from knowledge base:\n" + "\n".join(matches)

    @staticmethod
    def _determine_risk_level(state: dict) -> str:
        """Infer overall risk level from review / analysis outputs."""
        path = state.get("conditional_path", "")
        if path == "high_risk_review":
            return "HIGH"
        analysis = state.get("analysis", "").lower()
        if any(w in analysis for w in ["critical", "breach", "non-compliance", "litigation"]):
            return "HIGH"
        if any(w in analysis for w in ["risk", "issue", "liability"]):
            return "MEDIUM"
        return "LOW"

    # ── Node: pre_audit ────────────────────────────────────────────────────────

    def run_pre_audit(self, state: dict) -> dict:
        """
        Called at the START of an audit run.
        Loads relevant long-term context into state so all downstream agents
        can use it in their prompts and logic.
        """
        vendor_name = state.get("vendor_name", "")
        analysis = state.get("analysis", "")

        # Load vendor history
        vendor_history = self.get_vendor_history(vendor_name)
        state["vendor_history"] = vendor_history

        # Load matching risk patterns from knowledge base
        risk_patterns = self.get_relevant_risk_patterns(analysis or state.get("task", ""))
        state["known_risk_patterns_context"] = risk_patterns

        # Initialise short-term memory
        state = self.add_to_short_term(
            state,
            role="system",
            content=f"Audit started. Task: {state.get('task', '')}",
            node="memory_manager_pre",
        )

        state.setdefault("node_history", []).append("memory_manager_pre")
        return state

    # ── Node: post_audit ───────────────────────────────────────────────────────

    def run_post_audit(self, state: dict) -> dict:
        """
        Called at the END of an audit run.
        Saves audit results to long-term memory and updates vendor profile.
        """
        memory = _load_memory()
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        risk_level = self._determine_risk_level(state)

        # ── 1. Append audit record ─────────────────────────────────────────────
        audit_record = {
            "date": now,
            "task": state.get("task", ""),
            "vendor_name": state.get("vendor_name", ""),
            "risk_level": risk_level,
            "validation_status": state.get("validation_status", "UNKNOWN"),
            "summary": (state.get("analysis", "")[:500]
                        or state.get("decision", "")[:500]
                        or "No summary available."),
            "tool_errors": state.get("tool_errors", []),
            "node_history": state.get("node_history", []),
        }
        memory.setdefault("audit_records", []).append(audit_record)

        # ── 2. Update vendor profile ───────────────────────────────────────────
        vendor_name = state.get("vendor_name", "").strip()
        if vendor_name:
            key = vendor_name.lower()
            profile = memory.setdefault("vendor_profiles", {}).setdefault(key, {
                "vendor_name": vendor_name,
                "past_audits": [],
                "overall_risk": "UNKNOWN",
            })
            profile["past_audits"].append({
                "date": now,
                "risk_level": risk_level,
                "summary": audit_record["summary"][:300],
                "tool_errors": state.get("tool_errors", []),
            })
            # Escalate overall risk if this audit is higher
            risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "UNKNOWN": -1}
            current = profile.get("overall_risk", "UNKNOWN")
            if risk_order.get(risk_level, -1) > risk_order.get(current, -1):
                profile["overall_risk"] = risk_level
            profile["last_audited"] = now

        # ── 3. Persist ─────────────────────────────────────────────────────────
        try:
            _save_memory(memory)
            state["memory_save_status"] = "Long-term memory updated successfully."
        except Exception as exc:
            state["memory_save_status"] = f"Memory save failed: {exc}"
            state.setdefault("tool_errors", []).append(state["memory_save_status"])

        # ── 4. Final short-term entry ──────────────────────────────────────────
        state = self.add_to_short_term(
            state,
            role="system",
            content=f"Audit completed. Risk: {risk_level}. {state['memory_save_status']}",
            node="memory_manager_post",
        )

        state.setdefault("node_history", []).append("memory_manager_post")
        return state
