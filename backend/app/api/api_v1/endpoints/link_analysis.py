"""
Link analysis API endpoints with integrated caching.

Combines content extraction + AI analysis + caching for complete workflow.
Supports async processing, status tracking, and webhook notifications.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.exceptions.external import UnsupportedPlatformError
from app.schemas.link_analysis import (
    AnalysisResult,
    AnalysisStatus,
    AnalysisStatusResponse,
    BulkAnalyzeRequest,
    BulkAnalyzeResponse,
    LinkAnalyzeRequest,
    LinkAnalyzeResponse,
)
from app.services.monitoring.cache_manager import CacheKey, CacheManager
from app.services.places.content_extractor import ContentExtractor
from app.services.places.place_analysis_service import PlaceAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for analysis status (in production, use Redis/DB)
analysis_store: Dict[str, Dict] = {}


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
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        start_time = time.time()

        # Initialize cache manager
        await cache_manager.initialize()

        # Check cache first (unless force refresh)
        if not request.force_refresh:
            cache_key = CacheKey.link_analysis(str(request.url))
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                processing_time = time.time() - start_time
                logger.info(f"Cache hit for URL: {request.url}")

                # Store in analysis store for future retrieval
                analysis_store[analysis_id] = {
                    "status": AnalysisStatus.COMPLETED,
                    "result": cached_result,
                    "created_at": datetime.now(timezone.utc),
                    "url": str(request.url),
                    "cached": True,
                    "processing_time": processing_time,
                }

                return LinkAnalyzeResponse(
                    success=True,
                    analysis_id=analysis_id,
                    status=AnalysisStatus.COMPLETED,
                    result=AnalysisResult(**cached_result),
                    cached=True,
                    processing_time=processing_time,
                )

        logger.info(f"Cache miss for URL: {request.url}")

        # Store initial analysis status
        analysis_store[analysis_id] = {
            "status": AnalysisStatus.IN_PROGRESS,
            "url": str(request.url),
            "created_at": datetime.now(timezone.utc),
            "webhook_url": request.webhook_url,
            "cached": False,
            "progress": 0.1,
        }

        # If webhook provided, process asynchronously
        if request.webhook_url:
            background_tasks.add_task(
                _process_analysis_async, analysis_id, str(request.url), cache_manager
            )

            return LinkAnalyzeResponse(
                success=True,
                analysis_id=analysis_id,
                status=AnalysisStatus.IN_PROGRESS,
                result=None,
                cached=False,
                processing_time=time.time() - start_time,
            )

        # Process synchronously
        try:
            # Update progress
            analysis_store[analysis_id]["progress"] = 0.3

            # Extract content from URL
            content_extractor = ContentExtractor()
            content_data = await content_extractor.extract_content(str(request.url))

            analysis_store[analysis_id]["progress"] = 0.6

            # Analyze content with AI
            analysis_service = PlaceAnalysisService()

            # Convert content to metadata format for analysis
            from app.schemas.content import ContentMetadata

            content_metadata = ContentMetadata(
                title=content_data.metadata.title,
                description=content_data.metadata.description,
                images=content_data.metadata.images,
                hashtags=getattr(content_data, "hashtags", []),
            )

            # Perform AI analysis
            analysis_result = await analysis_service.analyze_content(
                content_metadata, content_data.metadata.images
            )

            if not analysis_result.success:
                analysis_store[analysis_id]["status"] = AnalysisStatus.FAILED
                analysis_store[analysis_id]["error"] = (
                    analysis_result.error or "AI analysis failed"
                )
                raise AIAnalysisError(analysis_result.error or "AI analysis failed")

            analysis_store[analysis_id]["progress"] = 0.9

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
                    "title": content_data.metadata.title,
                    "description": content_data.metadata.description,
                    "images": content_data.metadata.images[:3],  # Cache only first 3 images
                    "extraction_time": content_data.extraction_time,
                },
            }

            processing_time = time.time() - start_time

            # Update analysis store with result
            analysis_store[analysis_id].update(
                {
                    "status": AnalysisStatus.COMPLETED,
                    "result": result_data,
                    "processing_time": processing_time,
                    "progress": 1.0,
                }
            )

            # Cache the result (async in background)
            cache_key = CacheKey.link_analysis(str(request.url))
            cache_ttl = (
                3600 if analysis_result.confidence > 0.8 else 1800
            )  # Higher confidence = longer cache
            background_tasks.add_task(
                cache_manager.set, cache_key, result_data, cache_ttl
            )

            return LinkAnalyzeResponse(
                success=True,
                analysis_id=analysis_id,
                status=AnalysisStatus.COMPLETED,
                result=AnalysisResult(**result_data),
                cached=False,
                processing_time=processing_time,
            )

        except Exception as e:
            analysis_store[analysis_id].update(
                {
                    "status": AnalysisStatus.FAILED,
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                }
            )
            raise

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
        # Update analysis store if analysis_id exists
        if "analysis_id" in locals() and analysis_id in analysis_store:
            analysis_store[analysis_id].update(
                {"status": AnalysisStatus.FAILED, "error": str(e)}
            )
        raise HTTPException(
            status_code=500, detail="Internal server error during link analysis"
        )
    finally:
        await cache_manager.close()


@router.get("/analyses/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str, db: Session = Depends(get_db)
) -> AnalysisStatusResponse:
    """
    Get analysis status and result by ID.
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")

        analysis_data = analysis_store[analysis_id]

        # Calculate estimated completion for in-progress analyses
        estimated_completion = None
        if analysis_data["status"] == AnalysisStatus.IN_PROGRESS:
            # Estimate based on average processing time (30 seconds)
            estimated_completion = analysis_data["created_at"] + timedelta(seconds=30)

        response = AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=analysis_data["status"],
            progress=analysis_data.get("progress"),
            estimated_completion=estimated_completion,
            result=(
                AnalysisResult(**analysis_data["result"])
                if analysis_data.get("result")
                else None
            ),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analysis status"
        )


@router.delete("/analyses/{analysis_id}")
async def cancel_analysis(analysis_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Cancel ongoing analysis or clear cached result.
    """
    try:
        if analysis_id not in analysis_store:
            raise HTTPException(status_code=404, detail="Analysis not found")

        analysis_data = analysis_store[analysis_id]

        # Can only cancel pending or in-progress analyses
        if analysis_data["status"] in [
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel analysis with status: {analysis_data['status']}",
            )

        # Update status to cancelled
        analysis_store[analysis_id]["status"] = AnalysisStatus.CANCELLED

        # Clear from cache if it was cached
        if analysis_data.get("url"):
            cache_manager = CacheManager()
            try:
                await cache_manager.initialize()
                cache_key = CacheKey.link_analysis(analysis_data["url"])
                await cache_manager.invalidate(cache_key)
            except Exception as e:
                logger.warning(f"Failed to clear cache for {analysis_data['url']}: {e}")
            finally:
                await cache_manager.close()

        logger.info(f"Analysis cancelled: {analysis_id}")

        return {
            "success": True,
            "message": f"Analysis {analysis_id} cancelled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel analysis")


@router.post("/bulk-analyze", response_model=BulkAnalyzeResponse)
async def bulk_analyze_links(
    request: BulkAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> BulkAnalyzeResponse:
    """
    Analyze multiple URLs in batch.
    """
    batch_id = str(uuid.uuid4())
    accepted_urls = []
    rejected_urls = []

    # Validate URLs and separate accepted/rejected
    for url in request.urls:
        try:
            # Basic URL validation (additional validation can be added)
            if url.startswith(("http://", "https://")):
                accepted_urls.append(url)
            else:
                rejected_urls.append({"url": url, "reason": "Invalid URL format"})
        except Exception as e:
            rejected_urls.append({"url": url, "reason": str(e)})

    if not accepted_urls:
        raise HTTPException(
            status_code=400, detail="No valid URLs provided for analysis"
        )

    # Store batch info
    analysis_store[batch_id] = {
        "type": "batch",
        "status": AnalysisStatus.IN_PROGRESS,
        "urls": accepted_urls,
        "results": {},
        "created_at": datetime.now(timezone.utc),
        "webhook_url": request.webhook_url,
        "total_urls": len(accepted_urls),
        "completed": 0,
    }

    # Process URLs in background
    background_tasks.add_task(
        _process_batch_analysis, batch_id, accepted_urls, request.force_refresh
    )

    estimated_completion = datetime.now(timezone.utc) + timedelta(
        seconds=len(accepted_urls) * 30  # Estimate 30 seconds per URL
    )

    return BulkAnalyzeResponse(
        batch_id=batch_id,
        total_urls=len(accepted_urls),
        accepted_urls=accepted_urls,
        rejected_urls=rejected_urls,
        estimated_completion=estimated_completion,
    )


@router.get("/cache/stats")
async def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    cache_manager = CacheManager()

    try:
        await cache_manager.initialize()
        stats = await cache_manager.get_stats()

        return {
            "cache_hits": stats.cache_hits,
            "cache_misses": stats.cache_misses,
            "l1_hits": stats.l1_hits,
            "l2_hits": stats.l2_hits,
            "hit_rate": stats.hit_rate,
            "l1_hit_rate": stats.l1_hit_rate,
            "l2_hit_rate": stats.l2_hit_rate,
            "total_requests": stats.total_requests,
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "cache_hits": 0,
            "cache_misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "hit_rate": 0.0,
            "l1_hit_rate": 0.0,
            "l2_hit_rate": 0.0,
            "total_requests": 0,
            "error": "Stats unavailable",
        }
    finally:
        await cache_manager.close()


@router.get("/status")
async def get_service_status() -> dict:
    """Get service status and health check."""
    try:
        # Test cache connection
        cache_manager = CacheManager()
        await cache_manager.initialize()
        cache_healthy = True
        await cache_manager.close()
    except Exception:
        cache_healthy = False

    # Count active analyses
    active_analyses = len(
        [
            aid
            for aid, data in analysis_store.items()
            if data.get("status") == AnalysisStatus.IN_PROGRESS
        ]
    )

    return {
        "service": "Link Analysis API",
        "status": "healthy" if cache_healthy else "degraded",
        "cache_connection": cache_healthy,
        "active_analyses": active_analyses,
        "total_analyses": len(analysis_store),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Helper functions


async def _process_analysis_async(
    analysis_id: str, url: str, cache_manager: CacheManager
) -> None:
    """Process analysis asynchronously with webhook notification."""
    try:
        # Implementation similar to synchronous version
        # This is a simplified version - in production, use proper queue system

        analysis_store[analysis_id]["progress"] = 0.3

        # Extract content
        content_extractor = ContentExtractor()
        content_data = await content_extractor.extract_content(url)

        analysis_store[analysis_id]["progress"] = 0.6

        # AI analysis
        analysis_service = PlaceAnalysisService()
        from app.schemas.content import ContentMetadata

        content_metadata = ContentMetadata(
            title=content_data.metadata.title,
            description=content_data.metadata.description,
            images=content_data.metadata.images,
            hashtags=getattr(content_data, "hashtags", []),
        )

        analysis_result = await analysis_service.analyze_content(
            content_metadata, content_data.metadata.images
        )

        if not analysis_result.success:
            analysis_store[analysis_id].update(
                {
                    "status": AnalysisStatus.FAILED,
                    "error": analysis_result.error or "AI analysis failed",
                }
            )
            return

        # Prepare result
        result_data = {
            "place_info": (
                analysis_result.place_info.dict()
                if analysis_result.place_info
                else None
            ),
            "confidence": analysis_result.confidence,
            "analysis_time": analysis_result.analysis_time,
            "content_metadata": {
                "title": content_data.metadata.title,
                "description": content_data.metadata.description,
                "images": content_data.metadata.images[:3],
                "extraction_time": content_data.extraction_time,
            },
        }

        # Update analysis store
        analysis_store[analysis_id].update(
            {"status": AnalysisStatus.COMPLETED, "result": result_data, "progress": 1.0}
        )

        # Cache result
        cache_key = CacheKey.link_analysis(url)
        cache_ttl = 3600 if analysis_result.confidence > 0.8 else 1800
        await cache_manager.set(cache_key, result_data, cache_ttl)

        # Send webhook notification if configured
        webhook_url = analysis_store[analysis_id].get("webhook_url")
        if webhook_url:
            # In production, implement proper webhook delivery
            logger.info(f"Webhook notification would be sent to: {webhook_url}")

    except Exception as e:
        logger.error(f"Async analysis failed for {url}: {e}")
        analysis_store[analysis_id].update(
            {"status": AnalysisStatus.FAILED, "error": str(e)}
        )


async def _process_batch_analysis(
    batch_id: str, urls: list, force_refresh: bool = False
) -> None:
    """Process batch analysis in background."""
    try:
        cache_manager = CacheManager()
        await cache_manager.initialize()

        batch_data = analysis_store[batch_id]

        for i, url in enumerate(urls):
            try:
                # Create individual analysis for each URL
                url_analysis_id = str(uuid.uuid4())

                # Check cache first
                result_data = None
                if not force_refresh:
                    cache_key = CacheKey.link_analysis(url)
                    cached_result = await cache_manager.get(cache_key)
                    if cached_result:
                        result_data = cached_result

                # If not cached, perform analysis
                if not result_data:
                    content_extractor = ContentExtractor()
                    content_data = await content_extractor.extract_content(url)

                    analysis_service = PlaceAnalysisService()
                    from app.schemas.content import ContentMetadata

                    content_metadata = ContentMetadata(
                        title=content_data.metadata.title,
                        description=content_data.metadata.description,
                        images=content_data.metadata.images,
                        hashtags=getattr(content_data, "hashtags", []),
                    )

                    analysis_result = await analysis_service.analyze_content(
                        content_metadata, content_data.metadata.images
                    )

                    if analysis_result.success:
                        result_data = {
                            "place_info": (
                                analysis_result.place_info.dict()
                                if analysis_result.place_info
                                else None
                            ),
                            "confidence": analysis_result.confidence,
                            "analysis_time": analysis_result.analysis_time,
                            "content_metadata": {
                                "title": content_data.metadata.title,
                                "description": content_data.metadata.description,
                                "images": content_data.metadata.images[:3],
                                "extraction_time": content_data.extraction_time,
                            },
                        }

                        # Cache result
                        cache_key = CacheKey.link_analysis(url)
                        cache_ttl = 3600 if analysis_result.confidence > 0.8 else 1800
                        await cache_manager.set(cache_key, result_data, cache_ttl)

                # Store result in batch
                batch_data["results"][url] = {
                    "success": True,
                    "analysis_id": url_analysis_id,
                    "result": result_data,
                }

            except Exception as e:
                logger.error(f"Failed to analyze URL {url} in batch {batch_id}: {e}")
                batch_data["results"][url] = {"success": False, "error": str(e)}

            # Update progress
            batch_data["completed"] = i + 1

        # Mark batch as completed
        batch_data["status"] = AnalysisStatus.COMPLETED

        # Send webhook notification if configured
        webhook_url = batch_data.get("webhook_url")
        if webhook_url:
            logger.info(f"Batch webhook notification would be sent to: {webhook_url}")

        await cache_manager.close()

    except Exception as e:
        logger.error(f"Batch analysis failed for {batch_id}: {e}")
        if batch_id in analysis_store:
            analysis_store[batch_id].update(
                {"status": AnalysisStatus.FAILED, "error": str(e)}
            )
