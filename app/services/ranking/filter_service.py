"""
고급 필터 서비스 (Task 2-3-3)

다중 필터 조합, 동적 필터링, 성능 최적화를 통한 고급 검색 시스템
- 복합 AND/OR 필터 조합 로직
- 카테고리, 지역, 태그, 가격대, 평점 등 다중 필터 지원
- 캐시 기반 필터링 성능 최적화
- 사용자 필터 패턴 분석 및 추천
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, selectinload

from app.core.cache import CacheService
from app.core.config import get_settings
from app.models.place import Place
from app.schemas.filter import (
    FilterCriteria,
    FilterPreset,
    FilterRecommendation,
    FilterResult,
    FilterStats,
    SortCriteria,
    SortDirection,
    SortField,
)
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
settings = get_settings()


class FilterService:
    """고급 필터 서비스"""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
        analytics_service: AnalyticsService,
    ):
        self.db = db
        self.cache_service = cache_service
        self.analytics_service = analytics_service

    async def apply_filters(
        self,
        user_id: UUID,
        criteria: FilterCriteria,
        page: int = 1,
        page_size: int = 20,
    ) -> FilterResult:
        """
        다중 필터 조합을 적용하여 장소 검색

        Args:
            user_id: 사용자 ID
            criteria: 필터 조건들
            page: 페이지 번호
            page_size: 페이지 크기

        Returns:
            FilterResult: 필터링된 결과와 메타데이터
        """
        start_time = datetime.utcnow()

        # 캐시 키 생성
        cache_key = self._generate_cache_key(user_id, criteria, page, page_size)

        # 캐시에서 결과 확인
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Filter cache hit for user {user_id}")
            return FilterResult.parse_obj(cached_result)

        try:
            # 기본 쿼리 구성
            query = self.db.query(Place).filter(Place.user_id == user_id)

            # 필터 조건 적용
            query = await self._apply_filter_conditions(query, criteria)

            # 전체 개수 계산
            total_count = await query.count()

            # 정렬 적용
            if criteria.sort_criteria:
                query = self._apply_sorting(query, criteria.sort_criteria)
            else:
                # 기본 정렬: 최근 수정 순
                query = query.order_by(Place.updated_at.desc())

            # 페이지네이션
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # 결과 조회 (관련 데이터 eager loading)
            places = await query.options(
                selectinload(Place.tags),
                selectinload(Place.reviews),
            ).all()

            # 필터 통계 계산
            filter_stats = await self._calculate_filter_stats(
                user_id, criteria, total_count
            )

            # 결과 구성
            result = FilterResult(
                places=places,
                total_count=total_count,
                page=page,
                page_size=page_size,
                applied_filters=criteria,
                filter_stats=filter_stats,
                processing_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                cache_hit=False,
            )

            # 캐시에 저장 (5분 TTL)
            await self.cache_service.set(cache_key, result.dict(), ttl=300)

            # 필터 사용 통계 기록
            await self._track_filter_usage(user_id, criteria)

            logger.info(
                f"Applied filters for user {user_id}: {len(places)} results, "
                f"{result.processing_time_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Filter application failed for user {user_id}: {e}")
            raise

    async def _apply_filter_conditions(
        self, query: Query, criteria: FilterCriteria
    ) -> Query:
        """필터 조건들을 쿼리에 적용"""

        # 카테고리 필터 (OR 조건)
        if criteria.categories:
            query = query.filter(Place.category.in_(criteria.categories))

        # 지역 필터 (OR 조건)
        if criteria.regions:
            query = query.filter(Place.region.in_(criteria.regions))

        # 상태 필터 (OR 조건)
        if criteria.status_filters:
            query = query.filter(Place.status.in_(criteria.status_filters))

        # 가격대 필터 (OR 조건)
        if criteria.price_ranges:
            query = query.filter(Place.price_range.in_(criteria.price_ranges))

        # 평점 필터 (범위)
        if criteria.min_rating is not None:
            query = query.filter(Place.rating >= criteria.min_rating)
        if criteria.max_rating is not None:
            query = query.filter(Place.rating <= criteria.max_rating)

        # 거리 필터 (사용자 위치 기준)
        if criteria.max_distance_km and criteria.user_location:
            lat = criteria.user_location.latitude
            lng = criteria.user_location.longitude

            # Haversine 공식으로 거리 계산
            distance_formula = (
                func.acos(
                    func.cos(func.radians(lat))
                    * func.cos(func.radians(Place.latitude))
                    * func.cos(func.radians(Place.longitude) - func.radians(lng))
                    + func.sin(func.radians(lat))
                    * func.sin(func.radians(Place.latitude))
                )
                * 6371
            )  # 지구 반지름 (km)

            query = query.filter(distance_formula <= criteria.max_distance_km)

        # 태그 필터 (AND 조건 - 모든 태그를 포함해야 함)
        if criteria.required_tags:
            for tag in criteria.required_tags:
                query = query.filter(Place.tags.any(name=tag))

        # 제외할 태그 (NOT 조건)
        if criteria.excluded_tags:
            for tag in criteria.excluded_tags:
                query = query.filter(~Place.tags.any(name=tag))

        # 방문 상태 필터
        if criteria.visit_status:
            if criteria.visit_status == "visited":
                query = query.filter(Place.last_visited.isnot(None))
            elif criteria.visit_status == "not_visited":
                query = query.filter(Place.last_visited.is_(None))

        # 즐겨찾기 필터
        if criteria.favorites_only:
            query = query.filter(Place.is_favorite == True)

        # 생성/수정 날짜 필터
        if criteria.created_after:
            query = query.filter(Place.created_at >= criteria.created_after)
        if criteria.created_before:
            query = query.filter(Place.created_at <= criteria.created_before)

        if criteria.updated_after:
            query = query.filter(Place.updated_at >= criteria.updated_after)
        if criteria.updated_before:
            query = query.filter(Place.updated_at <= criteria.updated_before)

        # 커스텀 필터 조건 (고급 사용자용)
        if criteria.custom_conditions:
            for condition in criteria.custom_conditions:
                # SQL 조건을 텍스트로 추가 (보안상 검증 필요)
                query = query.filter(text(condition))

        return query

    def _apply_sorting(self, query: Query, sort_criteria: SortCriteria) -> Query:
        """정렬 조건을 쿼리에 적용"""

        for sort_field in sort_criteria.fields:
            direction = sort_field.direction

            if sort_field.field == SortField.NAME:
                order_by = (
                    Place.name.asc()
                    if direction == SortDirection.ASC
                    else Place.name.desc()
                )

            elif sort_field.field == SortField.CREATED_AT:
                order_by = (
                    Place.created_at.asc()
                    if direction == SortDirection.ASC
                    else Place.created_at.desc()
                )

            elif sort_field.field == SortField.UPDATED_AT:
                order_by = (
                    Place.updated_at.asc()
                    if direction == SortDirection.ASC
                    else Place.updated_at.desc()
                )

            elif sort_field.field == SortField.RATING:
                order_by = (
                    Place.rating.asc()
                    if direction == SortDirection.ASC
                    else Place.rating.desc()
                )

            elif sort_field.field == SortField.PRICE_RANGE:
                order_by = (
                    Place.price_range.asc()
                    if direction == SortDirection.ASC
                    else Place.price_range.desc()
                )

            elif sort_field.field == SortField.VISIT_COUNT:
                order_by = (
                    Place.visit_count.asc()
                    if direction == SortDirection.ASC
                    else Place.visit_count.desc()
                )

            elif sort_field.field == SortField.LAST_VISITED:
                # NULL 값을 마지막에 배치
                if direction == SortDirection.ASC:
                    order_by = Place.last_visited.asc().nullslast()
                else:
                    order_by = Place.last_visited.desc().nullsfirst()

            elif sort_field.field == SortField.DISTANCE:
                # 거리 정렬은 사용자 위치가 있을 때만 가능
                if (
                    hasattr(sort_criteria, "user_location")
                    and sort_criteria.user_location
                ):
                    lat = sort_criteria.user_location.latitude
                    lng = sort_criteria.user_location.longitude

                    distance_formula = (
                        func.acos(
                            func.cos(func.radians(lat))
                            * func.cos(func.radians(Place.latitude))
                            * func.cos(
                                func.radians(Place.longitude) - func.radians(lng)
                            )
                            + func.sin(func.radians(lat))
                            * func.sin(func.radians(Place.latitude))
                        )
                        * 6371
                    )

                    order_by = (
                        distance_formula.asc()
                        if direction == SortDirection.ASC
                        else distance_formula.desc()
                    )
                else:
                    # 거리 정렬이 불가능한 경우 이름 정렬로 대체
                    order_by = Place.name.asc()

            elif sort_field.field == SortField.RANDOM:
                # PostgreSQL의 RANDOM() 함수 사용
                order_by = func.random()

            else:
                # 기본값: 업데이트 날짜 내림차순
                order_by = Place.updated_at.desc()

            query = query.order_by(order_by)

        return query

    async def _calculate_filter_stats(
        self, user_id: UUID, criteria: FilterCriteria, filtered_count: int
    ) -> FilterStats:
        """필터 통계 정보 계산"""

        # 전체 장소 개수
        total_places = (
            await self.db.query(Place).filter(Place.user_id == user_id).count()
        )

        # 카테고리별 분포
        category_distribution = {}
        if criteria.categories:
            for category in criteria.categories:
                count = (
                    await self.db.query(Place)
                    .filter(Place.user_id == user_id, Place.category == category)
                    .count()
                )
                category_distribution[category] = count

        # 지역별 분포
        region_distribution = {}
        if criteria.regions:
            for region in criteria.regions:
                count = (
                    await self.db.query(Place)
                    .filter(Place.user_id == user_id, Place.region == region)
                    .count()
                )
                region_distribution[region] = count

        # 필터 효율성 계산 (얼마나 결과를 줄였는지)
        filter_efficiency = (
            (total_places - filtered_count) / total_places if total_places > 0 else 0
        )

        return FilterStats(
            total_places=total_places,
            filtered_count=filtered_count,
            filter_efficiency=filter_efficiency,
            category_distribution=category_distribution,
            region_distribution=region_distribution,
        )

    async def get_available_filters(self, user_id: UUID) -> Dict[str, List[str]]:
        """사용자가 사용할 수 있는 필터 옵션들 조회"""

        cache_key = f"hotly:filters:available:{user_id}"
        cached_filters = await self.cache_service.get(cache_key)

        if cached_filters:
            return cached_filters

        # 사용자의 장소 데이터에서 사용 가능한 필터 옵션 추출
        user_places = await self.db.query(Place).filter(Place.user_id == user_id).all()

        available_filters = {
            "categories": list(
                set(place.category for place in user_places if place.category)
            ),
            "regions": list(set(place.region for place in user_places if place.region)),
            "price_ranges": list(
                set(
                    str(place.price_range) for place in user_places if place.price_range
                )
            ),
            "tags": list(set(tag.name for place in user_places for tag in place.tags)),
            "status": ["가보고싶음", "즐겨찾기", "방문완료", "방문예정"],
        }

        # 캐시에 저장 (30분 TTL)
        await self.cache_service.set(cache_key, available_filters, ttl=1800)

        return available_filters

    async def save_filter_preset(
        self, user_id: UUID, name: str, criteria: FilterCriteria
    ) -> FilterPreset:
        """필터 프리셋 저장"""

        # 기존 프리셋 확인
        existing_preset = (
            await self.db.query(FilterPreset)
            .filter(FilterPreset.user_id == user_id, FilterPreset.name == name)
            .first()
        )

        if existing_preset:
            # 기존 프리셋 업데이트
            existing_preset.criteria = criteria.dict()
            existing_preset.updated_at = datetime.utcnow()
            preset = existing_preset
        else:
            # 새 프리셋 생성
            preset = FilterPreset(
                user_id=user_id,
                name=name,
                criteria=criteria.dict(),
            )
            self.db.add(preset)

        await self.db.commit()
        await self.db.refresh(preset)

        logger.info(f"Saved filter preset '{name}' for user {user_id}")

        return preset

    async def get_filter_presets(self, user_id: UUID) -> List[FilterPreset]:
        """사용자의 필터 프리셋 목록 조회"""

        presets = (
            await self.db.query(FilterPreset)
            .filter(FilterPreset.user_id == user_id)
            .order_by(FilterPreset.updated_at.desc())
            .all()
        )

        return presets

    async def get_recommended_filters(
        self, user_id: UUID, limit: int = 5
    ) -> List[FilterRecommendation]:
        """사용자별 추천 필터 생성"""

        # 사용자의 필터 사용 패턴 분석
        filter_usage = await self.analytics_service.get_user_filter_patterns(user_id)

        recommendations = []

        # 자주 사용하는 카테고리 기반 추천
        if filter_usage.frequent_categories:
            for category in filter_usage.frequent_categories[:3]:
                recommendation = FilterRecommendation(
                    name=f"{category} 전체",
                    description=f"{category} 카테고리의 모든 장소",
                    criteria=FilterCriteria(categories=[category]),
                    confidence_score=0.8,
                    usage_frequency=filter_usage.category_usage.get(category, 0),
                )
                recommendations.append(recommendation)

        # 지역 + 카테고리 조합 추천
        if filter_usage.frequent_regions and filter_usage.frequent_categories:
            region = filter_usage.frequent_regions[0]
            category = filter_usage.frequent_categories[0]

            recommendation = FilterRecommendation(
                name=f"{region} {category}",
                description=f"{region} 지역의 {category} 장소들",
                criteria=FilterCriteria(regions=[region], categories=[category]),
                confidence_score=0.9,
                usage_frequency=filter_usage.combination_usage.get(
                    f"{region}+{category}", 0
                ),
            )
            recommendations.append(recommendation)

        # 즐겨찾기 + 미방문 조합 추천
        favorite_count = (
            await self.db.query(Place)
            .filter(
                Place.user_id == user_id,
                Place.is_favorite == True,
                Place.last_visited.is_(None),
            )
            .count()
        )

        if favorite_count > 0:
            recommendation = FilterRecommendation(
                name="즐겨찾기 미방문",
                description="즐겨찾기한 곳 중 아직 가보지 않은 장소",
                criteria=FilterCriteria(
                    favorites_only=True, visit_status="not_visited"
                ),
                confidence_score=0.7,
                usage_frequency=0,
            )
            recommendations.append(recommendation)

        # 최근 저장된 장소 추천
        recent_places_count = (
            await self.db.query(Place)
            .filter(
                Place.user_id == user_id,
                Place.created_at >= datetime.utcnow().replace(day=1),  # 이번 달
            )
            .count()
        )

        if recent_places_count > 0:
            recommendation = FilterRecommendation(
                name="이번 달 추가",
                description="이번 달에 저장한 새로운 장소들",
                criteria=FilterCriteria(created_after=datetime.utcnow().replace(day=1)),
                confidence_score=0.6,
                usage_frequency=0,
            )
            recommendations.append(recommendation)

        # 신뢰도 점수순 정렬 후 제한
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        return recommendations[:limit]

    async def _track_filter_usage(
        self, user_id: UUID, criteria: FilterCriteria
    ) -> None:
        """필터 사용 통계 기록"""

        usage_data = {
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "filter_criteria": criteria.dict(),
            "categories": criteria.categories,
            "regions": criteria.regions,
            "tags": criteria.required_tags,
            "has_distance_filter": criteria.max_distance_km is not None,
            "has_rating_filter": criteria.min_rating is not None
            or criteria.max_rating is not None,
            "sort_fields": [f.field.value for f in criteria.sort_criteria.fields]
            if criteria.sort_criteria
            else [],
        }

        # 비동기로 분석 서비스에 전송
        await self.analytics_service.track_event("filter_applied", user_id, usage_data)

    def _generate_cache_key(
        self, user_id: UUID, criteria: FilterCriteria, page: int, page_size: int
    ) -> str:
        """필터 캐시 키 생성"""

        # 필터 조건을 정규화하여 일관된 키 생성
        criteria_hash = hash(str(sorted(criteria.dict().items())))

        return f"hotly:filter:result:{user_id}:{criteria_hash}:{page}:{page_size}"

    async def clear_filter_cache(self, user_id: Optional[UUID] = None) -> None:
        """필터 캐시 삭제"""

        if user_id:
            pattern = f"hotly:filter:*:{user_id}:*"
        else:
            pattern = "hotly:filter:*"

        await self.cache_service.delete_pattern(pattern)
        logger.info(f"Cleared filter cache for user: {user_id or 'all'}")
