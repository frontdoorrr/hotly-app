"""Link analysis endpoints."""
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.schemas.link import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.link_analyzer import LinkAnalyzerService

router = APIRouter()


@router.post("/", response_model=LinkAnalysisResponse)
async def analyze_link(request: LinkAnalysisRequest) -> LinkAnalysisResponse:
    """
    Analyze a URL and extract relevant information.

    Args:
        request: Link analysis request containing URL

    Returns:
        LinkAnalysisResponse with extracted information

    Raises:
        HTTPException: If URL analysis fails
    """
    try:
        analyzer = LinkAnalyzerService()
        result = await analyzer.analyze_url(request.url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze URL: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Check if the analyze endpoint is healthy."""
    return {"status": "ok", "endpoint": "analyze"}
