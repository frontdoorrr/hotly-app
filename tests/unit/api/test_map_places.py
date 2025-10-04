"""Tests for map places API endpoint."""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.place import Place, PlaceCategory, PlaceStatus

client = TestClient(app)

TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"


class TestMapPlacesAPI:
    """Test map places in bounds endpoint."""

    def test_getPlacesInBounds_validBounds_returnsPlacesWithinArea(
        self, db: Session
    ) -> None:
        """지도 범위 내 장소 조회 - 정상 케이스."""
        # Given: 3개 장소 - 2개는 범위 내, 1개는 범위 밖
        place1 = Place(
            user_id=UUID(TEMP_USER_ID),
            name="범위 내 카페",
            category=PlaceCategory.CAFE,
            status=PlaceStatus.ACTIVE,
        )
        place1.set_coordinates(37.5665, 126.9780)  # 서울시청

        place2 = Place(
            user_id=UUID(TEMP_USER_ID),
            name="범위 내 레스토랑",
            category=PlaceCategory.RESTAURANT,
            status=PlaceStatus.ACTIVE,
        )
        place2.set_coordinates(37.5700, 126.9850)  # 광화문

        place3 = Place(
            user_id=UUID(TEMP_USER_ID),
            name="범위 밖 장소",
            category=PlaceCategory.CAFE,
            status=PlaceStatus.ACTIVE,
        )
        place3.set_coordinates(37.4979, 127.0276)  # 강남역 (범위 밖)

        db.add_all([place1, place2, place3])
        db.commit()

        # When: 서울 중심부 범위로 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
            },
        )

        # Then: 범위 내 2개만 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        place_names = {p["name"] for p in data}
        assert "범위 내 카페" in place_names
        assert "범위 내 레스토랑" in place_names
        assert "범위 밖 장소" not in place_names

    def test_getPlacesInBounds_withCategoryFilter_returnsFilteredPlaces(
        self, db: Session
    ) -> None:
        """카테고리 필터 적용 - 지정된 카테고리만 반환."""
        # Given: 같은 범위 내 카페 1개, 레스토랑 1개
        cafe = Place(
            user_id=UUID(TEMP_USER_ID),
            name="테스트 카페",
            category=PlaceCategory.CAFE,
            status=PlaceStatus.ACTIVE,
        )
        cafe.set_coordinates(37.5665, 126.9780)

        restaurant = Place(
            user_id=UUID(TEMP_USER_ID),
            name="테스트 레스토랑",
            category=PlaceCategory.RESTAURANT,
            status=PlaceStatus.ACTIVE,
        )
        restaurant.set_coordinates(37.5700, 126.9850)

        db.add_all([cafe, restaurant])
        db.commit()

        # When: 카페만 필터링
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

        # Then: 카페만 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "테스트 카페"
        assert data[0]["category"] == "cafe"

    def test_getPlacesInBounds_emptyArea_returnsEmptyList(self) -> None:
        """범위 내 장소 없음 - 빈 배열 반환."""
        # Given: 장소 없음
        # When: 제주도 범위로 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 33.0,
                "sw_lng": 126.0,
                "ne_lat": 33.5,
                "ne_lng": 126.5,
            },
        )

        # Then: 빈 배열 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_getPlacesInBounds_invalidCoordinates_returnsBadRequest(self) -> None:
        """잘못된 좌표 - 400 에러."""
        # Given & When: 위도 범위 초과
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 91,  # 잘못된 위도
                "sw_lng": 126.0,
                "ne_lat": 92,
                "ne_lng": 127.0,
            },
        )

        # Then: 400 에러
        assert response.status_code == 422  # FastAPI validation error

    def test_getPlacesInBounds_inactivePlaces_excludesInactive(
        self, db: Session
    ) -> None:
        """비활성 장소 제외 - ACTIVE만 반환."""
        # Given: ACTIVE 1개, INACTIVE 1개
        active_place = Place(
            user_id=UUID(TEMP_USER_ID),
            name="활성 장소",
            category=PlaceCategory.CAFE,
            status=PlaceStatus.ACTIVE,
        )
        active_place.set_coordinates(37.5665, 126.9780)

        inactive_place = Place(
            user_id=UUID(TEMP_USER_ID),
            name="비활성 장소",
            category=PlaceCategory.CAFE,
            status=PlaceStatus.INACTIVE,
        )
        inactive_place.set_coordinates(37.5700, 126.9850)

        db.add_all([active_place, inactive_place])
        db.commit()

        # When: 범위 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
            },
        )

        # Then: ACTIVE만 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "활성 장소"

    def test_getPlacesInBounds_limitParameter_respectsLimit(self, db: Session) -> None:
        """Limit 파라미터 적용 - 지정된 개수만 반환."""
        # Given: 5개 장소
        for i in range(5):
            place = Place(
                user_id=UUID(TEMP_USER_ID),
                name=f"장소 {i}",
                category=PlaceCategory.CAFE,
                status=PlaceStatus.ACTIVE,
            )
            # 같은 범위 내에 분산
            place.set_coordinates(37.5665 + i * 0.001, 126.9780 + i * 0.001)
            db.add(place)
        db.commit()

        # When: Limit 3으로 조회
        response = client.get(
            "/api/v1/map/places",
            params={
                "sw_lat": 37.56,
                "sw_lng": 126.97,
                "ne_lat": 37.58,
                "ne_lng": 127.00,
                "limit": 3,
            },
        )

        # Then: 3개만 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
