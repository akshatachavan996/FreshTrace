"""Tests for claim volatility classification."""

import pytest
from app.schemas.claim import ClaimVolatility
from app.services.volatility_service import VolatilityService


def test_high_volatility_pricing():
    """Verify claims mentioning pricing are classified as HIGH volatility."""
    text = "The OpenAI API currently costs $20 per month for Plus subscribers."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Pricing")
    assert vol == ClaimVolatility.HIGH
    assert "changing" in reason or "Pricing" in reason


def test_high_volatility_software_version():
    """Verify claims referencing latest versions or releases are HIGH volatility."""
    text = "The latest stable release of Next.js is version 14.2."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Software versions")
    assert vol == ClaimVolatility.HIGH


def test_high_volatility_leadership():
    """Verify claims referencing current leadership/roles are HIGH volatility."""
    text = "Satya Nadella is the current CEO of Microsoft."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Company/person roles")
    assert vol == ClaimVolatility.HIGH


def test_low_volatility_historical():
    """Verify claims referencing established past history are LOW volatility."""
    text = "Python was first released by Guido van Rossum in 1991."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Historical facts")
    assert vol == ClaimVolatility.LOW


def test_low_volatility_mathematics():
    """Verify mathematical and scientific constants are LOW volatility."""
    text = "The speed of light in a vacuum is exactly 299,792,458 meters per second."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Fact")
    assert vol == ClaimVolatility.LOW


def test_medium_volatility_general():
    """Verify general specifications default to MEDIUM volatility."""
    text = "The camera sensor supports 4K video recording at 60fps."
    vol, reason = VolatilityService.classify_volatility(text, claim_type="Product features")
    assert vol == ClaimVolatility.MEDIUM
