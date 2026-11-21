"""Pydantic schemas for web search sources."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    """Base schema for a web evidence source."""

    title: str = Field(..., description="Page or article title")
    url: str = Field(..., description="Full canonical source URL")
    domain: str = Field(..., description="Extracted domain name, e.g. 'docs.python.org'")
    snippet: str = Field(..., description="Relevant text snippet or quote from the source")
    published_date: Optional[str] = Field(None, description="Published or last-updated date if available")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Heuristic relevance to the claim (0-1)")
    credibility_heuristic: str = Field(
        "MEDIUM",
        description="Heuristic assessment of domain credibility: HIGH, MEDIUM, LOW",
    )
    supports_claim: Optional[bool] = Field(
        None,
        description="Evidence assessment: True = supports claim, False = contradicts claim, None = inconclusive",
    )


class SourceCreate(SourceBase):
    """Schema for creating a source record."""

    id: Optional[str] = None


class SourceResponse(SourceBase):
    """Schema for returning source details to client."""

    id: str
    model_config = ConfigDict(from_attributes=True)
