"""AI analysis API endpoints."""

from fastapi import APIRouter, HTTPException

from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.schemas.ai import PlaceAnalysisRequest, PlaceAnalysisResponse
from app.schemas.content import ContentMetadata
from app.services.place_analysis_service import PlaceAnalysisService

router = APIRouter()


@router.post("/analyze-place", response_model=PlaceAnalysisResponse)
async def analyze_place(request: PlaceAnalysisRequest) -> PlaceAnalysisResponse:
    """Analyze content and extract place information using AI."""
    analysis_service = PlaceAnalysisService()

    try:
        # Convert request to ContentMetadata for analysis service
        content = ContentMetadata(
            title=request.content_text,
            description=request.content_description,
            hashtags=request.hashtags,
            images=request.images,
        )

        # Analyze content
        response = await analysis_service.analyze_content(content, request.images)

        return response

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="AI service rate limit exceeded. Please try again later.",
        )
    except AIAnalysisError as e:
        raise HTTPException(
            status_code=503, detail=f"AI analysis service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during AI analysis: {str(e)}",
        )
