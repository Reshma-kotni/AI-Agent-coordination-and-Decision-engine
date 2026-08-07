"""
tests/test_tools.py
───────────────────
Unit tests for Sprint 2 enterprise tools:
  - PandasAuditTool
  - PDFContractParserTool
  - VendorRiskApiTool
"""

import os
import tempfile
import pandas as pd
import pytest

from agents.tools import PandasAuditTool
from agents.doc_parser import PDFContractParserTool
from agents.vendor_api import VendorRiskApiTool


# ── PandasAuditTool ────────────────────────────────────────────────────────────

class TestPandasAuditTool:

    def test_missing_csv_path_returns_error(self):
        state = {}
        result = PandasAuditTool.run(state)
        assert "tool_errors" in result
        assert len(result["tool_errors"]) > 0

    def test_invalid_csv_path_logs_error(self):
        state = {"contract_csv_path": "non_existent_file.csv"}
        result = PandasAuditTool.run(state)
        assert "tool_errors" in result
        assert any("not found" in e for e in result["tool_errors"])

    def test_valid_csv_produces_summary(self, tmp_path):
        csv_file = tmp_path / "test_contract.csv"
        df = pd.DataFrame({
            "vendor": ["Acme", "Globex"],
            "value": [10000, 25000],
            "risk_level": ["Low", "High"],
            "compliance_status": ["OK", "Fail"],
        })
        df.to_csv(csv_file, index=False)

        state = {"contract_csv_path": str(csv_file)}
        result = PandasAuditTool.run(state)

        assert result.get("pandas_tool_result") == "Pandas audit tool executed successfully."
        assert "contract_dataframe_summary" in result
        assert "contract_risk_clause_detection" in result
        assert "risk_level" in result["contract_risk_clause_detection"]

    def test_csv_with_no_risk_columns(self, tmp_path):
        csv_file = tmp_path / "plain.csv"
        df = pd.DataFrame({"item": ["A", "B"], "price": [100, 200]})
        df.to_csv(csv_file, index=False)

        state = {"contract_csv_path": str(csv_file)}
        result = PandasAuditTool.run(state)
        assert "No explicit risk" in result["contract_risk_clause_detection"]


# ── PDFContractParserTool ──────────────────────────────────────────────────────

class TestPDFContractParserTool:

    def test_missing_pdf_path_returns_error(self):
        state = {}
        result = PDFContractParserTool.run(state)
        assert "tool_errors" in result

    def test_invalid_pdf_path_logs_error(self):
        state = {"contract_pdf_path": "non_existent.pdf"}
        result = PDFContractParserTool.run(state)
        assert "tool_errors" in result
        assert any("not found" in e for e in result["tool_errors"])


# ── VendorRiskApiTool ──────────────────────────────────────────────────────────

class TestVendorRiskApiTool:

    def test_missing_vendor_name_returns_error(self):
        state = {}
        result = VendorRiskApiTool.run(state)
        assert "tool_errors" in result

    def test_known_compliant_vendor(self):
        state = {"vendor_name": "Acme Corp"}
        result = VendorRiskApiTool.run(state)
        assert result.get("vendor_risk_tool_result") == "Vendor Risk API executed successfully."
        assert "Acme Corp" in result.get("vendor_risk_report", "")
        assert result.get("vendor_risk_data", {}).get("compliance_status") == "Compliant"

    def test_known_non_compliant_vendor_flags_in_analysis(self):
        state = {"vendor_name": "Initech Solutions", "analysis": "Initial analysis."}
        result = VendorRiskApiTool.run(state)
        # Risk flags should be appended to analysis
        assert "Vendor Risk Flags" in result.get("analysis", "")

    def test_known_risky_vendor(self):
        state = {"vendor_name": "Globex Ltd"}
        result = VendorRiskApiTool.run(state)
        data = result.get("vendor_risk_data", {})
        assert data.get("compliance_status") == "Under Review"
        assert len(data.get("past_risk_flags", [])) > 0

    def test_unknown_vendor_returns_default_profile(self):
        state = {"vendor_name": "Unknown Vendor XYZ"}
        result = VendorRiskApiTool.run(state)
        assert result.get("vendor_risk_tool_result") == "Vendor Risk API executed successfully."
        report = result.get("vendor_risk_report", "")
        assert "Unknown Vendor XYZ" in report

    def test_unregistered_vendor_detected(self):
        state = {"vendor_name": "Umbrella Technologies"}
        result = VendorRiskApiTool.run(state)
        data = result.get("vendor_risk_data", {})
        assert data.get("registered") is False
