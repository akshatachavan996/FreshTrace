"""SQLAlchemy models for FreshTrace."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class VerificationRun(Base):
    """Represents an entire verification job on an AI answer."""

    __tablename__ = "verification_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_answer = Column(Text, nullable=False)
    question = Column(Text, nullable=True)
    mode = Column(String(20), nullable=False, default="DEEP_CHECK")  # QUICK_CHECK, DEEP_CHECK
    status = Column(String(30), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, PARTIAL, FAILED

    overall_score = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    overall_temporal_risk = Column(Float, nullable=False, default=50.0)

    total_claims = Column(Integer, nullable=False, default=0)
    likely_current_count = Column(Integer, nullable=False, default=0)
    potentially_stale_count = Column(Integer, nullable=False, default=0)
    conflicting_count = Column(Integer, nullable=False, default=0)
    unverified_count = Column(Integer, nullable=False, default=0)
    not_time_sensitive_count = Column(Integer, nullable=False, default=0)

    report_summary = Column(Text, nullable=False, default="")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to individual extracted claims
    claims = relationship("Claim", back_populates="run", cascade="all, delete-orphan", order_by="Claim.created_at")


class Claim(Base):
    """Represents an individual factual claim extracted from an AI answer."""

    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("verification_runs.id", ondelete="CASCADE"), nullable=False)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), nullable=False, default="Fact")
    volatility = Column(String(20), nullable=False, default="MEDIUM")  # HIGH, MEDIUM, LOW
    status = Column(
        String(40), nullable=False, default="UNVERIFIED"
    )  # LIKELY_CURRENT, POTENTIALLY_STALE, CONFLICTING_EVIDENCE, UNVERIFIED, NOT_TIME_SENSITIVE

    freshness_score = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    temporal_risk_score = Column(Float, nullable=False, default=50.0)
    recheck_interval_days = Column(Integer, nullable=False, default=30)
    last_checked_at = Column(DateTime, default=get_utc_now, nullable=False)

    search_query = Column(Text, nullable=False, default="")
    explanation = Column(Text, nullable=False, default="")
    evidence_summary = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    run = relationship("VerificationRun", back_populates="claims")
    sources = relationship("Source", back_populates="claim", cascade="all, delete-orphan", order_by="Source.created_at")


class Source(Base):
    """Represents a live web source retrieved for evidence."""

    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False, default="")
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, default="")
    snippet = Column(Text, nullable=False, default="")
    published_date = Column(String(100), nullable=True)
    relevance_score = Column(Float, nullable=False, default=0.0)
    credibility_heuristic = Column(String(20), nullable=False, default="MEDIUM")  # HIGH, MEDIUM, LOW
    supports_claim = Column(Boolean, nullable=True)  # True = supports, False = contradicts, None = inconclusive

    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    claim = relationship("Claim", back_populates="sources")


class VerificationCache(Base):
    """Caches search and verification evidence to minimize redundant external API calls."""

    __tablename__ = "verification_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(64), unique=True, index=True, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False)
