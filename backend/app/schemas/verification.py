"""Pydantic schemas for verification requests, responses, and history."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.claim import ClaimEvaluation


class VerificationMode(str, Enum):
    """Verification depth mode."""

    QUICK_CHECK = "QUICK_CHECK"
    DEEP_CHECK = "DEEP_CHECK"


class VerificationStatus(str, Enum):
    """Verification overall execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class VerificationRequest(BaseModel):
    """Request payload to initiate answer freshness verification."""

    answer_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="The AI-generated answer text to verify for freshness.",
    )
    question: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional question/prompt that generated the answer, providing extra context.",
    )
    mode: VerificationMode = Field(
        VerificationMode.DEEP_CHECK,
        description="QUICK_CHECK prioritizes high-volatility claims; DEEP_CHECK verifies all extracted claims.",
    )


class VerificationResponse(BaseModel):
    """Full verification response including scores, claims, and sources."""

    run_id: str
    original_answer: str
    question: Optional[str] = None
    mode: VerificationMode
    status: VerificationStatus

    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall answer freshness score (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in this verification (0-100)")
    overall_temporal_risk: float = Field(50.0, ge=0.0, le=100.0, description="Overall temporal drift risk (0-100)")

    total_claims: int
    likely_current_count: int
    potentially_stale_count: int
    conflicting_count: int
    unverified_count: int
    not_time_sensitive_count: int

    report_summary: str
    error_message: Optional[str] = None

    created_at: datetime
    completed_at: Optional[datetime] = None

    claims: List[ClaimEvaluation] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class VerificationHistoryItem(BaseModel):
    """Summary item for the verification history list view."""

    id: str
    question: Optional[str] = None
    original_answer_snippet: str
    mode: str
    status: str
    overall_score: float
    confidence_score: float
    overall_temporal_risk: float = 50.0
    total_claims: int
    potentially_stale_count: int
    conflicting_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ClaimDiff(BaseModel):
    """Diff between a claim evaluated across two runs."""

    claim_text: str
    status_a: str
    status_b: str
    freshness_a: float
    freshness_b: float
    temporal_risk_a: float
    temporal_risk_b: float
    sources_count_a: int
    sources_count_b: int
    status_changed: bool
    risk_delta: float


class ComparisonResult(BaseModel):
    """Comparison diff between two verification runs."""

    run_a_id: str
    run_b_id: str
    created_at_a: datetime
    created_at_b: datetime
    overall_score_a: float
    overall_score_b: float
    score_delta: float
    temporal_risk_a: float
    temporal_risk_b: float
    risk_delta: float
    claims_diff: List[ClaimDiff]
    summary: str


class VerificationExport(VerificationResponse):
    """Export schema for downloading full verification reports as JSON."""

    system_metadata: dict = Field(
        default_factory=lambda: {
            "engine": "FreshTrace",
            "version": "0.1.0",
            "scoring_formula": "weighted_evidence_recency_and_agreement",
            "disclosure": "FreshTrace provides heuristic verification, not absolute certainty.",
        }
    )
