"""
동적 정렬 서비스 (Task 2-3-3)

다양한 정렬 기준과 복합 정렬을 지원하는 고급 정렬 시스템
- 거리, 평점, 가격, 최근성, 인기도 등 다중 정렬 기준
- 사용자 선호도 기반 개인화 정렬
- 정렬 성능 최적화 및 캐싱
- 정렬 프리셋 저장 및 추천
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from app.core.cache import CacheService
from app.models.place import Place
from app.schemas.filter import SortCriteria, SortDirection, SortField
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class SortService:
    """동적 정렬 서비스"""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
        analytics_service: AnalyticsService,
    ):
        self.db = db
        self.cache_service = cache_service
        self.analytics_service = analytics_service

    async def apply_sort(
        self,
        query: Query,
        sort_criteria: SortCriteria,
        user_id: Optional[UUID] = None,
        user_location: Optional[Tuple[float, float]] = None,
    ) -> Query:
        """
        정렬 조건을 쿼리에 적용

        Args:
            query: 기본 쿼리
            sort_criteria: 정렬 기준들
            user_id: 사용자 ID (개인화 정렬용)
            user_location: 사용자 위치 (lat, lng)

        Returns:
            Query: 정렬이 적용된 쿼리
        """
        if not sort_criteria.fields:
            # 기본 정렬: 최근 업데이트 순
            return query.order_by(Place.updated_at.desc())

        # 각 정렬 필드 적용
        for sort_field in sort_criteria.fields:
            query = await self._apply_single_sort_field(
                query, sort_field, user_id, user_location
            )

        return query

    async def _apply_single_sort_field(
        self,
        query: Query,
        sort_field,
        user_id: Optional[UUID] = None,
        user_location: Optional[Tuple[float, float]] = None,
    ) -> Query:
        """단일 정렬 필드 적용"""

        direction = sort_field.direction
        asc_order = direction == SortDirection.ASC

        if sort_field.field == SortField.NAME:
            # 이름 정렬 (알파벳/가나다순)
            order_expr = Place.name.asc() if asc_order else Place.name.desc()

        elif sort_field.field == SortField.CREATED_AT:
            # 생성 날짜 정렬
            order_expr = (
                Place.created_at.asc() if asc_order else Place.created_at.desc()
            )

        elif sort_field.field == SortField.UPDATED_AT:
            # 수정 날짜 정렬
            order_expr = (
                Place.updated_at.asc() if asc_order else Place.updated_at.desc()
            )

        elif sort_field.field == SortField.RATING:
            # 평점 정렬 (NULL 값 처리)
            if asc_order:
                order_expr = Place.rating.asc().nullslast()
            else:
                order_expr = Place.rating.desc().nullslast()

        elif sort_field.field == SortField.PRICE_RANGE:
            # 가격대 정렬
            order_expr = (
                Place.price_range.asc() if asc_order else Place.price_range.desc()
            )

        elif sort_field.field == SortField.VISIT_COUNT:
            # 방문 횟수 정렬
            order_expr = (
                Place.visit_count.asc() if asc_order else Place.visit_count.desc()
            )

        elif sort_field.field == SortField.LAST_VISITED:
            # 마지막 방문일 정렬 (NULL 값을 적절히 처리)
            if asc_order:
                order_expr = Place.last_visited.asc().nullslast()
            else:
                order_expr = Place.last_visited.desc().nullsfirst()

        elif sort_field.field == SortField.DISTANCE:
            # 거리 정렬 (사용자 위치 필요)
            if user_location:
                lat, lng = user_location
                distance_expr = self._calculate_distance_expression(lat, lng)
                order_expr = distance_expr.asc() if asc_order else distance_expr.desc()
            else:
                # 위치 정보가 없으면 이름 정렬로 대체
                logger.warning("Distance sort requested but user location not provided")
                order_expr = Place.name.asc()

        elif sort_field.field == SortField.POPULARITY:
            # 인기도 정렬 (방문 횟수 + 평점 가중 평균)
            popularity_expr = (
                func.coalesce(Place.visit_count, 0) * 0.3
                + func.coalesce(Place.rating, 0) * 0.7
            )
            order_expr = popularity_expr.asc() if asc_order else popularity_expr.desc()

        elif sort_field.field == SortField.RANDOM:
            # 랜덤 정렬
            order_expr = func.random()

        else:
            # 알 수 없는 정렬 필드는 기본 정렬 사용
            logger.warning(f"Unknown sort field: {sort_field.field}")
            order_expr = Place.updated_at.desc()

        return query.order_by(order_expr)

    def _calculate_distance_expression(self, user_lat: float, user_lng: float):
        """Haversine 공식을 사용한 거리 계산 표현식"""
        return (
            func.acos(
                func.cos(func.radians(user_lat))
                * func.cos(func.radians(Place.latitude))
                * func.cos(func.radians(Place.longitude) - func.radians(user_lng))
                + func.sin(func.radians(user_lat))
                * func.sin(func.radians(Place.latitude))
            )
            * 6371
        )  # 지구 반지름 (km)

    async def apply_personalized_sort(
        self,
        query: Query,
        user_id: UUID,
        user_location: Optional[Tuple[float, float]] = None,
        diversity_factor: float = 0.3,
    ) -> Query:
        """
        개인화된 정렬 적용

        Args:
            query: 기본 쿼리
            user_id: 사용자 ID
            user_location: 사용자 위치
            diversity_factor: 다양성 팩터 (0.0~1.0)

        Returns:
            Query: 개인화 정렬이 적용된 쿼리
        """

        # 사용자 행동 패턴 분석 (캐시 활용)
        cache_key = f"hotly:user_behavior:{user_id}"
        user_behavior = await self.cache_service.get(cache_key)

        if not user_behavior:
            user_behavior = await self._analyze_user_behavior(user_id)
            await self.cache_service.set(cache_key, user_behavior, ttl=3600)  # 1시간 캐시

        # 개인화 점수 계산
        personalized_score = await self._calculate_personalized_score(
            user_behavior, user_location
        )

        # 다양성 보장
        if diversity_factor > 0:
            personalized_score = self._apply_diversity_factor(
                personalized_score, diversity_factor
            )

        # 최종 정렬 적용
        return query.order_by(personalized_score.desc())

    async def _analyze_user_behavior(self, user_id: UUID) -> Dict[str, Any]:
        """사용자 행동 패턴 분석"""

        # 사용자의 장소 데이터 분석
        user_places = await self.db.query(Place).filter(Place.user_id == user_id).all()

        if not user_places:
            return self._get_default_behavior_pattern()

        # 카테고리 선호도 계산
        category_counts = {}
        category_ratings = {}

        for place in user_places:
            category = place.category
            category_counts[category] = category_counts.get(category, 0) + 1

            if place.rating:
                if category not in category_ratings:
                    category_ratings[category] = []
                category_ratings[category].append(place.rating)

        # 카테고리별 선호도 점수 계산 (빈도 + 평점)
        category_preferences = {}
        total_places = len(user_places)

        for category, count in category_counts.items():
            frequency_score = count / total_places
            rating_score = (
                sum(category_ratings.get(category, [3.0]))
                / len(category_ratings.get(category, [3.0]))
            ) / 5.0  # 0~1로 정규화

            category_preferences[category] = frequency_score * 0.6 + rating_score * 0.4

        # 지역 선호도 계산
        region_counts = {}
        for place in user_places:
            if place.region:
                region_counts[place.region] = region_counts.get(place.region, 0) + 1

        region_preferences = {
            region: count / total_places for region, count in region_counts.items()
        }

        # 가격대 선호도 계산
        price_counts = {}
        for place in user_places:
            if place.price_range:
                price_counts[place.price_range] = (
                    price_counts.get(place.price_range, 0) + 1
                )

        price_preferences = {
            price: count / total_places for price, count in price_counts.items()
        }

        # 시간대별 활동 패턴 분석
        time_patterns = await self._analyze_time_patterns(user_id)

        return {
            "category_preferences": category_preferences,
            "region_preferences": region_preferences,
            "price_preferences": price_preferences,
            "time_preferences": time_patterns,
            "most_preferred_category": max(
                category_preferences.keys(), key=category_preferences.get
            )
            if category_preferences
            else None,
            "average_rating": sum(p.rating for p in user_places if p.rating)
            / len([p for p in user_places if p.rating])
            if any(p.rating for p in user_places)
            else 3.0,
        }

    async def _analyze_time_patterns(self, user_id: UUID) -> Dict[str, float]:
        """시간대별 활동 패턴 분석"""

        # 실제 구현에서는 사용자의 방문 로그를 분석
        # 여기서는 기본 패턴 반환
        return {
            "morning": 1.0,  # 6-11시
            "lunch": 1.2,  # 11-14시
            "afternoon": 0.8,  # 14-18시
            "evening": 1.5,  # 18-22시
            "night": 0.5,  # 22-6시
        }

    def _get_default_behavior_pattern(self) -> Dict[str, Any]:
        """기본 행동 패턴 (신규 사용자용)"""

        return {
            "category_preferences": {
                "cafe": 0.3,
                "restaurant": 0.4,
                "cultural": 0.2,
                "activity": 0.1,
            },
            "region_preferences": {},
            "price_preferences": {1: 0.2, 2: 0.3, 3: 0.3, 4: 0.15, 5: 0.05},
            "time_preferences": {
                "morning": 1.0,
                "lunch": 1.2,
                "afternoon": 0.8,
                "evening": 1.5,
                "night": 0.5,
            },
            "most_preferred_category": "restaurant",
            "average_rating": 3.5,
        }

    async def _calculate_personalized_score(
        self,
        user_behavior: Dict[str, Any],
        user_location: Optional[Tuple[float, float]] = None,
    ):
        """개인화 점수 계산"""

        # 1. 카테고리 선호도 점수
        category_score = case(
            *[
                (Place.category == cat, score)
                for cat, score in user_behavior["category_preferences"].items()
            ],
            else_=0.5,  # 기본 점수
        )

        # 2. 지역 선호도 점수
        region_score = 0.5  # 기본값
        if user_behavior["region_preferences"]:
            region_score = case(
                *[
                    (Place.region == region, score)
                    for region, score in user_behavior["region_preferences"].items()
                ],
                else_=0.3,  # 알려지지 않은 지역은 낮은 점수
            )

        # 3. 가격대 선호도 점수
        price_score = case(
            *[
                (Place.price_range == price, score)
                for price, score in user_behavior["price_preferences"].items()
            ],
            else_=0.3,  # 기본 점수
        )

        # 4. 평점 점수 (사용자 평균 대비)
        user_avg_rating = user_behavior["average_rating"]
        rating_score = func.coalesce(Place.rating, user_avg_rating) / 5.0

        # 5. 거리 점수 (가까울수록 높음)
        distance_score = 0.5  # 기본값
        if user_location:
            lat, lng = user_location
            distance_km = self._calculate_distance_expression(lat, lng)
            # 최대 20km로 정규화
            distance_score = func.greatest(0, 1 - (distance_km / 20.0))

        # 6. 시간대별 가중치
        current_hour = datetime.now().hour
        time_weight = 1.0

        if 6 <= current_hour < 11:
            time_weight = user_behavior["time_preferences"]["morning"]
        elif 11 <= current_hour < 14:
            time_weight = user_behavior["time_preferences"]["lunch"]
        elif 14 <= current_hour < 18:
            time_weight = user_behavior["time_preferences"]["afternoon"]
        elif 18 <= current_hour < 22:
            time_weight = user_behavior["time_preferences"]["evening"]
        else:
            time_weight = user_behavior["time_preferences"]["night"]

        # 최종 개인화 점수 계산
        personalized_score = (
            category_score * 0.3
            + region_score * 0.2
            + price_score * 0.15
            + rating_score * 0.25
            + distance_score * 0.1
        ) * time_weight

        return personalized_score

    def _apply_diversity_factor(self, base_score, diversity_factor: float):
        """다양성 팩터 적용"""

        # 카테고리별 다양성 보장
        category_penalty = case(
            [
                (
                    func.row_number().over(partition_by=Place.category) > 2,
                    -diversity_factor * 0.1,
                )
            ],
            else_=0,
        )

        # 가격대별 다양성 보장
        price_penalty = case(
            [
                (
                    func.row_number().over(partition_by=Place.price_range) > 3,
                    -diversity_factor * 0.05,
                )
            ],
            else_=0,
        )

        return base_score + category_penalty + price_penalty

    async def get_recommended_sorts(
        self, user_id: UUID, context: str = "general", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """상황별 추천 정렬 생성"""

        recommendations = []
        current_hour = datetime.now().hour

        # 시간대별 추천
        if 6 <= current_hour < 11:  # 아침
            recommendations.append(
                {
                    "name": "아침 추천",
                    "description": "아침 시간에 적합한 장소 순으로 정렬",
                    "sort_fields": ["personalized"],
                    "context": "morning",
                    "confidence": 0.8,
                }
            )
        elif 11 <= current_hour < 14:  # 점심
            recommendations.append(
                {
                    "name": "점심 맛집",
                    "description": "점심 시간 맛집을 평점 순으로 정렬",
                    "sort_fields": ["rating", "distance"],
                    "context": "lunch",
                    "confidence": 0.9,
                }
            )
        elif 18 <= current_hour < 22:  # 저녁
            recommendations.append(
                {
                    "name": "저녁 데이트",
                    "description": "저녁 데이트에 적합한 분위기 좋은 곳 순으로 정렬",
                    "sort_fields": ["rating", "popularity"],
                    "context": "evening",
                    "confidence": 0.85,
                }
            )

        # 거리 기반 추천
        if context == "nearby":
            recommendations.append(
                {
                    "name": "가까운 순",
                    "description": "현재 위치에서 가까운 순으로 정렬",
                    "sort_fields": ["distance"],
                    "context": "location_based",
                    "confidence": 0.9,
                }
            )

        # 개인 취향 기반 추천
        recommendations.append(
            {
                "name": "내 취향",
                "description": "개인 취향을 반영한 맞춤 정렬",
                "sort_fields": ["personalized"],
                "context": "personalized",
                "confidence": 0.75,
            }
        )

        # 탐험 추천
        unvisited_count = (
            await self.db.query(Place)
            .filter(Place.user_id == user_id, Place.last_visited.is_(None))
            .count()
        )

        if unvisited_count > 0:
            recommendations.append(
                {
                    "name": "새로운 발견",
                    "description": "아직 가보지 않은 장소 우선 정렬",
                    "sort_fields": ["last_visited", "rating"],
                    "context": "exploration",
                    "confidence": 0.6,
                }
            )

        # 신뢰도 순 정렬
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:limit]

    async def track_sort_usage(
        self, user_id: UUID, sort_fields: List[str], result_count: int
    ) -> None:
        """정렬 사용 통계 기록"""

        usage_data = {
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "sort_fields": sort_fields,
            "result_count": result_count,
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
        }

        # 분석 서비스에 전송
        await self.analytics_service.track_event("sort_applied", user_id, usage_data)

    async def clear_sort_cache(self, user_id: Optional[UUID] = None) -> None:
        """정렬 관련 캐시 삭제"""

        if user_id:
            pattern = f"hotly:user_behavior:{user_id}"
        else:
            pattern = "hotly:user_behavior:*"

        await self.cache_service.delete_pattern(pattern)
        logger.info(f"Cleared sort cache for user: {user_id or 'all'}")
