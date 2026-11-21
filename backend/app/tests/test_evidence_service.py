"""Tests for EvidenceService credibility heuristics and source alignment."""

import pytest
from app.schemas.claim import ExtractedClaim
from app.schemas.source import SourceBase
from app.services.evidence_service import EvidenceService


def test_domain_credibility_heuristics():
    """Verify credibility rating heuristics for different domain types."""
    assert EvidenceService.evaluate_domain_credibility("docs.python.org") == "HIGH"
    assert EvidenceService.evaluate_domain_credibility("www.cdc.gov") == "HIGH"
    assert EvidenceService.evaluate_domain_credibility("stanford.edu") == "HIGH"
    assert EvidenceService.evaluate_domain_credibility("reuters.com") == "HIGH"
    assert EvidenceService.evaluate_domain_credibility("techcrunch.com") == "MEDIUM"
    assert EvidenceService.evaluate_domain_credibility("reddit.com") == "LOW"
    assert EvidenceService.evaluate_domain_credibility("quora.com") == "LOW"


def test_evidence_support_detection():
    """Verify that supportive snippet with keyword match returns True."""
    claim = ExtractedClaim(
        claim_text="FastAPI supports asynchronous request handling.",
        claim_type="Fact",
        suggested_search_query="FastAPI async request handling",
    )
    source = SourceBase(
        title="FastAPI Features",
        url="https://fastapi.tiangolo.com",
        domain="fastapi.tiangolo.com",
        snippet="FastAPI provides full native support for asynchronous request handling and concurrency.",
        relevance_score=0.9,
    )
    supports, rel = EvidenceService.analyze_source_alignment(claim.claim_text, source)
    assert supports is True


def test_evidence_contradiction_detection():
    """Verify that contradiction markers (discontinued, deprecated) return False."""
    claim = ExtractedClaim(
        claim_text="Google Podcasts is the primary podcast platform by Google.",
        claim_type="Current events",
        suggested_search_query="Google Podcasts active service",
    )
    source = SourceBase(
        title="Google Podcasts Shutdown",
        url="https://support.google.com/podcasts",
        domain="support.google.com",
        snippet="Google Podcasts has been discontinued and replaced by YouTube Music.",
        relevance_score=0.95,
    )
    supports, rel = EvidenceService.analyze_source_alignment(claim.claim_text, source)
    assert supports is False


def test_independent_domain_deduplication():
    """Verify that multiple articles from the same domain are counted as 1 independent domain."""
    service = EvidenceService()
    claim = ExtractedClaim(
        claim_text="Sample claim statement",
        claim_type="Fact",
        suggested_search_query="Sample query",
    )
    sources = [
        SourceBase(
            title="Article 1",
            url="https://reuters.com/news/1",
            domain="reuters.com",
            snippet="Report on sample claim.",
            relevance_score=0.8,
        ),
        SourceBase(
            title="Article 2",
            url="https://reuters.com/news/2",
            domain="reuters.com",
            snippet="Second report on sample claim.",
            relevance_score=0.8,
        ),
    ]

    analysis = service.analyze_claim_evidence(claim, sources)
    # 2 sources, but only 1 independent domain!
    assert len(analysis.evaluated_sources) == 2
    assert analysis.independent_domains == 1
