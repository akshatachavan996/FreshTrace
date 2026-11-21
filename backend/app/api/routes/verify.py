"""Verification API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BifrostError,
    ClaimExtractionError,
    MissingCredentialsError,
    ProviderError,
    TavilyError,
)
from app.core.logging import logger
from app.database.repositories.verification_repo import VerificationRepository
from app.database.session import get_db
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/api/v1", tags=["Verification"])


@router.post(
    "/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify AI Answer Freshness",
    description="Extracts claims from an AI answer, researches the live web using Tavily, and evaluates freshness.",
)
async def verify_answer(
    request: VerificationRequest,
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """Verify an AI-generated answer for freshness, staleness, or conflicts."""
    repository = VerificationRepository(db)
    service = VerificationService(repository=repository)

    try:
        response = await service.verify_answer(request)
        return response

    except MissingCredentialsError as exc:
        logger.warning("Verification rejected due to missing credentials: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "MISSING_CREDENTIALS",
                "message": exc.message,
                "details": exc.details,
            },
        )
    except BifrostError as exc:
        logger.error("Bifrost gateway error during verification: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "BIFROST_PROVIDER_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )
    except TavilyError as exc:
        logger.error("Tavily search error during verification: %s", exc.message)
        status_code = status.HTTP_429_TOO_MANY_REQUESTS if exc.status_code == 429 else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "TAVILY_SEARCH_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )
    except ClaimExtractionError as exc:
        logger.error("Claim extraction error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "CLAIM_EXTRACTION_ERROR",
                "message": exc.message,
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error in verification route: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected verification error occurred: {str(exc)}",
            },
        )
