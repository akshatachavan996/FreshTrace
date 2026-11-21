"""Service for evaluating retrieved web evidence against extracted claims.

Performs heuristic assessments of relevance, domain credibility, recency,
support vs contradiction, and multi-source agreement.
"""

from datetime import datetime
import re
from typing import Dict, List, Optional, Set, Tuple
from app.core.logging import logger
from app.schemas.claim import ExtractedClaim
from app.schemas.source import SourceBase, SourceResponse


# Authoritative & high-credibility domain patterns
HIGH_CREDIBILITY_DOMAINS = {
    "python.org", "github.com", "developer.mozilla.org", "w3.org", "ietf.org",
    "docs.microsoft.com", "learn.microsoft.com", "cloud.google.com", "aws.amazon.com",
    "kubernetes.io", "react.dev", "nodejs.org", "wikipedia.org", "arxiv.org",
    "reuters.com", "apnews.com", "bloomberg.com", "wsj.com", "bbc.com", "nytimes.com",
    "nature.com", "science.org", "sec.gov", "who.int", "cdc.gov",
}

# TLDs carrying inherent institutional authority heuristics
HIGH_CREDIBILITY_TLDS = (".gov", ".edu", ".mil")

# Known low-credibility or aggregator domain indicators
LOW_CREDIBILITY_DOMAINS = {
    "quora.com", "reddit.com", "pinterest.com", "buzzfeed.com", "tiktok.com",
    "answers.com", "yahoo.com",
}

# Words indicating contradiction or state change
CONTRADICTION_INDICATORS = [
    r"\bno longer\b", r"\bdiscontinued\b", r"\breplaced by\b", r"\bsuperseded by\b",
    r"\bdeprecated\b", r"\bstepped down\b", r"\bresigned\b", r"\bincorrect\b",
    r"\bdebunked\b", r"\bformerly\b", r"\bwas previously\b", r"\bnot true\b",
    r"\bincreased to\b", r"\bdecreased to\b", r"\bchanged from\b", r"\bnow costs\b",
]

# Words indicating support or ongoing status
SUPPORT_INDICATORS = [
    r"\bconfirms\b", r"\bofficially\b", r"\breleased on\b", r"\bpriced at\b",
    r"\bcurrently serves as\b", r"\bis available\b", r"\bannounced that\b",
    r"\baccording to\b", r"\bestablished in\b",
]


class EvidenceAnalysisResult:
    """Encapsulates evidence evaluation for a single claim."""

    def __init__(
        self,
        evaluated_sources: List[SourceBase],
        support_count: int,
        contradict_count: int,
        inconclusive_count: int,
        independent_domains: int,
        has_recent_evidence: bool,
        evidence_summary: str,
        heuristic_reason: str,
    ):
        self.evaluated_sources = evaluated_sources
        self.support_count = support_count
        self.contradict_count = contradict_count
        self.inconclusive_count = inconclusive_count
        self.independent_domains = independent_domains
        self.has_recent_evidence = has_recent_evidence
        self.evidence_summary = evidence_summary
        self.heuristic_reason = heuristic_reason


class EvidenceService:
    """Evaluates relevance, credibility heuristics, and alignment of evidence."""

    @classmethod
    def evaluate_domain_credibility(cls, domain: str) -> str:
        """Assign a heuristic credibility rating to a source domain.

        Note: Credibility is a heuristic assessment, not an objective truth.
        """
        clean_domain = domain.lower().strip()
        if any(clean_domain.endswith(tld) for tld in HIGH_CREDIBILITY_TLDS):
            return "HIGH"
        for d in HIGH_CREDIBILITY_DOMAINS:
            if clean_domain == d or clean_domain.endswith("." + d):
                return "HIGH"
        for d in LOW_CREDIBILITY_DOMAINS:
            if clean_domain == d or clean_domain.endswith("." + d):
                return "LOW"
        return "MEDIUM"

    @classmethod
    def extract_year_from_text(cls, text: str) -> Optional[int]:
        """Extract recent 4-digit years (2000-2029) from text or dates."""
        matches = re.findall(r"\b(20[0-2][0-9])\b", text)
        if matches:
            # Return the highest (most recent) year found
            return max(int(m) for m in matches)
        return None

    @classmethod
    def analyze_source_alignment(
        cls,
        claim_text: str,
        source: SourceBase,
    ) -> Tuple[Optional[bool], float]:
        """Evaluate whether a single source snippet supports or contradicts the claim.

        Returns:
            Tuple of (supports_claim: Optional[bool], adjusted_relevance: float)
        """
        snippet_lower = (source.title + " " + source.snippet).lower()
        claim_lower = claim_text.lower()

        # Extract meaningful terms from claim (ignoring stop words)
        words = set(re.findall(r"\b[a-z0-9_-]{3,}\b", claim_lower))
        stop_words = {"the", "and", "that", "this", "with", "from", "for", "was", "were", "are", "been"}
        keywords = words - stop_words

        if not keywords:
            return None, source.relevance_score

        matched_keywords = sum(1 for kw in keywords if kw in snippet_lower)
        relevance_ratio = matched_keywords / max(len(keywords), 1)

        # If too few keywords match, the snippet is likely irrelevant
        if relevance_ratio < 0.25:
            return None, max(source.relevance_score * 0.5, 0.1)

        # Check for contradiction patterns
        has_contradiction = any(re.search(pat, snippet_lower) for pat in CONTRADICTION_INDICATORS)

        # Check for version/price discrepancies:
        # e.g., if claim mentions v3.10 and snippet mentions v3.12 or v3.13 as current
        claim_versions = re.findall(r"\bv?(\d+\.\d+(?:\.\d+)?)\b", claim_lower)
        snippet_versions = re.findall(r"\bv?(\d+\.\d+(?:\.\d+)?)\b", snippet_lower)
        if claim_versions and snippet_versions:
            # If snippet features a newer version associated with 'latest' or 'release'
            if any("latest" in snippet_lower or "release" in snippet_lower for _ in [1]):
                try:
                    c_ver = [int(p) for p in claim_versions[0].split(".")]
                    s_vers = [[int(p) for p in sv.split(".")] for sv in snippet_versions]
                    if any(sv > c_ver for sv in s_vers):
                        has_contradiction = True
                except (ValueError, IndexError):
                    pass

        if has_contradiction:
            return False, min(source.relevance_score + 0.15, 1.0)

        # Check for support indicators or strong keyword overlap
        has_support = any(re.search(pat, snippet_lower) for pat in SUPPORT_INDICATORS)
        if has_support or relevance_ratio >= 0.5:
            return True, min(source.relevance_score + 0.1, 1.0)

        return None, source.relevance_score

    def analyze_claim_evidence(
        self,
        claim: ExtractedClaim,
        sources: List[SourceBase],
    ) -> EvidenceAnalysisResult:
        """Perform comprehensive evidence evaluation across all retrieved sources for a claim."""
        if not sources:
            return EvidenceAnalysisResult(
                evaluated_sources=[],
                support_count=0,
                contradict_count=0,
                inconclusive_count=0,
                independent_domains=0,
                has_recent_evidence=False,
                evidence_summary="No live web sources were retrieved for this claim.",
                heuristic_reason="Insufficient evidence to verify freshness.",
            )

        evaluated: List[SourceBase] = []
        domains_seen: Set[str] = set()
        support_count = 0
        contradict_count = 0
        inconclusive_count = 0
        latest_year = 0

        for src in sources:
            # 1. Evaluate heuristic domain credibility
            credibility = self.evaluate_domain_credibility(src.domain)

            # 2. Evaluate support vs contradiction
            supports, adjusted_rel = self.analyze_source_alignment(claim.claim_text, src)

            # 3. Check recency
            date_str = src.published_date or ""
            year = self.extract_year_from_text(date_str) or self.extract_year_from_text(src.snippet)
            if year and year > latest_year:
                latest_year = year

            # Count evidence alignment
            if supports is True:
                support_count += 1
            elif supports is False:
                contradict_count += 1
            else:
                inconclusive_count += 1

            if src.domain:
                domains_seen.add(src.domain)

            updated_src = SourceBase(
                title=src.title,
                url=src.url,
                domain=src.domain,
                snippet=src.snippet,
                published_date=src.published_date,
                relevance_score=round(adjusted_rel, 2),
                credibility_heuristic=credibility,
                supports_claim=supports,
            )
            evaluated.append(updated_src)

        independent_domains = len(domains_seen)
        current_year = datetime.now().year
        has_recent = latest_year >= (current_year - 1)  # within last 1-2 years

        # Construct concise evidence summary
        summary_parts = []
        if support_count > 0:
            summary_parts.append(f"{support_count} source(s) support the statement.")
        if contradict_count > 0:
            summary_parts.append(f"{contradict_count} source(s) present conflicting or updated information.")
        if inconclusive_count > 0:
            summary_parts.append(f"{inconclusive_count} source(s) were inconclusive.")
        summary_parts.append(f"Retrieved from {independent_domains} independent domain(s).")
        if latest_year > 0:
            summary_parts.append(f"Most recent evidence year detected: {latest_year}.")

        reason = "Heuristic analysis completed across retrieved live sources."

        return EvidenceAnalysisResult(
            evaluated_sources=evaluated,
            support_count=support_count,
            contradict_count=contradict_count,
            inconclusive_count=inconclusive_count,
            independent_domains=independent_domains,
            has_recent_evidence=has_recent,
            evidence_summary=" ".join(summary_parts),
            heuristic_reason=reason,
        )
