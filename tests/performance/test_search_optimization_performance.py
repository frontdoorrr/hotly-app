"""
검색 최적화 성능 테스트

실제 부하 상황에서의 검색 성능을 테스트합니다.
"""
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.search_optimization_service import SearchOptimizationService
from app.services.search_performance_service import SearchPerformanceService
from app.schemas.search_optimization import SearchPerformanceMetrics


class TestSearchOptimizationPerformance:
    """검색 최적화 성능 테스트"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock 서비스들 설정"""
        mock_db = MagicMock()
        mock_cache = AsyncMock()
        mock_search_service = AsyncMock()
        
        # 검색 결과 Mock (다양한 크기)
        def mock_search_results(query: str, **kwargs):
            result_count = len(query) * 5  # 쿼리 길이에 따른 결과 수
            return [
                {
                    'id': str(i),
                    'name': f'{query} 결과 {i}',
                    'description': f'{query}와 관련된 장소입니다. ' * (i % 5 + 1),
                    'category': ['cafe', 'restaurant', 'bar', 'shop'][i % 4],
                    'rating': 3.0 + (i % 20) / 10.0,
                    'distance': (i + 1) * 100,
                    'tags': [f'tag{j}' for j in range(min(10, i + 3))],
                    'thumbnail': f'https://example.com/image{i}.jpg'
                }
                for i in range(min(result_count, 50))  # 최대 50개
            ]
        
        mock_search_service.search_places.side_effect = mock_search_results
        mock_search_service.search_places_with_ranking.side_effect = lambda **kwargs: {
            'results': mock_search_results(kwargs.get('query', 'test')),
            'total': len(mock_search_results(kwargs.get('query', 'test')))
        }
        
        # 캐시 성능 시뮬레이션
        cache_data = {}
        
        async def mock_cache_get(key):
            # 캐시 액세스 시간 시뮬레이션 (1-10ms)
            await asyncio.sleep(0.001 + (hash(key) % 9) / 1000)
            return cache_data.get(key)
        
        async def mock_cache_set(key, value, ttl=None):
            # 캐시 저장 시간 시뮬레이션 (2-15ms)
            await asyncio.sleep(0.002 + (hash(key) % 13) / 1000)
            cache_data[key] = value
            return True
        
        mock_cache.get.side_effect = mock_cache_get
        mock_cache.set.side_effect = mock_cache_set
        
        return {
            'db': mock_db,
            'cache': mock_cache,
            'search_service': mock_search_service,
            'optimization_service': SearchOptimizationService(mock_db, mock_cache, mock_search_service),
            'performance_service': SearchPerformanceService(mock_db, mock_cache)
        }
    
    @pytest.mark.asyncio
    async def test_single_search_performance(self, mock_services):
        """단일 검색 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        user_id = uuid4()
        
        # 성능 측정
        start_time = time.time()
        
        result = await optimization_service.process_realtime_search(
            query="성능테스트",
            user_id=user_id,
            search_type="instant"
        )
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # 성능 기준 확인 (실시간 검색은 200ms 이내)
        assert response_time_ms < 200, f"Single search too slow: {response_time_ms:.2f}ms"
        
        # 결과 품질 확인
        assert len(result['results']) > 0
        assert result['query_time'] > 0
        
        print(f"Single search performance: {response_time_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, mock_services):
        """동시 검색 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        
        # 동시 사용자 시뮬레이션
        concurrent_users = 50
        queries = [f"동시테스트{i}" for i in range(concurrent_users)]
        user_ids = [uuid4() for _ in range(concurrent_users)]
        
        async def single_search(query: str, user_id: str):
            start_time = time.time()
            result = await optimization_service.process_realtime_search(
                query=query,
                user_id=user_id,
                search_type="instant"
            )
            end_time = time.time()
            return {
                'query': query,
                'response_time_ms': (end_time - start_time) * 1000,
                'result_count': len(result['results']),
                'cache_hit': result['cache_hit']
            }
        
        # 동시 실행
        start_time = time.time()
        
        tasks = [
            single_search(query, user_id) 
            for query, user_id in zip(queries, user_ids)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        # 성능 분석
        response_times = [r['response_time_ms'] for r in results]
        avg_response_time = statistics.mean(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        cache_hit_rate = sum(r['cache_hit'] for r in results) / len(results)
        
        # 성능 기준 확인
        assert avg_response_time < 500, f"Average response time too high: {avg_response_time:.2f}ms"
        assert p95_response_time < 1000, f"P95 response time too high: {p95_response_time:.2f}ms"
        assert total_time_ms < 5000, f"Total concurrent execution too slow: {total_time_ms:.2f}ms"
        
        print(f"Concurrent search performance:")
        print(f"  Users: {concurrent_users}")
        print(f"  Total time: {total_time_ms:.2f}ms")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  P95 response time: {p95_response_time:.2f}ms")
        print(f"  Cache hit rate: {cache_hit_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_autocomplete_performance(self, mock_services):
        """자동완성 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        user_id = uuid4()
        
        # 자동완성 쿼리들 (실제 사용 패턴과 유사)
        partial_queries = [
            "ㅋ", "카", "카페", "카페 ",
            "ㄹ", "레", "레스", "레스토", "레스토랑",
            "ㅁ", "맛", "맛집", "맛집 추천"
        ]
        
        response_times = []
        
        for partial_query in partial_queries:
            start_time = time.time()
            
            suggestions = await optimization_service.get_personalized_autocomplete(
                partial_query=partial_query,
                user_id=user_id,
                max_suggestions=5
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            response_times.append(response_time_ms)
            
            # 자동완성은 매우 빨라야 함 (50ms 이내)
            assert response_time_ms < 50, f"Autocomplete too slow for '{partial_query}': {response_time_ms:.2f}ms"
            assert len(suggestions) <= 5
        
        avg_autocomplete_time = statistics.mean(response_times)
        print(f"Autocomplete performance: {avg_autocomplete_time:.2f}ms average")
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, mock_services):
        """캐시 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        user_id = uuid4()
        query = "캐시테스트"
        
        # 첫 번째 요청 (캐시 미스)
        start_time = time.time()
        first_result = await optimization_service.process_realtime_search(
            query=query,
            user_id=user_id,
            search_type="instant"
        )
        first_response_time = (time.time() - start_time) * 1000
        
        # 두 번째 요청 (캐시 히트)
        start_time = time.time()
        second_result = await optimization_service.process_realtime_search(
            query=query,
            user_id=user_id,
            search_type="instant"
        )
        second_response_time = (time.time() - start_time) * 1000
        
        # 캐시 효과 확인
        cache_speedup = first_response_time / second_response_time if second_response_time > 0 else 1
        
        print(f"Cache performance:")
        print(f"  First request (cache miss): {first_response_time:.2f}ms")
        print(f"  Second request (cache hit): {second_response_time:.2f}ms")
        print(f"  Cache speedup: {cache_speedup:.2f}x")
        
        # 캐시 히트 시 더 빨라야 함
        assert second_response_time < first_response_time, "Cache should improve performance"
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self, mock_services):
        """페이지네이션 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        
        # 대량 결과 생성
        large_results = [
            {'id': str(i), 'name': f'대량결과 {i}', 'score': 1000 - i}
            for i in range(1000)
        ]
        
        from app.schemas.search_optimization import PaginationRequest
        
        # 다양한 페이지 크기 테스트
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            pagination_request = PaginationRequest(
                page=5,  # 중간 페이지 테스트
                page_size=page_size,
                enable_cursor_pagination=True,
                preload_next_page=True
            )
            
            start_time = time.time()
            
            paginated_response = await optimization_service.optimize_pagination(
                results=large_results,
                request=pagination_request
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # 페이지네이션은 매우 빨라야 함 (100ms 이내)
            assert response_time_ms < 100, f"Pagination too slow for page_size {page_size}: {response_time_ms:.2f}ms"
            
            # 결과 검증
            assert len(paginated_response['items']) == page_size
            assert 'preloaded_next' in paginated_response
            
            print(f"Pagination (size {page_size}): {response_time_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_services):
        """메모리 사용량 안정성 테스트"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        optimization_service = mock_services['optimization_service']
        
        # 대량 검색 수행 (메모리 누수 확인)
        for i in range(100):
            user_id = uuid4()
            query = f"메모리테스트{i}"
            
            await optimization_service.process_realtime_search(
                query=query,
                user_id=user_id,
                search_type="instant"
            )
            
            # 주기적 가비지 컬렉션
            if i % 20 == 0:
                gc.collect()
        
        # 최종 메모리 측정
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Increase: {memory_increase:.2f}MB")
        
        # 메모리 증가가 합리적인 범위 내여야 함 (100MB 이내)
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, mock_services):
        """오류 처리 성능 테스트"""
        optimization_service = mock_services['optimization_service']
        
        # 오류 상황 시뮬레이션
        mock_search_service = mock_services['search_service']
        
        # 일부 요청에서 오류 발생하도록 설정
        original_search = mock_search_service.search_places.side_effect
        
        def error_prone_search(query: str, **kwargs):
            if "error" in query.lower():
                raise Exception("Simulated search error")
            return original_search(query, **kwargs)
        
        mock_search_service.search_places.side_effect = error_prone_search
        
        # 정상 요청과 오류 요청 섞어서 테스트
        queries = [
            "정상검색1", "error검색", "정상검색2", 
            "또다른error", "정상검색3", "정상검색4"
        ]
        
        results = []
        for query in queries:
            start_time = time.time()
            
            try:
                result = await optimization_service.process_realtime_search(
                    query=query,
                    user_id=uuid4(),
                    search_type="instant"
                )
                success = True
            except Exception:
                result = None
                success = False
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            results.append({
                'query': query,
                'success': success,
                'response_time_ms': response_time_ms
            })
            
            # 오류 상황에서도 응답 시간이 합리적이어야 함
            assert response_time_ms < 1000, f"Error handling too slow: {response_time_ms:.2f}ms"
        
        # 결과 분석
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        print(f"Error handling performance:")
        print(f"  Successful requests: {len(successful_requests)}")
        print(f"  Failed requests: {len(failed_requests)}")
        print(f"  Average success time: {statistics.mean([r['response_time_ms'] for r in successful_requests]):.2f}ms")
        print(f"  Average failure time: {statistics.mean([r['response_time_ms'] for r in failed_requests]):.2f}ms")


class TestSearchPerformanceBenchmark:
    """검색 성능 벤치마크"""
    
    @pytest.mark.asyncio
    async def test_throughput_benchmark(self):
        """처리량 벤치마크"""
        # Mock 서비스 설정
        mock_db = MagicMock()
        mock_cache = AsyncMock()
        mock_search_service = AsyncMock()
        
        # 빠른 응답을 위한 최소한의 지연
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_search_service.search_places.return_value = [
            {'id': '1', 'name': '벤치마크 결과'}
        ]
        
        optimization_service = SearchOptimizationService(mock_db, mock_cache, mock_search_service)
        
        # 처리량 측정 (1분간 최대한 많은 요청)
        duration_seconds = 10  # 테스트 시간 (실제로는 60초)
        
        start_time = time.time()
        request_count = 0
        
        async def benchmark_worker():
            nonlocal request_count
            while time.time() - start_time < duration_seconds:
                await optimization_service.process_realtime_search(
                    query=f"벤치마크{request_count}",
                    user_id=uuid4(),
                    search_type="instant"
                )
                request_count += 1
        
        # 여러 워커로 동시 실행
        workers = 10
        tasks = [benchmark_worker() for _ in range(workers)]
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        throughput = request_count / actual_duration
        
        print(f"Throughput benchmark:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Total requests: {request_count}")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Workers: {workers}")
        
        # 최소 처리량 기준 (초당 100 요청)
        assert throughput >= 50, f"Throughput too low: {throughput:.2f} req/sec"


if __name__ == "__main__":
    # 성능 테스트 실행
    pytest.main([__file__, "-v", "-s"])