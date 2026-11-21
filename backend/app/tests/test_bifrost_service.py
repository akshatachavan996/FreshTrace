"""Tests for BifrostService and ClaimExtractionService."""

import pytest
import httpx
from app.config import Settings
from app.core.exceptions import BifrostError, ClaimExtractionError, MissingCredentialsError
from app.services.bifrost_service import BifrostService
from app.services.claim_extraction_service import ClaimExtractionService


@pytest.mark.asyncio
async def test_bifrost_missing_credentials():
    """Verify MissingCredentialsError is raised when Bifrost API key is not configured."""
    unconfigured_settings = Settings(
        BIFROST_BASE_URL="http://localhost:8080/v1",
        BIFROST_API_KEY="",
    )
    service = BifrostService(settings=unconfigured_settings)
    with pytest.raises(MissingCredentialsError):
        await service.chat_completion(messages=[{"role": "user", "content": "hello"}])


@pytest.mark.asyncio
async def test_bifrost_successful_call(monkeypatch, mock_settings):
    """Verify successful chat completion through Bifrost."""
    async def mock_post(self, url, json=None, headers=None):
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": '{"claims": []}'}}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    service = BifrostService(settings=mock_settings)
    result = await service.chat_completion(messages=[{"role": "user", "content": "extract"}])
    assert result == '{"claims": []}'


@pytest.mark.asyncio
async def test_bifrost_http_error(monkeypatch, mock_settings):
    """Verify BifrostError is raised on HTTP 500 error."""
    async def mock_post(self, url, json=None, headers=None):
        return httpx.Response(
            status_code=500,
            text="Gateway error: model unavailable",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    service = BifrostService(settings=mock_settings)
    with pytest.raises(BifrostError) as exc_info:
        await service.chat_completion(messages=[{"role": "user", "content": "hi"}])
    assert "HTTP 500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_claim_extraction_parsing(monkeypatch, mock_settings):
    """Verify JSON parsing and extraction into ExtractedClaim Pydantic models."""
    sample_json = """
    ```json
    {
      "claims": [
        {
          "claim_text": "Next.js 14 introduced Server Actions as stable.",
          "claim_type": "Software versions",
          "suggested_search_query": "Next.js 14 Server Actions stable release",
          "initial_volatility": "HIGH"
        }
      ]
    }
    ```
    """
    async def mock_chat(*args, **kwargs):
        return sample_json

    bifrost = BifrostService(settings=mock_settings)
    monkeypatch.setattr(bifrost, "chat_completion", mock_chat)

    extractor = ClaimExtractionService(bifrost_service=bifrost)
    claims = await extractor.extract_claims("Next.js 14 introduced Server Actions as stable.")

    assert len(claims) == 1
    assert claims[0].claim_text == "Next.js 14 introduced Server Actions as stable."
    assert claims[0].claim_type == "Software versions"
    assert claims[0].initial_volatility.value == "HIGH"


@pytest.mark.asyncio
async def test_claim_extraction_malformed_json(monkeypatch, mock_settings):
    """Verify ClaimExtractionError is raised on completely malformed model response."""
    async def mock_chat(*args, **kwargs):
        return "I am unable to answer this question in JSON format."

    bifrost = BifrostService(settings=mock_settings)
    monkeypatch.setattr(bifrost, "chat_completion", mock_chat)

    extractor = ClaimExtractionService(bifrost_service=bifrost)
    with pytest.raises(ClaimExtractionError):
        await extractor.extract_claims("Some input text.")
