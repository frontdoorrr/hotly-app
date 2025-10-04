"""
고도화된 자동완성 서비스 (Task 2-3-2)

개인화된 검색 제안, 인기도 기반 제안, 실시간 검색어 트렌드 분석을 제공하는
종합적인 자동완성 시스템
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.elasticsearch import es_manager
from app.models.place import Place, PlaceStatus
from app.utils.korean_analyzer import KoreanAnalyzer

logger = logging.getLogger(__name__)


class AutocompleteService:
    """고도화된 자동완성 서비스"""

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client
        self.korean_analyzer = KoreanAnalyzer()

        # 자동완성 설정
        self.min_query_length = 1
        self.max_suggestions = 20
        self.cache_ttl = 300  # 5분
        self.trending_window_hours = 24

    async def get_comprehensive_suggestions(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10,
        include_personal: bool = True,
        include_trending: bool = True,
        include_popular: bool = True,
        categories: Optional[List[str]] = None,
        location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        종합적인 자동완성 제안 제공

        개인화 제안, 인기 검색어, 트렌딩 검색어를 조합하여
        사용자에게 최적의 검색 제안을 제공
        """
        try:
            if len(query.strip()) < self.min_query_length:
                return {"suggestions": [], "categories": {}}

            # 병렬로 다양한 제안 수집
            tasks = []

            if include_personal:
                tasks.append(
                    self._get_personalized_suggestions(user_id, query, limit // 3)
                )

            if include_trending:
                tasks.append(self._get_trending_suggestions(query, limit // 3))

            if include_popular:
                tasks.append(
                    self._get_popular_suggestions(query, limit // 3, categories)
                )

            # Elasticsearch 제안도 포함
            tasks.append(
                self._get_elasticsearch_suggestions(
                    user_id, query, limit // 2, categories
                )
            )

            # 모든 제안 병렬 수집
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 통합 및 중복 제거
            all_suggestions = []
            for result in results:
                if isinstance(result, list):
                    all_suggestions.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Suggestion collection failed: {result}")

            # 제안 순위 매기기 및 중복 제거
            ranked_suggestions = self._rank_and_deduplicate_suggestions(
                all_suggestions, query, limit
            )

            # 카테고리별 분류
            categorized = self._categorize_suggestions(ranked_suggestions)

            # 검색 로그 기록 (비동기)
            asyncio.create_task(self._log_search_query(user_id, query))

            return {
                "suggestions": ranked_suggestions,
                "categories": categorized,
                "total": len(ranked_suggestions),
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Comprehensive suggestions failed: {e}")
            # 기본 제안으로 fallback
            return await self._get_basic_suggestions(user_id, query, limit)

    async def _get_personalized_suggestions(
        self, user_id: UUID, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """개인화된 검색 제안"""
        try:
            # 사용자의 과거 검색 기록에서 제안
            personal_suggestions = []

            if self.redis:
                # Redis에서 개인 검색 기록 조회
                history_key = f"user_search_history:{user_id}"
                recent_searches = await self.redis.lrange(history_key, 0, 100)

                for search_item in recent_searches:
                    try:
                        search_data = json.loads(search_item)
                        search_text = search_data.get("query", "")

                        if query.lower() in search_text.lower():
                            personal_suggestions.append(
                                {
                                    "text": search_text,
                                    "type": "personal_history",
                                    "score": search_data.get("frequency", 1)
                                    * 2.0,  # 개인 기록 가중치
                                    "last_searched": search_data.get("last_searched"),
                                    "metadata": {"source": "personal"},
                                }
                            )
                    except json.JSONDecodeError:
                        continue

            # 사용자가 저장한 장소에서 제안
            user_places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    func.lower(Place.name).contains(query.lower()),
                )
                .order_by(Place.visit_count.desc(), Place.created_at.desc())
                .limit(limit)
                .all()
            )

            for place in user_places:
                personal_suggestions.append(
                    {
                        "text": place.name,
                        "type": "user_place",
                        "score": 2.5 + (place.visit_count or 0) * 0.1,
                        "category": place.category,
                        "address": place.address,
                        "metadata": {
                            "source": "user_places",
                            "place_id": str(place.id),
                            "visit_count": place.visit_count,
                        },
                    }
                )

            return personal_suggestions[:limit]

        except Exception as e:
            logger.error(f"Personalized suggestions failed: {e}")
            return []

    async def _get_trending_suggestions(
        self, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """트렌딩 검색어 제안"""
        try:
            if not self.redis:
                return []

            trending_suggestions = []

            # 최근 24시간 인기 검색어
            trending_key = f"trending_searches:{datetime.now().strftime('%Y%m%d')}"
            trending_data = await self.redis.zrevrangebyscore(
                trending_key, "+inf", "-inf", withscores=True, start=0, num=100
            )

            for search_term, score in trending_data:
                if isinstance(search_term, bytes):
                    search_term = search_term.decode()

                if query.lower() in search_term.lower():
                    trending_suggestions.append(
                        {
                            "text": search_term,
                            "type": "trending",
                            "score": float(score) * 1.5,  # 트렌딩 가중치
                            "metadata": {
                                "source": "trending",
                                "trend_score": float(score),
                            },
                        }
                    )

            return trending_suggestions[:limit]

        except Exception as e:
            logger.error(f"Trending suggestions failed: {e}")
            return []

    async def _get_popular_suggestions(
        self, query: str, limit: int, categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """인기 검색어 제안"""
        try:
            popular_suggestions = []

            # 데이터베이스에서 인기 장소 검색
            base_query = self.db.query(
                Place, func.count().label("search_count")
            ).filter(
                Place.status == PlaceStatus.ACTIVE,
                func.lower(Place.name).contains(query.lower()),
            )

            if categories:
                base_query = base_query.filter(Place.category.in_(categories))

            popular_places = (
                base_query.group_by(Place.id)
                .order_by(func.count().desc(), Place.visit_count.desc())
                .limit(limit)
                .all()
            )

            for place, search_count in popular_places:
                popular_suggestions.append(
                    {
                        "text": place.name,
                        "type": "popular_place",
                        "score": 1.8 + search_count * 0.1,  # 인기도 점수
                        "category": place.category,
                        "address": place.address,
                        "metadata": {
                            "source": "popular",
                            "search_count": search_count,
                            "place_id": str(place.id),
                        },
                    }
                )

            return popular_suggestions

        except Exception as e:
            logger.error(f"Popular suggestions failed: {e}")
            return []

    async def _get_elasticsearch_suggestions(
        self,
        user_id: UUID,
        query: str,
        limit: int,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Elasticsearch 기반 제안"""
        try:
            if not es_manager.client:
                return []

            # Elasticsearch completion suggester 사용
            suggest_body = {
                "suggest": {
                    "place_suggest": {
                        "prefix": query,
                        "completion": {
                            "field": "suggest",
                            "size": limit,
                            "contexts": {"user_id": str(user_id)},
                        },
                    }
                }
            }

            if categories:
                suggest_body["suggest"]["place_suggest"]["completion"]["contexts"][
                    "category"
                ] = categories

            result = await es_manager.client.search(
                index=es_manager.get_index_name("places"), body=suggest_body
            )

            es_suggestions = []
            suggestions = result.get("suggest", {}).get("place_suggest", [])

            for suggestion_group in suggestions:
                for option in suggestion_group.get("options", []):
                    es_suggestions.append(
                        {
                            "text": option["text"],
                            "type": "elasticsearch",
                            "score": option["_score"] * 1.2,  # ES 가중치
                            "metadata": {
                                "source": "elasticsearch",
                                "es_score": option["_score"],
                            },
                        }
                    )

            return es_suggestions

        except Exception as e:
            logger.error(f"Elasticsearch suggestions failed: {e}")
            return []

    def _rank_and_deduplicate_suggestions(
        self, suggestions: List[Dict[str, Any]], query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """제안 순위 매기기 및 중복 제거"""
        try:
            # 중복 제거 (텍스트 기반)
            seen_texts = set()
            unique_suggestions = []

            for suggestion in suggestions:
                text = suggestion["text"].lower().strip()
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_suggestions.append(suggestion)

            # 한국어 분석을 통한 관련도 점수 조정
            analyzed_query = self.korean_analyzer.analyze_text(query)
            query_keywords = set(analyzed_query.get("keywords", [query]))

            for suggestion in unique_suggestions:
                # 텍스트 유사도 계산
                suggestion_analyzed = self.korean_analyzer.analyze_text(
                    suggestion["text"]
                )
                suggestion_keywords = set(suggestion_analyzed.get("keywords", []))

                # 키워드 겹침 정도로 관련도 점수 조정
                overlap = len(query_keywords & suggestion_keywords)
                if overlap > 0:
                    suggestion["score"] += overlap * 0.5

                # 쿼리와의 위치 기반 매칭 점수
                if query.lower() in suggestion["text"].lower():
                    position = suggestion["text"].lower().index(query.lower())
                    # 앞쪽에 위치할수록 높은 점수
                    position_score = max(0, 1.0 - position * 0.1)
                    suggestion["score"] += position_score

            # 점수순 정렬
            ranked_suggestions = sorted(
                unique_suggestions, key=lambda x: x["score"], reverse=True
            )

            return ranked_suggestions[:limit]

        except Exception as e:
            logger.error(f"Ranking and deduplication failed: {e}")
            return suggestions[:limit]

    def _categorize_suggestions(
        self, suggestions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """제안을 카테고리별로 분류"""
        categories = {
            "personal": [],
            "trending": [],
            "popular": [],
            "places": [],
            "other": [],
        }

        for suggestion in suggestions:
            suggestion_type = suggestion.get("type", "other")
            category = suggestion.get("category")

            if suggestion_type in ["personal_history", "user_place"]:
                categories["personal"].append(suggestion)
            elif suggestion_type == "trending":
                categories["trending"].append(suggestion)
            elif suggestion_type in ["popular_place", "popular"]:
                categories["popular"].append(suggestion)
            elif category:
                if "places" not in categories:
                    categories["places"] = []
                categories["places"].append(suggestion)
            else:
                categories["other"].append(suggestion)

        # 빈 카테고리 제거
        return {k: v for k, v in categories.items() if v}

    async def _log_search_query(self, user_id: UUID, query: str) -> None:
        """검색 쿼리 로그 기록"""
        try:
            if not self.redis:
                return

            # 개인 검색 기록 업데이트
            history_key = f"user_search_history:{user_id}"
            search_data = {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "frequency": 1,
                "last_searched": datetime.utcnow().isoformat(),
            }

            # 기존 검색어 빈도 증가
            existing = await self.redis.lrange(history_key, 0, -1)
            found = False

            for i, item in enumerate(existing):
                try:
                    data = json.loads(item)
                    if data["query"] == query:
                        data["frequency"] += 1
                        data["last_searched"] = datetime.utcnow().isoformat()
                        await self.redis.lset(history_key, i, json.dumps(data))
                        found = True
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

            if not found:
                await self.redis.lpush(history_key, json.dumps(search_data))
                await self.redis.ltrim(history_key, 0, 99)  # 최대 100개 유지

            await self.redis.expire(history_key, 86400 * 30)  # 30일 보관

            # 전체 트렌딩 검색어 업데이트
            trending_key = f"trending_searches:{datetime.now().strftime('%Y%m%d')}"
            await self.redis.zincrby(trending_key, 1, query)
            await self.redis.expire(trending_key, 86400 * 7)  # 7일 보관

        except Exception as e:
            logger.error(f"Search query logging failed: {e}")

    async def _get_basic_suggestions(
        self, user_id: UUID, query: str, limit: int
    ) -> Dict[str, Any]:
        """기본 제안 (fallback)"""
        try:
            # 간단한 데이터베이스 쿼리로 제안 생성
            places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    func.lower(Place.name).contains(query.lower()),
                )
                .limit(limit)
                .all()
            )

            suggestions = []
            for place in places:
                suggestions.append(
                    {
                        "text": place.name,
                        "type": "basic",
                        "score": 1.0,
                        "category": place.category,
                        "address": place.address,
                        "metadata": {"source": "basic"},
                    }
                )

            return {
                "suggestions": suggestions,
                "categories": {"basic": suggestions},
                "total": len(suggestions),
                "query": query,
            }

        except Exception as e:
            logger.error(f"Basic suggestions failed: {e}")
            return {"suggestions": [], "categories": {}, "total": 0, "query": query}

    async def get_search_analytics(
        self, user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """검색 분석 데이터 제공"""
        try:
            analytics = {
                "trending_searches": [],
                "popular_categories": {},
                "user_search_patterns": {},
                "performance_metrics": {},
            }

            if self.redis:
                # 트렌딩 검색어
                trending_key = f"trending_searches:{datetime.now().strftime('%Y%m%d')}"
                trending = await self.redis.zrevrangebyscore(
                    trending_key, "+inf", "-inf", withscores=True, start=0, num=10
                )

                analytics["trending_searches"] = [
                    {
                        "query": term.decode() if isinstance(term, bytes) else term,
                        "count": int(count),
                    }
                    for term, count in trending
                ]

                # 사용자별 검색 패턴 (개인정보 보호)
                if user_id:
                    history_key = f"user_search_history:{user_id}"
                    user_history = await self.redis.lrange(history_key, 0, 19)

                    recent_searches = []
                    for item in user_history:
                        try:
                            data = json.loads(item)
                            recent_searches.append(
                                {
                                    "query": data["query"],
                                    "frequency": data.get("frequency", 1),
                                    "last_searched": data.get("last_searched"),
                                }
                            )
                        except json.JSONDecodeError:
                            continue

                    analytics["user_search_patterns"][
                        "recent_searches"
                    ] = recent_searches

            # 카테고리별 인기도 (PostgreSQL)
            category_stats = (
                self.db.query(Place.category, func.count().label("count"))
                .filter(Place.status == PlaceStatus.ACTIVE)
                .group_by(Place.category)
                .order_by(func.count().desc())
                .limit(10)
                .all()
            )

            analytics["popular_categories"] = {
                category: count for category, count in category_stats if category
            }

            return analytics

        except Exception as e:
            logger.error(f"Search analytics failed: {e}")
            return {"error": str(e)}

    async def optimize_suggestions_cache(self) -> Dict[str, Any]:
        """제안 캐시 최적화"""
        try:
            if not self.redis:
                return {"status": "no_redis"}

            # 오래된 검색 기록 정리
            cleanup_stats = {
                "cleaned_users": 0,
                "cleaned_trending": 0,
                "optimized_cache": 0,
            }

            # 30일 이상된 사용자 검색 기록 정리
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            # 패턴으로 모든 사용자 검색 기록 키 찾기
            user_keys = []
            async for key in self.redis.scan_iter(match="user_search_history:*"):
                user_keys.append(key)

            for key in user_keys:
                try:
                    history = await self.redis.lrange(key, 0, -1)
                    cleaned_history = []

                    for item in history:
                        try:
                            data = json.loads(item)
                            search_date = datetime.fromisoformat(data["last_searched"])
                            if search_date > cutoff_date:
                                cleaned_history.append(item)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue

                    if len(cleaned_history) < len(history):
                        # 정리된 기록으로 업데이트
                        await self.redis.delete(key)
                        if cleaned_history:
                            await self.redis.lpush(key, *cleaned_history)
                            await self.redis.expire(key, 86400 * 30)
                        cleanup_stats["cleaned_users"] += 1

                except Exception as e:
                    logger.warning(f"Failed to clean user history {key}: {e}")
                    continue

            # 오래된 트렌딩 데이터 정리
            trending_keys = []
            async for key in self.redis.scan_iter(match="trending_searches:*"):
                trending_keys.append(key)

            cutoff_trending = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")
            for key in trending_keys:
                try:
                    key_date = (
                        key.decode().split(":")[1]
                        if isinstance(key, bytes)
                        else key.split(":")[1]
                    )
                    if key_date < cutoff_trending:
                        await self.redis.delete(key)
                        cleanup_stats["cleaned_trending"] += 1
                except (IndexError, ValueError):
                    continue

            return {
                "status": "completed",
                "cleanup_stats": cleanup_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"status": "failed", "error": str(e)}


# 글로벌 인스턴스 (의존성 주입용)
def get_autocomplete_service(
    db: Session, redis_client: Optional[redis.Redis] = None
) -> AutocompleteService:
    """자동완성 서비스 의존성"""
    return AutocompleteService(db, redis_client)
