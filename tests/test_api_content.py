"""Test content extraction API endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.exceptions.external import UnsupportedPlatformError
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType
from app.services.content_extractor import ContentExtractor


def test_extract_content_endpoint_success(client: TestClient) -> None:
    """Test successful content extraction via API."""
    # Mock the content extractor
    mock_content = ExtractedContent(
        url="https://www.instagram.com/p/test123/",
        platform=PlatformType.INSTAGRAM,
        metadata=ContentMetadata(
            title="Test Instagram Post",
            description="Test description",
            location="Seoul, Korea",
        ),
        extraction_time=1.5,
    )

    with patch.object(
        ContentExtractor, "extract_content", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = mock_content

        response = client.post(
            "/api/v1/content/extract",
            json={"url": "https://www.instagram.com/p/test123/"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"]["url"] == "https://www.instagram.com/p/test123/"
        assert data["content"]["platform"] == "instagram"
        assert data["cached"] is False


def test_extract_content_unsupported_platform(client: TestClient) -> None:
    """Test content extraction with unsupported platform."""
    with patch.object(
        ContentExtractor, "extract_content", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.side_effect = UnsupportedPlatformError(
            "Unsupported platform: unknown.com"
        )

        response = client.post(
            "/api/v1/content/extract", json={"url": "https://unknown.com/post/123"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "unsupported platform" in data["detail"].lower()


def test_extract_content_timeout(client: TestClient) -> None:
    """Test content extraction timeout handling."""
    with patch.object(
        ContentExtractor, "extract_content", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.side_effect = TimeoutError("Extraction timeout")

        response = client.post(
            "/api/v1/content/extract",
            json={"url": "https://www.instagram.com/p/timeout/"},
        )

        assert response.status_code == 408
        data = response.json()
        assert "timed out" in data["detail"].lower()


def test_extract_content_invalid_url(client: TestClient) -> None:
    """Test content extraction with invalid URL."""
    response = client.post("/api/v1/content/extract", json={"url": "not-a-valid-url"})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_extract_content_missing_url(client: TestClient) -> None:
    """Test content extraction with missing URL."""
    response = client.post("/api/v1/content/extract", json={})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_extract_content_force_refresh(client: TestClient) -> None:
    """Test content extraction with force refresh parameter."""
    mock_content = ExtractedContent(
        url="https://www.instagram.com/p/test123/",
        platform=PlatformType.INSTAGRAM,
        metadata=ContentMetadata(title="Test Post"),
        extraction_time=2.0,
    )

    with patch.object(
        ContentExtractor, "extract_content", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = mock_content

        response = client.post(
            "/api/v1/content/extract",
            json={"url": "https://www.instagram.com/p/test123/", "force_refresh": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
