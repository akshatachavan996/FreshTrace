"""Service for live web research using the Tavily Search API.

Retrieves authoritative web sources, snippets, and metadata with caching and rate limiting.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx

from app.config import Settings, get_settings
from app.core.exceptions import MissingCredentialsError, TavilyError
from app.core.logging import logger
from app.database.repositories.verification_repo import VerificationRepository
from app.schemas.source import SourceBase


class TavilyService:
    """Client for querying the Tavily Search API with caching."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        repository: Optional[VerificationRepository] = None,
    ):
        self.settings = settings or get_settings()
        self.repository = repository
        self.api_key = self.settings.TAVILY_API_KEY
        self.base_url = self.settings.TAVILY_BASE_URL.rstrip("/")
        self.timeout = self.settings.REQUEST_TIMEOUT_SECONDS
        self.max_results = self.settings.MAX_SEARCH_RESULTS

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain name from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            # Strip common 'www.'
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.lower()
        except Exception:
            return "unknown"

    def _get_cache_key(self, query: str) -> str:
        """Generate deterministic cache key for a search query."""
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: Optional[int] = None,
    ) -> List[SourceBase]:
        """Perform a live search query against Tavily.

        Args:
            query: The search query string.
            search_depth: "basic" or "advanced".
            max_results: Max items to return (defaults to config setting).

        Returns:
            List of SourceBase objects with retrieved evidence.

        Raises:
            MissingCredentialsError: If Tavily API key is not configured.
            TavilyError: If search fails, times out, or is rate-limited.
        """
        if not self.settings.is_tavily_configured:
            logger.warning("Tavily API key is not configured.")
            raise MissingCredentialsError("Tavily Search API", "TAVILY_API_KEY")

        limit = max_results or self.max_results
        cache_key = self._get_cache_key(f"{query}::{limit}::{search_depth}")

        # Check repository cache first if available
        if self.repository:
            cached_json = self.repository.get_cached_search(cache_key)
            if cached_json:
                logger.info("Retrieved search results from cache for query: '%s'", query)
                try:
                    cached_items = json.loads(cached_json)
                    return [SourceBase.model_validate(item) for item in cached_items]
                except Exception as exc:
                    logger.warning("Failed to deserialize cached search: %s", exc)

        url = f"{self.base_url}/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": False,
            "include_images": False,
            "max_results": limit,
        }

        logger.info("Executing live Tavily search for query: '%s'", query)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

            if response.status_code == 429:
                raise TavilyError("Tavily rate limit exceeded (HTTP 429).", status_code=429)

            if response.status_code != 200:
                raise TavilyError(
                    f"Tavily returned error status {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            raw_results = data.get("results", [])

            sources: List[SourceBase] = []
            for item in raw_results:
                src_url = item.get("url", "")
                if not src_url:
                    continue

                domain = self._extract_domain(src_url)
                relevance = float(item.get("score", 0.7))

                source = SourceBase(
                    title=item.get("title", "Untitled Source"),
                    url=src_url,
                    domain=domain,
                    snippet=item.get("content", ""),
                    published_date=item.get("published_date"),
                    relevance_score=min(max(relevance, 0.0), 1.0),
                    credibility_heuristic="MEDIUM",  # Computed later by evidence_service
                    supports_claim=None,
                )
                sources.append(source)

            # Cache results
            if self.repository and sources:
                try:
                    serialized = json.dumps([s.model_dump() for s in sources])
                    self.repository.set_cached_search(
                        cache_key=cache_key,
                        response_json=serialized,
                        hours=self.settings.CACHE_EXPIRATION_HOURS,
                    )
                except Exception as exc:
                    logger.warning("Failed to cache search results: %s", exc)

            logger.info("Tavily returned %d sources for query: '%s'", len(sources), query)
            return sources

        except httpx.ConnectError as exc:
            msg = "Could not connect to Tavily Search API. Check network connection."
            logger.error(msg)
            raise TavilyError(msg) from exc
        except httpx.TimeoutException as exc:
            msg = f"Tavily search request timed out after {self.timeout}s."
            logger.error(msg)
            raise TavilyError(msg) from exc
        except TavilyError:
            raise
        except Exception as exc:
            msg = f"Unexpected error during Tavily search: {str(exc)}"
            logger.error(msg)
            raise TavilyError(msg) from exc
