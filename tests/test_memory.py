"""
tests/test_memory.py
────────────────────
Unit tests for Sprint 3 memory system:
  - MemoryManagerAgent (short-term + long-term)
  - Knowledge base risk pattern matching
  - Vendor history read/write
  - ResearchAgent query generation (offline / mocked)
"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from agents.memory_manager import MemoryManagerAgent, _load_memory, _save_memory


# ── Fixture: isolated temp memory file ────────────────────────────────────────

@pytest.fixture
def temp_memory_file(tmp_path, monkeypatch):
    """Redirect MEMORY_FILE to a temp path for each test."""
    mem_file = tmp_path / "audit_memory.json"
    initial = {
        "audit_records": [],
        "vendor_profiles": {},
        "known_risk_patterns": [
            {
                "pattern": "GDPR non-compliance",
                "keywords": ["gdpr", "data protection"],
                "severity": "HIGH",
                "mitigation": "Request DPA from vendor.",
            },
            {
                "pattern": "SLA penalty",
                "keywords": ["sla", "penalty"],
                "severity": "MEDIUM",
                "mitigation": "Cap penalty at 10% of contract value.",
            },
        ],
    }
    mem_file.write_text(json.dumps(initial), encoding="utf-8")

    import agents.memory_manager as mm
    monkeypatch.setattr(mm, "MEMORY_FILE", mem_file)
    return mem_file


# ── Short-term Memory ──────────────────────────────────────────────────────────

class TestShortTermMemory:

    def test_add_to_short_term_appends_entry(self):
        state = {}
        state = MemoryManagerAgent.add_to_short_term(
            state, role="planner", content="Plan generated.", node="planner"
        )
        assert len(state["conversation_history"]) == 1
        assert state["conversation_history"][0]["role"] == "planner"
        assert state["conversation_history"][0]["node"] == "planner"

    def test_short_term_window_trims_to_max(self):
        state = {}
        from agents.memory_manager import SHORT_TERM_WINDOW
        for i in range(SHORT_TERM_WINDOW + 5):
            state = MemoryManagerAgent.add_to_short_term(
                state, role="agent", content=f"Message {i}", node="test"
            )
        assert len(state["conversation_history"]) == SHORT_TERM_WINDOW

    def test_get_short_term_summary_empty(self):
        summary = MemoryManagerAgent.get_short_term_summary({})
        assert "No conversation history" in summary

    def test_get_short_term_summary_with_entries(self):
        state = {}
        state = MemoryManagerAgent.add_to_short_term(
            state, role="analyzer", content="Risk found in clause 4.", node="analyzer"
        )
        summary = MemoryManagerAgent.get_short_term_summary(state)
        assert "ANALYZER" in summary
        assert "Risk found" in summary


# ── Long-term Memory ───────────────────────────────────────────────────────────

class TestLongTermMemory:

    def test_pre_audit_loads_vendor_history_unknown(self, temp_memory_file):
        manager = MemoryManagerAgent()
        state = {"task": "Audit test vendor", "vendor_name": "Unknown Co"}
        result = manager.run_pre_audit(state)
        assert "No previous audit history" in result.get("vendor_history", "")

    def test_pre_audit_loads_known_risk_patterns(self, temp_memory_file):
        manager = MemoryManagerAgent()
        state = {"task": "Review GDPR compliance in vendor contract", "vendor_name": ""}
        result = manager.run_pre_audit(state)
        assert "GDPR" in result.get("known_risk_patterns_context", "")

    def test_pre_audit_initialises_short_term_memory(self, temp_memory_file):
        manager = MemoryManagerAgent()
        state = {"task": "Audit vendor", "vendor_name": ""}
        result = manager.run_pre_audit(state)
        assert "conversation_history" in result
        assert len(result["conversation_history"]) >= 1

    def test_post_audit_saves_audit_record(self, temp_memory_file):
        manager = MemoryManagerAgent()
        state = {
            "task": "Audit Acme Corp contract",
            "vendor_name": "Acme Corp",
            "analysis": "High risk of indemnity overreach detected.",
            "decision": "Escalate to legal.",
            "validation_status": "PASS",
            "tool_errors": [],
            "node_history": ["memory_pre", "planner", "analyzer"],
            "conversation_history": [],
            "conditional_path": "high_risk_review",
        }
        result = manager.run_post_audit(state)
        assert "successfully" in result.get("memory_save_status", "")

        # Verify file was written
        memory = json.loads(temp_memory_file.read_text())
        assert len(memory["audit_records"]) == 1
        assert memory["audit_records"][0]["vendor_name"] == "Acme Corp"
        assert memory["audit_records"][0]["risk_level"] == "HIGH"

    def test_post_audit_updates_vendor_profile(self, temp_memory_file):
        manager = MemoryManagerAgent()
        state = {
            "task": "Audit Globex Ltd",
            "vendor_name": "Globex Ltd",
            "analysis": "SLA penalty clause is ambiguous.",
            "decision": "Negotiate penalty cap.",
            "validation_status": "PASS",
            "tool_errors": [],
            "node_history": [],
            "conversation_history": [],
        }
        manager.run_post_audit(state)

        memory = json.loads(temp_memory_file.read_text())
        assert "globex ltd" in memory["vendor_profiles"]
        profile = memory["vendor_profiles"]["globex ltd"]
        assert len(profile["past_audits"]) == 1

    def test_post_audit_vendor_history_retrieved_on_second_run(self, temp_memory_file):
        manager = MemoryManagerAgent()
        base_state = {
            "task": "Audit Initech",
            "vendor_name": "Initech",
            "analysis": "Non-compliance breach found.",
            "decision": "Terminate contract.",
            "validation_status": "PASS",
            "tool_errors": [],
            "node_history": [],
            "conversation_history": [],
        }
        # First audit — saves to memory
        manager.run_post_audit(base_state.copy())

        # Second audit — pre_audit should find the history
        state2 = {"task": "Re-audit Initech", "vendor_name": "Initech"}
        result = manager.run_pre_audit(state2)
        history = result.get("vendor_history", "")
        assert "Initech" in history
        assert "previous audit" in history.lower()

    def test_risk_level_escalation_across_runs(self, temp_memory_file):
        manager = MemoryManagerAgent()
        # Low-risk first run
        manager.run_post_audit({
            "task": "Audit A", "vendor_name": "TestCo",
            "analysis": "Minor issue.", "decision": "OK",
            "validation_status": "PASS", "tool_errors": [],
            "node_history": [], "conversation_history": [],
        })
        # High-risk second run
        manager.run_post_audit({
            "task": "Audit B", "vendor_name": "TestCo",
            "analysis": "Serious breach detected.", "decision": "Escalate.",
            "validation_status": "FAIL", "tool_errors": [],
            "node_history": [], "conversation_history": [],
            "conditional_path": "high_risk_review",
        })
        memory = json.loads(temp_memory_file.read_text())
        profile = memory["vendor_profiles"]["testco"]
        assert profile["overall_risk"] == "HIGH"
        assert len(profile["past_audits"]) == 2


# ── Risk Pattern Matching ──────────────────────────────────────────────────────

class TestRiskPatternMatching:

    def test_matches_gdpr_keyword(self, temp_memory_file):
        result = MemoryManagerAgent.get_relevant_risk_patterns(
            "The contract references gdpr data protection obligations."
        )
        assert "GDPR" in result

    def test_matches_sla_keyword(self, temp_memory_file):
        result = MemoryManagerAgent.get_relevant_risk_patterns(
            "The SLA penalty clause applies after 3 missed deliveries."
        )
        assert "SLA" in result

    def test_no_match_returns_message(self, temp_memory_file):
        result = MemoryManagerAgent.get_relevant_risk_patterns(
            "This contract covers office supplies procurement."
        )
        assert "No known risk patterns matched" in result
