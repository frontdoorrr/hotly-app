"""
즐겨찾는 검색 서비스 (Task 2-3-5)

사용자 즐겨찾는 검색 저장 및 관리 시스템
- 즐겨찾는 검색 생성, 수정, 삭제
- 스마트 제안 및 카테고리 분류
- 공유 및 동기화 기능
- 사용 패턴 분석 및 최적화
- 백업 및 복원 기능
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FavoriteSearchesService:
    """즐겨찾는 검색 서비스"""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        max_favorites_per_user: int = 50,
        enable_categorization: bool = True,
        smart_suggestions: bool = True,
        sharing_enabled: bool = True,
        templates_enabled: bool = True,
        analytics_enabled: bool = True,
        sync_enabled: bool = True,
        bulk_operations: bool = True,
        performance_optimized: bool = True,
        cache_frequently_used: bool = True,
        favorites_ttl_days: int = 365,
    ):
        self.redis = redis_client
        self.db = db_session
        self.max_favorites = max_favorites_per_user
        self.categorization_enabled = enable_categorization
        self.smart_suggestions = smart_suggestions
        self.sharing_enabled = sharing_enabled
        self.templates_enabled = templates_enabled
        self.analytics_enabled = analytics_enabled
        self.sync_enabled = sync_enabled
        self.bulk_operations = bulk_operations
        self.performance_optimized = performance_optimized
        self.cache_frequently_used = cache_frequently_used
        self.favorites_ttl = favorites_ttl_days * 24 * 3600

        # Redis 키 패턴
        self.favorites_key_pattern = "favorite_searches:{user_id}"
        self.shared_key_pattern = "shared_favorites:{share_token}"
        self.templates_key = "favorite_templates"
        self.analytics_key_pattern = "favorites_analytics:{user_id}:{date}"
        self.backup_key_pattern = "favorites_backup:{user_id}:{backup_id}"

        # 카테고리 매핑
        self.category_mapping = {
            "restaurant": "food_and_dining",
            "cafe": "food_and_dining",
            "bar": "food_and_dining",
            "shopping": "shopping",
            "culture": "culture_and_arts",
            "hospital": "healthcare",
            "hotel": "accommodation",
        }

    async def create_favorite_search(
        self,
        user_id: UUID,
        search_data: Dict[str, Any],
    ) -> str:
        """즐겨찾는 검색 생성"""
        try:
            # 즐겨찾는 검색 개수 제한 확인
            current_count = await self._get_favorites_count(user_id)
            if current_count >= self.max_favorites:
                raise ValueError(f"즐겨찾는 검색은 최대 {self.max_favorites}개까지 저장 가능합니다")

            # 즐겨찾는 검색 ID 생성
            favorite_id = str(uuid.uuid4())

            # 즐겨찾는 검색 데이터 구성
            favorite_data = {
                "id": favorite_id,
                "name": search_data.get("name", ""),
                "query": search_data.get("query", ""),
                "filters": search_data.get("filters", {}),
                "location": search_data.get("location", {}),
                "tags": search_data.get("tags", []),
                "created_at": datetime.utcnow().isoformat(),
                "last_used": datetime.utcnow().isoformat(),
                "use_count": 0,
                "category": self._determine_category(search_data),
                "is_active": True,
                "user_notes": search_data.get("notes", ""),
            }

            # Redis Hash에 저장
            favorites_key = self.favorites_key_pattern.format(user_id=user_id)
            await self.redis.hset(
                favorites_key, favorite_id, json.dumps(favorite_data, default=str)
            )

            # TTL 설정
            await self.redis.expire(favorites_key, self.favorites_ttl)

            # 분석 데이터 기록
            if self.analytics_enabled:
                await self._record_favorite_event(user_id, "created", favorite_id)

            logger.info(f"Created favorite search {favorite_id} for user {user_id}")
            return favorite_id

        except Exception as e:
            logger.error(f"Failed to create favorite search: {str(e)}")
            raise

    async def get_favorite_searches(
        self,
        user_id: UUID,
        limit: int = 20,
        sort_by: str = "use_count",  # use_count, created_at, last_used, name
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """즐겨찾는 검색 목록 조회"""
        try:
            favorites_key = self.favorites_key_pattern.format(user_id=user_id)
            favorites_data = await self.redis.hgetall(favorites_key)

            if not favorites_data:
                return []

            # 데이터 파싱 및 필터링
            favorites = []
            for favorite_id, favorite_json in favorites_data.items():
                try:
                    favorite = json.loads(favorite_json)

                    # 활성 상태 확인
                    if not favorite.get("is_active", True):
                        continue

                    # 카테고리 필터 적용
                    if category_filter and favorite.get("category") != category_filter:
                        continue

                    favorites.append(favorite)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in favorite {favorite_id}")
                    continue

            # 정렬
            reverse = sort_by in ["use_count", "created_at", "last_used"]
            if sort_by == "name":
                favorites.sort(key=lambda x: x.get("name", "").lower())
            else:
                favorites.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

            return favorites[:limit]

        except Exception as e:
            logger.error(f"Failed to get favorite searches: {str(e)}")
            return []

    async def execute_favorite_search(
        self,
        user_id: UUID,
        favorite_id: str,
    ) -> Dict[str, Any]:
        """즐겨찾는 검색 실행"""
        try:
            # 즐겨찾는 검색 데이터 조회
            favorite_data = await self._get_favorite_by_id(user_id, favorite_id)

            if not favorite_data:
                raise ValueError("즐겨찾는 검색을 찾을 수 없습니다")

            # 검색 실행
            search_params = {
                "query": favorite_data.get("query", ""),
                "filters": favorite_data.get("filters", {}),
                "location": favorite_data.get("location", {}),
            }

            search_results = await self._execute_search(user_id, search_params)

            # 사용 횟수 증가 및 마지막 사용 시간 업데이트
            await self._update_usage_stats(user_id, favorite_id)

            # 분석 데이터 기록
            if self.analytics_enabled:
                await self._record_favorite_event(user_id, "executed", favorite_id)

            return {
                "results": search_results.get("results", []),
                "total_count": search_results.get("count", 0),
                "favorite_info": {
                    "id": favorite_id,
                    "name": favorite_data.get("name"),
                    "tags": favorite_data.get("tags", []),
                },
                "execution_metadata": {
                    "executed_at": datetime.utcnow().isoformat(),
                    "search_params": search_params,
                },
            }

        except Exception as e:
            logger.error(f"Failed to execute favorite search: {str(e)}")
            raise

    async def get_categorized_favorites(
        self, user_id: UUID
    ) -> Dict[str, List[Dict[str, Any]]]:
        """카테고리별 즐겨찾는 검색 분류"""
        try:
            if not self.categorization_enabled:
                return {}

            favorites = await self.get_favorite_searches(user_id, limit=100)
            categorized = {}

            for favorite in favorites:
                category = favorite.get("category", "other")
                mapped_category = self.category_mapping.get(category, "other")

                if mapped_category not in categorized:
                    categorized[mapped_category] = []

                categorized[mapped_category].append(favorite)

            # 각 카테고리 내에서 사용 빈도순 정렬
            for category, items in categorized.items():
                items.sort(key=lambda x: x.get("use_count", 0), reverse=True)

            return categorized

        except Exception as e:
            logger.error(f"Failed to categorize favorites: {str(e)}")
            return {}

    async def generate_smart_suggestions(
        self,
        user_id: UUID,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """스마트 즐겨찾는 검색 제안"""
        try:
            if not self.smart_suggestions:
                return []

            # 사용자 검색 패턴 분석
            search_patterns = await self._analyze_search_patterns(user_id)
            existing_favorites = await self.get_favorite_searches(user_id)

            suggestions = []
            existing_queries = {
                fav.get("query", "").lower() for fav in existing_favorites
            }

            for pattern in search_patterns[: limit * 2]:  # 여유분 확보
                query = pattern.get("query", "").lower()
                frequency = pattern.get("frequency", 0)

                # 이미 즐겨찾기로 저장된 검색은 제외
                if query in existing_queries:
                    continue

                # 신뢰도 점수 계산
                confidence_score = self._calculate_confidence_score(
                    pattern, existing_favorites
                )

                if confidence_score > 0.6:  # 60% 이상 신뢰도
                    suggestion = {
                        "suggested_name": self._generate_suggested_name(pattern),
                        "suggested_query": pattern["query"],
                        "suggested_filters": self._suggest_filters(pattern),
                        "confidence_score": confidence_score,
                        "reason": f"최근 {frequency}회 검색하셨습니다",
                        "estimated_usage": self._estimate_future_usage(pattern),
                    }
                    suggestions.append(suggestion)

                if len(suggestions) >= limit:
                    break

            return sorted(
                suggestions, key=lambda x: x["confidence_score"], reverse=True
            )

        except Exception as e:
            logger.error(f"Failed to generate smart suggestions: {str(e)}")
            return []

    async def share_favorite_search(
        self,
        user_id: UUID,
        favorite_id: str,
        share_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """즐겨찾는 검색 공유"""
        try:
            if not self.sharing_enabled:
                raise ValueError("공유 기능이 비활성화되어 있습니다")

            # 즐겨찾는 검색 데이터 조회
            favorite_data = await self._get_favorite_by_id(user_id, favorite_id)
            if not favorite_data:
                raise ValueError("즐겨찾는 검색을 찾을 수 없습니다")

            # 공유 토큰 생성
            share_token = str(uuid.uuid4())

            # 공유 데이터 구성
            expiry_hours = share_settings.get("expiry_hours", 24)
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

            share_data = {
                "original_user_id": str(user_id),
                "favorite_data": favorite_data,
                "share_settings": share_settings,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "access_count": 0,
                "is_public": share_settings.get("public", False),
            }

            # Redis에 공유 데이터 저장
            shared_key = self.shared_key_pattern.format(share_token=share_token)
            await self.redis.setex(
                shared_key,
                int(expiry_hours * 3600),
                json.dumps(share_data, default=str),
            )

            return {
                "share_token": share_token,
                "share_url": f"/shared-favorites/{share_token}",
                "expires_at": expires_at.isoformat(),
                "settings": share_settings,
            }

        except Exception as e:
            logger.error(f"Failed to share favorite search: {str(e)}")
            raise

    async def get_favorite_templates(
        self,
        user_location: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """즐겨찾는 검색 템플릿 조회"""
        try:
            if not self.templates_enabled:
                return []

            # 기본 템플릿들
            base_templates = [
                {
                    "id": "nearby_restaurants",
                    "name_template": "{location} 맛집 탐방",
                    "query_template": "{location} 맛집",
                    "category": "restaurant",
                    "suggested_filters": {
                        "categories": ["restaurant"],
                        "rating_min": 4.0,
                    },
                    "tags": ["맛집", "음식", "{location}"],
                    "popularity_score": 0.9,
                },
                {
                    "id": "coffee_shops",
                    "name_template": "{location} 카페 투어",
                    "query_template": "{location} 카페",
                    "category": "cafe",
                    "suggested_filters": {
                        "categories": ["cafe"],
                        "atmosphere": ["cozy"],
                    },
                    "tags": ["카페", "커피", "{location}"],
                    "popularity_score": 0.85,
                },
                {
                    "id": "nightlife",
                    "name_template": "{location} 나이트라이프",
                    "query_template": "{location} 바 술집",
                    "category": "bar",
                    "suggested_filters": {"categories": ["bar"], "open_late": True},
                    "tags": ["바", "술집", "{location}", "밤"],
                    "popularity_score": 0.7,
                },
                {
                    "id": "cultural_spots",
                    "name_template": "{location} 문화체험",
                    "query_template": "{location} 박물관 갤러리",
                    "category": "culture",
                    "suggested_filters": {"categories": ["culture", "museum"]},
                    "tags": ["문화", "예술", "{location}"],
                    "popularity_score": 0.6,
                },
            ]

            # 사용자 선호도에 따른 필터링
            if user_preferences:
                filtered_templates = [
                    template
                    for template in base_templates
                    if template["category"] in user_preferences
                ]
            else:
                filtered_templates = base_templates

            # 위치 정보가 있으면 템플릿 개인화
            if user_location:
                location_name = user_location.get("name", "주변")
                for template in filtered_templates:
                    template["name_template"] = template["name_template"].format(
                        location=location_name
                    )
                    template["query_template"] = template["query_template"].format(
                        location=location_name
                    )
                    template["tags"] = [
                        tag.format(location=location_name)
                        if "{location}" in tag
                        else tag
                        for tag in template["tags"]
                    ]

            # 인기도순 정렬
            return sorted(
                filtered_templates, key=lambda x: x["popularity_score"], reverse=True
            )

        except Exception as e:
            logger.error(f"Failed to get favorite templates: {str(e)}")
            return []

    async def analyze_favorite_usage(
        self,
        user_id: UUID,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """즐겨찾는 검색 사용 패턴 분석"""
        try:
            if not self.analytics_enabled:
                return {}

            favorites = await self.get_favorite_searches(user_id, limit=100)

            if not favorites:
                return {"total_favorites": 0, "message": "분석할 데이터가 없습니다"}

            # 기본 통계
            total_favorites = len(favorites)
            total_uses = sum(fav.get("use_count", 0) for fav in favorites)

            # 카테고리별 분석
            category_usage = {}
            for favorite in favorites:
                category = favorite.get("category", "other")
                if category not in category_usage:
                    category_usage[category] = {"count": 0, "total_uses": 0}
                category_usage[category]["count"] += 1
                category_usage[category]["total_uses"] += favorite.get("use_count", 0)

            # 가장 많이 사용된 카테고리
            most_used_category = (
                max(category_usage.items(), key=lambda x: x[1]["total_uses"])[0]
                if category_usage
                else "none"
            )

            # 사용 트렌드 분석
            usage_trends = await self._analyze_usage_trends(user_id, period_days)

            # 추천사항 생성
            recommendations = self._generate_usage_recommendations(
                favorites, category_usage
            )

            return {
                "total_favorites": total_favorites,
                "total_uses": total_uses,
                "avg_uses_per_favorite": total_uses / total_favorites
                if total_favorites > 0
                else 0,
                "most_used_category": most_used_category,
                "category_breakdown": category_usage,
                "usage_trends": usage_trends,
                "recommendations": recommendations,
                "analysis_period_days": period_days,
            }

        except Exception as e:
            logger.error(f"Failed to analyze favorite usage: {str(e)}")
            return {"error": str(e)}

    async def sync_favorites_across_devices(
        self,
        user_id: UUID,
        device_id: str,
        local_favorites: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """디바이스 간 즐겨찾는 검색 동기화"""
        try:
            if not self.sync_enabled:
                return {"error": "동기화 기능이 비활성화되어 있습니다"}

            # 서버의 현재 즐겨찾는 검색 조회
            server_favorites = await self.get_favorite_searches(user_id, limit=100)
            server_favorites_dict = {fav["id"]: fav for fav in server_favorites}

            synchronized_count = 0
            conflicts_resolved = 0
            updated_favorites = []

            # 로컬 즐겨찾는 검색 처리
            for local_fav in local_favorites:
                local_id = local_fav.get("id")

                if local_id in server_favorites_dict:
                    # 기존 항목 - 충돌 해결
                    server_fav = server_favorites_dict[local_id]
                    merged_fav = await self._resolve_sync_conflict(
                        server_fav, local_fav
                    )

                    if merged_fav != server_fav:
                        await self._update_favorite(user_id, local_id, merged_fav)
                        conflicts_resolved += 1
                        updated_favorites.append(merged_fav)
                else:
                    # 새로운 항목 - 서버에 추가
                    await self._create_favorite_from_sync(user_id, local_fav)
                    synchronized_count += 1
                    updated_favorites.append(local_fav)

            return {
                "synchronized_count": synchronized_count,
                "conflicts_resolved": conflicts_resolved,
                "updated_favorites": updated_favorites,
                "sync_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to sync favorites: {str(e)}")
            return {"error": str(e)}

    async def create_backup(self, user_id: UUID) -> Dict[str, Any]:
        """즐겨찾는 검색 백업 생성"""
        try:
            favorites = await self.get_favorite_searches(user_id, limit=1000)

            backup_id = str(uuid.uuid4())
            backup_data = {
                "backup_id": backup_id,
                "user_id": str(user_id),
                "created_at": datetime.utcnow().isoformat(),
                "favorites": favorites,
                "favorites_count": len(favorites),
                "version": "1.0",
            }

            # Redis에 백업 저장 (90일 보관)
            backup_key = self.backup_key_pattern.format(
                user_id=user_id, backup_id=backup_id
            )
            await self.redis.setex(
                backup_key, 90 * 24 * 3600, json.dumps(backup_data, default=str)  # 90일
            )

            return {
                "backup_id": backup_id,
                "created_at": backup_data["created_at"],
                "favorites_count": len(favorites),
                "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise

    async def restore_from_backup(
        self, user_id: UUID, backup_id: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """백업으로부터 즐겨찾는 검색 복원"""
        try:
            backup_key = self.backup_key_pattern.format(
                user_id=user_id, backup_id=backup_id
            )
            backup_data = await self.redis.get(backup_key)

            if not backup_data:
                raise ValueError("백업을 찾을 수 없습니다")

            backup = json.loads(backup_data)
            favorites_to_restore = backup.get("favorites", [])

            if not overwrite:
                # 기존 즐겨찾는 검색과 충돌 확인
                existing_favorites = await self.get_favorite_searches(
                    user_id, limit=1000
                )
                existing_ids = {fav["id"] for fav in existing_favorites}

                # 중복되지 않는 항목만 복원
                favorites_to_restore = [
                    fav for fav in favorites_to_restore if fav["id"] not in existing_ids
                ]

            # 즐겨찾는 검색 복원
            restored_count = 0
            favorites_key = self.favorites_key_pattern.format(user_id=user_id)

            for favorite in favorites_to_restore:
                try:
                    await self.redis.hset(
                        favorites_key, favorite["id"], json.dumps(favorite, default=str)
                    )
                    restored_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to restore favorite {favorite.get('id')}: {str(e)}"
                    )

            # TTL 재설정
            await self.redis.expire(favorites_key, self.favorites_ttl)

            return {
                "restored_count": restored_count,
                "total_backup_count": len(backup.get("favorites", [])),
                "success": True,
                "restored_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to restore from backup: {str(e)}")
            return {"success": False, "error": str(e)}

    async def filter_favorites(
        self,
        user_id: UUID,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """고급 필터링으로 즐겨찾는 검색 조회"""
        try:
            all_favorites = await self.get_favorite_searches(user_id, limit=1000)
            filtered = []

            for favorite in all_favorites:
                # 카테고리 필터
                if "category" in filters:
                    if favorite.get("category") != filters["category"]:
                        continue

                # 최소 사용 횟수 필터
                if "min_use_count" in filters:
                    if favorite.get("use_count", 0) < filters["min_use_count"]:
                        continue

                # 생성일 필터
                if "created_since" in filters:
                    created_at = datetime.fromisoformat(favorite.get("created_at"))
                    if created_at < filters["created_since"]:
                        continue

                # 태그 필터
                if "tags" in filters:
                    favorite_tags = set(favorite.get("tags", []))
                    required_tags = set(filters["tags"])
                    if not required_tags.intersection(favorite_tags):
                        continue

                filtered.append(favorite)

            return filtered

        except Exception as e:
            logger.error(f"Failed to filter favorites: {str(e)}")
            return []

    async def bulk_create_favorites(
        self,
        user_id: UUID,
        favorites_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """일괄 즐겨찾는 검색 생성"""
        try:
            if not self.bulk_operations:
                raise ValueError("일괄 작업 기능이 비활성화되어 있습니다")

            created_count = 0
            failed_count = 0
            created_ids = []

            for favorite_data in favorites_data:
                try:
                    favorite_id = await self.create_favorite_search(
                        user_id, favorite_data
                    )
                    created_ids.append(favorite_id)
                    created_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create favorite: {str(e)}")
                    failed_count += 1

            return {
                "created_count": created_count,
                "failed_count": failed_count,
                "created_ids": created_ids,
                "total_requested": len(favorites_data),
            }

        except Exception as e:
            logger.error(f"Failed to bulk create favorites: {str(e)}")
            return {"error": str(e)}

    async def bulk_delete_favorites(
        self,
        user_id: UUID,
        favorite_ids: List[str],
    ) -> Dict[str, Any]:
        """일괄 즐겨찾는 검색 삭제"""
        try:
            if not self.bulk_operations:
                raise ValueError("일괄 작업 기능이 비활성화되어 있습니다")

            favorites_key = self.favorites_key_pattern.format(user_id=user_id)

            # Redis HDEL로 일괄 삭제
            deleted_count = await self.redis.hdel(favorites_key, *favorite_ids)

            return {
                "deleted_count": deleted_count,
                "requested_count": len(favorite_ids),
                "success_rate": deleted_count / len(favorite_ids)
                if favorite_ids
                else 0,
            }

        except Exception as e:
            logger.error(f"Failed to bulk delete favorites: {str(e)}")
            return {"error": str(e)}

    async def get_favorites_optimized(
        self,
        user_id: UUID,
        optimization_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """성능 최적화된 즐겨찾는 검색 조회"""
        try:
            if not self.performance_optimized:
                return {"error": "성능 최적화 기능이 비활성화되어 있습니다"}

            start_time = datetime.utcnow()

            # 캐시 확인 (자주 사용되는 즐겨찾기만)
            cache_hit = False
            if optimization_params.get("use_cache") and self.cache_frequently_used:
                cached_favorites = await self._get_cached_frequent_favorites(user_id)
                if cached_favorites:
                    cache_hit = True
                    favorites = cached_favorites
                else:
                    favorites = await self.get_favorite_searches(user_id)
                    # 자주 사용되는 즐겨찾기만 캐싱
                    frequent_favorites = [
                        fav for fav in favorites if fav.get("use_count", 0) > 3
                    ]
                    if frequent_favorites:
                        await self._cache_frequent_favorites(
                            user_id, frequent_favorites
                        )
            else:
                favorites = await self.get_favorite_searches(user_id)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "favorites": favorites,
                "performance_metrics": {
                    "response_time_ms": processing_time,
                    "cache_hit_rate": 1.0 if cache_hit else 0.0,
                    "memory_usage_mb": len(json.dumps(favorites, default=str))
                    / (1024 * 1024),
                    "optimization_applied": True,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get optimized favorites: {str(e)}")
            return {"error": str(e)}

    # Private helper methods

    async def _get_favorites_count(self, user_id: UUID) -> int:
        """즐겨찾는 검색 개수 조회"""
        try:
            favorites_key = self.favorites_key_pattern.format(user_id=user_id)
            return await self.redis.hlen(favorites_key)
        except Exception:
            return 0

    def _determine_category(self, search_data: Dict[str, Any]) -> str:
        """검색 데이터로부터 카테고리 결정"""
        filters = search_data.get("filters", {})
        categories = filters.get("categories", [])

        if categories:
            return categories[0]  # 첫 번째 카테고리 사용

        # 쿼리나 태그에서 카테고리 추론
        query = search_data.get("query", "").lower()
        tags = [tag.lower() for tag in search_data.get("tags", [])]

        if any(
            word in query or word in " ".join(tags) for word in ["맛집", "음식", "레스토랑"]
        ):
            return "restaurant"
        elif any(word in query or word in " ".join(tags) for word in ["카페", "커피"]):
            return "cafe"
        elif any(word in query or word in " ".join(tags) for word in ["바", "술집", "맥주"]):
            return "bar"

        return "other"

    async def _get_favorite_by_id(
        self, user_id: UUID, favorite_id: str
    ) -> Optional[Dict[str, Any]]:
        """ID로 즐겨찾는 검색 조회"""
        try:
            favorites_key = self.favorites_key_pattern.format(user_id=user_id)
            favorite_json = await self.redis.hget(favorites_key, favorite_id)

            if favorite_json:
                return json.loads(favorite_json)
            return None
        except Exception:
            return None

    async def _execute_search(
        self, user_id: UUID, search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """검색 실행 (Mock)"""
        # 실제로는 검색 서비스를 호출
        return {
            "results": [
                {"id": "place_1", "name": "검색 결과 1"},
                {"id": "place_2", "name": "검색 결과 2"},
            ],
            "count": 2,
        }

    async def _update_usage_stats(self, user_id: UUID, favorite_id: str) -> None:
        """사용 통계 업데이트"""
        try:
            favorite_data = await self._get_favorite_by_id(user_id, favorite_id)
            if favorite_data:
                favorite_data["use_count"] = favorite_data.get("use_count", 0) + 1
                favorite_data["last_used"] = datetime.utcnow().isoformat()

                favorites_key = self.favorites_key_pattern.format(user_id=user_id)
                await self.redis.hset(
                    favorites_key, favorite_id, json.dumps(favorite_data, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to update usage stats: {str(e)}")

    async def _record_favorite_event(
        self, user_id: UUID, event_type: str, favorite_id: str
    ) -> None:
        """즐겨찾는 검색 이벤트 기록"""
        try:
            if not self.analytics_enabled:
                return

            analytics_key = self.analytics_key_pattern.format(
                user_id=user_id, date=datetime.utcnow().strftime("%Y-%m-%d")
            )

            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "favorite_id": favorite_id,
            }

            await self.redis.lpush(analytics_key, json.dumps(event))
            await self.redis.expire(analytics_key, 86400 * 30)  # 30일 보관
        except Exception as e:
            logger.error(f"Failed to record favorite event: {str(e)}")

    # Mock implementation methods

    async def _analyze_search_patterns(self, user_id: UUID) -> List[Dict[str, Any]]:
        """사용자 검색 패턴 분석 (Mock)"""
        return [
            {"query": "홍대 맛집", "frequency": 15, "last_searched": "2024-01-15"},
            {"query": "홍대 카페", "frequency": 8, "last_searched": "2024-01-14"},
            {"query": "홍대 술집", "frequency": 5, "last_searched": "2024-01-13"},
        ]

    def _calculate_confidence_score(
        self, pattern: Dict[str, Any], existing_favorites: List[Dict[str, Any]]
    ) -> float:
        """신뢰도 점수 계산 (Mock)"""
        frequency = pattern.get("frequency", 0)
        return min(frequency / 20, 1.0)  # 20회 이상 검색 시 100% 신뢰도

    def _generate_suggested_name(self, pattern: Dict[str, Any]) -> str:
        """제안 이름 생성 (Mock)"""
        query = pattern.get("query", "")
        return f"{query} 즐겨찾기"

    def _suggest_filters(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """필터 제안 (Mock)"""
        return {"rating_min": 4.0}

    def _estimate_future_usage(self, pattern: Dict[str, Any]) -> int:
        """미래 사용량 예측 (Mock)"""
        return pattern.get("frequency", 0) * 2

    async def _analyze_usage_trends(
        self, user_id: UUID, period_days: int
    ) -> Dict[str, Any]:
        """사용 트렌드 분석 (Mock)"""
        return {
            "weekly_usage": [5, 8, 12, 7],
            "peak_day": "Tuesday",
            "peak_hour": 14,
        }

    def _generate_usage_recommendations(
        self, favorites: List[Dict[str, Any]], category_usage: Dict[str, Any]
    ) -> List[str]:
        """사용량 기반 추천사항 생성 (Mock)"""
        return [
            "자주 사용하지 않는 즐겨찾기는 정리해보세요",
            "맛집 카테고리 검색을 즐겨찾기로 더 추가해보세요",
        ]

    async def _resolve_sync_conflict(
        self, server_fav: Dict[str, Any], local_fav: Dict[str, Any]
    ) -> Dict[str, Any]:
        """동기화 충돌 해결 (Mock)"""
        # 사용 횟수가 더 많은 것을 선택
        if server_fav.get("use_count", 0) >= local_fav.get("use_count", 0):
            return server_fav
        else:
            return local_fav

    async def _create_favorite_from_sync(
        self, user_id: UUID, favorite_data: Dict[str, Any]
    ) -> None:
        """동기화로부터 즐겨찾는 검색 생성 (Mock)"""
        # 실제로는 create_favorite_search 호출

    async def _update_favorite(
        self, user_id: UUID, favorite_id: str, favorite_data: Dict[str, Any]
    ) -> None:
        """즐겨찾는 검색 업데이트 (Mock)"""
        favorites_key = self.favorites_key_pattern.format(user_id=user_id)
        await self.redis.hset(
            favorites_key, favorite_id, json.dumps(favorite_data, default=str)
        )

    async def _get_cached_frequent_favorites(
        self, user_id: UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """자주 사용되는 즐겨찾기 캐시 조회 (Mock)"""
        return None

    async def _cache_frequent_favorites(
        self, user_id: UUID, favorites: List[Dict[str, Any]]
    ) -> None:
        """자주 사용되는 즐겨찾기 캐싱 (Mock)"""


# 의존성 주입용 팩토리 함수
def get_favorite_searches_service(
    redis_client: redis.Redis, db_session: Session
) -> FavoriteSearchesService:
    """즐겨찾는 검색 서비스 의존성"""
    return FavoriteSearchesService(redis_client, db_session)
