"""Integration tests for verification and history API endpoints."""

import pytest
from app.config import Settings
from app.schemas.claim import ExtractedClaim
from app.schemas.source import SourceBase
from app.services.claim_extraction_service import ClaimExtractionService
from app.services.tavily_service import TavilyService


def test_verify_empty_input(client):
    """Verify 422 Unprocessable Entity on empty answer_text."""
    response = client.post("/api/v1/verify", json={"answer_text": ""})
    assert response.status_code == 422


def test_verify_too_short_input(client):
    """Verify 422 Unprocessable Entity when input is less than 10 characters."""
    response = client.post("/api/v1/verify", json={"answer_text": "Too short"})
    assert response.status_code == 422


def test_verify_too_long_input(client):
    """Verify 422 Unprocessable Entity when input exceeds maximum character limit."""
    long_text = "a" * 10001
    response = client.post("/api/v1/verify", json={"answer_text": long_text})
    assert response.status_code == 422


def test_verify_full_pipeline_success(client, monkeypatch):
    """Verify complete end-to-end verification pipeline with mocked AI and Search services."""
    # Mock Claim Extraction
    async def mock_extract(self, answer_text, question=None):
        return [
            ExtractedClaim(
                claim_text="Python 3.12 is the latest major release.",
                claim_type="Software versions",
                suggested_search_query="Python 3.12 release date",
            )
        ]

    # Mock Tavily Search
    async def mock_search(self, query, search_depth="basic", max_results=None):
        return [
            SourceBase(
                title="Python 3.12 Details",
                url="https://docs.python.org/3/whatsnew/3.12.html",
                domain="python.org",
                snippet="Python 3.12 has been officially released.",
                published_date="2023-10-02",
                relevance_score=0.9,
            )
        ]

    monkeypatch.setattr(ClaimExtractionService, "extract_claims", mock_extract)
    monkeypatch.setattr(TavilyService, "search", mock_search)

    payload = {
        "answer_text": "Python 3.12 is currently the latest major stable release of Python.",
        "question": "What is the latest version of Python?",
        "mode": "DEEP_CHECK",
    }

    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["status"] in ("COMPLETED", "PARTIAL")
    assert data["total_claims"] == 1
    assert data["overall_score"] > 0
    assert len(data["claims"]) == 1
    claim = data["claims"][0]
    assert claim["claim_text"] == "Python 3.12 is the latest major release."
    assert len(claim["sources"]) == 1

    run_id = data["run_id"]

    # Test GET /api/v1/history
    hist_res = client.get("/api/v1/history")
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    assert len(history_items) >= 1
    assert any(item["id"] == run_id for item in history_items)

    # Test GET /api/v1/history/{run_id}
    detail_res = client.get(f"/api/v1/history/{run_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["run_id"] == run_id
    assert len(detail_data["claims"]) == 1

    # Test GET /api/v1/history/{run_id}/export
    export_res = client.get(f"/api/v1/history/{run_id}/export")
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["run_id"] == run_id
    assert "system_metadata" in export_data

    # Test DELETE /api/v1/history/{run_id}
    del_res = client.delete(f"/api/v1/history/{run_id}")
    assert del_res.status_code == 200

    # Ensure run is now 404
    detail_404 = client.get(f"/api/v1/history/{run_id}")
    assert detail_404.status_code == 404


def test_verify_missing_bifrost_credentials(client, monkeypatch):
    """Verify 503 Service Unavailable when Bifrost credentials are not configured."""
    unconfigured_settings = Settings(BIFROST_API_KEY="", TAVILY_API_KEY="test")
    from app.services.bifrost_service import BifrostService
    bifrost = BifrostService(settings=unconfigured_settings)

    # Let the service attempt to run with unconfigured settings
    from app.services.verification_service import VerificationService
    original_init = VerificationService.__init__

    def mock_init(self, repository, **kwargs):
        kwargs["settings"] = unconfigured_settings
        kwargs["bifrost_service"] = bifrost
        original_init(self, repository, **kwargs)

    monkeypatch.setattr(VerificationService, "__init__", mock_init)

    payload = {"answer_text": "Sample answer to verify for testing."}
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "MISSING_CREDENTIALS"
