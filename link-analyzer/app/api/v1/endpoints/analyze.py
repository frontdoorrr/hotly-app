"""Link analysis endpoints."""

import os
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisError,
    Platform,
    ContentType,
    VideoAnalysis,
    ImageAnalysis,
    ClassificationResult
)
from app.services.link_analyzer_service import LinkAnalyzerService

router = APIRouter()


def get_analyzer_service() -> LinkAnalyzerService:
    """Get configured analyzer service instance."""
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: Missing API keys"
        )

    return LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key,
        download_dir="temp"
    )


@router.post("/", response_model=AnalysisResponse, responses={
    400: {"model": AnalysisError, "description": "Invalid URL or unsupported platform"},
    500: {"model": AnalysisError, "description": "Server error during analysis"}
})
async def analyze_link(
    request: AnalysisRequest,
    analyzer: LinkAnalyzerService = Depends(get_analyzer_service)
) -> AnalysisResponse:
    """
    Analyze a social media URL and extract comprehensive information.

    Supports:
    - **YouTube**: Direct URL analysis (no download), Shorts support
    - **Instagram**: Video/image/carousel analysis with yt-dlp
    - **TikTok**: Video analysis with yt-dlp

    Processing pipeline:
    1. Platform detection
    2. Metadata extraction (title, description, hashtags)
    3. Gemini video/image analysis (transcription, OCR, scene understanding)
    4. AI content classification (category, confidence, extracted info)

    Args:
        request: Analysis request with URL and optional settings

    Returns:
        Comprehensive analysis result including:
        - Platform and content type
        - Metadata (title, description, hashtags)
        - Video analysis (transcript, OCR, visual elements)
        - Image analysis (OCR, objects, scene)
        - AI classification (category, place info, menu items, confidence)

    Raises:
        HTTPException 400: Invalid URL or unsupported platform
        HTTPException 500: Server error during analysis

    Example:
        ```json
        {
            "url": "https://www.youtube.com/watch?v=xxx"
        }
        ```

    Response:
        ```json
        {
            "url": "https://...",
            "platform": "youtube",
            "content_type": "video",
            "title": "Video Title",
            "classification": {
                "primary_category": "음식점",
                "confidence": 0.95
            }
        }
        ```
    """
    try:
        # Analyze URL with integrated service
        result = await analyzer.analyze(str(request.url), request.options)

        # Map to response schema
        response = AnalysisResponse(
            url=result['url'],
            platform=Platform(result['platform']),
            content_type=ContentType(result['content_type']),
            title=result['metadata'].get('title', ''),
            description=result['metadata'].get('description', ''),
            hashtags=result['metadata'].get('hashtags', []),
            metadata=result['metadata'],
            analyzed_at=result['analyzed_at']
        )

        # Add video analysis if available
        if result.get('video_analysis') and not result['video_analysis'].get('error'):
            video_data = result['video_analysis']
            response.video_analysis = VideoAnalysis(
                transcript=video_data.get('transcript', ''),
                extracted_text=video_data.get('extracted_text', []),
                visual_elements=video_data.get('visual_elements', [])
            )

        # Add image analysis if available
        if result.get('image_analysis') and not result['image_analysis'].get('error'):
            image_data = result['image_analysis']
            response.image_analysis = ImageAnalysis(
                extracted_text=image_data.get('extracted_text', ''),
                objects=image_data.get('objects', []),
                scene_description=image_data.get('scene_description', '')
            )

        # Add classification if available
        if result.get('classification') and not result['classification'].get('error'):
            classification_data = result['classification']
            response.classification = ClassificationResult(
                primary_category=classification_data.get('primary_category', ''),
                sub_categories=classification_data.get('sub_categories', []),
                place_info=classification_data.get('place_info'),
                menu_items=classification_data.get('menu_items', []),
                features=classification_data.get('features', []),
                price_range=classification_data.get('price_range'),
                recommended_for=classification_data.get('recommended_for', []),
                sentiment=classification_data.get('sentiment', 'neutral'),
                sentiment_score=classification_data.get('sentiment_score', 0.0),
                summary=classification_data.get('summary', ''),
                keywords=classification_data.get('keywords', []),
                confidence=classification_data.get('confidence', 0.0)
            )

        return response

    except ValueError as e:
        # Invalid URL or unsupported platform
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected server error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze URL: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status indicating service health
    """
    return {"status": "ok", "service": "link-analyzer"}


@router.get("/platforms")
async def get_supported_platforms() -> Dict[str, list]:
    """
    Get list of supported platforms.

    Returns:
        List of supported social media platforms
    """
    return {
        "platforms": [
            {
                "name": "YouTube",
                "value": "youtube",
                "supports": ["video", "shorts"],
                "features": ["direct_url_analysis", "no_download_required"]
            },
            {
                "name": "Instagram",
                "value": "instagram",
                "supports": ["video", "image", "carousel"],
                "features": ["yt_dlp_download", "ocr", "multi_media"]
            },
            {
                "name": "TikTok",
                "value": "tiktok",
                "supports": ["video"],
                "features": ["yt_dlp_download", "music_info"]
            }
        ]
    }
