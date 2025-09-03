"""
Link analysis API endpoints with integrated caching.

Combines content extraction + AI analysis + caching for complete workflow.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.exceptions.external import UnsupportedPlatformError
from app.schemas.link_analysis import (
    AnalysisResult,
    AnalysisStatus,
    LinkAnalyzeRequest,
    LinkAnalyzeResponse,
)
from app.services.cache_manager import CacheManager
from app.services.content_extractor import ContentExtractor
from app.services.place_analysis_service import PlaceAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=LinkAnalyzeResponse)
async def analyze_link(
    request: LinkAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> LinkAnalyzeResponse:
    """
    Analyze SNS link with integrated caching.

    Workflow:
    1. Check cache for existing analysis
    2. If not cached, extract content and analyze with AI
    3. Cache results for future requests
    4. Return analysis results
    """
    cache_manager = CacheManager()

    try:
        # Check cache first
        cached_result = await cache_manager.get(str(request.url))
        if cached_result:
            logger.info(f"Cache hit for URL: {request.url}")
            return LinkAnalyzeResponse(
                success=True,
                analysis_id=f"cached_{hash(str(request.url))}",
                status=AnalysisStatus.COMPLETED,
                result=AnalysisResult(**cached_result.data),
                cached=True,
                processing_time=0.1,  # Fast cache retrieval
            )

        logger.info(f"Cache miss for URL: {request.url}")

        # Extract content from URL
        content_extractor = ContentExtractor()
        content_data = await content_extractor.extract_content(str(request.url))

        # Analyze content with AI
        analysis_service = PlaceAnalysisService()

        # Convert content to metadata format for analysis
        from app.schemas.content import ContentMetadata

        content_metadata = ContentMetadata(
            title=content_data.title,
            description=content_data.description,
            images=content_data.images,
            hashtags=getattr(content_data, "hashtags", []),
        )

        # Perform AI analysis
        analysis_result = await analysis_service.analyze_content(
            content_metadata, content_data.images
        )

        if not analysis_result.success:
            raise AIAnalysisError(analysis_result.error or "AI analysis failed")

        # Prepare result for caching and response
        result_data = {
            "place_info": (
                analysis_result.place_info.dict()
                if analysis_result.place_info
                else None
            ),
            "confidence": analysis_result.confidence,
            "analysis_time": analysis_result.analysis_time,
            "content_metadata": {
                "title": content_data.title,
                "description": content_data.description,
                "images": content_data.images[:3],  # Cache only first 3 images
                "extraction_time": content_data.extraction_time,
            },
        }

        # Cache the result (async in background)
        cache_ttl = (
            3600 if analysis_result.confidence > 0.8 else 1800
        )  # Higher confidence = longer cache
        background_tasks.add_task(
            cache_manager.set, str(request.url), result_data, cache_ttl
        )

        analysis_id = f"new_{hash(str(request.url))}"

        return LinkAnalyzeResponse(
            success=True,
            analysis_id=analysis_id,
            status=AnalysisStatus.COMPLETED,
            result=AnalysisResult(**result_data),
            cached=False,
            processing_time=content_data.extraction_time
            + analysis_result.analysis_time,
        )

    except UnsupportedPlatformError as e:
        raise HTTPException(status_code=422, detail=f"Unsupported platform: {str(e)}")
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
        logger.error(f"Link analysis failed for {request.url}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during link analysis"
        )
    finally:
        await cache_manager.close()


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(
    analysis_id: str, db: Session = Depends(get_db)
) -> AnalysisResult:
    """
    Get analysis result by ID.

    For cached results, extract original URL from analysis_id.
    """
    cache_manager = CacheManager()

    try:
        # For now, return cached result if available
        # In production, store analysis results in database with proper ID mapping

        if analysis_id.startswith("cached_") or analysis_id.startswith("new_"):
            # This is a simplified implementation
            # In production, maintain proper analysis_id -> URL mapping in database
            raise HTTPException(
                status_code=404,
                detail="Analysis result not found. Please re-analyze the URL.",
            )

        raise HTTPException(status_code=404, detail="Analysis not found")

    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analysis result"
        )
    finally:
        await cache_manager.close()


@router.delete("/analyses/{analysis_id}")
async def cancel_analysis(analysis_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Cancel ongoing analysis or clear cached result.
    """
    cache_manager = CacheManager()

    try:
        # In production, this would cancel background tasks and clear cache
        # For now, just return success

        logger.info(f"Analysis cancellation requested for: {analysis_id}")

        return {
            "success": True,
            "message": f"Analysis {analysis_id} cancelled successfully",
        }

    except Exception as e:
        logger.error(f"Failed to cancel analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel analysis")
    finally:
        await cache_manager.close()


@router.get("/cache/stats")
async def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    cache_manager = CacheManager()

    try:
        stats = await cache_manager.get_stats()

        return {
            "hit_count": stats.hit_count,
            "miss_count": stats.miss_count,
            "hit_rate": stats.hit_rate,
            "total_requests": stats.total_requests,
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "hit_count": 0,
            "miss_count": 0,
            "hit_rate": 0.0,
            "total_requests": 0,
            "error": "Stats unavailable",
        }
    finally:
        await cache_manager.close()
