"""Verification orchestration service.

Coordinates the complete claim extraction, volatility classification, live Tavily search,
evidence evaluation, scoring, and history persistence pipeline.
"""

import asyncio
from typing import List, Optional
import uuid

from app.config import Settings, get_settings
from app.core.exceptions import (
    BifrostError,
    ClaimExtractionError,
    FreshTraceError,
    MissingCredentialsError,
    TavilyError,
)
from app.core.logging import logger
from app.database.repositories.verification_repo import VerificationRepository
from app.schemas.claim import ClaimEvaluation, ClaimStatus, ClaimVolatility, ExtractedClaim
from app.schemas.source import SourceBase, SourceResponse
from app.schemas.verification import (
    VerificationMode,
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
)
from app.services.bifrost_service import BifrostService
from app.services.claim_extraction_service import ClaimExtractionService
from app.services.evidence_service import EvidenceService
from app.services.scoring_service import ScoringService
from app.services.tavily_service import TavilyService
from app.services.volatility_service import VolatilityService


class VerificationService:
    """Orchestrates end-to-end answer freshness verification."""

    def __init__(
        self,
        repository: VerificationRepository,
        settings: Optional[Settings] = None,
        bifrost_service: Optional[BifrostService] = None,
        claim_extraction_service: Optional[ClaimExtractionService] = None,
        tavily_service: Optional[TavilyService] = None,
        volatility_service: Optional[VolatilityService] = None,
        evidence_service: Optional[EvidenceService] = None,
        scoring_service: Optional[ScoringService] = None,
    ):
        self.repository = repository
        self.settings = settings or get_settings()
        self.bifrost_service = bifrost_service or BifrostService(self.settings)
        self.claim_extraction_service = (
            claim_extraction_service or ClaimExtractionService(self.bifrost_service)
        )
        self.tavily_service = (
            tavily_service or TavilyService(self.settings, repository=self.repository)
        )
        self.volatility_service = volatility_service or VolatilityService()
        self.evidence_service = evidence_service or EvidenceService()
        self.scoring_service = scoring_service or ScoringService()

    async def verify_answer(self, request: VerificationRequest) -> VerificationResponse:
        """Execute full verification pipeline on AI answer text.

        Args:
            request: VerificationRequest containing answer_text, optional question, and mode.

        Returns:
            VerificationResponse detailing freshness scores and claim breakdown.
        """
        run_id = str(uuid.uuid4())
        logger.info("Initiating verification run [%s] in mode %s", run_id, request.mode.value)

        # 1. Create pending record in database
        run_record = self.repository.create_run(
            original_answer=request.answer_text,
            question=request.question,
            mode=request.mode.value,
            run_id=run_id,
        )

        # 2. Extract verifiable claims via Bifrost
        try:
            raw_claims = await self.claim_extraction_service.extract_claims(
                answer_text=request.answer_text,
                question=request.question,
            )
        except MissingCredentialsError as exc:
            logger.error("Run [%s] aborted: %s", run_id, exc)
            self.repository.save_completed_run(
                run_id=run_id,
                overall_score=0.0,
                confidence_score=0.0,
                status=VerificationStatus.FAILED.value,
                report_summary=f"Verification failed: {exc.message}",
                claims_data=[],
                error_message=exc.message,
            )
            raise
        except (BifrostError, ClaimExtractionError) as exc:
            logger.error("Run [%s] claim extraction failed: %s", run_id, exc)
            self.repository.save_completed_run(
                run_id=run_id,
                overall_score=0.0,
                confidence_score=0.0,
                status=VerificationStatus.FAILED.value,
                report_summary=f"AI Claim Extraction Failed: {str(exc)}",
                claims_data=[],
                error_message=str(exc),
            )
            raise

        if not raw_claims:
            # Answer had no verifiable factual claims
            summary = "No independently verifiable factual claims were detected in this answer."
            saved_run = self.repository.save_completed_run(
                run_id=run_id,
                overall_score=100.0,
                confidence_score=90.0,
                status=VerificationStatus.COMPLETED.value,
                report_summary=summary,
                claims_data=[],
            )
            return self._build_response(saved_run, [])

        # 3. Classify claim volatility
        claims_with_volatility = []
        for claim in raw_claims:
            volatility, vol_reason = self.volatility_service.classify_volatility(
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                initial_volatility=claim.initial_volatility,
            )
            claims_with_volatility.append((claim, volatility, vol_reason))

        # 4. Search live web concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent Tavily search requests
        evaluated_claims: List[dict] = []
        scores_for_overall: List[tuple] = []
        partial_failures = 0

        async def _research_claim(claim: ExtractedClaim, volatility: ClaimVolatility, vol_reason: str) -> dict:
            nonlocal partial_failures
            claim_id = str(uuid.uuid4())

            # In QUICK_CHECK mode, skip live web search for LOW volatility claims to save queries
            if request.mode == VerificationMode.QUICK_CHECK and volatility == ClaimVolatility.LOW:
                freshness, confidence, temporal_risk, recheck_days, status, explanation = self.scoring_service.calculate_claim_scores(
                    volatility=volatility,
                    analysis=self.evidence_service.analyze_claim_evidence(claim, []),
                )
                return {
                    "id": claim_id,
                    "claim_text": claim.claim_text,
                    "claim_type": claim.claim_type,
                    "volatility": volatility.value,
                    "status": status.value,
                    "freshness_score": freshness,
                    "confidence_score": confidence,
                    "temporal_risk_score": temporal_risk,
                    "recheck_interval_days": recheck_days,
                    "search_query": claim.suggested_search_query,
                    "explanation": f"{explanation} ({vol_reason})",
                    "evidence_summary": "Skipped live web search in Quick Check mode due to low volatility classification.",
                    "sources": [],
                }

            # Otherwise, perform live web search via Tavily
            sources: List[SourceBase] = []
            search_error = None
            async with semaphore:
                try:
                    sources = await self.tavily_service.search(query=claim.suggested_search_query)
                except MissingCredentialsError:
                    raise
                except Exception as exc:
                    logger.warning("Search failed for query '%s': %s", claim.suggested_search_query, exc)
                    partial_failures += 1
                    search_error = str(exc)

            # Analyze retrieved sources
            analysis = self.evidence_service.analyze_claim_evidence(claim, sources)
            freshness, confidence, temporal_risk, recheck_days, status, explanation = self.scoring_service.calculate_claim_scores(
                volatility=volatility,
                analysis=analysis,
            )

            if search_error:
                explanation = f"Search error occurred: {search_error}. Evaluation is based on available evidence."

            # Prepare source data dictionaries
            formatted_sources = []
            for src in analysis.evaluated_sources:
                formatted_sources.append({
                    "id": str(uuid.uuid4()),
                    "title": src.title,
                    "url": src.url,
                    "domain": src.domain,
                    "snippet": src.snippet,
                    "published_date": src.published_date,
                    "relevance_score": src.relevance_score,
                    "credibility_heuristic": src.credibility_heuristic,
                    "supports_claim": src.supports_claim,
                })

            return {
                "id": claim_id,
                "claim_text": claim.claim_text,
                "claim_type": claim.claim_type,
                "volatility": volatility.value,
                "status": status.value,
                "freshness_score": freshness,
                "confidence_score": confidence,
                "temporal_risk_score": temporal_risk,
                "recheck_interval_days": recheck_days,
                "search_query": claim.suggested_search_query,
                "explanation": f"{explanation} ({vol_reason})",
                "evidence_summary": analysis.evidence_summary,
                "sources": formatted_sources,
            }

        # Run claim evaluations concurrently
        tasks = [
            _research_claim(c, vol, reason)
            for c, vol, reason in claims_with_volatility
        ]

        try:
            claims_results = await asyncio.gather(*tasks)
        except MissingCredentialsError as exc:
            # Tavily credentials missing
            self.repository.save_completed_run(
                run_id=run_id,
                overall_score=0.0,
                confidence_score=0.0,
                status=VerificationStatus.FAILED.value,
                report_summary=f"Verification failed: {exc.message}",
                claims_data=[],
                error_message=exc.message,
            )
            raise

        # 5. Compute overall scores and summary
        for res in claims_results:
            scores_for_overall.append((
                res["freshness_score"],
                res["confidence_score"],
                res["temporal_risk_score"],
                ClaimVolatility(res["volatility"]),
            ))

        overall_freshness, overall_confidence, overall_temporal_risk = self.scoring_service.calculate_overall_scores(
            scores_for_overall
        )

        # Determine run status (COMPLETED, PARTIAL, or FAILED)
        if partial_failures > 0 and partial_failures == len(claims_results):
            final_status = VerificationStatus.FAILED
        elif partial_failures > 0:
            final_status = VerificationStatus.PARTIAL
        else:
            final_status = VerificationStatus.COMPLETED

        # Construct report summary
        stale_count = sum(1 for c in claims_results if c["status"] == "POTENTIALLY_STALE")
        conflict_count = sum(1 for c in claims_results if c["status"] == "CONFLICTING_EVIDENCE")
        likely_count = sum(1 for c in claims_results if c["status"] == "LIKELY_CURRENT")
        unverified_count = sum(1 for c in claims_results if c["status"] == "UNVERIFIED")

        summary_parts = [
            f"Analyzed {len(claims_results)} factual claim(s) from the target answer.",
            f"Overall Freshness Score: {overall_freshness}/100 with {overall_confidence}% confidence.",
            f"Temporal Drift Risk: {overall_temporal_risk}/100.",
            f"Results: {likely_count} likely current, {stale_count} potentially stale, {conflict_count} conflicting, and {unverified_count} unverified.",
        ]
        if stale_count > 0:
            summary_parts.append("Caution: Some claims appear to reference outdated software, pricing, or figures.")
        if conflict_count > 0:
            summary_parts.append("Notice: Active discrepancies were detected between web sources.")

        report_summary = " ".join(summary_parts)

        # 6. Save completed verification to repository
        saved_run = self.repository.save_completed_run(
            run_id=run_id,
            overall_score=overall_freshness,
            confidence_score=overall_confidence,
            overall_temporal_risk=overall_temporal_risk,
            status=final_status.value,
            report_summary=report_summary,
            claims_data=claims_results,
            error_message="Some queries encountered search errors." if partial_failures > 0 else None,
        )

        return self._build_response(saved_run, claims_results)

    def _build_response(self, run_record, claims_data: List[dict]) -> VerificationResponse:
        """Build standard VerificationResponse from DB record and claim data."""
        claim_models = []
        # If run_record has claims loaded from DB relations, use them
        if hasattr(run_record, "claims") and run_record.claims:
            for c in run_record.claims:
                sources = [
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
                claim_models.append(
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
                        sources=sources,
                    )
                )
        else:
            for cd in claims_data:
                sources = [SourceResponse.model_validate(s) for s in cd.get("sources", [])]
                claim_models.append(
                    ClaimEvaluation(
                        id=cd["id"],
                        claim_text=cd["claim_text"],
                        claim_type=cd["claim_type"],
                        volatility=ClaimVolatility(cd["volatility"]),
                        status=ClaimStatus(cd["status"]),
                        freshness_score=cd["freshness_score"],
                        confidence_score=cd["confidence_score"],
                        temporal_risk_score=cd.get("temporal_risk_score", 50.0),
                        recheck_interval_days=cd.get("recheck_interval_days", 30),
                        search_query=cd["search_query"],
                        explanation=cd["explanation"],
                        evidence_summary=cd["evidence_summary"],
                        sources=sources,
                    )
                )

        return VerificationResponse(
            run_id=run_record.id,
            original_answer=run_record.original_answer,
            question=run_record.question,
            mode=VerificationMode(run_record.mode),
            status=VerificationStatus(run_record.status),
            overall_score=run_record.overall_score,
            confidence_score=run_record.confidence_score,
            overall_temporal_risk=getattr(run_record, "overall_temporal_risk", 50.0),
            total_claims=run_record.total_claims,
            likely_current_count=run_record.likely_current_count,
            potentially_stale_count=run_record.potentially_stale_count,
            conflicting_count=run_record.conflicting_count,
            unverified_count=run_record.unverified_count,
            not_time_sensitive_count=run_record.not_time_sensitive_count,
            report_summary=run_record.report_summary,
            error_message=run_record.error_message,
            created_at=run_record.created_at,
            completed_at=run_record.completed_at,
            claims=claim_models,
        )
