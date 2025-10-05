"""Integration tests for map places API endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMapPlacesIntegration:
    """Integration tests for map places endpoint."""

    def test_getPlacesInBounds_validRequest_returns200(self) -> None:
        """지도 범위 조회 API - 정상 요청 시 200 반환."""
        # Given & When: 서울 중심부 범위로 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
            },
        )

        # Then: 200 OK
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_getPlacesInBounds_withCategory_acceptsCategoryFilter(self) -> None:
        """카테고리 필터 파라미터 - 정상 동작."""
        # Given & When: 카페 필터 적용
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
                "category": "cafe",
            },
        )

        # Then: 200 OK
        assert response.status_code == 200

    def test_getPlacesInBounds_invalidLatitude_returns422(self) -> None:
        """잘못된 위도 - 422 Validation Error."""
        # Given & When: 위도 범위 초과
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 91,  # Invalid latitude
                "sw_lng": 126.0,
                "ne_lat": 92,
                "ne_lng": 127.0,
            },
        )

        # Then: 422 Validation Error
        assert response.status_code == 422

    def test_getPlacesInBounds_withLimit_respectsParameter(self) -> None:
        """Limit 파라미터 - 정상 처리."""
        # Given & When: Limit 10으로 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
                "limit": 10,
            },
        )

        # Then: 200 OK
        assert response.status_code == 200
        data = response.json()
        # 최대 10개만 반환
        assert len(data) <= 10

    def test_getPlacesInBounds_missingParameter_returns422(self) -> None:
        """필수 파라미터 누락 - 422 에러."""
        # Given & When: sw_lat 누락
        response = client.get(
            "/api/v1/map/places",
            params={
                # sw_lat 누락
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
            },
        )

        # Then: 422 Validation Error
        assert response.status_code == 422
