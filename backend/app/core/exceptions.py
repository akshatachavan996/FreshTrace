"""Custom exception classes for FreshTrace.

Differentiates between missing credentials, provider outages, validation issues,
and missing resources.
"""


class FreshTraceError(Exception):
    """Base exception for all FreshTrace domain errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MissingCredentialsError(FreshTraceError):
    """Raised when an API key or configuration required for live operation is missing."""

    def __init__(self, provider: str, env_var: str):
        message = f"Missing credentials for {provider}. Please set {env_var} in your .env file."
        super().__init__(message, details={"provider": provider, "env_var": env_var})


class ProviderError(FreshTraceError):
    """Raised when an external service (Bifrost, Tavily) fails or returns an error status."""

    def __init__(self, provider: str, message: str, status_code: int | None = None):
        super().__init__(
            f"{provider} error: {message}",
            details={"provider": provider, "status_code": status_code, "raw_message": message},
        )
        self.provider = provider
        self.status_code = status_code


class BifrostError(ProviderError):
    """Raised when the Bifrost AI Gateway encounters an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(provider="Bifrost", message=message, status_code=status_code)


class TavilyError(ProviderError):
    """Raised when Tavily search fails or is rate-limited."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(provider="Tavily", message=message, status_code=status_code)


class ClaimExtractionError(FreshTraceError):
    """Raised when AI claim extraction fails or produces unparseable output."""

    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message, details={"raw_response": raw_response})


class NotFoundError(FreshTraceError):
    """Raised when a requested resource (such as a verification run) is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(f"{resource_type} with ID '{resource_id}' was not found.")
        self.resource_type = resource_type
        self.resource_id = resource_id
