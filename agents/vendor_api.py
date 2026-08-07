"""
vendor_api.py
─────────────
VendorRiskApiTool — Simulates an enterprise Vendor Risk Management (VRM) API.

In a real deployment this module would call an internal REST API (e.g., SAP Ariba,
Coupa, or a custom vendor portal). For now, it returns deterministic mock data so
the rest of the pipeline can be built and tested end-to-end without a live service.

Tool Metadata (used by the LLM agent for intelligent tool selection)
─────────────────────────────────────────────────────────────────────
name        : vendor_risk_api
description : Use this tool to look up a vendor's registration status, credit
              rating, compliance history, and past risk flags from the enterprise
              Vendor Risk Management system. Provide the vendor name extracted
              from the contract.
args_schema : { "vendor_name": { "type": "string",
                "description": "Name of the vendor to look up." } }
"""

from __future__ import annotations

import datetime
import random


# ── Mock database ──────────────────────────────────────────────────────────────
# Simulate a small internal vendor registry.
_VENDOR_DB: dict[str, dict] = {
    "acme corp": {
        "registered": True,
        "registration_date": "2018-03-15",
        "credit_rating": "A",
        "compliance_status": "Compliant",
        "past_risk_flags": [],
        "active_contracts": 4,
        "country": "US",
    },
    "globex ltd": {
        "registered": True,
        "registration_date": "2020-07-22",
        "credit_rating": "B+",
        "compliance_status": "Under Review",
        "past_risk_flags": ["Late delivery (2022-Q3)", "Invoice dispute (2023-Q1)"],
        "active_contracts": 2,
        "country": "UK",
    },
    "initech solutions": {
        "registered": True,
        "registration_date": "2015-11-01",
        "credit_rating": "C",
        "compliance_status": "Non-Compliant",
        "past_risk_flags": [
            "GDPR violation (2021)",
            "Breach of SLA (2022-Q2)",
            "Pending litigation (2023)",
        ],
        "active_contracts": 1,
        "country": "IN",
    },
    "umbrella technologies": {
        "registered": False,
        "registration_date": None,
        "credit_rating": "N/A",
        "compliance_status": "Unknown",
        "past_risk_flags": ["Not registered in vendor portal"],
        "active_contracts": 0,
        "country": "Unknown",
    },
}
# ──────────────────────────────────────────────────────────────────────────────


def _lookup_vendor(vendor_name: str) -> dict:
    """Return mock vendor data or generate a default 'unknown vendor' record."""
    key = vendor_name.strip().lower()
    if key in _VENDOR_DB:
        return _VENDOR_DB[key]

    # For any unknown vendor, return a plausible neutral record
    return {
        "registered": True,
        "registration_date": "2019-01-01",
        "credit_rating": "B",
        "compliance_status": "Compliant",
        "past_risk_flags": [],
        "active_contracts": random.randint(1, 10),
        "country": "Unknown",
        "_note": f"Vendor '{vendor_name}' not found in internal registry. Returned default profile.",
    }


def _format_vendor_report(vendor_name: str, data: dict) -> str:
    """Convert the vendor data dictionary to a human-readable audit report string."""
    flags = data.get("past_risk_flags", [])
    flags_str = "\n    - " + "\n    - ".join(flags) if flags else "\n    None"

    return (
        f"Vendor Risk API Report\n"
        f"{'─' * 40}\n"
        f"Vendor Name        : {vendor_name}\n"
        f"Registered         : {'Yes' if data.get('registered') else 'No'}\n"
        f"Registration Date  : {data.get('registration_date', 'N/A')}\n"
        f"Country            : {data.get('country', 'N/A')}\n"
        f"Credit Rating      : {data.get('credit_rating', 'N/A')}\n"
        f"Compliance Status  : {data.get('compliance_status', 'N/A')}\n"
        f"Active Contracts   : {data.get('active_contracts', 0)}\n"
        f"Past Risk Flags    : {flags_str}\n"
        f"Report Generated   : {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    )


class VendorRiskApiTool:
    """
    Simulates an enterprise Vendor Risk Management (VRM) API call.
    Returns the vendor's registration status, credit rating, compliance
    history, and historical risk flags.
    """

    name: str = "vendor_risk_api"
    description: str = (
        "Use this tool to look up a vendor's registration status, credit rating, "
        "compliance history, and past risk flags from the enterprise Vendor Risk "
        "Management system. Provide the vendor name extracted from the contract."
    )
    args_schema: dict = {
        "vendor_name": {
            "type": "string",
            "description": "Name of the vendor as it appears in the contract.",
        }
    }

    @staticmethod
    def run(state: dict) -> dict:
        """
        Reads `vendor_name` from state, queries the mock VRM API, and stores
        the formatted report in `vendor_risk_report`.
        """
        vendor_name = state.get("vendor_name", "").strip()

        if not vendor_name:
            msg = "VendorRiskApiTool: no 'vendor_name' found in state."
            state["vendor_risk_report"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]
            return state

        try:
            data = _lookup_vendor(vendor_name)
            report = _format_vendor_report(vendor_name, data)
            state["vendor_risk_report"] = report
            state["vendor_risk_data"] = data          # raw dict for downstream logic
            state["vendor_risk_tool_result"] = "Vendor Risk API executed successfully."

            # Surface critical risk signals into the main analysis context
            if data.get("past_risk_flags"):
                existing = state.get("analysis", "")
                state["analysis"] = (
                    existing
                    + f"\n\n[Vendor Risk Flags for '{vendor_name}']: "
                    + "; ".join(data["past_risk_flags"])
                )

        except Exception as exc:
            msg = f"VendorRiskApiTool: unexpected error — {exc}"
            state["vendor_risk_report"] = msg
            state["tool_errors"] = state.get("tool_errors", []) + [msg]

        return state
