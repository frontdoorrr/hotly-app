"""Test AI analysis API endpoints."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.schemas.ai import PlaceAnalysisResponse, PlaceCategory, PlaceInfo
from app.services.place_analysis_service import PlaceAnalysisService


def test_analyze_place_endpoint_success(client: TestClient) -> None:
    """Test successful place analysis via API."""
    # Mock successful analysis response
    mock_place_info = PlaceInfo(
        name="강남 한우집",
        category=PlaceCategory.RESTAURANT,
        keywords=["한우", "고급", "강남"],
        recommendation_score=9,
        address="서울 강남구 테헤란로 123",
    )

    mock_response = PlaceAnalysisResponse(
        success=True,
        place_info=mock_place_info,
        confidence=0.85,
        analysis_time=2.5,
        model_version="gemini-pro-vision",
    )

    with patch.object(
        PlaceAnalysisService, "analyze_content", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.return_value = mock_response

        response = client.post(
            "/api/v1/ai/analyze-place",
            json={
                "content_text": "Amazing Korean beef restaurant",
                "content_description": "Best Korean BBQ in Gangnam",
                "hashtags": ["#koreanbbq", "#gangnam"],
                "images": ["https://example.com/image1.jpg"],
                "platform": "instagram",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["place_info"]["name"] == "강남 한우집"
        assert data["place_info"]["category"] == "restaurant"
        assert data["confidence"] == 0.85


def test_analyze_place_rate_limit(client: TestClient) -> None:
    """Test AI analysis rate limit handling."""
    with patch.object(
        PlaceAnalysisService, "analyze_content", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.side_effect = RateLimitError("Rate limit exceeded")

        response = client.post(
            "/api/v1/ai/analyze-place",
            json={"content_text": "Test content", "platform": "instagram"},
        )

        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()


def test_analyze_place_ai_service_unavailable(client: TestClient) -> None:
    """Test AI service unavailable handling."""
    with patch.object(
        PlaceAnalysisService, "analyze_content", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.side_effect = AIAnalysisError("AI service down")

        response = client.post(
            "/api/v1/ai/analyze-place",
            json={"content_text": "Test content", "platform": "instagram"},
        )

        assert response.status_code == 503
        data = response.json()
        assert "ai analysis service unavailable" in data["detail"].lower()


def test_analyze_place_invalid_request(client: TestClient) -> None:
    """Test invalid request handling."""
    # Missing required fields
    response = client.post(
        "/api/v1/ai/analyze-place",
        json={
            "content_text": "Test content"
            # Missing platform field
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_analyze_place_empty_content(client: TestClient) -> None:
    """Test analysis with minimal content."""
    response = client.post(
        "/api/v1/ai/analyze-place", json={"content_text": "", "platform": "instagram"}
    )

    # Should accept empty content but may return low confidence
    assert response.status_code in [200, 422]


def test_analyze_place_with_images(client: TestClient) -> None:
    """Test place analysis with image content."""
    mock_response = PlaceAnalysisResponse(
        success=True,
        place_info=PlaceInfo(
            name="비주얼 카페",
            category=PlaceCategory.CAFE,
            keywords=["카페", "디저트", "인스타"],
            recommendation_score=7,
        ),
        confidence=0.9,
        analysis_time=3.2,
        model_version="gemini-pro-vision",
    )

    with patch.object(
        PlaceAnalysisService, "analyze_content", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.return_value = mock_response

        response = client.post(
            "/api/v1/ai/analyze-place",
            json={
                "content_text": "Beautiful cafe with great desserts",
                "content_description": "Instagram-worthy cafe",
                "hashtags": ["#cafe", "#dessert", "#instagram"],
                "images": [
                    "https://example.com/cafe1.jpg",
                    "https://example.com/dessert.jpg",
                ],
                "platform": "instagram",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["place_info"]["category"] == "cafe"
        assert data["confidence"] == 0.9
