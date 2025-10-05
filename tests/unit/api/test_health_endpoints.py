"""Tests for health check endpoints."""

from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Health check endpoint tests."""

    def test_health_basicCheck_returns200(self) -> None:
        """기본 헬스체크 - 항상 200 OK 반환."""
        # When
        response = client.get("/health")

        # Then
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_healthDetailed_databaseOk_returns200(self) -> None:
        """상세 헬스체크 - DB 정상 시 200 반환."""
        # When
        response = client.get("/health/detailed")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data

    @patch("app.api.health.CacheManager")
    def test_healthReady_allServicesOk_returns200(
        self, mock_cache_manager: MagicMock
    ) -> None:
        """준비 상태 체크 - 모든 서비스 정상 시 200 반환."""
        # Given: Redis 연결 정상
        mock_instance = MagicMock()
        mock_instance.redis_client.ping.return_value = True
        mock_cache_manager.return_value = mock_instance

        # When
        response = client.get("/health/ready")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["services"]["database"] == "ok"
        assert data["services"]["redis"] == "ok"

    @patch("app.api.health.CacheManager")
    def test_healthReady_redisFailed_returns503(
        self, mock_cache_manager: MagicMock
    ) -> None:
        """준비 상태 체크 - Redis 실패 시 503 반환."""
        # Given: Redis 연결 실패
        mock_cache_manager.side_effect = Exception("Redis connection failed")

        # When
        response = client.get("/health/ready")

        # Then
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["ready"] is False
        assert "error" in data["services"]["redis"]
