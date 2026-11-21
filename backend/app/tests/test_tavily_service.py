"""Tests for TavilyService web search and caching."""

import pytest
import httpx
from app.config import Settings
from app.core.exceptions import MissingCredentialsError, TavilyError
from app.database.repositories.verification_repo import VerificationRepository
from app.services.tavily_service import TavilyService


@pytest.mark.asyncio
async def test_tavily_missing_credentials():
    """Verify MissingCredentialsError when TAVILY_API_KEY is not set."""
    unconfigured = Settings(TAVILY_API_KEY="")
    service = TavilyService(settings=unconfigured)
    with pytest.raises(MissingCredentialsError):
        await service.search("Python 3.12 release date")


@pytest.mark.asyncio
async def test_tavily_successful_search(monkeypatch, mock_settings):
    """Verify parsing of successful Tavily search response."""
    async def mock_post(self, url, json=None, headers=None):
        return httpx.Response(
            status_code=200,
            json={
                "results": [
                    {
                        "title": "Python 3.12 Release Schedule",
                        "url": "https://docs.python.org/3/whatsnew/3.12.html",
                        "content": "Python 3.12 was officially released in October 2023.",
                        "score": 0.95,
                        "published_date": "2023-10-02",
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    service = TavilyService(settings=mock_settings)
    sources = await service.search("Python 3.12 release")

    assert len(sources) == 1
    assert sources[0].title == "Python 3.12 Release Schedule"
    assert sources[0].domain == "docs.python.org"
    assert sources[0].relevance_score == 0.95
    assert sources[0].published_date == "2023-10-02"


@pytest.mark.asyncio
async def test_tavily_rate_limit_error(monkeypatch, mock_settings):
    """Verify TavilyError with status_code 429 when rate limit is hit."""
    async def mock_post(self, url, json=None, headers=None):
        return httpx.Response(
            status_code=429,
            text="Monthly request limit exceeded.",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    service = TavilyService(settings=mock_settings)
    with pytest.raises(TavilyError) as exc_info:
        await service.search("some query")
    assert exc_info.value.status_code == 429
    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tavily_caching(monkeypatch, mock_settings, db_session):
    """Verify that subsequent searches for identical query are served from cache."""
    repo = VerificationRepository(db_session)
    call_count = 0

    async def mock_post(self, url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            status_code=200,
            json={
                "results": [
                    {
                        "title": "Cached Result",
                        "url": "https://example.com/cached",
                        "content": "Snippet content",
                        "score": 0.8,
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    service = TavilyService(settings=mock_settings, repository=repo)

    # First call - queries API and populates cache
    results_1 = await service.search("cached query")
    assert call_count == 1
    assert len(results_1) == 1

    # Second call - should hit repository cache without incrementing API calls
    results_2 = await service.search("cached query")
    assert call_count == 1
    assert len(results_2) == 1
    assert results_2[0].url == "https://example.com/cached"
