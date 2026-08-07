"""
app.py
──────
FastAPI application for the AI Agent Coordination & Decision Engine.

Endpoints:
  GET  /              → health check
  POST /audit         → run a full audit pipeline
  GET  /report        → download the latest final_report.txt
  GET  /history       → all past audit run records
  GET  /metrics       → aggregate pipeline metrics summary
  GET  /vendors       → all vendor profiles from long-term memory
  GET  /vendors/{name}→ specific vendor profile

Sprint 5: Module 5 — Enterprise API, Dashboard & Deployment
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.schemas import (
    AuditRequest,
    AuditResponse,
    HealthResponse,
    MetricsSummaryResponse,
    VendorProfileResponse,
)
from workflows.Orchestrator import Orchestrator
from workflows.metrics import get_metrics_summary, load_all_metrics

MEMORY_FILE = Path(__file__).parent.parent / "memory" / "audit_memory.json"
REPORT_FILE = Path(__file__).parent.parent / "final_report.txt"
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Agent Audit Engine",
    description="Multi-agent contract & procurement audit platform",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard static files
if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

# Single shared orchestrator instance
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="ok",
        version="4.0.0",
        milestone="Module 5 — Enterprise API & Dashboard",
    )


@app.post("/audit", response_model=AuditResponse, tags=["Audit"])
def run_audit(request: AuditRequest):
    """
    Run a full multi-agent contract audit pipeline.
    Returns the complete audit state including scores, analysis, and decision.
    """
    try:
        orc = get_orchestrator()
        kwargs = {}
        if request.vendor_name:
            kwargs["vendor_name"] = request.vendor_name
        if request.contract_csv_path:
            kwargs["contract_csv_path"] = request.contract_csv_path
        if request.contract_pdf_path:
            kwargs["contract_pdf_path"] = request.contract_pdf_path

        state = orc.run(request.task, **kwargs)

        return AuditResponse(
            status="completed",
            task=request.task,
            vendor_name=request.vendor_name,
            audit_score=state.get("audit_score"),
            audit_quality_band=state.get("audit_quality_band"),
            score_breakdown=state.get("score_breakdown"),
            validation_status=state.get("validation_status"),
            validation_errors=state.get("validation_errors", []),
            node_history=state.get("node_history", []),
            tool_errors=state.get("tool_errors", []),
            re_plan_triggered=state.get("re_plan_triggered", False),
            report_path=state.get("report_path"),
            pipeline_metrics=state.get("pipeline_metrics"),
            plan=state.get("plan"),
            analysis=state.get("analysis"),
            decision=state.get("decision"),
            review_notes=state.get("review_notes"),
            vendor_risk_report=state.get("vendor_risk_report"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/report", tags=["Audit"])
def download_report():
    """Download the latest generated audit report as a text file."""
    if not REPORT_FILE.exists():
        raise HTTPException(status_code=404, detail="No report found. Run /audit first.")
    return FileResponse(
        path=str(REPORT_FILE),
        filename="audit_report.txt",
        media_type="text/plain",
    )


@app.get("/history", tags=["Analytics"])
def get_audit_history():
    """Return all past audit run records from the persistent metrics log."""
    records = load_all_metrics()
    return {"total": len(records), "records": records}


@app.get("/metrics", response_model=MetricsSummaryResponse, tags=["Analytics"])
def get_metrics():
    """Return aggregate statistics across all audit runs."""
    summary = get_metrics_summary()
    return MetricsSummaryResponse(**summary)


@app.get("/vendors", tags=["Vendors"])
def list_vendors():
    """Return all vendor profiles stored in long-term memory."""
    if not MEMORY_FILE.exists():
        return {"vendors": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
    profiles = memory.get("vendor_profiles", {})
    return {
        "total": len(profiles),
        "vendors": [
            {
                "vendor_name": v.get("vendor_name", k),
                "overall_risk": v.get("overall_risk"),
                "last_audited": v.get("last_audited"),
                "audit_count": len(v.get("past_audits", [])),
            }
            for k, v in profiles.items()
        ],
    }


@app.get("/vendors/{vendor_name}", response_model=VendorProfileResponse, tags=["Vendors"])
def get_vendor(vendor_name: str):
    """Return the full profile and audit history for a specific vendor."""
    if not MEMORY_FILE.exists():
        raise HTTPException(status_code=404, detail="Memory store not found.")
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
    key = vendor_name.strip().lower()
    profile = memory.get("vendor_profiles", {}).get(key)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_name}' not found.")
    return VendorProfileResponse(
        vendor_name=profile.get("vendor_name", vendor_name),
        overall_risk=profile.get("overall_risk"),
        last_audited=profile.get("last_audited"),
        past_audits=profile.get("past_audits", []),
    )


@app.get("/risk-patterns", tags=["Analytics"])
def get_risk_patterns():
    """Return the known risk pattern library from the knowledge base."""
    if not MEMORY_FILE.exists():
        return {"patterns": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
    return {"patterns": memory.get("known_risk_patterns", [])}
