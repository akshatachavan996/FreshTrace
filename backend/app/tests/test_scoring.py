"""Tests for freshness scoring, confidence scoring, and temporal risk logic."""

import pytest
from app.schemas.claim import ClaimStatus, ClaimVolatility
from app.schemas.source import SourceBase
from app.services.evidence_service import EvidenceAnalysisResult
from app.services.scoring_service import ScoringService


def test_zero_sources_unverified():
    """Verify that claims with zero retrieved sources are scored 0 and marked UNVERIFIED."""
    empty_analysis = EvidenceAnalysisResult(
        evaluated_sources=[],
        support_count=0,
        contradict_count=0,
        inconclusive_count=0,
        independent_domains=0,
        has_recent_evidence=False,
        evidence_summary="No sources found.",
        heuristic_reason="Insufficient evidence.",
    )

    freshness, confidence, risk, recheck, status, exp = ScoringService.calculate_claim_scores(
        volatility=ClaimVolatility.HIGH,
        analysis=empty_analysis,
    )

    assert freshness == 0.0
    assert confidence == 0.0
    assert risk >= 70.0
    assert status == ClaimStatus.UNVERIFIED


def test_low_volatility_not_time_sensitive():
    """Verify that low volatility claims with no contradictions receive NOT_TIME_SENSITIVE."""
    analysis = EvidenceAnalysisResult(
        evaluated_sources=[],
        support_count=0,
        contradict_count=0,
        inconclusive_count=0,
        independent_domains=0,
        has_recent_evidence=False,
        evidence_summary="Fundamental fact.",
        heuristic_reason="Stable truth.",
    )

    freshness, confidence, risk, recheck, status, exp = ScoringService.calculate_claim_scores(
        volatility=ClaimVolatility.LOW,
        analysis=analysis,
    )

    assert freshness == 95.0
    assert confidence == 70.0
    assert risk <= 20.0
    assert recheck >= 180
    assert status == ClaimStatus.NOT_TIME_SENSITIVE


def test_supporting_evidence_likely_current():
    """Verify that consistent supporting evidence produces high freshness and LIKELY_CURRENT."""
    sources = [
        SourceBase(
            title="Official Documentation",
            url="https://docs.python.org/3/whatsnew/3.12.html",
            domain="python.org",
            snippet="Python 3.12 is the newest major release.",
            published_date="2024-01-15",
            relevance_score=0.95,
            credibility_heuristic="HIGH",
            supports_claim=True,
        ),
        SourceBase(
            title="Tech News Python 3.12",
            url="https://arstechnica.com/gadgets/python-3-12",
            domain="arstechnica.com",
            snippet="The Python foundation announced Python 3.12.",
            published_date="2024-02-01",
            relevance_score=0.85,
            credibility_heuristic="MEDIUM",
            supports_claim=True,
        ),
    ]

    analysis = EvidenceAnalysisResult(
        evaluated_sources=sources,
        support_count=2,
        contradict_count=0,
        inconclusive_count=0,
        independent_domains=2,
        has_recent_evidence=True,
        evidence_summary="2 sources support.",
        heuristic_reason="Multi-source confirmation.",
    )

    freshness, confidence, risk, recheck, status, exp = ScoringService.calculate_claim_scores(
        volatility=ClaimVolatility.MEDIUM,
        analysis=analysis,
    )

    assert freshness >= 75.0
    assert confidence >= 50.0
    assert status == ClaimStatus.LIKELY_CURRENT


def test_contradicting_evidence_potentially_stale():
    """Verify that contradictory evidence significantly lowers freshness and marks POTENTIALLY_STALE."""
    sources = [
        SourceBase(
            title="Pricing Update",
            url="https://openai.com/pricing",
            domain="openai.com",
            snippet="Pricing has been discontinued and replaced with new enterprise tiers.",
            published_date="2024-08-01",
            relevance_score=0.9,
            credibility_heuristic="HIGH",
            supports_claim=False,
        )
    ]

    analysis = EvidenceAnalysisResult(
        evaluated_sources=sources,
        support_count=0,
        contradict_count=1,
        inconclusive_count=0,
        independent_domains=1,
        has_recent_evidence=True,
        evidence_summary="Contradictory evidence found.",
        heuristic_reason="Pricing has changed.",
    )

    freshness, confidence, risk, recheck, status, exp = ScoringService.calculate_claim_scores(
        volatility=ClaimVolatility.HIGH,
        analysis=analysis,
    )

    assert freshness < 50.0
    assert risk >= 70.0
    assert recheck == 7
    assert status == ClaimStatus.POTENTIALLY_STALE


def test_conflicting_evidence_detected():
    """Verify that mixed supporting and contradicting sources trigger CONFLICTING_EVIDENCE."""
    sources = [
        SourceBase(
            title="Old Article",
            url="https://example.com/a",
            domain="example.com",
            snippet="The service is free.",
            relevance_score=0.8,
            credibility_heuristic="MEDIUM",
            supports_claim=True,
        ),
        SourceBase(
            title="New Announcement",
            url="https://other.com/b",
            domain="other.com",
            snippet="The service is no longer free.",
            relevance_score=0.85,
            credibility_heuristic="MEDIUM",
            supports_claim=False,
        ),
    ]

    analysis = EvidenceAnalysisResult(
        evaluated_sources=sources,
        support_count=1,
        contradict_count=1,
        inconclusive_count=0,
        independent_domains=2,
        has_recent_evidence=False,
        evidence_summary="1 supports, 1 contradicts.",
        heuristic_reason="Mixed reports.",
    )

    freshness, confidence, risk, recheck, status, exp = ScoringService.calculate_claim_scores(
        volatility=ClaimVolatility.HIGH,
        analysis=analysis,
    )

    assert status == ClaimStatus.CONFLICTING_EVIDENCE
    assert "Conflicting evidence" in exp


def test_overall_weighted_scoring():
    """Verify that overall score weights high volatility claims more heavily than low."""
    # (freshness, confidence, temporal_risk, volatility)
    claims = [
        (20.0, 80.0, 85.0, ClaimVolatility.HIGH),  # Stale high-volatility claim
        (100.0, 90.0, 15.0, ClaimVolatility.LOW),  # Fresh low-volatility claim
    ]
    overall_freshness, overall_confidence, overall_risk = ScoringService.calculate_overall_scores(claims)

    # High weight = 1.5, Low weight = 0.5. Total = 2.0.
    # Weighted freshness = (20 * 1.5 + 100 * 0.5) / 2.0 = (30 + 50) / 2 = 40.0
    assert overall_freshness == 40.0
    assert overall_confidence > 0
    assert overall_risk > 0
