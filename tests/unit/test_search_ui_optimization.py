"""
검색 UI/UX 최적화 기능 테스트

검색 최적화, 성능 모니터링, 실시간 검색 등의 기능을 테스트합니다.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.search_optimization import (
    PaginationRequest,
    SearchCacheStrategy,
    SearchOptimizationConfig,
    SearchPerformanceMetrics,
)
from app.services.search_optimization_service import SearchOptimizationService
from app.services.search_performance_service import SearchPerformanceService


class TestSearchOptimizationService:
    """검색 최적화 서비스 테스트"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        cache = AsyncMock()
        cache.get.return_value = None
        cache.set.return_value = True
        cache.delete.return_value = True
        return cache

    @pytest.fixture
    def mock_search_service(self):
        service = AsyncMock()
        service.search_places.return_value = [
            {
                "id": "1",
                "name": "테스트 카페",
                "description": "맛있는 커피를 파는 카페입니다",
                "category": "cafe",
                "rating": 4.5,
                "distance": 250,
                "tags": ["커피", "디저트", "무선인터넷"],
                "thumbnail": "https://example.com/image.jpg",
            },
            {
                "id": "2",
                "name": "테스트 레스토랑",
                "description": "신선한 재료로 만든 맛있는 요리를 제공하는 레스토랑입니다",
                "category": "restaurant",
                "rating": 4.2,
                "distance": 500,
                "tags": ["한식", "점심", "저녁"],
                "thumbnail": "https://example.com/image2.jpg",
            },
        ]
        return service

    @pytest.fixture
    def optimization_service(self, mock_db, mock_cache, mock_search_service):
        return SearchOptimizationService(mock_db, mock_cache, mock_search_service)

    @pytest.mark.asyncio
    async def test_generate_search_cache_key(self, optimization_service):
        """검색 캐시 키 생성 테스트"""
        user_id = uuid4()
        query = "테스트 쿼리"
        filters = {"category": "cafe", "distance": 1000}

        cache_key = await optimization_service.generate_search_cache_key(
            query=query,
            user_id=user_id,
            filters=filters,
            cache_strategy=SearchCacheStrategy.BALANCED,
        )

        assert cache_key.startswith("search:optimized:")
        assert len(cache_key.split(":")) == 3

    @pytest.mark.asyncio
    async def test_optimize_search_response(self, optimization_service):
        """검색 응답 최적화 테스트"""
        results = [
            {
                "id": "1",
                "name": "테스트 카페",
                "description": "매우 긴 설명이 들어있는 카페입니다. " * 20,
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
                "thumbnail": "https://example.com/image.jpg",
                "internal_id": "internal_123",
                "metadata": {"debug": "info"},
            }
        ]

        config = SearchOptimizationConfig(
            max_description_length=100,
            enable_thumbnail_optimization=True,
            enable_tag_filtering=True,
        )

        optimized_results = await optimization_service.optimize_search_response(
            results=results, config=config
        )

        assert len(optimized_results) == 1
        result = optimized_results[0]

        # 설명 길이 제한 확인
        assert len(result["description"]) <= 103  # 100 + "..."
        assert result["description"].endswith("...")

        # 썸네일 최적화 확인
        assert "thumbnail_small" in result
        assert "size=small" in result["thumbnail_small"]

        # 태그 필터링 확인 (최대 5개)
        assert len(result["tags"]) <= 5

        # 불필요한 필드 제거 확인
        assert "internal_id" not in result
        assert "metadata" not in result

        # UI 친화적 데이터 추가 확인
        assert "has_images" in result
        assert "image_count" in result

    @pytest.mark.asyncio
    async def test_optimize_pagination(self, optimization_service):
        """페이지네이션 최적화 테스트"""
        results = [{"id": str(i), "name": f"아이템 {i}"} for i in range(50)]

        pagination_request = PaginationRequest(
            page=2, page_size=10, enable_cursor_pagination=True, preload_next_page=True
        )

        paginated_response = await optimization_service.optimize_pagination(
            results=results, request=pagination_request
        )

        assert len(paginated_response["items"]) == 10
        assert paginated_response["pagination"]["current_page"] == 2
        assert paginated_response["pagination"]["total_pages"] == 5
        assert paginated_response["pagination"]["has_next"] is True
        assert paginated_response["pagination"]["has_previous"] is True

        # 미리로드된 다음 페이지 확인
        assert "preloaded_next" in paginated_response
        assert len(paginated_response["preloaded_next"]) == 10

    @pytest.mark.asyncio
    async def test_process_realtime_search(self, optimization_service, mock_cache):
        """실시간 검색 처리 테스트"""
        user_id = uuid4()
        query = "테스트"

        # 캐시 미스 시나리오
        mock_cache.get.return_value = None

        result = await optimization_service.process_realtime_search(
            query=query, user_id=user_id, search_type="instant"
        )

        assert "results" in result
        assert "suggestions" in result
        assert "query_time" in result
        assert "cache_hit" in result
        assert result["cache_hit"] is False
        assert len(result["results"]) <= 5  # 실시간 검색은 5개로 제한

    @pytest.mark.asyncio
    async def test_personalized_autocomplete(self, optimization_service, mock_cache):
        """개인화된 자동완성 테스트"""
        user_id = uuid4()
        partial_query = "테스트"

        # Mock 검색 히스토리
        mock_cache.get.return_value = [
            {"query": "테스트 카페", "timestamp": datetime.utcnow().isoformat(), "count": 5},
            {
                "query": "테스트 레스토랑",
                "timestamp": datetime.utcnow().isoformat(),
                "count": 3,
            },
            {"query": "다른 검색어", "timestamp": datetime.utcnow().isoformat(), "count": 2},
        ]

        suggestions = await optimization_service.get_personalized_autocomplete(
            partial_query=partial_query, user_id=user_id, max_suggestions=5
        )

        assert len(suggestions) <= 5
        # 히스토리에서 매칭되는 쿼리들이 포함되어야 함
        matching_suggestions = [s for s in suggestions if partial_query in s]
        assert len(matching_suggestions) >= 2

    @pytest.mark.asyncio
    async def test_record_user_search(self, optimization_service, mock_cache):
        """사용자 검색 기록 저장 테스트"""
        user_id = uuid4()
        query = "테스트 쿼리"
        timestamp = datetime.utcnow()

        # 빈 히스토리에서 시작
        mock_cache.get.return_value = []

        success = await optimization_service.record_user_search(
            user_id=user_id, query=query, timestamp=timestamp
        )

        assert success is True

        # 캐시 set이 호출되었는지 확인
        mock_cache.set.assert_called()

        # 인기 검색어 업데이트 호출 확인 (내부적으로)
        # 실제로는 _update_popular_queries가 호출되는지 확인해야 함

    @pytest.mark.asyncio
    async def test_get_infinite_scroll_page(self, optimization_service, mock_cache):
        """무한 스크롤 페이지 조회 테스트"""
        user_id = uuid4()
        query = "테스트"
        page_size = 10

        # 캐시 미스
        mock_cache.get.return_value = None

        response = await optimization_service.get_infinite_scroll_page(
            query=query, cursor=None, page_size=page_size, user_id=user_id
        )

        assert "items" in response
        assert "next_cursor" in response
        assert "has_more" in response
        assert "total_loaded" in response
        assert len(response["items"]) <= page_size


class TestSearchPerformanceService:
    """검색 성능 서비스 테스트"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        cache = AsyncMock()
        cache.get.return_value = None
        cache.set.return_value = True
        return cache

    @pytest.fixture
    def performance_service(self, mock_db, mock_cache):
        return SearchPerformanceService(mock_db, mock_cache)

    @pytest.mark.asyncio
    async def test_start_search_session(self, performance_service, mock_cache):
        """검색 세션 시작 테스트"""
        user_id = uuid4()
        query = "테스트 쿼리"
        timestamp = datetime.utcnow()

        session_id = await performance_service.start_search_session(
            user_id=user_id, query=query, timestamp=timestamp
        )

        assert session_id is not None
        assert len(session_id) > 0

        # 세션 정보가 캐시에 저장되었는지 확인
        mock_cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_record_search_metrics(self, performance_service, mock_cache):
        """검색 성능 메트릭 기록 테스트"""
        metrics = SearchPerformanceMetrics(
            session_id="test_session",
            query="테스트 쿼리",
            response_time_ms=250.5,
            result_count=15,
            cache_hit=True,
            user_id=uuid4(),
            timestamp=datetime.utcnow(),
            error_occurred=False,
        )

        success = await performance_service.record_search_metrics(metrics)

        assert success is True

        # 메트릭이 캐시에 저장되었는지 확인
        mock_cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_check_performance_alert(self, performance_service):
        """성능 알림 확인 테스트"""
        # 느린 응답 시간으로 알림 트리거
        slow_metrics = SearchPerformanceMetrics(
            session_id="slow_session",
            query="느린 쿼리",
            response_time_ms=3000,  # 3초 (임계값 초과)
            result_count=5,
            cache_hit=False,
            user_id=uuid4(),
            timestamp=datetime.utcnow(),
            error_occurred=False,
        )

        alert_triggered = await performance_service.check_performance_alert(
            slow_metrics
        )

        assert alert_triggered is True

    @pytest.mark.asyncio
    async def test_analyze_search_performance(self, performance_service):
        """검색 성능 분석 테스트"""
        user_id = uuid4()
        time_period = timedelta(days=7)

        analysis = await performance_service.analyze_search_performance(
            user_id=user_id, time_period=time_period
        )

        assert "total_searches" in analysis
        assert "avg_response_time" in analysis
        assert "cache_hit_rate" in analysis
        assert "error_rate" in analysis
        assert "performance_trend" in analysis
        assert "hourly_stats" in analysis

        # Mock 데이터가 있으므로 총 검색 수가 0보다 커야 함
        assert analysis["total_searches"] > 0

    @pytest.mark.asyncio
    async def test_generate_ui_optimization_report(self, performance_service):
        """UI 최적화 리포트 생성 테스트"""
        user_id = uuid4()
        time_period = timedelta(days=7)

        report = await performance_service.generate_ui_optimization_report(
            user_id=user_id, time_period=time_period
        )

        assert "user_id" in report
        assert "report_period" in report
        assert "total_searches" in report
        assert "performance_stats" in report
        assert "recommendations" in report
        assert "autocomplete_usage_rate" in report
        assert "infinite_scroll_usage_rate" in report
        assert "filter_usage_rate" in report

        # 추천 사항이 있어야 함
        assert len(report["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_search_heatmap(self, performance_service):
        """검색 히트맵 분석 테스트"""
        time_period = timedelta(days=7)

        heatmap_data = await performance_service.analyze_search_heatmap(time_period)

        assert len(heatmap_data) == 7 * 24  # 7일 × 24시간

        for data_point in heatmap_data[:5]:  # 일부만 확인
            assert "hour" in data_point
            assert "day_of_week" in data_point
            assert "search_count" in data_point
            assert "average_response_time" in data_point
            assert "success_rate" in data_point

            assert 0 <= data_point["hour"] <= 23
            assert 0 <= data_point["day_of_week"] <= 6
            assert data_point["search_count"] > 0
            assert data_point["average_response_time"] > 0
            assert 0 <= data_point["success_rate"] <= 1

    @pytest.mark.asyncio
    async def test_detect_search_anomalies(self, performance_service):
        """검색 이상 징후 탐지 테스트"""
        time_period = timedelta(hours=24)

        anomalies = await performance_service.detect_search_anomalies(time_period)

        # Mock 구현에서는 일부 이상 징후가 감지될 수 있음
        assert isinstance(anomalies, list)

        # 이상 징후가 감지된 경우 구조 확인
        if anomalies:
            anomaly = anomalies[0]
            assert "type" in anomaly
            assert "severity" in anomaly
            assert "current_value" in anomaly
            assert "message" in anomaly
            assert "detected_at" in anomaly

    @pytest.mark.asyncio
    async def test_calculate_search_quality_score(self, performance_service):
        """검색 품질 점수 계산 테스트"""
        query = "맛집 추천"
        results = [
            {"id": "1", "category": "restaurant", "updated_recently": True},
            {"id": "2", "category": "cafe", "updated_recently": False},
            {"id": "3", "category": "restaurant", "updated_recently": True},
        ]
        user_feedback = {"rating": 4}

        quality_score = await performance_service.calculate_search_quality_score(
            query=query, results=results, user_feedback=user_feedback
        )

        assert "relevance_score" in quality_score
        assert "diversity_score" in quality_score
        assert "freshness_score" in quality_score
        assert "overall_score" in quality_score
        assert "factors" in quality_score

        # 점수는 0과 1 사이여야 함
        for score_key in [
            "relevance_score",
            "diversity_score",
            "freshness_score",
            "overall_score",
        ]:
            score = quality_score[score_key]
            assert 0 <= score <= 1, f"{score_key}: {score} is not between 0 and 1"

    @pytest.mark.asyncio
    async def test_track_search_ab_test_metrics(self, performance_service, mock_cache):
        """A/B 테스트 메트릭 추적 테스트"""
        user_id = uuid4()
        variant = "variant_a"
        metrics = {
            "response_time_ms": 250,
            "result_count": 15,
            "user_interaction_count": 3,
            "conversion": True,
        }

        mock_cache.get.return_value = []  # 빈 일별 데이터

        success = await performance_service.track_search_ab_test_metrics(
            user_id=user_id, variant=variant, metrics=metrics
        )

        assert success is True

        # A/B 테스트 데이터가 캐시에 저장되었는지 확인
        mock_cache.set.assert_called()


class TestSearchUIIntegration:
    """검색 UI 통합 테스트"""

    @pytest.mark.asyncio
    async def test_complete_search_flow(self):
        """완전한 검색 플로우 통합 테스트"""
        # Mock 서비스들 설정
        mock_db = MagicMock()
        mock_cache = AsyncMock()
        mock_search_service = AsyncMock()

        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        mock_search_service.search_places.return_value = [
            {"id": "1", "name": "통합테스트 카페", "category": "cafe"}
        ]

        # 서비스 초기화
        optimization_service = SearchOptimizationService(
            mock_db, mock_cache, mock_search_service
        )
        performance_service = SearchPerformanceService(mock_db, mock_cache)

        user_id = uuid4()
        query = "통합테스트"

        # 1. 검색 세션 시작
        session_id = await performance_service.start_search_session(
            user_id=user_id, query=query, timestamp=datetime.utcnow()
        )

        # 2. 실시간 검색 수행
        realtime_result = await optimization_service.process_realtime_search(
            query=query, user_id=user_id, search_type="instant"
        )

        # 3. 검색 기록 저장
        await optimization_service.record_user_search(
            user_id=user_id, query=query, timestamp=datetime.utcnow()
        )

        # 4. 성능 메트릭 기록
        metrics = SearchPerformanceMetrics(
            session_id=session_id,
            query=query,
            response_time_ms=realtime_result["query_time"],
            result_count=len(realtime_result["results"]),
            cache_hit=realtime_result["cache_hit"],
            user_id=user_id,
            timestamp=datetime.utcnow(),
        )

        await performance_service.record_search_metrics(metrics)

        # 5. 결과 검증
        assert session_id is not None
        assert "results" in realtime_result
        assert "query_time" in realtime_result

        # Mock 호출 검증
        assert mock_cache.set.call_count >= 2  # 세션 정보, 메트릭 최소 2회 저장
        mock_search_service.search_places.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
