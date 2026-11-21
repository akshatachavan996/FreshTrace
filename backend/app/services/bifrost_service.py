"""Service for communicating with the Bifrost AI Gateway.

Provides a standardized, robust interface for calling AI models through Bifrost,
handling authentication, timeouts, and error formatting.
"""

from typing import Any, Dict, List, Optional
import httpx

from app.config import Settings, get_settings
from app.core.exceptions import BifrostError, MissingCredentialsError
from app.core.logging import logger


class BifrostService:
    """Client for the Bifrost AI Gateway."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.BIFROST_BASE_URL.rstrip("/")
        self.api_key = self.settings.BIFROST_API_KEY
        self.provider = self.settings.AI_PROVIDER
        self.model = self.settings.AI_MODEL
        self.timeout = self.settings.REQUEST_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers for Bifrost."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            # Some Bifrost setups also accept custom provider headers
            headers["x-bifrost-provider"] = self.provider
        return headers

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call the Bifrost chat completions endpoint.

        Args:
            messages: List of chat messages with 'role' and 'content'.
            temperature: Sampling temperature (0.0 for deterministic factual tasks).
            max_tokens: Maximum tokens in response.
            response_format: Optional JSON schema / format enforcement.

        Returns:
            The raw string content returned by the assistant.

        Raises:
            MissingCredentialsError: If Bifrost credentials are not configured.
            BifrostError: If Bifrost returns an error or cannot be reached.
        """
        if not self.settings.is_bifrost_configured:
            logger.warning("Bifrost credentials are not configured in environment.")
            raise MissingCredentialsError("Bifrost AI Gateway", "BIFROST_API_KEY")

        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        logger.info("Sending chat completion request to Bifrost at %s for model %s", url, self.model)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._get_headers())

            if response.status_code != 200:
                error_msg = f"Bifrost returned HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise BifrostError(message=error_msg, status_code=response.status_code)

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise BifrostError("Bifrost response contained no choices.")

            content = choices[0].get("message", {}).get("content", "")
            return content.strip()

        except httpx.ConnectError as exc:
            msg = f"Failed to connect to Bifrost gateway at {self.base_url}. Ensure Bifrost is running."
            logger.error("%s: %s", msg, str(exc))
            raise BifrostError(msg) from exc
        except httpx.TimeoutException as exc:
            msg = f"Request to Bifrost gateway timed out after {self.timeout}s."
            logger.error(msg)
            raise BifrostError(msg) from exc
        except BifrostError:
            raise
        except Exception as exc:
            msg = f"Unexpected error during Bifrost request: {str(exc)}"
            logger.error(msg)
            raise BifrostError(msg) from exc

    async def check_health(self) -> Dict[str, Any]:
        """Check the operational health of the Bifrost gateway."""
        if not self.settings.is_bifrost_configured:
            return {
                "status": "unconfigured",
                "configured": False,
                "message": "BIFROST_API_KEY is not configured.",
            }

        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code in (200, 204):
                    return {"status": "healthy", "configured": True, "base_url": self.base_url}
                return {
                    "status": "unhealthy",
                    "configured": True,
                    "code": res.status_code,
                    "message": f"HTTP {res.status_code}",
                }
        except Exception as exc:
            return {
                "status": "unreachable",
                "configured": True,
                "base_url": self.base_url,
                "error": str(exc),
            }
