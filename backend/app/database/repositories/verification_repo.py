"""Repository for database operations on verification runs, claims, and cache."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.database.models import Claim, Source, VerificationCache, VerificationRun, get_utc_now


class VerificationRepository:
    """Encapsulates database access for FreshTrace."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self,
        original_answer: str,
        question: Optional[str] = None,
        mode: str = "DEEP_CHECK",
        run_id: Optional[str] = None,
    ) -> VerificationRun:
        """Create a new verification run record."""
        run = VerificationRun(
            original_answer=original_answer,
            question=question,
            mode=mode,
            status="PENDING",
        )
        if run_id:
            run.id = run_id
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: str) -> Optional[VerificationRun]:
        """Retrieve a verification run with its claims and sources loaded."""
        return (
            self.db.query(VerificationRun)
            .options(
                joinedload(VerificationRun.claims).joinedload(Claim.sources)
            )
            .filter(VerificationRun.id == run_id)
            .first()
        )

    def list_runs(self, limit: int = 50, offset: int = 0) -> List[VerificationRun]:
        """List past verification runs ordered by creation time descending."""
        return (
            self.db.query(VerificationRun)
            .order_by(VerificationRun.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_run(self, run_id: str) -> bool:
        """Delete a verification run and all associated claims/sources."""
        run = self.db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
        if not run:
            return False
        self.db.delete(run)
        self.db.commit()
        return True

    def save_completed_run(
        self,
        run_id: str,
        overall_score: float,
        confidence_score: float,
        status: str,
        report_summary: str,
        claims_data: List[dict],
        overall_temporal_risk: float = 50.0,
        error_message: Optional[str] = None,
    ) -> Optional[VerificationRun]:
        """Save claims, sources, and final score summary to an existing verification run."""
        run = self.db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
        if not run:
            return None

        run.overall_score = round(overall_score, 1)
        run.confidence_score = round(confidence_score, 1)
        run.overall_temporal_risk = round(overall_temporal_risk, 1)
        run.status = status
        run.report_summary = report_summary
        run.error_message = error_message
        run.completed_at = get_utc_now()

        # Count statuses
        likely_current = 0
        potentially_stale = 0
        conflicting = 0
        unverified = 0
        not_time_sensitive = 0

        for c_data in claims_data:
            c_status = c_data.get("status", "UNVERIFIED")
            if c_status == "LIKELY_CURRENT":
                likely_current += 1
            elif c_status == "POTENTIALLY_STALE":
                potentially_stale += 1
            elif c_status == "CONFLICTING_EVIDENCE":
                conflicting += 1
            elif c_status == "NOT_TIME_SENSITIVE":
                not_time_sensitive += 1
            else:
                unverified += 1

            claim = Claim(
                id=c_data.get("id"),
                run_id=run.id,
                claim_text=c_data["claim_text"],
                claim_type=c_data.get("claim_type", "Fact"),
                volatility=c_data.get("volatility", "MEDIUM"),
                status=c_status,
                freshness_score=round(c_data.get("freshness_score", 0.0), 1),
                confidence_score=round(c_data.get("confidence_score", 0.0), 1),
                temporal_risk_score=round(c_data.get("temporal_risk_score", 50.0), 1),
                recheck_interval_days=int(c_data.get("recheck_interval_days", 30)),
                search_query=c_data.get("search_query", ""),
                explanation=c_data.get("explanation", ""),
                evidence_summary=c_data.get("evidence_summary", ""),
            )
            self.db.add(claim)
            self.db.flush()

            for s_data in c_data.get("sources", []):
                source = Source(
                    id=s_data.get("id"),
                    claim_id=claim.id,
                    title=s_data.get("title", ""),
                    url=s_data.get("url", ""),
                    domain=s_data.get("domain", ""),
                    snippet=s_data.get("snippet", ""),
                    published_date=s_data.get("published_date"),
                    relevance_score=round(s_data.get("relevance_score", 0.0), 2),
                    credibility_heuristic=s_data.get("credibility_heuristic", "MEDIUM"),
                    supports_claim=s_data.get("supports_claim"),
                )
                self.db.add(source)

        run.total_claims = len(claims_data)
        run.likely_current_count = likely_current
        run.potentially_stale_count = potentially_stale
        run.conflicting_count = conflicting
        run.unverified_count = unverified
        run.not_time_sensitive_count = not_time_sensitive

        self.db.commit()
        return self.get_run(run_id)

    # --- Cache Operations ---

    def get_cached_search(self, cache_key: str) -> Optional[str]:
        """Retrieve valid cached search results."""
        now = get_utc_now()
        entry = (
            self.db.query(VerificationCache)
            .filter(
                VerificationCache.cache_key == cache_key,
                VerificationCache.expires_at > now,
            )
            .first()
        )
        if entry:
            return entry.response_json
        return None

    def set_cached_search(self, cache_key: str, response_json: str, hours: int = 24) -> None:
        """Store or update search results in cache with expiration."""
        now = get_utc_now()
        expires_at = now + timedelta(hours=hours)

        existing = self.db.query(VerificationCache).filter(VerificationCache.cache_key == cache_key).first()
        if existing:
            existing.response_json = response_json
            existing.expires_at = expires_at
        else:
            new_entry = VerificationCache(
                cache_key=cache_key,
                response_json=response_json,
                created_at=now,
                expires_at=expires_at,
            )
            self.db.add(new_entry)
        self.db.commit()
