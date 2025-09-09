"""
고급 필터링 서비스 테스트 코드 (Task 2-3-3)

TDD Red Phase: 고급 필터링 시스템의 전체 플로우 테스트
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.services.advanced_filter_service import AdvancedFilterService


class TestAdvancedFilterService:
    """고급 필터링 서비스 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_db = Mock()
        self.mock_redis = AsyncMock()
        self.mock_es_manager = AsyncMock()

        # Mock 장소 데이터
        self.mock_places = [
            Mock(
                id=str(uuid4()),
                user_id=str(self.test_user_id),
                name="홍대 감성 카페",
                description="조용하고 분위기 좋은 카페",
                address="서울시 마포구 홍익로 123",
                category="cafe",
                tags=["조용한", "분위기좋은", "와이파이"],
                latitude=37.5563,
                longitude=126.9225,
                rating=4.5,
                price_range=15000,
                visit_status="wishlist",
                created_at=datetime.utcnow(),
            ),
            Mock(
                id=str(uuid4()),
                user_id=str(self.test_user_id),
                name="강남 이탈리안 레스토랑",
                description="고급스러운 이탈리안 요리",
                address="서울시 강남구 테헤란로 456",
                category="restaurant",
                tags=["고급", "데이트", "파스타"],
                latitude=37.5665,
                longitude=127.0780,
                rating=4.8,
                price_range=45000,
                visit_status="visited",
                created_at=datetime.utcnow() - timedelta(days=7),
            ),
        ]

    async def test_comprehensive_filter_search_basic(self):
        """
        Given: 기본 필터 조건들
        When: 종합 필터 검색을 수행함
        Then: 모든 필터 조건을 AND로 조합하여 정확한 결과를 반환함
        """
        # Given: 필터 서비스 초기화
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)
        
        filter_criteria = {
            "categories": ["cafe"],
            "regions": ["홍대", "마포구"],
            "tags": ["조용한"],
            "price_ranges": ["10000-20000"],
            "visit_status": ["wishlist"],
            "rating_min": 4.0,
            "sort_by": "rating",
            "sort_order": "desc"
        }

        # Mock Elasticsearch 검색 결과
        mock_es_result = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 2.5,
                        "_source": {
                            "id": self.mock_places[0].id,
                            "name": "홍대 감성 카페",
                            "description": "조용하고 분위기 좋은 카페",
                            "category": "cafe",
                            "tags": ["조용한", "분위기좋은"],
                            "rating": 4.5,
                            "price_range": 15000,
                            "visit_status": "wishlist",
                            "location": {"lat": 37.5563, "lon": 126.9225},
                        },
                    }
                ],
            },
            "aggregations": {
                "categories": {
                    "buckets": [{"key": "cafe", "doc_count": 1}]
                },
                "regions": {
                    "buckets": [{"key": "마포구", "doc_count": 1}]
                },
                "price_ranges": {
                    "buckets": [{"key": "10000-20000", "doc_count": 1}]
                }
            }
        }

        self.mock_es_manager.search.return_value = mock_es_result

        # When: 종합 필터 검색 수행
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria,
            limit=20,
            offset=0
        )

        # Then: 필터링된 결과 확인
        assert "places" in result
        assert "facets" in result
        assert "total" in result
        assert result["total"] == 1
        assert len(result["places"]) == 1
        assert result["places"][0]["name"] == "홍대 감성 카페"
        assert result["places"][0]["category"] == "cafe"
        assert result["places"][0]["rating"] == 4.5

        # 패싯 정보 확인
        assert "categories" in result["facets"]
        assert "regions" in result["facets"]
        assert "price_ranges" in result["facets"]

    async def test_multi_category_filter(self):
        """
        Given: 여러 카테고리 필터 조건
        When: 다중 카테고리 필터링을 수행함
        Then: OR 조건으로 매칭되는 모든 카테고리의 장소를 반환함
        """
        # Given: 다중 카테고리 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "categories": ["cafe", "restaurant"],
            "sort_by": "recent",
        }

        mock_es_result = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {"_score": 3.0, "_source": {"id": self.mock_places[0].id, "category": "cafe"}},
                    {"_score": 2.8, "_source": {"id": self.mock_places[1].id, "category": "restaurant"}},
                ],
            }
        }
        
        self.mock_es_manager.search.return_value = mock_es_result

        # When: 다중 카테고리 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 두 카테고리 모두 포함된 결과 확인
        assert result["total"] == 2
        categories_found = [place["category"] for place in result["places"]]
        assert "cafe" in categories_found
        assert "restaurant" in categories_found

    async def test_price_range_filter(self):
        """
        Given: 가격대 필터 조건
        When: 가격 범위 필터링을 수행함
        Then: 지정된 가격 범위 내의 장소만 반환함
        """
        # Given: 가격대 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "price_ranges": ["10000-30000"],
            "sort_by": "price",
            "sort_order": "asc"
        }

        # When: 가격 범위 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 가격 범위 내 장소만 반환 확인
        for place in result["places"]:
            assert 10000 <= place.get("price_range", 0) <= 30000

    async def test_location_based_filter(self):
        """
        Given: 위치 기반 필터 조건 (거리, 지역)
        When: 지리적 필터링을 수행함
        Then: 지정된 위치 근처의 장소만 반환함
        """
        # Given: 위치 기반 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "location": {"lat": 37.5563, "lng": 126.9225},
            "radius_km": 2.0,
            "regions": ["마포구"],
            "sort_by": "distance",
        }

        mock_es_result = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 1.0,
                        "sort": [0.5],  # 거리 (km)
                        "_source": {
                            **self.mock_places[0].__dict__,
                            "location": {"lat": 37.5563, "lon": 126.9225},
                        },
                    }
                ],
            }
        }

        self.mock_es_manager.search.return_value = mock_es_result

        # When: 위치 기반 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 거리 순 정렬 및 거리 정보 포함 확인
        assert result["total"] >= 1
        for place in result["places"]:
            assert "distance_km" in place
            assert place["distance_km"] <= 2.0

    async def test_rating_and_review_filter(self):
        """
        Given: 평점 및 리뷰 기반 필터 조건
        When: 품질 기반 필터링을 수행함
        Then: 평점 조건을 만족하는 장소만 반환함
        """
        # Given: 평점 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "rating_min": 4.5,
            "review_count_min": 10,
            "sort_by": "rating",
            "sort_order": "desc"
        }

        # When: 품질 기반 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 평점 조건 만족하는 장소만 반환
        for place in result["places"]:
            assert place.get("rating", 0) >= 4.5

    async def test_visit_status_filter(self):
        """
        Given: 방문 상태 필터 조건
        When: 방문 상태별 필터링을 수행함
        Then: 지정된 방문 상태의 장소만 반환함
        """
        # Given: 방문 상태 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "visit_status": ["wishlist", "planned"],
            "sort_by": "recent",
        }

        # When: 방문 상태 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 지정된 방문 상태만 반환
        for place in result["places"]:
            assert place.get("visit_status") in ["wishlist", "planned"]

    async def test_tag_based_filter(self):
        """
        Given: 태그 기반 필터 조건
        When: 태그 조합 필터링을 수행함
        Then: 모든 태그 조건을 만족하는 장소를 반환함
        """
        # Given: 태그 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {
            "tags": ["조용한", "와이파이"],
            "tag_match_mode": "all",  # 모든 태그 포함
        }

        # When: 태그 기반 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 모든 태그를 포함하는 장소만 반환
        for place in result["places"]:
            place_tags = place.get("tags", [])
            assert "조용한" in place_tags
            assert "와이파이" in place_tags

    async def test_time_based_filter(self):
        """
        Given: 시간 기반 필터 조건
        When: 생성/수정 시간 필터링을 수행함
        Then: 지정된 시간 범위의 장소만 반환함
        """
        # Given: 시간 기반 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        one_week_ago = datetime.utcnow() - timedelta(days=7)
        filter_criteria = {
            "created_after": one_week_ago.isoformat(),
            "sort_by": "recent",
        }

        # When: 시간 기반 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 지정 시간 이후 생성된 장소만 반환
        for place in result["places"]:
            created_date = datetime.fromisoformat(place["created_at"])
            assert created_date >= one_week_ago

    async def test_complex_filter_combination(self):
        """
        Given: 복합 필터 조건들 (카테고리 + 태그 + 가격 + 위치)
        When: 복합 필터링을 수행함
        Then: 모든 조건을 만족하는 장소만 반환함
        """
        # Given: 복합 필터 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        complex_filter = {
            "categories": ["cafe"],
            "tags": ["조용한"],
            "price_ranges": ["10000-30000"],
            "regions": ["마포구"],
            "rating_min": 4.0,
            "visit_status": ["wishlist"],
            "location": {"lat": 37.5563, "lng": 126.9225},
            "radius_km": 5.0,
            "sort_by": "rating",
            "sort_order": "desc"
        }

        # When: 복합 필터링
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=complex_filter
        )

        # Then: 모든 조건 만족하는 장소만 반환
        for place in result["places"]:
            assert place["category"] == "cafe"
            assert "조용한" in place.get("tags", [])
            assert 10000 <= place.get("price_range", 0) <= 30000
            assert place.get("rating", 0) >= 4.0
            assert place.get("visit_status") == "wishlist"

    async def test_filter_facets_generation(self):
        """
        Given: 필터링 결과
        When: 패싯 정보를 생성함
        Then: 현재 필터 상태에 맞는 패싯 옵션을 제공함
        """
        # Given: 패싯 생성 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        mock_es_result = {
            "hits": {"total": {"value": 10}},
            "aggregations": {
                "categories": {
                    "buckets": [
                        {"key": "cafe", "doc_count": 5},
                        {"key": "restaurant", "doc_count": 3},
                        {"key": "bar", "doc_count": 2},
                    ]
                },
                "regions": {
                    "buckets": [
                        {"key": "마포구", "doc_count": 4},
                        {"key": "강남구", "doc_count": 3},
                        {"key": "종로구", "doc_count": 3},
                    ]
                },
                "price_ranges": {
                    "buckets": [
                        {"key": "10000-20000", "doc_count": 4},
                        {"key": "20000-50000", "doc_count": 4},
                        {"key": "50000+", "doc_count": 2},
                    ]
                },
                "tags": {
                    "buckets": [
                        {"key": "조용한", "doc_count": 6},
                        {"key": "분위기좋은", "doc_count": 5},
                        {"key": "와이파이", "doc_count": 4},
                    ]
                }
            }
        }

        self.mock_es_manager.search.return_value = mock_es_result

        # When: 패싯 정보 생성
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria={},
            include_facets=True
        )

        # Then: 패싯 정보 확인
        facets = result["facets"]
        assert "categories" in facets
        assert "regions" in facets
        assert "price_ranges" in facets
        assert "tags" in facets

        # 카테고리 패싯 검증
        categories = facets["categories"]
        assert len(categories) == 3
        assert categories[0]["name"] == "cafe"
        assert categories[0]["count"] == 5

        # 지역 패싯 검증
        regions = facets["regions"]
        assert len(regions) == 3
        assert regions[0]["name"] == "마포구"
        assert regions[0]["count"] == 4

    async def test_sort_options(self):
        """
        Given: 다양한 정렬 조건
        When: 정렬 옵션별 검색을 수행함
        Then: 올바른 정렬 순서로 결과를 반환함
        """
        # Given: 정렬 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        sort_options = [
            {"sort_by": "relevance", "sort_order": "desc"},
            {"sort_by": "rating", "sort_order": "desc"},
            {"sort_by": "recent", "sort_order": "desc"},
            {"sort_by": "price", "sort_order": "asc"},
            {"sort_by": "distance", "location": {"lat": 37.5563, "lng": 126.9225}},
            {"sort_by": "name", "sort_order": "asc"},
        ]

        for sort_option in sort_options:
            # When: 각 정렬 옵션 테스트
            result = await service.comprehensive_filter_search(
                user_id=self.test_user_id,
                filter_criteria=sort_option
            )

            # Then: 정렬이 적용된 결과 확인
            assert "places" in result
            if sort_option["sort_by"] == "distance":
                # 거리순의 경우 distance_km 필드 확인
                for place in result["places"]:
                    assert "distance_km" in place

    async def test_pagination_with_filters(self):
        """
        Given: 페이지네이션과 필터 조건
        When: 페이지별 필터링을 수행함
        Then: 올바른 페이지네이션과 함께 필터된 결과를 반환함
        """
        # Given: 페이지네이션 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {"categories": ["cafe"]}

        # When: 첫 번째 페이지
        page1 = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria,
            limit=10,
            offset=0
        )

        # When: 두 번째 페이지
        page2 = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria,
            limit=10,
            offset=10
        )

        # Then: 페이지네이션 정보 확인
        assert "pagination" in page1
        assert "pagination" in page2
        assert page1["pagination"]["limit"] == 10
        assert page1["pagination"]["offset"] == 0
        assert page2["pagination"]["offset"] == 10

    async def test_empty_results_handling(self):
        """
        Given: 조건에 맞는 결과가 없는 필터
        When: 빈 결과 검색을 수행함
        Then: 빈 결과와 대안 제안을 반환함
        """
        # Given: 빈 결과 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        # 매우 제한적인 필터 조건
        restrictive_filter = {
            "categories": ["nonexistent_category"],
            "rating_min": 5.0,
            "price_ranges": ["1-5"],
        }

        mock_empty_result = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {}
        }
        
        self.mock_es_manager.search.return_value = mock_empty_result

        # When: 빈 결과 검색
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=restrictive_filter
        )

        # Then: 빈 결과 처리 확인
        assert result["total"] == 0
        assert len(result["places"]) == 0
        assert "suggestions" in result  # 대안 제안 제공
        assert result["suggestions"]["message"] == "검색 조건을 완화해보세요"

    async def test_performance_optimization(self):
        """
        Given: 성능 최적화 설정
        When: 대용량 데이터에서 필터링을 수행함
        Then: 최적화된 쿼리로 빠른 응답을 제공함
        """
        # Given: 성능 최적화 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        # When: 성능 테스트 필터링
        start_time = datetime.utcnow()
        
        result = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria={"categories": ["cafe"]},
            optimization_mode=True
        )

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        # Then: 성능 기준 확인
        assert "performance" in result
        assert response_time < 3000  # 3초 이내 응답
        assert result["performance"]["optimized"] is True

    async def test_filter_cache_integration(self):
        """
        Given: 필터 결과 캐싱 설정
        When: 동일한 필터를 반복 요청함
        Then: 캐시된 결과를 빠르게 반환함
        """
        # Given: 캐시 통합 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        filter_criteria = {"categories": ["cafe"], "regions": ["마포구"]}

        # Mock 캐시 키 생성
        cache_key = service._generate_filter_cache_key(self.test_user_id, filter_criteria)

        # 첫 번째 요청 - 캐시 미스
        self.mock_redis.get.return_value = None

        # When: 첫 번째 필터링 (캐시 저장)
        result1 = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # 두 번째 요청 - 캐시 히트
        cached_result = json.dumps({"places": [], "total": 0, "cached": True})
        self.mock_redis.get.return_value = cached_result

        # When: 두 번째 필터링 (캐시 사용)
        result2 = await service.comprehensive_filter_search(
            user_id=self.test_user_id,
            filter_criteria=filter_criteria
        )

        # Then: 캐시 사용 확인
        assert result2.get("cached") is True
        self.mock_redis.set.assert_called()  # 첫 번째 요청에서 캐시 저장
        self.mock_redis.get.assert_called()  # 두 번째 요청에서 캐시 조회

    async def test_error_handling_and_fallback(self):
        """
        Given: Elasticsearch 장애 상황
        When: 필터링을 시도함
        Then: PostgreSQL 기본 검색으로 fallback함
        """
        # Given: 에러 핸들링 테스트 서비스
        service = AdvancedFilterService(self.mock_db, self.mock_redis, self.mock_es_manager)

        # Elasticsearch 에러 시뮬레이션
        self.mock_es_manager.search.side_effect = Exception("ES connection failed")

        # PostgreSQL fallback 결과 Mock
        mock_pg_results = [
            (self.mock_places[0], 0.8),  # (place, similarity_score)
        ]

        with patch.object(service, '_fallback_postgresql_filter') as mock_fallback:
            mock_fallback.return_value = {
                "places": [{"name": "홍대 감성 카페", "source": "postgresql"}],
                "total": 1,
                "source": "postgresql_fallback"
            }

            # When: 에러 상황에서 필터링
            result = await service.comprehensive_filter_search(
                user_id=self.test_user_id,
                filter_criteria={"categories": ["cafe"]}
            )

            # Then: PostgreSQL fallback 확인
            assert result["source"] == "postgresql_fallback"
            assert len(result["places"]) >= 1
            mock_fallback.assert_called_once()