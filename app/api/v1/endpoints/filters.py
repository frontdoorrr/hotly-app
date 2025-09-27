"""
고급 필터 API 엔드포인트 (Task 2-3-3)

필터링, 정렬, 검색 설정 관련 API
- 사용 가능한 필터 옵션 조회
- 필터 프리셋 저장/조회
- 필터 추천 시스템
- 성능 최적화된 필터링
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.cache import CacheService
from app.models.user import User
from app.schemas.filter import (
    FilterCriteria,
    FilterPreset,
    FilterPresetCreate,
    FilterPresetUpdate,
    FilterRecommendation,
    FilterResult,
    FilterStats,
)
from app.services.analytics_service import AnalyticsService
from app.services.filter_service import FilterService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/available", response_model=Dict[str, List[str]])
async def get_available_filters(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    사용자가 사용할 수 있는 필터 옵션들 조회
    
    사용자의 장소 데이터를 기반으로 실제 적용 가능한 필터 옵션들을 반환합니다.
    """
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        available_filters = await filter_service.get_available_filters(current_user.id)
        
        logger.info(f"Retrieved available filters for user {current_user.id}")
        
        return available_filters
        
    except Exception as e:
        logger.error(f"Failed to get available filters for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 옵션 조회에 실패했습니다."
        )


@router.post("/apply", response_model=FilterResult)
async def apply_filters(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
    filter_criteria: FilterCriteria,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> Any:
    """
    필터 조건을 적용하여 장소 검색
    
    다중 필터 조합, 정렬, 페이지네이션을 지원하는 고급 검색 기능입니다.
    """
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        # 필터 적용
        result = await filter_service.apply_filters(
            user_id=current_user.id,
            criteria=filter_criteria,
            page=page,
            page_size=page_size,
        )
        
        logger.info(
            f"Applied filters for user {current_user.id}: "
            f"{result.total_count} results, {result.processing_time_ms}ms"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to apply filters for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 적용에 실패했습니다."
        )


@router.get("/presets", response_model=List[FilterPreset])
async def get_filter_presets(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """사용자의 필터 프리셋 목록 조회"""
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        presets = await filter_service.get_filter_presets(current_user.id)
        
        logger.info(f"Retrieved {len(presets)} filter presets for user {current_user.id}")
        
        return presets
        
    except Exception as e:
        logger.error(f"Failed to get filter presets for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 프리셋 조회에 실패했습니다."
        )


@router.post("/presets", response_model=FilterPreset)
async def save_filter_preset(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
    preset_data: FilterPresetCreate,
) -> Any:
    """필터 프리셋 저장"""
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        preset = await filter_service.save_filter_preset(
            user_id=current_user.id,
            name=preset_data.name,
            criteria=preset_data.criteria,
        )
        
        logger.info(f"Saved filter preset '{preset_data.name}' for user {current_user.id}")
        
        return preset
        
    except Exception as e:
        logger.error(f"Failed to save filter preset for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 프리셋 저장에 실패했습니다."
        )


@router.put("/presets/{preset_id}", response_model=FilterPreset)
async def update_filter_preset(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
    preset_id: UUID,
    preset_data: FilterPresetUpdate,
) -> Any:
    """필터 프리셋 수정"""
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        # 기존 프리셋 확인
        preset = await db.query(FilterPreset).filter(
            FilterPreset.id == preset_id,
            FilterPreset.user_id == current_user.id
        ).first()
        
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="필터 프리셋을 찾을 수 없습니다."
            )
        
        # 프리셋 업데이트
        if preset_data.name is not None:
            preset.name = preset_data.name
        if preset_data.criteria is not None:
            preset.criteria = preset_data.criteria.dict()
        if preset_data.description is not None:
            preset.description = preset_data.description
            
        preset.updated_at = func.now()
        
        await db.commit()
        await db.refresh(preset)
        
        logger.info(f"Updated filter preset {preset_id} for user {current_user.id}")
        
        return preset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update filter preset {preset_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 프리셋 수정에 실패했습니다."
        )


@router.delete("/presets/{preset_id}")
async def delete_filter_preset(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    preset_id: UUID,
) -> Any:
    """필터 프리셋 삭제"""
    try:
        # 기존 프리셋 확인
        preset = await db.query(FilterPreset).filter(
            FilterPreset.id == preset_id,
            FilterPreset.user_id == current_user.id
        ).first()
        
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="필터 프리셋을 찾을 수 없습니다."
            )
        
        await db.delete(preset)
        await db.commit()
        
        logger.info(f"Deleted filter preset {preset_id} for user {current_user.id}")
        
        return {"message": "필터 프리셋이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete filter preset {preset_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 프리셋 삭제에 실패했습니다."
        )


@router.get("/recommendations", response_model=List[FilterRecommendation])
async def get_filter_recommendations(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = Query(5, ge=1, le=20, description="추천 개수"),
) -> Any:
    """사용자별 필터 추천"""
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        recommendations = await filter_service.get_recommended_filters(
            user_id=current_user.id,
            limit=limit
        )
        
        logger.info(f"Generated {len(recommendations)} filter recommendations for user {current_user.id}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to get filter recommendations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 추천 생성에 실패했습니다."
        )


@router.post("/clear-cache")
async def clear_filter_cache(
    *,
    cache_service: CacheService = Depends(deps.get_cache_service),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """사용자의 필터 캐시 삭제"""
    try:
        # 사용자별 필터 캐시 삭제
        await cache_service.delete_pattern(f"hotly:filter:*:{current_user.id}:*")
        await cache_service.delete_pattern(f"hotly:filters:available:{current_user.id}")
        
        logger.info(f"Cleared filter cache for user {current_user.id}")
        
        return {"message": "필터 캐시가 삭제되었습니다."}
        
    except Exception as e:
        logger.error(f"Failed to clear filter cache for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 캐시 삭제에 실패했습니다."
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_filter_usage_stats(
    *,
    db: AsyncSession = Depends(deps.get_db),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
) -> Any:
    """사용자의 필터 사용 통계"""
    try:
        # 필터 사용 패턴 분석
        filter_patterns = await analytics_service.get_user_filter_patterns(
            user_id=current_user.id,
            days=days
        )
        
        # 자주 사용하는 필터 조합
        frequent_combinations = await analytics_service.get_frequent_filter_combinations(
            user_id=current_user.id,
            limit=10
        )
        
        # 필터 효율성 분석
        filter_efficiency = await analytics_service.calculate_filter_efficiency(
            user_id=current_user.id,
            days=days
        )
        
        stats = {
            "period_days": days,
            "total_filter_uses": filter_patterns.total_uses,
            "unique_filter_combinations": filter_patterns.unique_combinations,
            "most_used_categories": filter_patterns.frequent_categories[:5],
            "most_used_regions": filter_patterns.frequent_regions[:5],
            "frequent_combinations": frequent_combinations,
            "average_results_per_filter": filter_patterns.avg_results_per_filter,
            "filter_efficiency_score": filter_efficiency.overall_score,
            "time_patterns": {
                "most_active_hours": filter_patterns.peak_hours,
                "most_active_days": filter_patterns.peak_days,
            },
            "performance_metrics": {
                "average_response_time_ms": filter_patterns.avg_response_time,
                "cache_hit_rate": filter_patterns.cache_hit_rate,
            }
        }
        
        logger.info(f"Retrieved filter usage stats for user {current_user.id}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get filter usage stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 사용 통계 조회에 실패했습니다."
        )


@router.post("/optimize")
async def optimize_user_filters(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cache_service: CacheService = Depends(deps.get_cache_service),
    analytics_service: AnalyticsService = Depends(deps.get_analytics_service),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """사용자 필터 최적화"""
    filter_service = FilterService(db, cache_service, analytics_service)
    
    try:
        # 사용자 필터 패턴 분석
        patterns = await analytics_service.get_user_filter_patterns(current_user.id)
        
        optimizations = []
        
        # 1. 자주 사용하는 필터 조합을 프리셋으로 제안
        if patterns.frequent_combinations:
            for combination in patterns.frequent_combinations[:3]:
                if combination.usage_count >= 5:  # 5회 이상 사용된 조합
                    preset_name = f"자주 사용하는 {combination.name}"
                    
                    # 이미 비슷한 프리셋이 있는지 확인
                    existing_preset = await filter_service.get_similar_preset(
                        user_id=current_user.id,
                        criteria=combination.criteria
                    )
                    
                    if not existing_preset:
                        optimizations.append({
                            "type": "preset_suggestion",
                            "name": preset_name,
                            "criteria": combination.criteria,
                            "reason": f"{combination.usage_count}회 사용된 조합입니다.",
                            "confidence": 0.8,
                        })
        
        # 2. 비효율적인 필터 조합 감지
        inefficient_filters = await analytics_service.detect_inefficient_filters(
            current_user.id
        )
        
        for inefficient in inefficient_filters:
            optimizations.append({
                "type": "efficiency_warning",
                "filter_combination": inefficient.combination,
                "issue": inefficient.issue_description,
                "suggestion": inefficient.improvement_suggestion,
                "confidence": inefficient.confidence,
            })
        
        # 3. 새로운 필터 옵션 제안
        new_options = await analytics_service.suggest_new_filter_options(
            current_user.id
        )
        
        for option in new_options:
            optimizations.append({
                "type": "new_option",
                "filter_type": option.filter_type,
                "option_value": option.value,
                "expected_benefit": option.expected_benefit,
                "confidence": option.confidence,
            })
        
        logger.info(f"Generated {len(optimizations)} filter optimizations for user {current_user.id}")
        
        return {
            "optimizations": optimizations,
            "total_suggestions": len(optimizations),
            "analysis_period": "last_30_days",
            "next_analysis_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize filters for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 최적화에 실패했습니다."
        )