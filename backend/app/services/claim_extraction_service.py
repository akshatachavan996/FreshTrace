"""Service for extracting independently verifiable claims from AI-generated text."""

import json
import re
from typing import List, Optional
import uuid

from app.core.exceptions import ClaimExtractionError, FreshTraceError, MissingCredentialsError
from app.core.logging import logger
from app.schemas.claim import ClaimVolatility, ExtractedClaim, ExtractedClaimList
from app.services.bifrost_service import BifrostService


EXTRACTION_SYSTEM_PROMPT = """You are FreshTrace's Claim Extraction Engine.
Your task is to analyze the provided AI-generated text and extract all independently verifiable, factual claims.

Extraction Guidelines:
1. Extract claims of these specific types:
   - Facts (concrete assertions about entities, history, or science)
   - Dates & Timelines
   - Statistics & Numerical measurements
   - Pricing & Fees (subscriptions, costs, plan tiers)
   - Software versions & API capabilities
   - Regulations & Legal policies
   - Roles (current CEO, leaders, affiliations)
   - Current events & Recent announcements
   - Product details (specifications, availability, features)

2. DO NOT extract:
   - Subjective opinions ("this tool is amazing", "it is easy to learn")
   - Pure conversational filler or greetings
   - Hedged or speculative predictions ("this might happen in 2030")

3. For each claim:
   - Provide a concise, self-contained statement of the claim (`claim_text`).
   - Specify the `claim_type`.
   - Provide an optimized search query (`suggested_search_query`) designed to locate recent, authoritative evidence.
   - Estimate initial volatility (`initial_volatility`: "HIGH", "MEDIUM", or "LOW").

Return ONLY a valid JSON object matching this exact schema:
{
  "claims": [
    {
      "claim_text": "Python 3.12 was released in October 2023.",
      "claim_type": "Software versions",
      "suggested_search_query": "Python 3.12 release date official python.org",
      "initial_volatility": "LOW"
    }
  ]
}
"""


class ClaimExtractionService:
    """Extracts factual claims using an AI model through Bifrost."""

    def __init__(self, bifrost_service: Optional[BifrostService] = None):
        self.bifrost_service = bifrost_service or BifrostService()

    async def extract_claims(
        self,
        answer_text: str,
        question: Optional[str] = None,
    ) -> List[ExtractedClaim]:
        """Extract verifiable claims from the answer text.

        Args:
            answer_text: The AI-generated answer.
            question: Optional context prompt that generated the answer.

        Returns:
            List of ExtractedClaim models.

        Raises:
            MissingCredentialsError: If Bifrost credentials are not configured.
            ClaimExtractionError: If extraction fails or response cannot be parsed.
        """
        user_prompt = f"Target Answer to Analyze:\n\"\"\"\n{answer_text}\n\"\"\""
        if question:
            user_prompt = f"Original Prompt/Question:\n{question}\n\n" + user_prompt

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info("Extracting claims via Bifrost AI Gateway...")
        try:
            raw_response = await self.bifrost_service.chat_completion(
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        except MissingCredentialsError:
            raise
        except Exception as exc:
            logger.error("Bifrost claim extraction failed: %s", exc)
            raise ClaimExtractionError(f"AI claim extraction failed: {str(exc)}") from exc

        return self._parse_claims_json(raw_response)

    def _parse_claims_json(self, raw_content: str) -> List[ExtractedClaim]:
        """Safely parse model output into structured claims."""
        cleaned = raw_content.strip()

        # Strip markdown fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # Attempt to find JSON object bounds
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    raise ClaimExtractionError(
                        f"Failed to parse JSON from AI response: {str(exc)}",
                        raw_response=raw_content,
                    )
            else:
                raise ClaimExtractionError(
                    f"Model response was not valid JSON: {str(exc)}",
                    raw_response=raw_content,
                )

        try:
            validated = ExtractedClaimList.model_validate(data)
            logger.info("Successfully extracted %d claims.", len(validated.claims))
            return validated.claims
        except Exception as exc:
            logger.error("Pydantic validation of claims failed: %s", exc)
            raise ClaimExtractionError(
                f"Extracted claims do not match expected schema: {str(exc)}",
                raw_response=raw_content,
            )
