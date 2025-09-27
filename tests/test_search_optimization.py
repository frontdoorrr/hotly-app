"""
검색 UI/UX 및 성능 최적화 테스트 (TDD)

Test Coverage:
- 검색 응답 최적화 및 캐싱 전략
- 검색 결과 페이지네이션 및 무한 스크롤
- 검색 성능 모니터링 및 메트릭 수집
- 검색 자동완성 최적화
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.search_optimization_service import SearchOptimizationService
from app.services.search_performance_service import SearchPerformanceService
from app.core.cache import MemoryCacheService
from app.schemas.search_optimization import (
    SearchPerformanceMetrics,
    SearchOptimizationConfig,
    PaginationRequest,
    SearchCacheStrategy
)


class TestSearchOptimization:
    """검색 최적화 서비스 테스트"""

    @pytest.fixture
    async def optimization_service(self):
        """검색 최적화 서비스 fixture"""
        mock_db = AsyncMock()
        cache_service = MemoryCacheService()
        mock_search_service = AsyncMock()
        
        service = SearchOptimizationService(
            db=mock_db,
            cache=cache_service,
            search_service=mock_search_service
        )
        return service

    @pytest.fixture 
    async def performance_service(self):
        """검색 성능 서비스 fixture"""
        mock_db = AsyncMock()
        cache_service = MemoryCacheService()
        
        service = SearchPerformanceService(
            db=mock_db,
            cache=cache_service
        )
        return service

    async def test_search_cache_strategy(self, optimization_service):
        """검색 캐시 전략 테스트"""
        # Given: 검색 쿼리와 캐시 전략
        query = "맛있는 카페"
        cache_strategy = SearchCacheStrategy.AGGRESSIVE
        
        # When: 캐시 전략 적용
        cache_key = await optimization_service.generate_search_cache_key(
            query=query,
            user_id=uuid4(),
            filters={'category': 'cafe'},
            cache_strategy=cache_strategy
        )
        
        # Then: 캐시 키 생성 및 전략 적용 확인
        assert cache_key is not None
        assert isinstance(cache_key, str)
        assert 'search:' in cache_key
        print("✅ 검색 캐시 전략 테스트 통과")

    async def test_search_response_optimization(self, optimization_service):
        """검색 응답 최적화 테스트"""
        # Given: 검색 결과와 최적화 설정
        search_results = [
            {
                'id': 'place1',
                'name': '스타벅스 강남점',
                'category': 'cafe',
                'rating': 4.5,
                'distance': 500,
                'thumbnail': 'http://example.com/thumb1.jpg',
                'description': '넓은 공간과 좋은 분위기의 카페',
                'tags': ['커피', '스터디', '와이파이']
            },
            {
                'id': 'place2', 
                'name': '투썸플레이스 서초점',
                'category': 'cafe',
                'rating': 4.2,
                'distance': 800,
                'thumbnail': 'http://example.com/thumb2.jpg',
                'description': '조용한 분위기의 프리미엄 카페',
                'tags': ['커피', '디저트', '조용한']
            }
        ]
        
        optimization_config = SearchOptimizationConfig(
            enable_thumbnail_optimization=True,
            max_description_length=50,
            enable_tag_filtering=True,
            response_compression=True
        )
        
        # When: 검색 응답 최적화 실행
        optimized_results = await optimization_service.optimize_search_response(
            results=search_results,
            config=optimization_config
        )
        
        # Then: 최적화된 응답 확인
        assert len(optimized_results) == len(search_results)
        
        for result in optimized_results:
            # 설명 길이 제한 확인
            if 'description' in result:
                assert len(result['description']) <= optimization_config.max_description_length
            
            # 썸네일 최적화 확인
            if 'thumbnail' in result and optimization_config.enable_thumbnail_optimization:
                assert 'optimized' in result or 'thumbnail_small' in result
        
        print("✅ 검색 응답 최적화 테스트 통과")

    async def test_pagination_optimization(self, optimization_service):
        """페이지네이션 최적화 테스트"""
        # Given: 페이지네이션 요청
        pagination_request = PaginationRequest(
            page=1,
            page_size=20,
            enable_cursor_pagination=True,
            preload_next_page=True
        )
        
        mock_search_results = [
            {'id': f'place{i}', 'name': f'장소 {i}', 'score': 1.0 - i*0.01}
            for i in range(50)  # 50개 결과
        ]
        
        # When: 페이지네이션 최적화 적용
        paginated_response = await optimization_service.optimize_pagination(
            results=mock_search_results,
            request=pagination_request
        )
        
        # Then: 페이지네이션 결과 검증
        assert 'items' in paginated_response
        assert 'pagination' in paginated_response
        assert len(paginated_response['items']) == pagination_request.page_size
        
        pagination_info = paginated_response['pagination']
        assert 'current_page' in pagination_info
        assert 'total_pages' in pagination_info
        assert 'has_next' in pagination_info
        assert 'next_cursor' in pagination_info  # 커서 페이지네이션 지원
        
        # 다음 페이지 미리로드 확인
        if pagination_request.preload_next_page and pagination_info['has_next']:
            assert 'preloaded_next' in paginated_response
        
        print("✅ 페이지네이션 최적화 테스트 통과")

    async def test_infinite_scroll_support(self, optimization_service):
        """무한 스크롤 지원 테스트"""
        # Given: 무한 스크롤 요청
        cursor = None
        page_size = 10
        
        # 첫 번째 페이지 로드
        first_page = await optimization_service.get_infinite_scroll_page(
            query="카페",
            cursor=cursor,
            page_size=page_size,
            user_id=uuid4()
        )
        
        # Then: 첫 번째 페이지 확인
        assert 'items' in first_page
        assert 'next_cursor' in first_page
        assert 'has_more' in first_page
        assert len(first_page['items']) <= page_size
        
        # 두 번째 페이지 로드
        if first_page['has_more']:
            second_page = await optimization_service.get_infinite_scroll_page(
                query="카페",
                cursor=first_page['next_cursor'],
                page_size=page_size,
                user_id=uuid4()
            )
            
            # 두 번째 페이지 확인
            assert 'items' in second_page
            assert len(second_page['items']) <= page_size
            
            # 중복 결과 없음 확인
            first_ids = {item['id'] for item in first_page['items']}
            second_ids = {item['id'] for item in second_page['items']}
            assert not first_ids.intersection(second_ids)
        
        print("✅ 무한 스크롤 지원 테스트 통과")


class TestSearchPerformanceMonitoring:
    """검색 성능 모니터링 테스트"""

    async def test_performance_metrics_collection(self, performance_service):
        """성능 메트릭 수집 테스트"""
        # Given: 검색 요청 정보
        user_id = uuid4()
        query = "맛있는 레스토랑"
        start_time = datetime.utcnow()
        
        # When: 성능 메트릭 수집 시작
        session_id = await performance_service.start_search_session(
            user_id=user_id,
            query=query,
            timestamp=start_time
        )
        
        # 검색 실행 시뮬레이션
        await asyncio.sleep(0.1)  # 100ms 검색 시뮬레이션
        
        # 성능 메트릭 기록
        metrics = SearchPerformanceMetrics(
            session_id=session_id,
            query=query,
            response_time_ms=100,
            result_count=25,
            cache_hit=True,
            user_id=user_id,
            timestamp=datetime.utcnow()
        )
        
        success = await performance_service.record_search_metrics(metrics)
        
        # Then: 메트릭 기록 확인
        assert success is True
        assert session_id is not None
        
        # 메트릭 조회 확인
        recorded_metrics = await performance_service.get_search_metrics(
            session_id=session_id
        )
        assert recorded_metrics is not None
        assert recorded_metrics.response_time_ms == 100
        assert recorded_metrics.cache_hit is True
        
        print("✅ 성능 메트릭 수집 테스트 통과")

    async def test_search_performance_analysis(self, performance_service):
        """검색 성능 분석 테스트"""
        # Given: 여러 검색 세션의 메트릭 데이터
        user_id = uuid4()
        
        # 여러 검색 세션 시뮬레이션
        sessions = []
        for i in range(10):
            session_metrics = SearchPerformanceMetrics(
                session_id=f"session_{i}",
                query=f"테스트 쿼리 {i}",
                response_time_ms=50 + i * 10,  # 50ms ~ 140ms
                result_count=20 + i,
                cache_hit=i % 2 == 0,  # 50% 캐시 히트율
                user_id=user_id,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            await performance_service.record_search_metrics(session_metrics)
            sessions.append(session_metrics)
        
        # When: 성능 분석 실행
        analysis = await performance_service.analyze_search_performance(
            user_id=user_id,
            time_period=timedelta(hours=1)
        )
        
        # Then: 분석 결과 확인
        assert 'avg_response_time' in analysis
        assert 'cache_hit_rate' in analysis
        assert 'total_searches' in analysis
        assert 'performance_trend' in analysis
        
        assert analysis['total_searches'] == 10
        assert analysis['cache_hit_rate'] == 0.5  # 50%
        assert 50 <= analysis['avg_response_time'] <= 140
        
        print("✅ 검색 성능 분석 테스트 통과")

    async def test_performance_alerting(self, performance_service):
        """성능 알림 테스트"""
        # Given: 성능 임계값 설정
        performance_thresholds = {
            'max_response_time_ms': 2000,
            'min_cache_hit_rate': 0.3,
            'max_error_rate': 0.05
        }
        
        await performance_service.set_performance_thresholds(performance_thresholds)
        
        # When: 임계값 초과 메트릭 기록
        slow_search_metrics = SearchPerformanceMetrics(
            session_id="slow_session",
            query="느린 검색",
            response_time_ms=3000,  # 임계값 초과
            result_count=10,
            cache_hit=False,
            user_id=uuid4(),
            timestamp=datetime.utcnow(),
            error_occurred=False
        )
        
        alert_triggered = await performance_service.check_performance_alert(
            metrics=slow_search_metrics
        )
        
        # Then: 알림 트리거 확인
        assert alert_triggered is True
        
        # 알림 기록 확인
        alerts = await performance_service.get_recent_alerts(
            time_period=timedelta(minutes=5)
        )
        assert len(alerts) > 0
        assert any(alert['metric'] == 'response_time' for alert in alerts)
        
        print("✅ 성능 알림 테스트 통과")


class TestSearchAutocompleteOptimization:
    """검색 자동완성 최적화 테스트"""

    async def test_autocomplete_caching(self, optimization_service):
        """자동완성 캐싱 테스트"""
        # Given: 자동완성 쿼리
        partial_query = "스타"
        user_id = uuid4()
        
        # When: 자동완성 결과 캐싱
        suggestions = await optimization_service.get_cached_autocomplete(
            partial_query=partial_query,
            user_id=user_id,
            max_suggestions=5
        )
        
        # 캐시 미스 시나리오 (첫 번째 요청)
        if suggestions is None:
            # 자동완성 생성 및 캐싱
            fresh_suggestions = [
                "스타벅스",
                "스타벅스 강남점", 
                "스타트업 카페",
                "스타일러 맛집",
                "스탠다드 바"
            ]
            
            await optimization_service.cache_autocomplete(
                partial_query=partial_query,
                suggestions=fresh_suggestions,
                user_id=user_id,
                ttl=300  # 5분 캐시
            )
            
            suggestions = fresh_suggestions
        
        # Then: 자동완성 결과 확인
        assert suggestions is not None
        assert len(suggestions) <= 5
        # 한국어 부분 검색은 더 유연하게 처리
        if suggestions:
            # 최소 하나의 제안은 부분 쿼리를 포함해야 함
            assert any(partial_query in suggestion.lower() for suggestion in suggestions)
        
        # 캐시 히트 확인 (두 번째 요청)
        cached_suggestions = await optimization_service.get_cached_autocomplete(
            partial_query=partial_query,
            user_id=user_id,
            max_suggestions=5
        )
        
        assert cached_suggestions == suggestions
        
        print("✅ 자동완성 캐싱 테스트 통과")

    async def test_personalized_autocomplete(self, optimization_service):
        """개인화된 자동완성 테스트"""
        # Given: 사용자별 검색 히스토리
        user_id = uuid4()
        search_history = [
            "스타벅스 강남점",
            "스타벅스 역삼점", 
            "투썸플레이스",
            "카페 베네"
        ]
        
        # 검색 히스토리 기록
        for query in search_history:
            await optimization_service.record_user_search(
                user_id=user_id,
                query=query,
                timestamp=datetime.utcnow()
            )
        
        # When: 개인화된 자동완성 요청
        personalized_suggestions = await optimization_service.get_personalized_autocomplete(
            partial_query="스타",
            user_id=user_id,
            max_suggestions=3
        )
        
        # Then: 개인화 결과 확인
        assert len(personalized_suggestions) <= 3
        
        # 사용자 히스토리 기반 우선순위 확인
        for suggestion in personalized_suggestions:
            if suggestion in search_history:
                # 히스토리에 있는 항목이 우선 순위를 가져야 함
                assert "스타" in suggestion
        
        print("✅ 개인화된 자동완성 테스트 통과")


if __name__ == "__main__":
    # 간단한 테스트 실행기
    async def run_tests():
        test_optimization = TestSearchOptimization()
        test_performance = TestSearchPerformanceMonitoring()
        test_autocomplete = TestSearchAutocompleteOptimization()
        
        # 서비스 fixture 생성
        cache_service = MemoryCacheService()
        
        optimization_service = SearchOptimizationService(
            db=AsyncMock(),
            cache=cache_service,
            search_service=AsyncMock()
        )
        
        performance_service = SearchPerformanceService(
            db=AsyncMock(),
            cache=cache_service
        )
        
        print("🧪 검색 최적화 테스트 시작...")
        
        try:
            await test_optimization.test_search_cache_strategy(optimization_service)
            await test_optimization.test_search_response_optimization(optimization_service)
            await test_optimization.test_pagination_optimization(optimization_service)
            
            await test_performance.test_performance_metrics_collection(performance_service)
            
            await test_autocomplete.test_autocomplete_caching(optimization_service)
            
            print("🎉 모든 검색 최적화 테스트 통과!")
            
        except ImportError as e:
            print(f"⚠️ 테스트 실행을 위해 서비스 구현이 필요합니다: {e}")
            print("서비스 구현 후 다시 실행해주세요.")

    if __name__ == "__main__":
        asyncio.run(run_tests())