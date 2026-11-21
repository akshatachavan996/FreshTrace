"""Service for classifying claim volatility.

Categorizes claims into HIGH, MEDIUM, and LOW volatility to determine verification
priority and freshness decay sensitivity.
"""

import re
from typing import Tuple
from app.schemas.claim import ClaimVolatility


# Keyword and pattern matching heuristics for claim volatility
HIGH_VOLATILITY_KEYWORDS = [
    r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bfee\b", r"\bsubscription\b", r"\bper month\b",
    r"\bper year\b", r"\b\$\d+", r"\b€\d+", r"\b£\d+", r"\b₹\d+",
    r"\blatest\b", r"\bcurrent\b", r"\brecent\b", r"\bnow\b", r"\bpresently\b",
    r"\bversion\b", r"\bv\d+\.\d+", r"\brelease\b", r"\bupdate\b", r"\bdeprecated\b",
    r"\bceo\b", r"\bcto\b", r"\bcfo\b", r"\bleader\b", r"\bpresident\b", r"\bhead of\b",
    r"\bregulation\b", r"\blaw\b", r"\bpolicy\b", r"\btariff\b", r"\bbill\b", r"\bcompliance\b",
    r"\bstock\b", r"\bshares\b", r"\bmarket cap\b", r"\bvaluation\b", r"\bearnings\b",
    r"\bactive\b", r"\bavailable\b", r"\bdiscontinued\b", r"\blaunch\b", r"\brole\b",
]

LOW_VOLATILITY_KEYWORDS = [
    r"\bmathematics\b", r"\btheorem\b", r"\bformula\b", r"\bequation\b", r"\bphysics\b",
    r"\bgravity\b", r"\belement\b", r"\bperiodic table\b", r"\bspeed of light\b",
    r"\bconstant\b", r"\bdefinition\b", r"\betymology\b", r"\bdiscovered in 1\d{3}\b",
    r"\bfounded in 1\d{3}\b", r"\bborn in\b", r"\bdied in\b", r"\bworld war\b",
    r"\bancient\b", r"\bcentury\b", r"\bhistorical\b",
]

# Types categorized as HIGH volatility by default
HIGH_VOLATILITY_TYPES = {
    "pricing", "software versions", "company/person roles", "current events",
    "regulations", "availability", "policies"
}

# Types categorized as LOW volatility by default
LOW_VOLATILITY_TYPES = {
    "mathematics", "historical facts", "definitions", "scientific principles"
}


class VolatilityService:
    """Classifies how rapidly information in a claim is subject to change."""

    @classmethod
    def classify_volatility(
        cls,
        claim_text: str,
        claim_type: str = "Fact",
        initial_volatility: ClaimVolatility = ClaimVolatility.MEDIUM,
    ) -> Tuple[ClaimVolatility, str]:
        """Classify volatility of a claim statement.

        Returns:
            Tuple of (ClaimVolatility, explanation_reason)
        """
        lower_text = claim_text.lower()
        lower_type = claim_type.lower()

        # Check explicit high volatility types
        for high_type in HIGH_VOLATILITY_TYPES:
            if high_type in lower_type:
                return ClaimVolatility.HIGH, f"Claim type '{claim_type}' typically changes frequently."

        # Check explicit low volatility types
        for low_type in LOW_VOLATILITY_TYPES:
            if low_type in lower_type:
                return ClaimVolatility.LOW, f"Claim type '{claim_type}' is fundamentally stable over time."

        # Check regex keywords for HIGH volatility
        for pattern in HIGH_VOLATILITY_KEYWORDS:
            if re.search(pattern, lower_text):
                return (
                    ClaimVolatility.HIGH,
                    "Claim references rapidly changing factors (pricing, leadership, versioning, or current state).",
                )

        # Check regex keywords for LOW volatility
        for pattern in LOW_VOLATILITY_KEYWORDS:
            if re.search(pattern, lower_text):
                return (
                    ClaimVolatility.LOW,
                    "Claim references established historical, scientific, or mathematical fundamentals.",
                )

        # Look for past date indicators (e.g. "in 1995", "in 2008")
        past_year_match = re.search(r"\bin (18\d{2}|19\d{2}|200\d|201[0-9])\b", lower_text)
        if past_year_match:
            return (
                ClaimVolatility.LOW,
                f"Claim references a specific historical event/date ({past_year_match.group(0)}).",
            )

        # If model provided initial classification, respect it if sensible
        if initial_volatility == ClaimVolatility.HIGH:
            return ClaimVolatility.HIGH, "Model-indicated high volatility domain."
        if initial_volatility == ClaimVolatility.LOW:
            return ClaimVolatility.LOW, "Model-indicated low volatility domain."

        # Default to MEDIUM volatility
        return (
            ClaimVolatility.MEDIUM,
            "Claim describes specifications, product features, or statistics that evolve periodically.",
        )
