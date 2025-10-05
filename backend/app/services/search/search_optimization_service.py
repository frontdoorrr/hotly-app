"""
검색 UI/UX 및 성능 최적화 서비스

이 서비스는 검색 응답 최적화, 페이지네이션, 무한 스크롤,
자동완성 캐싱 등의 기능을 제공합니다.
"""
import base64
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.cache import CacheService
from app.schemas.search_optimization import (
    PaginationRequest,
    PaginationResponse,
    SearchCacheStrategy,
    SearchOptimizationConfig,
)

logger = logging.getLogger(__name__)


class SearchOptimizationService:
    """검색 최적화 서비스"""

    def __init__(self, db, cache: CacheService, search_service):
        """
        검색 최적화 서비스 초기화

        Args:
            db: 데이터베이스 세션
            cache: 캐시 서비스
            search_service: 검색 서비스
        """
        self.db = db
        self.cache = cache
        self.search_service = search_service

        # 캐시 TTL 설정
        self.cache_ttl = {
            SearchCacheStrategy.CONSERVATIVE: 300,  # 5분
            SearchCacheStrategy.BALANCED: 900,  # 15분
            SearchCacheStrategy.AGGRESSIVE: 3600,  # 1시간
        }

        # 최적화 설정
        self.optimization_config = SearchOptimizationConfig()

    # 검색 성능 최적화 메서드들

    async def generate_search_cache_key(
        self,
        query: str,
        user_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        cache_strategy: SearchCacheStrategy = SearchCacheStrategy.BALANCED,
    ) -> str:
        """
        검색 캐시 키 생성

        Args:
            query: 검색 쿼리
            user_id: 사용자 ID
            filters: 검색 필터
            cache_strategy: 캐시 전략

        Returns:
            캐시 키 문자열
        """
        try:
            # 필터 정규화
            normalized_filters = self._normalize_filters(filters or {})

            # 캐시 키 구성 요소
            key_components = {
                "query": query.lower().strip(),
                "user_id": str(user_id),
                "filters": normalized_filters,
                "strategy": cache_strategy.value,
            }

            # 해시 생성
            key_string = json.dumps(key_components, sort_keys=True)
            key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]

            cache_key = f"search:optimized:{key_hash}"

            logger.debug(f"Generated search cache key: {cache_key}")
            return cache_key

        except Exception as e:
            logger.error(f"Failed to generate search cache key: {e}")
            # 기본 캐시 키 반환
            return f"search:basic:{hashlib.md5(query.encode()).hexdigest()[:8]}"

    async def optimize_search_response(
        self, results: List[Dict[str, Any]], config: SearchOptimizationConfig
    ) -> List[Dict[str, Any]]:
        """
        검색 응답 최적화

        Args:
            results: 원본 검색 결과
            config: 최적화 설정

        Returns:
            최적화된 검색 결과
        """
        try:
            optimized_results = []

            for result in results:
                optimized_result = result.copy()

                # 설명 길이 제한
                if "description" in optimized_result and config.max_description_length:
                    description = optimized_result["description"]
                    if len(description) > config.max_description_length:
                        optimized_result["description"] = (
                            description[: config.max_description_length - 3] + "..."
                        )

                # 썸네일 최적화
                if (
                    config.enable_thumbnail_optimization
                    and "thumbnail" in optimized_result
                ):
                    optimized_result["thumbnail_small"] = self._optimize_thumbnail_url(
                        optimized_result["thumbnail"]
                    )
                    optimized_result["optimized"] = True

                # 태그 필터링
                if config.enable_tag_filtering and "tags" in optimized_result:
                    optimized_result["tags"] = self._filter_relevant_tags(
                        optimized_result["tags"]
                    )

                # 불필요한 필드 제거 (성능 최적화)
                self._remove_unnecessary_fields(optimized_result)

                # UI 친화적 데이터 추가
                self._add_ui_friendly_data(optimized_result)

                optimized_results.append(optimized_result)

            logger.info(f"Optimized {len(results)} search results")
            return optimized_results

        except Exception as e:
            logger.error(f"Search response optimization failed: {e}")
            return results  # 최적화 실패 시 원본 반환

    async def optimize_pagination(
        self, results: List[Dict[str, Any]], request: PaginationRequest
    ) -> Dict[str, Any]:
        """
        페이지네이션 최적화

        Args:
            results: 검색 결과
            request: 페이지네이션 요청

        Returns:
            페이지네이션된 응답
        """
        try:
            total_items = len(results)
            total_pages = (total_items + request.page_size - 1) // request.page_size

            # 현재 페이지 결과 추출
            start_idx = (request.page - 1) * request.page_size
            end_idx = start_idx + request.page_size
            page_items = results[start_idx:end_idx]

            # 페이지네이션 정보 구성
            pagination_info = PaginationResponse(
                current_page=request.page,
                page_size=request.page_size,
                total_pages=total_pages,
                total_items=total_items,
                has_next=request.page < total_pages,
                has_previous=request.page > 1,
            )

            # 커서 페이지네이션 지원
            if request.enable_cursor_pagination:
                next_cursor = (
                    self._generate_cursor(
                        page_items[-1] if page_items else None, request.page + 1
                    )
                    if pagination_info.has_next
                    else None
                )

                previous_cursor = (
                    self._generate_cursor(
                        page_items[0] if page_items else None, request.page - 1
                    )
                    if request.page > 1
                    else None
                )

                # 페이지네이션 응답에 커서 정보 추가
                pagination_info.next_cursor = next_cursor
                pagination_info.previous_cursor = previous_cursor

            response = {"items": page_items, "pagination": pagination_info.dict()}

            # 다음 페이지 미리로드
            if (
                request.preload_next_page
                and pagination_info.has_next
                and end_idx < total_items
            ):
                preload_end = min(end_idx + request.page_size, total_items)
                response["preloaded_next"] = results[end_idx:preload_end]

            logger.info(
                f"Optimized pagination: page {request.page}/{total_pages}, "
                f"items {len(page_items)}/{total_items}"
            )

            return response

        except Exception as e:
            logger.error(f"Pagination optimization failed: {e}")
            return {
                "items": results[: request.page_size],
                "pagination": {
                    "current_page": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                },
            }

    async def get_infinite_scroll_page(
        self, query: str, cursor: Optional[str], page_size: int, user_id: UUID
    ) -> Dict[str, Any]:
        """
        무한 스크롤 페이지 조회

        Args:
            query: 검색 쿼리
            cursor: 페이지 커서
            page_size: 페이지 크기
            user_id: 사용자 ID

        Returns:
            무한 스크롤 응답
        """
        try:
            # 커서 파싱
            offset = self._parse_cursor(cursor) if cursor else 0

            # 캐시된 결과 조회
            cache_key = await self.generate_search_cache_key(
                query=query,
                user_id=user_id,
                filters={"offset": offset, "limit": page_size},
            )

            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for infinite scroll: {cache_key}")
                return cached_response

            # 검색 서비스에서 결과 조회
            search_results = await self.search_service.search_places(
                query=query,
                user_id=user_id,
                offset=offset,
                limit=page_size + 1,  # 다음 페이지 존재 여부 확인용
            )

            has_more = len(search_results) > page_size
            items = search_results[:page_size] if has_more else search_results

            # 다음 커서 생성
            next_cursor = (
                self._generate_cursor(items[-1] if items else None, offset + page_size)
                if has_more
                else None
            )

            response = {
                "items": items,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total_loaded": offset + len(items),
            }

            # 응답 캐싱
            await self.cache.set(
                cache_key, response, ttl=self.cache_ttl[SearchCacheStrategy.BALANCED]
            )

            logger.info(
                f"Infinite scroll page loaded: offset={offset}, "
                f"items={len(items)}, has_more={has_more}"
            )

            return response

        except Exception as e:
            logger.error(f"Infinite scroll failed: {e}")
            return {
                "items": [],
                "next_cursor": None,
                "has_more": False,
                "total_loaded": 0,
            }

    # 자동완성 최적화 메서드들

    async def get_cached_autocomplete(
        self, partial_query: str, user_id: UUID, max_suggestions: int = 5
    ) -> Optional[List[str]]:
        """
        캐시된 자동완성 결과 조회

        Args:
            partial_query: 부분 쿼리
            user_id: 사용자 ID
            max_suggestions: 최대 제안 수

        Returns:
            자동완성 제안 목록 (캐시 미스 시 None)
        """
        try:
            # 자동완성 캐시 키 생성
            cache_key = self._generate_autocomplete_cache_key(partial_query, user_id)

            # 캐시에서 조회
            cached_suggestions = await self.cache.get(cache_key)
            if cached_suggestions:
                logger.debug(f"Autocomplete cache hit: {partial_query}")
                return cached_suggestions[:max_suggestions]

            return None

        except Exception as e:
            logger.error(f"Autocomplete cache retrieval failed: {e}")
            return None

    async def cache_autocomplete(
        self, partial_query: str, suggestions: List[str], user_id: UUID, ttl: int = 300
    ) -> bool:
        """
        자동완성 결과 캐싱

        Args:
            partial_query: 부분 쿼리
            suggestions: 자동완성 제안
            user_id: 사용자 ID
            ttl: 캐시 TTL (초)

        Returns:
            캐싱 성공 여부
        """
        try:
            cache_key = self._generate_autocomplete_cache_key(partial_query, user_id)

            success = await self.cache.set(cache_key, suggestions, ttl)

            if success:
                logger.debug(
                    f"Cached autocomplete: {partial_query} -> {len(suggestions)} suggestions"
                )

            return success

        except Exception as e:
            logger.error(f"Autocomplete caching failed: {e}")
            return False

    async def get_personalized_autocomplete(
        self, partial_query: str, user_id: UUID, max_suggestions: int = 5
    ) -> List[str]:
        """
        개인화된 자동완성 제안

        Args:
            partial_query: 부분 쿼리
            user_id: 사용자 ID
            max_suggestions: 최대 제안 수

        Returns:
            개인화된 자동완성 제안
        """
        try:
            suggestions = []

            # 사용자 검색 히스토리 조회
            history_key = f"search:history:{user_id}"
            search_history = await self.cache.get(history_key) or []

            # 히스토리에서 매칭되는 쿼리 찾기
            for record in search_history:
                query = record["query"]
                if partial_query.lower() in query.lower() and query not in suggestions:
                    suggestions.append(query)

                    if len(suggestions) >= max_suggestions:
                        break

            # 부족한 경우 일반 자동완성으로 보완
            if len(suggestions) < max_suggestions:
                general_suggestions = await self._get_general_autocomplete(
                    partial_query, max_suggestions - len(suggestions)
                )

                for suggestion in general_suggestions:
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)

            logger.info(
                f"Generated {len(suggestions)} personalized autocomplete "
                f"suggestions for: {partial_query}"
            )

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Personalized autocomplete failed: {e}")
            return []

    # 실시간 검색 기능

    async def process_realtime_search(
        self, query: str, user_id: UUID, search_type: str = "instant"
    ) -> Dict[str, Any]:
        """
        실시간 검색 처리

        Args:
            query: 검색 쿼리
            user_id: 사용자 ID
            search_type: 검색 타입 (instant, as_you_type)

        Returns:
            실시간 검색 결과
        """
        try:
            # 최소 검색어 길이 확인
            if len(query.strip()) < 2:
                return {
                    "results": [],
                    "suggestions": [],
                    "query_time": 0,
                    "cache_hit": False,
                }

            start_time = time.time()

            # 실시간 캐시 키 생성
            realtime_cache_key = f"realtime:search:{user_id}:{hashlib.md5(query.encode()).hexdigest()[:8]}"

            # 캐시 조회 (짧은 TTL 적용)
            cached_result = await self.cache.get(realtime_cache_key)
            if cached_result:
                cached_result["cache_hit"] = True
                return cached_result

            # 검색 실행
            search_results = await self.search_service.search_places(
                query=query,
                user_id=user_id,
                limit=10,  # 실시간 검색은 적은 수로 제한
                quick_search=True,
            )

            # 자동완성 제안 생성
            suggestions = await self.get_personalized_autocomplete(
                query, user_id, max_suggestions=3
            )

            query_time = (time.time() - start_time) * 1000  # ms 단위

            result = {
                "results": search_results[:5],  # 실시간은 5개로 제한
                "suggestions": suggestions,
                "query_time": round(query_time, 2),
                "cache_hit": False,
                "total_found": len(search_results),
            }

            # 결과 캐싱 (30초 TTL)
            await self.cache.set(realtime_cache_key, result, ttl=30)

            logger.info(f"Realtime search completed: {query} in {query_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"Realtime search failed: {e}")
            return {
                "results": [],
                "suggestions": [],
                "query_time": 0,
                "cache_hit": False,
                "error": str(e),
            }

    # 검색 히스토리 관리

    async def record_user_search(
        self, user_id: UUID, query: str, timestamp: datetime
    ) -> bool:
        """
        사용자 검색 기록 저장

        Args:
            user_id: 사용자 ID
            query: 검색 쿼리
            timestamp: 검색 시간

        Returns:
            기록 성공 여부
        """
        try:
            # 검색 히스토리 캐시 키
            history_key = f"search:history:{user_id}"

            # 기존 히스토리 조회
            history = await self.cache.get(history_key) or []

            # 새 검색 기록 추가
            search_record = {
                "query": query,
                "timestamp": timestamp.isoformat(),
                "count": 1,
            }

            # 중복 쿼리 처리
            updated = False
            for record in history:
                if record["query"] == query:
                    record["count"] += 1
                    record["timestamp"] = timestamp.isoformat()
                    updated = True
                    break

            if not updated:
                history.append(search_record)

            # 최신 순으로 정렬 및 제한 (최대 100개)
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            history = history[:100]

            # 캐시 업데이트
            await self.cache.set(history_key, history, ttl=86400)  # 24시간

            # 인기 검색어 업데이트
            await self._update_popular_queries(query)

            return True

        except Exception as e:
            logger.error(f"User search recording failed: {e}")
            return False

    async def get_search_history(
        self, user_id: UUID, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        사용자 검색 히스토리 조회

        Args:
            user_id: 사용자 ID
            limit: 조회 제한

        Returns:
            검색 히스토리 목록
        """
        try:
            history_key = f"search:history:{user_id}"
            history = await self.cache.get(history_key) or []

            return history[:limit]

        except Exception as e:
            logger.error(f"Get search history failed: {e}")
            return []

    async def clear_search_history(self, user_id: UUID) -> bool:
        """
        검색 히스토리 삭제

        Args:
            user_id: 사용자 ID

        Returns:
            삭제 성공 여부
        """
        try:
            history_key = f"search:history:{user_id}"
            await self.cache.delete(history_key)

            logger.info(f"Cleared search history for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Clear search history failed: {e}")
            return False

    # 성능 메트릭 수집

    async def record_search_metrics(
        self,
        user_id: UUID,
        query: str,
        response_time: float,
        result_count: int,
        cache_hit: bool,
        client_metrics: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        검색 성능 메트릭 기록

        Args:
            user_id: 사용자 ID
            query: 검색 쿼리
            response_time: 응답 시간 (ms)
            result_count: 결과 개수
            cache_hit: 캐시 적중 여부
            client_metrics: 클라이언트 메트릭

        Returns:
            기록 성공 여부
        """
        try:
            metrics = {
                "user_id": str(user_id),
                "query": query,
                "query_length": len(query),
                "response_time": response_time,
                "result_count": result_count,
                "cache_hit": cache_hit,
                "timestamp": datetime.utcnow().isoformat(),
                "client_metrics": client_metrics or {},
            }

            # 메트릭 캐시에 저장 (배치 처리용)
            metrics_key = f"search:metrics:{datetime.utcnow().strftime('%Y%m%d')}"
            daily_metrics = await self.cache.get(metrics_key) or []
            daily_metrics.append(metrics)

            # 일일 메트릭 업데이트 (최대 1000개)
            if len(daily_metrics) > 1000:
                daily_metrics = daily_metrics[-1000:]

            await self.cache.set(metrics_key, daily_metrics, ttl=86400 * 7)  # 7일간 보관

            # 실시간 통계 업데이트
            await self._update_realtime_stats(response_time, cache_hit)

            logger.debug(f"Recorded search metrics: {query} in {response_time}ms")
            return True

        except Exception as e:
            logger.error(f"Record search metrics failed: {e}")
            return False

    async def get_search_performance_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        검색 성능 통계 조회

        Args:
            days: 조회 기간 (일)

        Returns:
            성능 통계
        """
        try:
            stats = {
                "average_response_time": 0,
                "cache_hit_rate": 0,
                "total_searches": 0,
                "daily_stats": [],
            }

            total_response_time = 0
            total_cache_hits = 0
            total_searches = 0

            # 일별 메트릭 수집
            for i in range(days):
                date = datetime.utcnow() - timedelta(days=i)
                metrics_key = f"search:metrics:{date.strftime('%Y%m%d')}"
                daily_metrics = await self.cache.get(metrics_key) or []

                if daily_metrics:
                    day_response_times = [m["response_time"] for m in daily_metrics]
                    day_cache_hits = sum(1 for m in daily_metrics if m["cache_hit"])
                    day_total = len(daily_metrics)

                    daily_stat = {
                        "date": date.strftime("%Y-%m-%d"),
                        "searches": day_total,
                        "avg_response_time": sum(day_response_times) / day_total
                        if day_total > 0
                        else 0,
                        "cache_hit_rate": (day_cache_hits / day_total * 100)
                        if day_total > 0
                        else 0,
                    }

                    stats["daily_stats"].append(daily_stat)

                    total_response_time += sum(day_response_times)
                    total_cache_hits += day_cache_hits
                    total_searches += day_total

            # 전체 통계 계산
            if total_searches > 0:
                stats["average_response_time"] = total_response_time / total_searches
                stats["cache_hit_rate"] = (total_cache_hits / total_searches) * 100
                stats["total_searches"] = total_searches

            return stats

        except Exception as e:
            logger.error(f"Get search performance stats failed: {e}")
            return {
                "average_response_time": 0,
                "cache_hit_rate": 0,
                "total_searches": 0,
                "daily_stats": [],
            }

    # Private 헬퍼 메서드들

    def _normalize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """필터 정규화"""
        normalized = {}
        for key, value in filters.items():
            if isinstance(value, list):
                normalized[key] = sorted(value)
            else:
                normalized[key] = value
        return dict(sorted(normalized.items()))

    def _optimize_thumbnail_url(self, thumbnail_url: str) -> str:
        """썸네일 URL 최적화"""
        # 실제 구현에서는 이미지 리사이징 서비스 연동
        if "?" in thumbnail_url:
            return f"{thumbnail_url}&size=small"
        else:
            return f"{thumbnail_url}?size=small"

    def _filter_relevant_tags(self, tags: List[str]) -> List[str]:
        """관련 태그 필터링"""
        # 중요한 태그만 유지 (최대 5개)
        return tags[:5]

    def _remove_unnecessary_fields(self, result: Dict[str, Any]) -> None:
        """불필요한 필드 제거"""
        unnecessary_fields = ["internal_id", "raw_data", "debug_info", "metadata"]
        for field in unnecessary_fields:
            result.pop(field, None)

    def _add_ui_friendly_data(self, result: Dict[str, Any]) -> None:
        """UI 친화적 데이터 추가"""
        # 거리 포맷팅
        if "distance" in result and isinstance(result["distance"], (int, float)):
            if result["distance"] < 1000:
                result["distance_formatted"] = f"{int(result['distance'])}m"
            else:
                result["distance_formatted"] = f"{result['distance']/1000:.1f}km"

        # 평점 스타 생성
        if "rating" in result:
            rating = float(result["rating"])
            result["rating_stars"] = "★" * int(rating) + "☆" * (5 - int(rating))

        # 이미지 최적화 플래그
        if "images" in result and len(result["images"]) > 0:
            result["has_images"] = True
            result["image_count"] = len(result["images"])
        else:
            result["has_images"] = False
            result["image_count"] = 0

    def _generate_cursor(self, last_item: Optional[Dict[str, Any]], offset: int) -> str:
        """페이지네이션 커서 생성"""
        if last_item:
            cursor_data = {
                "id": last_item.get("id"),
                "score": last_item.get("score", 0),
                "offset": offset,
            }
        else:
            cursor_data = {"offset": offset}

        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()

    def _parse_cursor(self, cursor: str) -> int:
        """커서 파싱"""
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            cursor_data = json.loads(cursor_json)
            return cursor_data.get("offset", 0)
        except Exception:
            return 0

    def _generate_autocomplete_cache_key(
        self, partial_query: str, user_id: UUID
    ) -> str:
        """자동완성 캐시 키 생성"""
        query_hash = hashlib.md5(partial_query.lower().encode()).hexdigest()[:8]
        return f"autocomplete:{user_id}:{query_hash}"

    async def _get_general_autocomplete(
        self, partial_query: str, max_suggestions: int
    ) -> List[str]:
        """일반 자동완성 제안 (구현 예시)"""
        # 실제로는 Elasticsearch나 전용 자동완성 서비스 사용
        general_suggestions = [
            f"{partial_query}벅스",
            f"{partial_query}일리언 레스토랑",
            f"{partial_query}드커피",
            f"{partial_query}디오",
            f"{partial_query}터디 카페",
        ]
        return general_suggestions[:max_suggestions]

    async def _update_popular_queries(self, query: str) -> None:
        """인기 검색어 업데이트"""
        try:
            popular_key = "search:popular:queries"
            popular_queries = await self.cache.get(popular_key) or {}

            # 쿼리 카운트 증가
            popular_queries[query] = popular_queries.get(query, 0) + 1

            # 인기 검색어 제한 (최대 1000개)
            if len(popular_queries) > 1000:
                # 카운트 기준으로 상위 100개만 유지
                sorted_queries = sorted(
                    popular_queries.items(), key=lambda x: x[1], reverse=True
                )[:100]
                popular_queries = dict(sorted_queries)

            await self.cache.set(popular_key, popular_queries, ttl=86400)

        except Exception as e:
            logger.error(f"Update popular queries failed: {e}")

    async def _update_realtime_stats(
        self, response_time: float, cache_hit: bool
    ) -> None:
        """실시간 통계 업데이트"""
        try:
            stats_key = "search:realtime:stats"
            stats = await self.cache.get(stats_key) or {
                "total_searches": 0,
                "total_response_time": 0,
                "cache_hits": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

            stats["total_searches"] += 1
            stats["total_response_time"] += response_time
            if cache_hit:
                stats["cache_hits"] += 1
            stats["last_updated"] = datetime.utcnow().isoformat()

            await self.cache.set(stats_key, stats, ttl=300)  # 5분

        except Exception as e:
            logger.error(f"Update realtime stats failed: {e}")

    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 검색어 조회"""
        try:
            popular_key = "search:popular:queries"
            popular_queries = await self.cache.get(popular_key) or {}

            # 카운트 기준으로 정렬
            sorted_queries = sorted(
                popular_queries.items(), key=lambda x: x[1], reverse=True
            )

            result = []
            for query, count in sorted_queries[:limit]:
                result.append({"query": query, "count": count, "rank": len(result) + 1})

            return result

        except Exception as e:
            logger.error(f"Get popular queries failed: {e}")
            return []
