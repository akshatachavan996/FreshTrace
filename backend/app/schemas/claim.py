"""Pydantic schemas for extracted claims and claim evaluation results."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import SourceCreate, SourceResponse


class ClaimVolatility(str, Enum):
    """Volatility category determining likelihood of claim becoming outdated."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClaimStatus(str, Enum):
    """Evaluation status of a claim against retrieved web evidence."""

    LIKELY_CURRENT = "LIKELY_CURRENT"
    POTENTIALLY_STALE = "POTENTIALLY_STALE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNVERIFIED = "UNVERIFIED"
    NOT_TIME_SENSITIVE = "NOT_TIME_SENSITIVE"


class ExtractedClaim(BaseModel):
    """Structured claim output extracted by the AI model."""

    claim_text: str = Field(..., description="Self-contained, factual, verifiable claim statement")
    claim_type: str = Field(
        "Fact",
        description="Type of claim (Fact, Pricing, Version, Statistic, Date, Regulation, Role, Event, Product)",
    )
    suggested_search_query: str = Field(
        ...,
        description="Optimized search query to find recent web evidence for this claim",
    )
    initial_volatility: ClaimVolatility = Field(
        ClaimVolatility.MEDIUM,
        description="Initial estimation of how quickly this claim changes",
    )


class ExtractedClaimList(BaseModel):
    """List of extracted claims returned from AI model structured parsing."""

    claims: List[ExtractedClaim] = Field(default_factory=list)


class ClaimEvaluation(BaseModel):
    """Full evaluated claim with evidence and scores."""

    id: str
    claim_text: str
    claim_type: str
    volatility: ClaimVolatility
    status: ClaimStatus
    freshness_score: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    temporal_risk_score: float = Field(50.0, ge=0.0, le=100.0, description="Risk of claim becoming stale (0-100)")
    recheck_interval_days: int = Field(30, description="Suggested recheck interval in days")
    last_checked_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    search_query: str
    explanation: str
    evidence_summary: str
    sources: List[SourceResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
