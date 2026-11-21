"""Transparent scoring service for FreshTrace.

Calculates independent Freshness (0-100), Confidence (0-100), and Temporal Risk (0-100) scores
along with recheck intervals based on evidence support, recency, domain credibility, and agreement.
"""

from typing import List, Tuple
from app.schemas.claim import ClaimStatus, ClaimVolatility
from app.services.evidence_service import EvidenceAnalysisResult


class ScoringService:
    """Calculates transparent freshness, confidence, and temporal risk scores.

    Scoring Formula Documentation:
    -------------------------------
    1. Freshness Score (0-100):
       Represents how strongly evidence indicates the claim reflects current truth.
       - Base score: 50 (neutral starting point).
       - Support Impact: +15 to +35 based on supporting sources weighted by domain credibility.
       - Contradiction Impact: -25 to -50 based on contradicting sources.
       - Recency Adjustment: +15 for recent evidence (last 1-2 years), -15 if high-volatility claim lacks recent evidence.
       - Multi-Source Consensus: +10 if 2+ independent domains agree without contradiction.
       - Special case: NOT_TIME_SENSITIVE claims default to 95 freshness.
       - Special case: Zero retrieved sources default to 0 freshness and UNVERIFIED status.

    2. Confidence Score (0-100):
       Represents the statistical robustness of our assessment, regardless of whether the claim is fresh or stale.
       - Source Volume: Up to 40 points based on number of relevant sources.
       - Domain Diversity: Up to 30 points for multiple independent domains (avoiding echo chambers).
       - Source Credibility: Up to 20 points from institutional or authoritative domains (.gov, .edu, official docs).
       - Ambiguity Penalty: -15 if sources directly conflict with each other without clear majority.

    3. Temporal Risk Score (0-100):
       Heuristic measure of how quickly this information is prone to decay or become obsolete.
       - Base volatility: HIGH = 50, MEDIUM = 30, LOW = 10.
       - Drift penalty: +35 if currently stale, +30 if conflicting, +25 if unverified, -15 if currently confirmed.
       - Recency penalty: +15 if high-volatility claim lacks evidence from the last 1-2 years.
       - Recheck Recommendation:
         * Temporal Risk >= 70: Recheck within 7 days.
         * Temporal Risk >= 40: Recheck within 30 days.
         * Temporal Risk < 40: Recheck within 180 days.
    """

    @classmethod
    def calculate_claim_scores(
        cls,
        volatility: ClaimVolatility,
        analysis: EvidenceAnalysisResult,
    ) -> Tuple[float, float, float, int, ClaimStatus, str]:
        """Calculate freshness score, confidence score, temporal risk, recheck days, status, and explanation.

        Returns:
            Tuple of (freshness_score, confidence_score, temporal_risk_score, recheck_days, status, explanation)
        """
        # Case A: Low volatility / not time sensitive
        if volatility == ClaimVolatility.LOW and analysis.contradict_count == 0:
            if analysis.support_count > 0 or len(analysis.evaluated_sources) == 0:
                return (
                    95.0,
                    85.0 if analysis.support_count > 0 else 70.0,
                    15.0,
                    180,
                    ClaimStatus.NOT_TIME_SENSITIVE,
                    "Claim is classified as Low Volatility (historical, mathematical, or scientific fundamental) with no conflicting evidence.",
                )

        # Case B: No sources retrieved / search returned nothing
        if not analysis.evaluated_sources:
            return (
                0.0,
                0.0,
                80.0 if volatility == ClaimVolatility.HIGH else 60.0,
                14 if volatility == ClaimVolatility.HIGH else 30,
                ClaimStatus.UNVERIFIED,
                "No live web evidence could be retrieved to verify or refute this claim.",
            )

        # --- Freshness Score Calculation ---
        score = 50.0  # Base

        # Support contribution
        for src in analysis.evaluated_sources:
            cred_weight = 1.0 if src.credibility_heuristic == "HIGH" else (0.7 if src.credibility_heuristic == "MEDIUM" else 0.4)
            if src.supports_claim is True:
                score += 15.0 * cred_weight
            elif src.supports_claim is False:
                score -= 30.0 * cred_weight

        # Recency impact
        if analysis.has_recent_evidence:
            score += 15.0
        elif volatility == ClaimVolatility.HIGH:
            score -= 15.0

        # Independent domain consensus bonus
        if analysis.independent_domains >= 2 and analysis.contradict_count == 0 and analysis.support_count >= 2:
            score += 10.0

        freshness_score = round(max(0.0, min(100.0, score)), 1)

        # --- Confidence Score Calculation ---
        confidence = 0.0
        source_count = len(analysis.evaluated_sources)
        confidence += min(source_count * 12.0, 40.0)
        confidence += min(analysis.independent_domains * 10.0, 30.0)
        high_cred = sum(1 for s in analysis.evaluated_sources if s.credibility_heuristic == "HIGH")
        confidence += min(high_cred * 10.0, 20.0)

        if analysis.support_count > 0 and analysis.contradict_count > 0:
            confidence = max(confidence - 15.0, 10.0)

        confidence_score = round(max(0.0, min(100.0, confidence)), 1)

        # --- Status Determination ---
        if analysis.support_count > 0 and analysis.contradict_count > 0:
            status = ClaimStatus.CONFLICTING_EVIDENCE
            explanation = (
                f"Conflicting evidence detected: {analysis.support_count} source(s) support while "
                f"{analysis.contradict_count} source(s) contradict the statement across {analysis.independent_domains} domain(s)."
            )
        elif analysis.contradict_count > 0:
            status = ClaimStatus.POTENTIALLY_STALE
            explanation = (
                f"Potential staleness: {analysis.contradict_count} source(s) provide updated or contradicting information. "
                "The claim likely reflects an outdated state."
            )
        elif analysis.support_count > 0 and freshness_score >= 70.0:
            status = ClaimStatus.LIKELY_CURRENT
            explanation = (
                f"Evidence indicates claim is current: {analysis.support_count} supporting source(s) found across "
                f"{analysis.independent_domains} independent domain(s)."
            )
        elif analysis.support_count > 0 and freshness_score < 70.0:
            status = ClaimStatus.POTENTIALLY_STALE
            explanation = (
                "Supporting sources were found, but lack recent verification timestamps for a high-volatility claim."
            )
        else:
            status = ClaimStatus.UNVERIFIED
            explanation = "Retrieved sources were inconclusive or did not contain sufficient factual overlap."

        # --- Temporal Risk Score Calculation ---
        base_risk = 50.0 if volatility == ClaimVolatility.HIGH else (30.0 if volatility == ClaimVolatility.MEDIUM else 10.0)
        if status == ClaimStatus.POTENTIALLY_STALE:
            base_risk += 35.0
        elif status == ClaimStatus.CONFLICTING_EVIDENCE:
            base_risk += 30.0
        elif status == ClaimStatus.UNVERIFIED:
            base_risk += 20.0
        elif status == ClaimStatus.LIKELY_CURRENT:
            base_risk -= 15.0

        if not analysis.has_recent_evidence and volatility in (ClaimVolatility.HIGH, ClaimVolatility.MEDIUM):
            base_risk += 15.0

        temporal_risk_score = round(max(5.0, min(95.0, base_risk)), 1)

        # Recheck interval recommendation (in days)
        if temporal_risk_score >= 70.0:
            recheck_days = 7
        elif temporal_risk_score >= 40.0:
            recheck_days = 30
        else:
            recheck_days = 180

        return freshness_score, confidence_score, temporal_risk_score, recheck_days, status, explanation

    @classmethod
    def calculate_overall_scores(
        cls,
        claims_scores: List[Tuple[float, float, float, ClaimVolatility]],
    ) -> Tuple[float, float, float]:
        """Compute weighted overall freshness, confidence, and temporal risk for the run.

        High-volatility claims are weighted higher (1.5x) than medium (1.0x) or low (0.5x).
        """
        if not claims_scores:
            return 0.0, 0.0, 50.0

        total_weight = 0.0
        weighted_freshness = 0.0
        weighted_confidence = 0.0
        weighted_risk = 0.0

        for freshness, confidence, risk, volatility in claims_scores:
            weight = 1.5 if volatility == ClaimVolatility.HIGH else (1.0 if volatility == ClaimVolatility.MEDIUM else 0.5)
            total_weight += weight
            weighted_freshness += freshness * weight
            weighted_confidence += confidence * weight
            weighted_risk += risk * weight

        overall_freshness = round(weighted_freshness / max(total_weight, 1.0), 1)
        overall_confidence = round(weighted_confidence / max(total_weight, 1.0), 1)
        overall_risk = round(weighted_risk / max(total_weight, 1.0), 1)

        return overall_freshness, overall_confidence, overall_risk
