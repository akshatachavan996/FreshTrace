"""Application settings and configuration management using Pydantic Settings."""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "FreshTrace"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./freshtrace.db"

    # Bifrost AI Gateway Configuration
    # Bifrost can run locally (e.g. http://localhost:8080/v1) or via hosted endpoint
    BIFROST_BASE_URL: str = "http://localhost:8080/v1"
    BIFROST_API_KEY: str = ""
    AI_PROVIDER: str = "openai"  # openai, anthropic, google, etc.
    AI_MODEL: str = "gpt-4o-mini"

    # Tavily Web Search API Configuration
    TAVILY_API_KEY: str = ""
    TAVILY_BASE_URL: str = "https://api.tavily.com"

    # Verification Pipeline Settings
    CACHE_EXPIRATION_HOURS: int = 24
    MAX_SEARCH_RESULTS: int = 5
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    MAX_INPUT_LENGTH: int = 10000
    MIN_INPUT_LENGTH: int = 10

    @property
    def is_bifrost_configured(self) -> bool:
        """Returns True if Bifrost base URL and API key are set with valid non-placeholder values."""
        key = self.BIFROST_API_KEY.strip()
        if not key or "your_" in key.lower() or key == "placeholder":
            return False
        return bool(self.BIFROST_BASE_URL.strip())

    @property
    def is_tavily_configured(self) -> bool:
        """Returns True if Tavily API key is set with a valid non-placeholder value."""
        key = self.TAVILY_API_KEY.strip()
        if not key or "your_" in key.lower() or key == "placeholder":
            return False
        return True


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
