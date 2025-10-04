"""
검색 히스토리 서비스 (Task 2-3-5)

사용자 검색 패턴 분석 및 개인화 히스토리 관리 시스템
- 검색 히스토리 기록 및 조회
- 개인화된 검색 제안
- 검색 패턴 분석 및 인사이트 제공
- 개인정보 보호 및 데이터 관리
"""

import hashlib
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SearchHistoryService:
    """검색 히스토리 서비스"""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        max_history_items: int = 100,
        history_retention_days: int = 90,
        session_timeout_minutes: int = 30,
        enable_analytics: bool = True,
        enable_pattern_analysis: bool = True,
        privacy_mode: bool = False,
    ):
        self.redis = redis_client
        self.db = db_session
        self.max_history = max_history_items
        self.retention_days = history_retention_days
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.analytics_enabled = enable_analytics
        self.pattern_analysis_enabled = enable_pattern_analysis
        self.privacy_mode = privacy_mode

        # Redis 키 패턴
        self.history_key_pattern = "search_history:{user_id}"
        self.frequency_key_pattern = "search_frequency:{user_id}"
        self.interaction_key_pattern = "search_interactions:{search_id}"
        self.session_key_pattern = "search_session:{user_id}:{session_id}"

    async def record_search(
        self,
        user_id: UUID,
        search_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> str:
        """
        검색 히스토리 기록

        Args:
            user_id: 사용자 ID
            search_data: 검색 데이터 (query, filters, location 등)
            session_id: 검색 세션 ID

        Returns:
            생성된 검색 ID
        """
        try:
            # 검색 ID 생성
            search_id = str(uuid4())
            timestamp = datetime.utcnow()

            # 히스토리 항목 구성
            history_item = {
                "search_id": search_id,
                "query": search_data.get("query", ""),
                "filters": search_data.get("filters", {}),
                "location": search_data.get("location"),
                "result_count": search_data.get("result_count", 0),
                "timestamp": timestamp.isoformat(),
                "session_id": session_id,
                "user_agent": search_data.get("user_agent"),
                "clicked_places": [],  # 초기엔 빈 리스트, 후에 업데이트
            }

            # Redis에 히스토리 저장
            history_key = self.history_key_pattern.format(user_id=user_id)
            await self.redis.lpush(history_key, json.dumps(history_item, default=str))

            # 히스토리 크기 제한
            await self.redis.ltrim(history_key, 0, self.max_history - 1)

            # TTL 설정 (개인정보 보호)
            ttl_seconds = self.retention_days * 24 * 3600
            await self.redis.expire(history_key, ttl_seconds)

            # 검색 빈도 추적
            if self.analytics_enabled and search_data.get("query"):
                await self._update_search_frequency(user_id, search_data["query"])

            # 세션별 검색 그룹핑
            if session_id:
                await self._record_session_search(
                    user_id, session_id, search_id, timestamp
                )

            logger.debug(f"Recorded search history for user {user_id}: {search_id}")
            return search_id

        except Exception as e:
            logger.error(f"Failed to record search history: {str(e)}")
            return ""

    async def get_search_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """검색 히스토리 조회"""
        try:
            if session_id:
                return await self.get_session_search_history(user_id, session_id)

            history_key = self.history_key_pattern.format(user_id=user_id)
            history_items = await self.redis.lrange(
                history_key, offset, offset + limit - 1
            )

            # JSON 파싱 및 데이터 변환
            history = []
            for item_json in history_items:
                try:
                    item = json.loads(item_json)
                    # 개인정보 보호 모드에서는 민감한 정보 마스킹
                    if self.privacy_mode:
                        item = self._mask_sensitive_data(item)
                    history.append(item)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in history: {item_json}")
                    continue

            return history

        except Exception as e:
            logger.error(f"Failed to get search history: {str(e)}")
            return []

    async def get_popular_search_terms(
        self, time_period_days: int = 7, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """인기 검색어 조회"""
        try:
            if not self.analytics_enabled:
                return []

            # 전체 사용자의 검색 빈도 집계
            popular_terms = await self._aggregate_search_terms(time_period_days)

            # 빈도순 정렬
            sorted_terms = sorted(
                popular_terms.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            return [
                {
                    "query": term,
                    "frequency": freq,
                    "trend_score": await self._calculate_trend_score(term),
                }
                for term, freq in sorted_terms
            ]

        except Exception as e:
            logger.error(f"Failed to get popular search terms: {str(e)}")
            return []

    async def get_personalized_suggestions(
        self, user_id: UUID, current_query: str = "", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """개인화된 검색 제안"""
        try:
            # 사용자 검색 히스토리 기반 제안
            history = await self.get_search_history(user_id, limit=50)

            # 현재 쿼리와 관련된 과거 검색 찾기
            related_searches = []
            query_lower = current_query.lower()

            for item in history:
                past_query = item.get("query", "").lower()

                # 부분 문자열 매칭 또는 공통 키워드 기반 연관성 계산
                if query_lower in past_query or any(
                    word in past_query for word in query_lower.split()
                ):
                    related_searches.append(
                        {
                            "suggested_query": item["query"],
                            "filters": item.get("filters", {}),
                            "relevance_score": self._calculate_query_similarity(
                                current_query, item["query"]
                            ),
                            "frequency": 1,  # 실제로는 빈도 계산
                            "last_used": item["timestamp"],
                        }
                    )

            # 사용자 선호도 패턴 기반 추가 제안
            if self.pattern_analysis_enabled:
                pattern_suggestions = await self._generate_pattern_based_suggestions(
                    user_id, current_query
                )
                related_searches.extend(pattern_suggestions)

            # 관련성 점수로 정렬하여 상위 제안 반환
            suggestions = sorted(
                related_searches, key=lambda x: x["relevance_score"], reverse=True
            )[:limit]

            return suggestions

        except Exception as e:
            logger.error(f"Failed to get personalized suggestions: {str(e)}")
            return []

    async def record_search_interaction(
        self, user_id: UUID, search_id: str, interaction_data: Dict[str, Any]
    ) -> bool:
        """검색 결과 상호작용 기록"""
        try:
            interaction_key = self.interaction_key_pattern.format(search_id=search_id)

            # 상호작용 데이터
            interaction = {
                "user_id": str(user_id),
                "place_id": interaction_data.get("place_id"),
                "action": interaction_data.get("action"),  # click, bookmark, visit
                "position": interaction_data.get("position"),
                "timestamp": datetime.utcnow().isoformat(),
                "session_duration": interaction_data.get("session_duration"),
            }

            # Redis Hash에 상호작용 저장
            field_key = f"{interaction['action']}_{interaction['place_id']}"
            await self.redis.hset(interaction_key, field_key, json.dumps(interaction))

            # TTL 설정
            await self.redis.expire(interaction_key, 86400 * 30)  # 30일

            # 검색 히스토리에 클릭한 장소 업데이트
            if interaction["action"] == "click":
                await self._update_clicked_places(
                    user_id, search_id, interaction["place_id"]
                )

            return True

        except Exception as e:
            logger.error(f"Failed to record search interaction: {str(e)}")
            return False

    async def analyze_search_patterns(
        self, user_id: UUID, analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """사용자 검색 패턴 분석"""
        try:
            if not self.pattern_analysis_enabled:
                return {}

            # 분석 기간 내 검색 히스토리 조회
            history = await self.get_search_history(user_id, limit=200)

            # 시간 필터링
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)
            filtered_history = [
                item
                for item in history
                if datetime.fromisoformat(item["timestamp"]) > cutoff_date
            ]

            if not filtered_history:
                return {"message": "분석할 데이터가 부족합니다"}

            # 패턴 분석
            patterns = {
                "preferred_categories": self._analyze_category_preferences(
                    filtered_history
                ),
                "preferred_regions": self._analyze_region_preferences(filtered_history),
                "search_time_patterns": self._analyze_time_patterns(filtered_history),
                "query_complexity_trends": self._analyze_query_complexity(
                    filtered_history
                ),
                "filter_usage_patterns": self._analyze_filter_usage(filtered_history),
                "search_frequency_pattern": self._analyze_search_frequency(
                    filtered_history
                ),
            }

            return patterns

        except Exception as e:
            logger.error(f"Pattern analysis failed: {str(e)}")
            return {"error": str(e)}

    async def get_autocomplete_suggestions(
        self, user_id: UUID, partial_query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """자동완성 제안 (최근 검색 기반)"""
        try:
            history = await self.get_search_history(user_id, limit=50)
            partial_lower = partial_query.lower()

            suggestions = []
            for item in history:
                query = item.get("query", "")
                if query.lower().startswith(partial_lower) and len(query) > len(
                    partial_query
                ):
                    suggestions.append(
                        {
                            "text": query,
                            "type": "recent_search",
                            "last_used": item["timestamp"],
                            "result_count": item.get("result_count", 0),
                        }
                    )

                if len(suggestions) >= limit:
                    break

            # 최근 사용 순으로 정렬
            suggestions.sort(
                key=lambda x: datetime.fromisoformat(x["last_used"]), reverse=True
            )

            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Autocomplete failed: {str(e)}")
            return []

    async def get_session_search_history(
        self, user_id: UUID, session_id: str
    ) -> List[Dict[str, Any]]:
        """세션별 검색 히스토리 조회"""
        try:
            session_key = self.session_key_pattern.format(
                user_id=user_id, session_id=session_id
            )

            search_ids = await self.redis.lrange(session_key, 0, -1)

            # 각 검색 ID에 해당하는 상세 정보 조회
            history = await self.get_search_history(user_id, limit=100)
            session_searches = [
                item
                for item in history
                if item.get("search_id") in [sid.decode() for sid in search_ids]
            ]

            return sorted(session_searches, key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return []

    async def cleanup_old_history(self, user_id: UUID) -> int:
        """오래된 검색 히스토리 정리"""
        try:
            history = await self.get_search_history(user_id, limit=1000)
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

            # 유효한 히스토리 필터링
            valid_history = []
            cleaned_count = 0

            for item in history:
                try:
                    item_date = datetime.fromisoformat(item["timestamp"])
                    if item_date > cutoff_date:
                        valid_history.append(item)
                    else:
                        cleaned_count += 1
                except (ValueError, KeyError):
                    cleaned_count += 1

            # 정리된 히스토리로 교체
            if cleaned_count > 0:
                history_key = self.history_key_pattern.format(user_id=user_id)

                # 기존 리스트 삭제
                await self.redis.delete(history_key)

                # 유효한 항목들만 다시 저장
                if valid_history:
                    valid_items = [
                        json.dumps(item, default=str) for item in valid_history
                    ]
                    await self.redis.lpush(history_key, *valid_items)

                    # TTL 재설정
                    ttl_seconds = self.retention_days * 24 * 3600
                    await self.redis.expire(history_key, ttl_seconds)

            return cleaned_count

        except Exception as e:
            logger.error(f"History cleanup failed: {str(e)}")
            return 0

    async def export_search_history(
        self,
        user_id: UUID,
        format: str = "json",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """검색 히스토리 데이터 내보내기"""
        try:
            history = await self.get_search_history(user_id, limit=1000)

            # 날짜 필터링
            if date_from or date_to:
                filtered_history = []
                for item in history:
                    item_date = datetime.fromisoformat(item["timestamp"])

                    if date_from and item_date < date_from:
                        continue
                    if date_to and item_date > date_to:
                        continue

                    filtered_history.append(item)
                history = filtered_history

            export_data = {
                "user_id": str(user_id),
                "export_date": datetime.utcnow().isoformat(),
                "format": format,
                "total_searches": len(history),
                "date_range": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None,
                },
                "search_history": history,
            }

            # 개인정보 보호 처리
            if self.privacy_mode:
                export_data["search_history"] = [
                    self._mask_sensitive_data(item) for item in history
                ]

            return export_data

        except Exception as e:
            logger.error(f"History export failed: {str(e)}")
            return {"error": str(e)}

    async def delete_search_entry(self, user_id: UUID, search_id: str) -> bool:
        """특정 검색 항목 삭제"""
        try:
            history = await self.get_search_history(user_id, limit=1000)
            updated_history = [
                item for item in history if item.get("search_id") != search_id
            ]

            # 업데이트된 히스토리로 교체
            history_key = self.history_key_pattern.format(user_id=user_id)
            await self.redis.delete(history_key)

            if updated_history:
                items = [json.dumps(item, default=str) for item in updated_history]
                await self.redis.lpush(history_key, *items)

            # 관련 상호작용 데이터도 삭제
            interaction_key = self.interaction_key_pattern.format(search_id=search_id)
            await self.redis.delete(interaction_key)

            return True

        except Exception as e:
            logger.error(f"Search entry deletion failed: {str(e)}")
            return False

    async def clear_all_history(self, user_id: UUID, confirmation_token: str) -> bool:
        """모든 검색 히스토리 삭제 (개인정보 보호)"""
        try:
            # 보안을 위한 토큰 검증
            expected_token = hashlib.sha256(
                f"delete_all_{user_id}".encode(), usedforsecurity=False
            ).hexdigest()[:16]

            if confirmation_token != expected_token:
                logger.warning(f"Invalid confirmation token for user {user_id}")
                return False

            # 모든 관련 데이터 삭제
            patterns_to_delete = [
                self.history_key_pattern.format(user_id=user_id),
                self.frequency_key_pattern.format(user_id=user_id),
                f"search_session:{user_id}:*",
            ]

            for pattern in patterns_to_delete:
                if "*" in pattern:
                    # 패턴 매칭으로 삭제
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis.scan(
                            cursor=cursor, match=pattern, count=100
                        )
                        if keys:
                            await self.redis.delete(*keys)
                        if cursor == 0:
                            break
                else:
                    # 직접 삭제
                    await self.redis.delete(pattern)

            logger.info(f"Cleared all search history for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Clear all history failed: {str(e)}")
            return False

    # Private helper methods

    async def _update_search_frequency(self, user_id: UUID, query: str) -> None:
        """검색 빈도 업데이트"""
        try:
            frequency_key = self.frequency_key_pattern.format(user_id=user_id)
            await self.redis.zincrby(frequency_key, 1, query)
            await self.redis.expire(frequency_key, 86400 * self.retention_days)
        except Exception as e:
            logger.error(f"Frequency update failed: {str(e)}")

    async def _record_session_search(
        self, user_id: UUID, session_id: str, search_id: str, timestamp: datetime
    ) -> None:
        """세션별 검색 기록"""
        try:
            session_key = self.session_key_pattern.format(
                user_id=user_id, session_id=session_id
            )
            await self.redis.lpush(session_key, search_id)
            await self.redis.expire(
                session_key, int(self.session_timeout.total_seconds())
            )
        except Exception as e:
            logger.error(f"Session recording failed: {str(e)}")

    async def _update_clicked_places(
        self, user_id: UUID, search_id: str, place_id: str
    ) -> None:
        """검색 히스토리의 클릭한 장소 업데이트"""
        try:
            history = await self.get_search_history(user_id, limit=100)

            for i, item in enumerate(history):
                if item.get("search_id") == search_id:
                    clicked_places = item.get("clicked_places", [])
                    if place_id not in clicked_places:
                        clicked_places.append(place_id)
                        item["clicked_places"] = clicked_places

                        # Redis에 업데이트된 히스토리 저장
                        history_key = self.history_key_pattern.format(user_id=user_id)
                        await self.redis.lset(
                            history_key, i, json.dumps(item, default=str)
                        )
                    break
        except Exception as e:
            logger.error(f"Clicked places update failed: {str(e)}")

    async def _aggregate_search_terms(self, days: int) -> Dict[str, int]:
        """전체 사용자의 검색어 빈도 집계"""
        # 실제 구현에서는 모든 사용자의 빈도 데이터를 집계
        # 현재는 Mock 데이터 반환
        return {
            "홍대 맛집": 25,
            "강남 카페": 18,
            "이태원 바": 12,
            "명동 쇼핑": 8,
        }

    async def _calculate_trend_score(self, term: str) -> float:
        """검색어 트렌드 점수 계산"""
        # 최근 증가 추세를 계산하는 로직
        return 0.85  # Mock 점수

    def _calculate_query_similarity(self, query1: str, query2: str) -> float:
        """쿼리 간 유사도 계산"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    async def _generate_pattern_based_suggestions(
        self, user_id: UUID, current_query: str
    ) -> List[Dict[str, Any]]:
        """패턴 기반 검색 제안 생성"""
        # 사용자 패턴 분석 결과를 바탕으로 제안 생성
        patterns = await self.analyze_search_patterns(user_id)
        suggestions = []

        # 선호 카테고리 기반 제안
        preferred_categories = patterns.get("preferred_categories", [])
        if preferred_categories and current_query:
            for category_info in preferred_categories[:2]:
                category = category_info.get("category", "")
                suggested_query = f"{current_query} {category}"
                suggestions.append(
                    {
                        "suggested_query": suggested_query,
                        "relevance_score": 0.7,
                        "type": "pattern_based",
                        "reason": f"선호 카테고리 '{category}' 기반 제안",
                    }
                )

        return suggestions

    def _analyze_category_preferences(self, history: List[Dict]) -> List[Dict]:
        """카테고리 선호도 분석"""
        categories = []
        for item in history:
            filters = item.get("filters", {})
            item_categories = filters.get("categories", [])
            categories.extend(item_categories)

        category_counts = Counter(categories)
        return [
            {"category": cat, "frequency": count}
            for cat, count in category_counts.most_common(5)
        ]

    def _analyze_region_preferences(self, history: List[Dict]) -> List[Dict]:
        """지역 선호도 분석"""
        regions = []
        for item in history:
            filters = item.get("filters", {})
            item_regions = filters.get("regions", [])
            regions.extend(item_regions)

        region_counts = Counter(regions)
        return [
            {"region": region, "frequency": count}
            for region, count in region_counts.most_common(5)
        ]

    def _analyze_time_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """시간대별 검색 패턴 분석"""
        hours = []
        days = []

        for item in history:
            timestamp = datetime.fromisoformat(item["timestamp"])
            hours.append(timestamp.hour)
            days.append(timestamp.strftime("%A"))

        return {
            "preferred_hours": dict(Counter(hours).most_common(3)),
            "preferred_days": dict(Counter(days).most_common(3)),
        }

    def _analyze_query_complexity(self, history: List[Dict]) -> Dict[str, Any]:
        """검색어 복잡도 트렌드 분석"""
        query_lengths = [len(item.get("query", "")) for item in history]
        filter_counts = [len(item.get("filters", {})) for item in history]

        return {
            "avg_query_length": sum(query_lengths) / len(query_lengths)
            if query_lengths
            else 0,
            "avg_filter_count": sum(filter_counts) / len(filter_counts)
            if filter_counts
            else 0,
        }

    def _analyze_filter_usage(self, history: List[Dict]) -> Dict[str, int]:
        """필터 사용 패턴 분석"""
        filter_usage = defaultdict(int)

        for item in history:
            filters = item.get("filters", {})
            for filter_key in filters.keys():
                filter_usage[filter_key] += 1

        return dict(filter_usage)

    def _analyze_search_frequency(self, history: List[Dict]) -> Dict[str, Any]:
        """검색 빈도 패턴 분석"""
        if not history:
            return {}

        timestamps = [datetime.fromisoformat(item["timestamp"]) for item in history]
        timestamps.sort()

        # 일별 검색 빈도 계산
        daily_counts = defaultdict(int)
        for ts in timestamps:
            date_key = ts.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

        return {
            "searches_per_day": dict(daily_counts),
            "peak_activity_day": max(daily_counts, key=daily_counts.get)
            if daily_counts
            else None,
        }

    def _mask_sensitive_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """개인정보 마스킹"""
        masked_item = item.copy()

        # 위치 정보 마스킹
        if "location" in masked_item:
            location = masked_item["location"]
            if isinstance(location, dict):
                masked_item["location"] = {
                    "lat": round(location.get("lat", 0), 2),  # 소수점 둘째 자리까지만
                    "lng": round(location.get("lng", 0), 2),
                }

        # 민감한 검색어 마스킹 (예: 개인명, 주소 등)
        query = masked_item.get("query", "")
        if len(query) > 10:
            masked_item["query"] = query[:3] + "*" * (len(query) - 6) + query[-3:]

        return masked_item


# 의존성 주입용 팩토리 함수
def get_search_history_service(
    redis_client: redis.Redis, db_session: Session
) -> SearchHistoryService:
    """검색 히스토리 서비스 의존성"""
    return SearchHistoryService(redis_client, db_session)
