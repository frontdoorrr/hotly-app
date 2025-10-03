"""코스 생성 API 통합 테스트."""
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


class TestCourseGenerationAPI:
    """코스 생성 API 통합 테스트."""

    @pytest.fixture
    def client(self) -> TestClient:
        """테스트 클라이언트."""
        return TestClient(app)

    @pytest.fixture
    def sample_request(self) -> Dict[str, Any]:
        """샘플 코스 생성 요청."""
        return {
            "place_ids": ["place1", "place2", "place3", "place4"],
            "transport_method": "walking",
            "start_time": "10:00",
            "preferences": {
                "max_total_duration": 480,
                "avoid_rush_hours": True,
            },
        }

    @pytest.fixture
    def mock_places(self) -> List[MagicMock]:
        """Mock 장소 데이터."""
        places = []
        coordinates_data = [
            (37.5563, 126.9241),  # 홍대
            (37.5658, 126.9244),  # 연남동
            (37.5533, 126.8947),  # 망원
            (37.5478, 126.9227),  # 상수
        ]

        for i, (lat, lon) in enumerate(coordinates_data, 1):
            place = MagicMock()
            place.id = f"place{i}"
            place.name = f"Place {i}"
            place.category = "cafe" if i % 2 == 0 else "restaurant"
            place.coordinates = MagicMock()
            # Mock PostGIS point object
            place.coordinates.__geo_interface__ = {
                "type": "Point",
                "coordinates": [lon, lat],
            }
            places.append(place)

        return places

    def test_generateCourse_validRequest_returns200(
        self,
        client: TestClient,
        sample_request: Dict[str, Any],
        mock_places: List[MagicMock],
    ) -> None:
        """유효한 요청 시 200 응답 및 최적화된 코스 반환."""
        # Given: 유효한 장소 데이터
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_places
            )

            # When: POST /api/v1/courses/generate
            response = client.post("/api/v1/courses/generate", json=sample_request)

            # Then: 200 응답
            assert response.status_code == status.HTTP_200_OK

            # And: 응답 데이터 검증
            data = response.json()
            assert "course_id" in data
            assert "course" in data
            assert "optimization_score" in data
            assert "generation_time_ms" in data

            # And: 코스 상세 검증
            course = data["course"]
            assert len(course["places"]) == 4
            assert course["total_distance_km"] > 0
            assert course["total_duration_minutes"] > 0
            assert course["difficulty"] in ["easy", "moderate", "hard"]

            # And: 성능 검증 (500ms 이내)
            assert data["generation_time_ms"] < 500

    def test_generateCourse_tooFewPlaces_returns422(self, client: TestClient) -> None:
        """3개 미만 장소 시 422 검증 에러."""
        # Given: 2개 장소만
        request_data = {
            "place_ids": ["place1", "place2"],
            "transport_method": "walking",
        }

        # When: POST /api/v1/courses/generate
        response = client.post("/api/v1/courses/generate", json=request_data)

        # Then: 422 Validation Error (Pydantic validator)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Pydantic validation error message
        detail = response.json()["detail"]
        assert any("최소 3개" in str(d) for d in detail if isinstance(detail, list))

    def test_generateCourse_tooManyPlaces_returns422(self, client: TestClient) -> None:
        """6개 초과 장소 시 422 검증 에러."""
        # Given: 7개 장소
        request_data = {
            "place_ids": [f"place{i}" for i in range(1, 8)],
            "transport_method": "walking",
        }

        # When: POST /api/v1/courses/generate
        response = client.post("/api/v1/courses/generate", json=request_data)

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = response.json()["detail"]
        assert any("최대 6개" in str(d) for d in detail if isinstance(detail, list))

    def test_generateCourse_invalidPlaceId_returns400(
        self, client: TestClient, sample_request: Dict[str, Any]
    ) -> None:
        """존재하지 않는 장소 ID 시 400 에러."""
        # Given: 존재하지 않는 장소
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            # 일부 장소만 반환 (불완전)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            # When: POST /api/v1/courses/generate
            response = client.post("/api/v1/courses/generate", json=sample_request)

            # Then: 400 에러
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generateCourse_differentTransportMethods_variesDuration(
        self, client: TestClient, mock_places: List[MagicMock]
    ) -> None:
        """교통수단별 소요시간 차이 확인."""
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_places
            )

            # When: 각기 다른 교통수단으로 요청
            walking_request = {
                "place_ids": ["place1", "place2", "place3", "place4"],
                "transport_method": "walking",
            }
            driving_request = {
                "place_ids": ["place1", "place2", "place3", "place4"],
                "transport_method": "driving",
            }

            walking_response = client.post(
                "/api/v1/courses/generate", json=walking_request
            )
            driving_response = client.post(
                "/api/v1/courses/generate", json=driving_request
            )

            # Then: 도보가 차량보다 시간이 더 걸림
            walking_duration = walking_response.json()["course"][
                "total_duration_minutes"
            ]
            driving_duration = driving_response.json()["course"][
                "total_duration_minutes"
            ]
            assert walking_duration > driving_duration

    def test_generateCourse_withPreferences_respectsConstraints(
        self, client: TestClient, mock_places: List[MagicMock]
    ) -> None:
        """선호도 설정이 코스 생성에 반영됨."""
        # Given: 최대 시간 제약이 있는 요청
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_places
            )

            request_data = {
                "place_ids": ["place1", "place2", "place3"],
                "transport_method": "walking",
                "preferences": {
                    "max_total_duration": 240,  # 4���간 제한
                    "avoid_rush_hours": True,
                },
            }

            # When: POST /api/v1/courses/generate
            response = client.post("/api/v1/courses/generate", json=request_data)

            # Then: 성공 응답
            assert response.status_code == status.HTTP_200_OK

            # And: 총 소요시간이 제약 이내
            total_duration = response.json()["course"]["total_duration_minutes"]
            assert total_duration <= 240

    def test_generateCourse_optimizationScore_inRange(
        self,
        client: TestClient,
        sample_request: Dict[str, Any],
        mock_places: List[MagicMock],
    ) -> None:
        """최적화 점수가 0-1 범위 내."""
        # Given: 유효한 요청
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_places
            )

            # When: POST /api/v1/courses/generate
            response = client.post("/api/v1/courses/generate", json=sample_request)

            # Then: 최적화 점수가 0-1 사이
            score = response.json()["optimization_score"]
            assert 0 <= score <= 1

    def test_generateCourse_includesArrivalTimes_whenStartTimeProvided(
        self,
        client: TestClient,
        sample_request: Dict[str, Any],
        mock_places: List[MagicMock],
    ) -> None:
        """시작 시간 제공 시 도착 시간 계산."""
        # Given: 시작 시간이 포함된 요청
        with patch("app.api.api_v1.endpoints.courses.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_places
            )

            # When: POST /api/v1/courses/generate
            response = client.post("/api/v1/courses/generate", json=sample_request)

            # Then: 각 장소별 도착/출발 시간 포함
            places = response.json()["course"]["places"]
            for place in places:
                assert "arrival_time" in place
                assert "departure_time" in place
                # 시간 형식 검증 (HH:MM)
                assert len(place["arrival_time"].split(":")) == 2

    def test_getCourseById_notImplemented_returns501(self, client: TestClient) -> None:
        """코스 조회 API는 아직 미구현."""
        # When: GET /api/v1/courses/{course_id}
        response = client.get("/api/v1/courses/test-course-id")

        # Then: 501 Not Implemented
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        assert "not implemented" in response.json()["detail"].lower()
