"""History and export API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.repositories.verification_repo import VerificationRepository
from app.database.session import get_db
from app.schemas.claim import ClaimEvaluation, ClaimStatus, ClaimVolatility
from app.schemas.source import SourceResponse
from app.schemas.verification import (
    ClaimDiff,
    ComparisonResult,
    VerificationExport,
    VerificationHistoryItem,
    VerificationMode,
    VerificationResponse,
    VerificationStatus,
)

router = APIRouter(prefix="/api/v1", tags=["History"])


def _map_run_to_response(run) -> VerificationResponse:
    """Helper to convert a DB run model into a full VerificationResponse."""
    claims_list = []
    for c in run.claims:
        sources_list = [
            SourceResponse(
                id=s.id,
                title=s.title,
                url=s.url,
                domain=s.domain,
                snippet=s.snippet,
                published_date=s.published_date,
                relevance_score=s.relevance_score,
                credibility_heuristic=s.credibility_heuristic,
                supports_claim=s.supports_claim,
            )
            for s in c.sources
        ]
        claims_list.append(
            ClaimEvaluation(
                id=c.id,
                claim_text=c.claim_text,
                claim_type=c.claim_type,
                volatility=ClaimVolatility(c.volatility),
                status=ClaimStatus(c.status),
                freshness_score=c.freshness_score,
                confidence_score=c.confidence_score,
                temporal_risk_score=getattr(c, "temporal_risk_score", 50.0),
                recheck_interval_days=getattr(c, "recheck_interval_days", 30),
                last_checked_at=getattr(c, "last_checked_at", None),
                search_query=c.search_query,
                explanation=c.explanation,
                evidence_summary=c.evidence_summary,
                sources=sources_list,
            )
        )

    return VerificationResponse(
        run_id=run.id,
        original_answer=run.original_answer,
        question=run.question,
        mode=VerificationMode(run.mode),
        status=VerificationStatus(run.status),
        overall_score=run.overall_score,
        confidence_score=run.confidence_score,
        overall_temporal_risk=getattr(run, "overall_temporal_risk", 50.0),
        total_claims=run.total_claims,
        likely_current_count=run.likely_current_count,
        potentially_stale_count=run.potentially_stale_count,
        conflicting_count=run.conflicting_count,
        unverified_count=run.unverified_count,
        not_time_sensitive_count=run.not_time_sensitive_count,
        report_summary=run.report_summary,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
        claims=claims_list,
    )


@router.get(
    "/history",
    response_model=List[VerificationHistoryItem],
    summary="List Verification History",
)
def list_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[VerificationHistoryItem]:
    """Retrieve past verification runs in reverse chronological order."""
    repo = VerificationRepository(db)
    runs = repo.list_runs(limit=limit, offset=offset)

    items = []
    for r in runs:
        snippet = r.original_answer[:120] + "..." if len(r.original_answer) > 120 else r.original_answer
        items.append(
            VerificationHistoryItem(
                id=r.id,
                question=r.question,
                original_answer_snippet=snippet,
                mode=r.mode,
                status=r.status,
                overall_score=r.overall_score,
                confidence_score=r.confidence_score,
                total_claims=r.total_claims,
                potentially_stale_count=r.potentially_stale_count,
                conflicting_count=r.conflicting_count,
                created_at=r.created_at,
            )
        )
    return items


@router.get(
    "/history/{run_id}",
    response_model=VerificationResponse,
    summary="Get Verification Run Details",
)
def get_run_details(
    run_id: str,
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """Retrieve full details of a specific verification run including all claims and sources."""
    repo = VerificationRepository(db)
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification run '{run_id}' not found.",
        )
    return _map_run_to_response(run)


@router.delete(
    "/history/{run_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Verification Run",
)
def delete_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Permanently delete a verification run and its associated claims."""
    repo = VerificationRepository(db)
    success = repo.delete_run(run_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification run '{run_id}' not found.",
        )
    return {"status": "success", "message": f"Run '{run_id}' deleted successfully."}


@router.get(
    "/history/{run_id}/export",
    response_model=VerificationExport,
    summary="Export Verification Report",
)
def export_run_report(
    run_id: str,
    db: Session = Depends(get_db),
) -> VerificationExport:
    """Export complete verification data as a structured JSON report."""
    repo = VerificationRepository(db)
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification run '{run_id}' not found.",
        )
    base_response = _map_run_to_response(run)
    return VerificationExport(**base_response.model_dump())


@router.get(
    "/history/compare",
    response_model=ComparisonResult,
    summary="Compare Two Verification Runs for Changes",
)
def compare_runs(
    run_a: str = Query(..., description="ID of baseline/older run"),
    run_b: str = Query(..., description="ID of newer run"),
    db: Session = Depends(get_db),
) -> ComparisonResult:
    """Compare two verification runs to detect changed claim statuses, risk shifts, and new evidence."""
    repo = VerificationRepository(db)
    r_a = repo.get_run(run_a)
    r_b = repo.get_run(run_b)

    if not r_a:
        raise HTTPException(status_code=404, detail=f"Run '{run_a}' not found.")
    if not r_b:
        raise HTTPException(status_code=404, detail=f"Run '{run_b}' not found.")

    diffs = []
    claims_a_map = {c.claim_text.lower().strip(): c for c in r_a.claims}
    claims_b_map = {c.claim_text.lower().strip(): c for c in r_b.claims}

    all_keys = set(claims_a_map.keys()) | set(claims_b_map.keys())

    status_changes_count = 0
    for key in all_keys:
        ca = claims_a_map.get(key)
        cb = claims_b_map.get(key)

        text = ca.claim_text if ca else cb.claim_text
        status_a = ca.status if ca else "NOT_PRESENT"
        status_b = cb.status if cb else "NOT_PRESENT"
        fresh_a = ca.freshness_score if ca else 0.0
        fresh_b = cb.freshness_score if cb else 0.0
        risk_a = getattr(ca, "temporal_risk_score", 50.0) if ca else 50.0
        risk_b = getattr(cb, "temporal_risk_score", 50.0) if cb else 50.0
        src_a = len(ca.sources) if ca else 0
        src_b = len(cb.sources) if cb else 0

        changed = status_a != status_b
        if changed:
            status_changes_count += 1

        diffs.append(
            ClaimDiff(
                claim_text=text,
                status_a=status_a,
                status_b=status_b,
                freshness_a=fresh_a,
                freshness_b=fresh_b,
                temporal_risk_a=risk_a,
                temporal_risk_b=risk_b,
                sources_count_a=src_a,
                sources_count_b=src_b,
                status_changed=changed,
                risk_delta=round(risk_b - risk_a, 1),
            )
        )

    score_delta = round(r_b.overall_score - r_a.overall_score, 1)
    risk_a_overall = getattr(r_a, "overall_temporal_risk", 50.0)
    risk_b_overall = getattr(r_b, "overall_temporal_risk", 50.0)
    risk_delta = round(risk_b_overall - risk_a_overall, 1)

    summary = (
        f"Compared Run A ({r_a.id[:8]}) to Run B ({r_b.id[:8]}). "
        f"Freshness score shifted by {score_delta:+} points. "
        f"Detected {status_changes_count} status change(s) across {len(diffs)} total claim(s)."
    )

    return ComparisonResult(
        run_a_id=r_a.id,
        run_b_id=r_b.id,
        created_at_a=r_a.created_at,
        created_at_b=r_b.created_at,
        overall_score_a=r_a.overall_score,
        overall_score_b=r_b.overall_score,
        score_delta=score_delta,
        temporal_risk_a=risk_a_overall,
        temporal_risk_b=risk_b_overall,
        risk_delta=risk_delta,
        claims_diff=diffs,
        summary=summary,
    )
