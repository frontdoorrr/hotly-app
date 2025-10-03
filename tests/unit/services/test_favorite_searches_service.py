"""
즐겨찾는 검색 서비스 테스트 코드 (Task 2-3-5)

TDD Red Phase: 사용자 즐겨찾는 검색 저장 및 관리 시스템 테스트
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.favorite_searches_service import FavoriteSearchesService


class TestFavoriteSearchesService:
    """즐겨찾는 검색 서비스 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_redis = AsyncMock()
        self.mock_db = Mock()

        # 테스트 즐겨찾는 검색 데이터
        self.sample_favorite_searches = [
            {
                "id": "fav_1",
                "name": "홍대 맛집 탐방",
                "query": "홍대 맛집",
                "filters": {"categories": ["restaurant"], "price_max": 30000},
                "location": {"lat": 37.5563, "lng": 126.9233, "name": "홍대입구역"},
                "created_at": datetime.utcnow().isoformat(),
                "last_used": datetime.utcnow().isoformat(),
                "use_count": 15,
                "tags": ["맛집", "홍대", "저녁"],
            },
            {
                "id": "fav_2",
                "name": "강남 카페 둘러보기",
                "query": "강남 카페",
                "filters": {"categories": ["cafe"], "rating_min": 4.0},
                "location": {"lat": 37.4979, "lng": 127.0276, "name": "강남역"},
                "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "last_used": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "use_count": 8,
                "tags": ["카페", "강남", "데이트"],
            },
        ]

    async def test_favorite_search_creation(self) -> None:
        """
        Given: 사용자가 자주 사용하는 검색 조건
        When: 즐겨찾는 검색으로 저장함
        Then: 올바른 형태로 즐겨찾는 검색이 생성됨
        """
        # Given: 즐겨찾는 검색 서비스 초기화
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        search_data = {
            "name": "이태원 분위기 좋은 바",
            "query": "이태원 바",
            "filters": {"categories": ["bar"], "atmosphere": ["cozy", "romantic"]},
            "location": {"lat": 37.5349, "lng": 126.9941, "name": "이태원역"},
            "tags": ["바", "이태원", "분위기", "데이트"],
        }

        # When: 즐겨찾는 검색 생성
        favorite_id = await favorite_service.create_favorite_search(
            user_id=self.test_user_id, search_data=search_data
        )

        # Then: 즐겨찾는 검색 생성 확인
        assert favorite_id is not None
        assert len(favorite_id) > 0

        # Redis 저장 확인
        self.mock_redis.hset.assert_called()
        call_args = self.mock_redis.hset.call_args
        assert f"favorite_searches:{self.test_user_id}" in call_args[0][0]

        # 저장된 데이터 구조 확인
        stored_data = json.loads(call_args[0][2])
        assert stored_data["name"] == search_data["name"]
        assert stored_data["query"] == search_data["query"]
        assert stored_data["filters"] == search_data["filters"]
        assert "created_at" in stored_data
        assert stored_data["use_count"] == 0  # 초기값

    async def test_favorite_searches_retrieval(self) -> None:
        """
        Given: 저장된 즐겨찾는 검색들
        When: 사용자의 즐겨찾는 검색 목록을 조회함
        Then: 사용 빈도순으로 정렬된 목록을 반환함
        """
        # Given: 즐겨찾는 검색 서비스와 저장된 데이터
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock Redis Hash 데이터
        mock_favorites = {
            "fav_1": json.dumps(self.sample_favorite_searches[0]),
            "fav_2": json.dumps(self.sample_favorite_searches[1]),
        }
        self.mock_redis.hgetall.return_value = mock_favorites

        # When: 즐겨찾는 검색 목록 조회
        favorites = await favorite_service.get_favorite_searches(
            user_id=self.test_user_id, limit=10
        )

        # Then: 올바른 즐겨찾는 검색 목록 반환
        assert len(favorites) == 2

        # 사용 빈도순 정렬 확인 (use_count 기준)
        assert favorites[0]["use_count"] >= favorites[1]["use_count"]
        assert favorites[0]["name"] == "홍대 맛집 탐방"
        assert favorites[1]["name"] == "강남 카페 둘러보기"

    async def test_favorite_search_execution(self) -> None:
        """
        Given: 저장된 즐겨찾는 검색
        When: 즐겨찾는 검색을 실행함
        Then: 저장된 조건으로 검색을 수행하고 사용 횟수를 증가시킴
        """
        # Given: 즐겨찾는 검색 실행 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock 저장된 즐겨찾는 검색
        favorite_data = self.sample_favorite_searches[0].copy()
        self.mock_redis.hget.return_value = json.dumps(favorite_data)

        # Mock 검색 서비스
        mock_search_results = [
            {"id": "place_1", "name": "맛집1", "category": "restaurant"},
            {"id": "place_2", "name": "맛집2", "category": "restaurant"},
        ]

        with patch.object(favorite_service, "_execute_search") as mock_search:
            mock_search.return_value = {"results": mock_search_results, "count": 2}

            # When: 즐겨찾는 검색 실행
            search_result = await favorite_service.execute_favorite_search(
                user_id=self.test_user_id, favorite_id="fav_1"
            )

            # Then: 검색 실행 결과 확인
            assert "results" in search_result
            assert search_result["favorite_info"]["name"] == "홍대 맛집 탐방"
            assert len(search_result["results"]) == 2

            # 사용 횟수 증가 확인
            self.mock_redis.hset.assert_called()  # 업데이트된 데이터 저장

    async def test_favorite_search_categorization(self) -> None:
        """
        Given: 다양한 카테고리의 즐겨찾는 검색들
        When: 카테고리별로 분류함
        Then: 음식, 카페, 문화 등의 카테고리로 그룹핑됨
        """
        # Given: 카테고리 분석 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_categorization=True,
        )

        # 다양한 카테고리의 즐겨찾는 검색
        diverse_favorites = self.sample_favorite_searches + [
            {
                "id": "fav_3",
                "name": "명동 쇼핑",
                "query": "명동 쇼핑몰",
                "filters": {"categories": ["shopping"]},
                "tags": ["쇼핑", "명동", "쇼핑몰"],
            }
        ]

        mock_favorites = {
            f"fav_{i + 1}": json.dumps(fav) for i, fav in enumerate(diverse_favorites)
        }
        self.mock_redis.hgetall.return_value = mock_favorites

        # When: 카테고리별 분류
        categorized = await favorite_service.get_categorized_favorites(
            user_id=self.test_user_id
        )

        # Then: 카테고리별 그룹핑 확인
        assert "food_and_dining" in categorized
        assert "shopping" in categorized
        assert len(categorized["food_and_dining"]) >= 1  # 맛집 관련
        assert len(categorized["shopping"]) >= 1  # 쇼핑 관련

    async def test_favorite_search_smart_suggestions(self) -> None:
        """
        Given: 사용자의 검색 패턴과 즐겨찾는 검색
        When: 스마트 제안을 생성함
        Then: 유사한 패턴의 새로운 즐겨찾는 검색을 제안함
        """
        # Given: 스마트 제안 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            smart_suggestions=True,
        )

        # Mock 사용자 검색 패턴
        search_patterns = [
            {"query": "홍대 맛집", "frequency": 15},
            {"query": "홍대 카페", "frequency": 8},
            {"query": "홍대 술집", "frequency": 5},
        ]

        with patch.object(
            favorite_service, "_analyze_search_patterns"
        ) as mock_patterns:
            mock_patterns.return_value = search_patterns

            # When: 스마트 제안 생성
            suggestions = await favorite_service.generate_smart_suggestions(
                user_id=self.test_user_id, limit=3
            )

            # Then: 유사 패턴 기반 제안 확인
            assert len(suggestions) > 0
            assert any(
                "홍대" in suggestion["suggested_name"] for suggestion in suggestions
            )
            assert any(
                suggestion["confidence_score"] > 0.7 for suggestion in suggestions
            )

    async def test_favorite_search_sharing(self) -> None:
        """
        Given: 사용자의 즐겨찾는 검색
        When: 다른 사용자와 공유함
        Then: 공유 링크 생성 및 공유 권한 관리
        """
        # Given: 공유 기능이 있는 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db, sharing_enabled=True
        )

        favorite_data = self.sample_favorite_searches[0]
        self.mock_redis.hget.return_value = json.dumps(favorite_data)

        # When: 즐겨찾는 검색 공유
        share_result = await favorite_service.share_favorite_search(
            user_id=self.test_user_id,
            favorite_id="fav_1",
            share_settings={
                "public": False,
                "expiry_hours": 24,
                "allow_modifications": False,
            },
        )

        # Then: 공유 결과 확인
        assert "share_token" in share_result
        assert "share_url" in share_result
        assert share_result["expires_at"] is not None

        # 공유 데이터 저장 확인
        self.mock_redis.setex.assert_called()

    async def test_favorite_search_templates(self) -> None:
        """
        Given: 일반적인 검색 패턴
        When: 즐겨찾는 검색 템플릿을 제공함
        Then: 사용자가 쉽게 즐겨찾는 검색을 만들 수 있는 템플릿 제공
        """
        # Given: 템플릿 기능이 있는 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            templates_enabled=True,
        )

        # When: 즐겨찾는 검색 템플릿 조회
        templates = await favorite_service.get_favorite_templates(
            user_location={"lat": 37.5665, "lng": 126.9780},  # 서울시청
            user_preferences=["restaurant", "cafe"],
        )

        # Then: 템플릿 확인
        assert len(templates) > 0
        assert any(template["category"] == "restaurant" for template in templates)
        assert any(template["category"] == "cafe" for template in templates)

        # 템플릿 구조 확인
        first_template = templates[0]
        assert "name_template" in first_template
        assert "query_template" in first_template
        assert "suggested_filters" in first_template

    async def test_favorite_search_analytics(self) -> None:
        """
        Given: 즐겨찾는 검색 사용 데이터
        When: 사용 패턴을 분석함
        Then: 사용자의 즐겨찾는 검색 인사이트 제공
        """
        # Given: 분석 기능이 있는 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            analytics_enabled=True,
        )

        # Mock 사용 데이터
        mock_favorites = {
            "fav_1": json.dumps(self.sample_favorite_searches[0]),
            "fav_2": json.dumps(self.sample_favorite_searches[1]),
        }
        self.mock_redis.hgetall.return_value = mock_favorites

        # When: 즐겨찾는 검색 분석
        analytics = await favorite_service.analyze_favorite_usage(
            user_id=self.test_user_id, period_days=30
        )

        # Then: 분석 결과 확인
        assert "total_favorites" in analytics
        assert "most_used_category" in analytics
        assert "usage_trends" in analytics
        assert "recommendations" in analytics

        assert analytics["total_favorites"] == 2
        assert analytics["most_used_category"] == "restaurant"  # 사용횟수 기준

    async def test_favorite_search_synchronization(self) -> None:
        """
        Given: 여러 디바이스의 즐겨찾는 검색
        When: 디바이스 간 동기화를 수행함
        Then: 모든 디바이스에서 일관된 즐겨찾는 검색 상태 유지
        """
        # Given: 동기화 기능이 있는 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db, sync_enabled=True
        )

        # When: 디바이스 동기화 요청
        sync_result = await favorite_service.sync_favorites_across_devices(
            user_id=self.test_user_id,
            device_id="device_123",
            local_favorites=[
                {"id": "local_1", "name": "새로운 즐겨찾기", "query": "새 검색"},
                {"id": "fav_1", "name": "홍대 맛집 탐방", "use_count": 18},  # 업데이트된 데이터
            ],
        )

        # Then: 동기화 결과 확인
        assert "synchronized_count" in sync_result
        assert "conflicts_resolved" in sync_result
        assert "updated_favorites" in sync_result

        # 동기화된 데이터 저장 확인
        self.mock_redis.hset.assert_called()

    async def test_favorite_search_backup_restore(self) -> None:
        """
        Given: 즐겨찾는 검색 데이터
        When: 백업 및 복원을 수행함
        Then: 데이터 손실 없이 백업/복원됨
        """
        # Given: 백업/복원 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock 즐겨찾는 검색 데이터
        mock_favorites = {
            "fav_1": json.dumps(self.sample_favorite_searches[0]),
            "fav_2": json.dumps(self.sample_favorite_searches[1]),
        }
        self.mock_redis.hgetall.return_value = mock_favorites

        # When: 백업 생성
        backup_data = await favorite_service.create_backup(user_id=self.test_user_id)

        # Then: 백업 데이터 확인
        assert "backup_id" in backup_data
        assert "created_at" in backup_data
        assert "favorites_count" in backup_data
        assert backup_data["favorites_count"] == 2

        # When: 백업 복원
        restore_result = await favorite_service.restore_from_backup(
            user_id=self.test_user_id, backup_id=backup_data["backup_id"]
        )

        # Then: 복원 결과 확인
        assert restore_result["restored_count"] == 2
        assert restore_result["success"] is True

    async def test_favorite_search_advanced_filtering(self) -> None:
        """
        Given: 다양한 즐겨찾는 검색들
        When: 고급 필터링을 적용함
        Then: 조건에 맞는 즐겨찾는 검색만 반환됨
        """
        # Given: 고급 필터링 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock 확장된 즐겨찾는 검색 데이터
        extended_favorites = self.sample_favorite_searches + [
            {
                "id": "fav_3",
                "name": "종로 문화체험",
                "query": "종로 갤러리",
                "filters": {"categories": ["culture"]},
                "tags": ["문화", "갤러리", "종로"],
                "use_count": 3,
                "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            }
        ]

        mock_favorites = {
            f"fav_{i + 1}": json.dumps(fav) for i, fav in enumerate(extended_favorites)
        }
        self.mock_redis.hgetall.return_value = mock_favorites

        # When: 고급 필터링 적용
        filtered_results = await favorite_service.filter_favorites(
            user_id=self.test_user_id,
            filters={
                "category": "restaurant",
                "min_use_count": 5,
                "created_since": datetime.utcnow() - timedelta(days=7),
            },
        )

        # Then: 필터링 결과 확인
        assert len(filtered_results) == 1  # 조건에 맞는 맛집 검색만
        assert filtered_results[0]["name"] == "홍대 맛집 탐방"
        assert filtered_results[0]["use_count"] >= 5

    async def test_favorite_search_bulk_operations(self) -> None:
        """
        Given: 여러 즐겨찾는 검색들
        When: 일괄 작업을 수행함
        Then: 효율적으로 여러 즐겨찾는 검색을 처리함
        """
        # Given: 일괄 작업 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis, db_session=self.mock_db, bulk_operations=True
        )

        # When: 일괄 생성
        bulk_create_data = [
            {"name": "강남 맛집", "query": "강남 맛집", "tags": ["맛집", "강남"]},
            {"name": "홍대 카페", "query": "홍대 카페", "tags": ["카페", "홍대"]},
            {"name": "이태원 바", "query": "이태원 바", "tags": ["바", "이태원"]},
        ]

        bulk_result = await favorite_service.bulk_create_favorites(
            user_id=self.test_user_id, favorites_data=bulk_create_data
        )

        # Then: 일괄 생성 결과 확인
        assert "created_count" in bulk_result
        assert "failed_count" in bulk_result
        assert bulk_result["created_count"] == 3
        assert bulk_result["failed_count"] == 0

        # When: 일괄 삭제
        bulk_delete_result = await favorite_service.bulk_delete_favorites(
            user_id=self.test_user_id, favorite_ids=["fav_1", "fav_2", "fav_3"]
        )

        # Then: 일괄 삭제 결과 확인
        assert bulk_delete_result["deleted_count"] >= 0
        self.mock_redis.hdel.assert_called()

    async def test_favorite_search_performance_optimization(self) -> None:
        """
        Given: 대량의 즐겨찾는 검색 데이터
        When: 성능 최적화를 적용함
        Then: 빠른 응답 속도와 효율적인 메모리 사용
        """
        # Given: 성능 최적화된 서비스
        favorite_service = FavoriteSearchesService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            performance_optimized=True,
            cache_frequently_used=True,
        )

        # When: 대량 데이터 처리
        performance_result = await favorite_service.get_favorites_optimized(
            user_id=self.test_user_id,
            optimization_params={
                "use_cache": True,
                "lazy_loading": True,
                "compression": True,
            },
        )

        # Then: 성능 최적화 확인
        assert "favorites" in performance_result
        assert "performance_metrics" in performance_result

        metrics = performance_result["performance_metrics"]
        assert "response_time_ms" in metrics
        assert "cache_hit_rate" in metrics
        assert "memory_usage_mb" in metrics
