"""
schemas.py
──────────
Pydantic request/response models for the FastAPI audit engine API.

Sprint 5: Module 5 — Enterprise API, Dashboard & Deployment
"""

from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field


# ── Request Models ─────────────────────────────────────────────────────────────

class AuditRequest(BaseModel):
    task: str = Field(..., description="Audit task description", min_length=10)
    vendor_name: Optional[str] = Field(None, description="Vendor name to look up in VRM")
    contract_csv_path: Optional[str] = Field(None, description="Path to CSV contract file")
    contract_pdf_path: Optional[str] = Field(None, description="Path to PDF contract file")


# ── Response Models ────────────────────────────────────────────────────────────

class ScoreDimension(BaseModel):
    score: int
    max: int
    notes: list[str]


class ScoreBreakdown(BaseModel):
    completeness: Optional[ScoreDimension] = None
    risk_coverage: Optional[ScoreDimension] = None
    tool_coverage: Optional[ScoreDimension] = None
    decision_quality: Optional[ScoreDimension] = None


class AuditResponse(BaseModel):
    status: str
    task: str
    vendor_name: Optional[str]
    audit_score: Optional[int]
    audit_quality_band: Optional[str]
    score_breakdown: Optional[dict]
    validation_status: Optional[str]
    validation_errors: Optional[list[str]]
    node_history: Optional[list[str]]
    tool_errors: Optional[list[str]]
    re_plan_triggered: Optional[bool]
    report_path: Optional[str]
    pipeline_metrics: Optional[dict]
    plan: Optional[str]
    analysis: Optional[str]
    decision: Optional[str]
    review_notes: Optional[str]
    vendor_risk_report: Optional[str]


class MetricsSummaryResponse(BaseModel):
    total_runs: int
    pass_rate_pct: Optional[float]
    avg_audit_score: Optional[float]
    avg_duration_s: Optional[float]
    fastest_run_s: Optional[float]
    slowest_run_s: Optional[float]
    quality_distribution: Optional[dict]


class VendorProfileResponse(BaseModel):
    vendor_name: str
    overall_risk: Optional[str]
    last_audited: Optional[str]
    past_audits: Optional[list[dict]]


class HealthResponse(BaseModel):
    status: str
    version: str
    milestone: str
