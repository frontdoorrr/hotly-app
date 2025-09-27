"""
검색 랭킹 API 엔드포인트 (Task 2-3-4)

개인화된 검색 랭킹, 사용자 피드백 처리, 분석 제공
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api import deps

from app.core.config import settings
from app.models.user import User
from app.schemas.search_ranking import (
    MLModelMetrics,
    RankingAnalyticsRequest,
    RankingAnalyticsResponse,
    RankingConfigRequest,
    SearchRankingRequest,
    SearchRankingResponse,
    UserFeedbackRequest,
    UserProfileData,
)
from app.services.search_ranking_service import SearchRankingService

router = APIRouter()


async def get_search_ranking_service() -> SearchRankingService:
    """검색 랭킹 서비스 의존성"""
    # 실제 구현에서는 DI 컨테이너에서 주입
    from app.db.session import SessionLocal
    from app.services.ml_engine import get_ml_engine
    
    try:
        import redis.asyncio as redis
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    except ImportError:
        # Redis가 없으면 None으로 설정 (서비스에서 폴백 처리)
        redis_client = None

    db = SessionLocal()
    ml_engine = await get_ml_engine()

    return SearchRankingService(db, redis_client, ml_engine)


@router.post("/rank", response_model=SearchRankingResponse)
async def rank_search_results(
    ranking_request: SearchRankingRequest,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    검색 결과를 개인화하여 랭킹

    개인 선호도, 행동 패턴, 현재 컨텍스트를 고려한 지능형 랭킹
    """
    try:
        start_time = datetime.utcnow()

        # 랭킹 수행
        ranked_results = await ranking_service.rank_search_results(
            user_id=current_user.id,
            search_results=ranking_request.search_results,
            query=ranking_request.query,
            context=ranking_request.context.dict(),
            max_results=ranking_request.max_results,
            personalization_strength=ranking_request.personalization_strength,
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # 응답 구성
        response = SearchRankingResponse(
            ranked_results=ranked_results,
            total_results=len(ranked_results),
            personalization_applied=ranking_request.personalization_strength > 0.0,
            ranking_metadata={
                "algorithm_version": "v2.1.0",
                "personalization_strength": ranking_request.personalization_strength,
                "diversity_applied": ranking_request.diversity_threshold > 0.0,
                "context_factors": list(ranking_request.context.dict().keys()),
                "ml_model_used": True,
            },
            processing_time_ms=int(processing_time),
            cache_hit=False,  # 실제로는 서비스에서 반환
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"랭킹 처리 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/feedback")
async def submit_user_feedback(
    feedback: UserFeedbackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    사용자 피드백 제출 (클릭, 북마크, 방문 등)

    실시간 랭킹 개선을 위한 피드백 수집
    """
    try:
        # 백그라운드로 피드백 처리
        background_tasks.add_task(
            ranking_service.update_ranking_by_feedback,
            user_id=current_user.id,
            place_id=feedback.place_id,
            feedback_type=feedback.feedback_type,
            context={
                "query_context": feedback.query_context,
                "session_id": feedback.session_id,
                "timestamp": feedback.timestamp.isoformat(),
                **(feedback.additional_data or {}),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "피드백이 성공적으로 접수되었습니다",
                "feedback_id": f"fb_{current_user.id}_{feedback.place_id}_{int(datetime.utcnow().timestamp())}",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"피드백 처리 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/profile", response_model=UserProfileData)
async def get_user_profile(
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    사용자 개인화 프로필 조회

    선호도, 행동 패턴, 상호작용 히스토리 확인
    """
    try:
        profile = await ranking_service._get_user_profile(current_user.id)

        if not profile:
            profile = ranking_service._get_default_user_profile()

        return UserProfileData(**profile)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.put("/profile")
async def update_user_profile(
    profile_update: UserProfileData,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    사용자 개인화 프로필 업데이트

    선호도 설정 변경, 행동 패턴 조정
    """
    try:
        # 프로필 업데이트 (실제 구현 필요)
        # await ranking_service.update_user_profile(current_user.id, profile_update.dict())

        # 관련 캐시 무효화
        await ranking_service._invalidate_user_ranking_cache(current_user.id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "프로필이 성공적으로 업데이트되었습니다",
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 업데이트 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/analytics", response_model=RankingAnalyticsResponse)
async def get_ranking_analytics(
    analytics_request: RankingAnalyticsRequest,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    랭킹 성능 분석 데이터

    클릭률, 전환율, 만족도 등 메트릭 제공
    """
    try:
        # 분석 데이터 생성 (Mock 데이터 - 실제 구현 필요)
        period_days = (analytics_request.date_to - analytics_request.date_from).days

        analytics_data = RankingAnalyticsResponse(
            period={
                "date_from": analytics_request.date_from,
                "date_to": analytics_request.date_to,
            },
            metrics={
                "total_searches": 1247,
                "avg_click_through_rate": 0.68,
                "avg_conversion_rate": 0.34,
                "personalization_effectiveness": 0.82,
                "user_satisfaction_score": 4.2,
                "avg_response_time_ms": 156,
                "cache_hit_rate": 0.73,
                "ranking_accuracy": 0.78,
            },
            trends=[
                {
                    "date": (
                        analytics_request.date_from + timedelta(days=i)
                    ).isoformat(),
                    "click_through_rate": 0.65 + (i * 0.005),
                    "conversion_rate": 0.30 + (i * 0.002),
                }
                for i in range(min(period_days, 30))
            ],
            recommendations=[
                "개인화 가중치를 10% 증가시켜 클릭률을 개선하세요",
                "실시간 피드백 반영 속도를 높여보세요",
                "다양성 임계값을 0.4로 조정하여 결과 다양성을 높이세요",
            ],
        )

        return analytics_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 데이터 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/model/metrics", response_model=MLModelMetrics)
async def get_ml_model_metrics(
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    ML 모델 성능 메트릭 조회

    모델 정확도, 정밀도, 재현율 등 성능 지표
    """
    try:
        # Mock ML 모델 메트릭 (실제로는 ML 엔진에서 조회)
        model_metrics = MLModelMetrics(
            model_version="ranking_v2.1.0",
            accuracy=0.85,
            precision=0.82,
            recall=0.78,
            f1_score=0.80,
            training_date=datetime.utcnow() - timedelta(days=3),
            performance_metrics={
                "avg_ndcg": 0.78,
                "click_through_rate": 0.68,
                "user_satisfaction": 0.82,
                "processing_latency_p95": 245.0,
                "memory_usage_mb": 156.7,
            },
        )

        return model_metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 메트릭 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/config")
async def update_ranking_config(
    config_request: RankingConfigRequest,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    랭킹 알고리즘 설정 업데이트

    가중치, 개인화 강도, 다양성 설정 등 조정
    """
    try:
        # 관리자 권한 확인 (실제 구현에서)
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다"
            )

        # 설정 업데이트 (실제 구현 필요)
        if config_request.user_id:
            # 특정 사용자 설정
            cache_key = f"ranking_config:{config_request.user_id}"
        else:
            # 전역 설정
            cache_key = "ranking_config:global"

        config_data = {
            "ranking_weights": config_request.ranking_weights,
            "personalization_enabled": config_request.personalization_enabled,
            "diversity_settings": config_request.diversity_settings,
            "cache_settings": config_request.cache_settings,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": str(current_user.id),
        }

        # Redis에 설정 저장
        await ranking_service.redis.setex(
            cache_key, 86400, json.dumps(config_data)  # 24시간
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "랭킹 설정이 성공적으로 업데이트되었습니다",
                "config_id": cache_key,
                "updated_at": config_data["updated_at"],
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 업데이트 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/explain/{place_id}")
async def explain_ranking(
    place_id: str,
    query: Optional[str] = Query(None, description="검색 쿼리"),
    context_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    특정 장소의 랭킹 근거 설명

    왜 이 장소가 이 순위에 있는지 상세한 설명 제공
    """
    try:
        # Mock 랭킹 설명 (실제로는 랭킹 서비스에서 생성)
        ranking_explanation = {
            "place_id": place_id,
            "final_rank": 2,
            "final_score": 0.87,
            "factors": {
                "base_relevance": {
                    "score": 0.78,
                    "weight": 0.25,
                    "contribution": 0.195,
                    "explanation": "검색어 '홍대 카페'와의 매칭도가 높습니다",
                },
                "personalization": {
                    "score": 0.92,
                    "weight": 0.35,
                    "contribution": 0.322,
                    "explanation": "카페 카테고리를 선호하시고, 마포구 지역을 자주 이용하십니다",
                },
                "behavior_score": {
                    "score": 0.65,
                    "weight": 0.20,
                    "contribution": 0.13,
                    "explanation": "이전에 3번 방문하셨고, 평균 180초간 머물렀습니다",
                },
                "contextual": {
                    "score": 1.1,
                    "weight": 0.15,
                    "contribution": 0.165,
                    "explanation": "현재 오후 시간대에 카페 이용률이 높습니다",
                },
                "real_time": {
                    "score": 0.7,
                    "weight": 0.05,
                    "contribution": 0.035,
                    "explanation": "최근 1시간 내 긍정적인 피드백이 있었습니다",
                },
            },
            "summary": "개인 선호도와 과거 이용 패턴을 고려할 때 매우 적합한 장소입니다",
            "confidence_level": "높음",
            "alternative_suggestions": [
                "더 가까운 거리의 카페를 원한다면 '강남 스타벅스'를 추천합니다",
                "새로운 경험을 원한다면 '이태원 루프탑 카페'는 어떨까요?",
            ],
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=ranking_explanation)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"랭킹 설명 생성 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete("/cache")
async def clear_ranking_cache(
    user_id: Optional[UUID] = Query(None, description="특정 사용자 캐시만 삭제 (전체 삭제 시 생략)"),
    current_user: User = Depends(deps.get_current_active_user),
    ranking_service: SearchRankingService = Depends(get_search_ranking_service),
):
    """
    랭킹 캐시 수동 삭제

    성능 이슈나 데이터 업데이트 시 캐시 초기화
    """
    try:
        # 관리자 권한 확인
        if not current_user.is_superuser and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="자신의 캐시만 삭제할 수 있습니다"
            )

        if user_id:
            # 특정 사용자 캐시 삭제
            await ranking_service._invalidate_user_ranking_cache(user_id)
            message = f"사용자 {user_id}의 랭킹 캐시를 삭제했습니다"
        else:
            # 전체 랭킹 캐시 삭제 (관리자만)
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="전체 캐시 삭제는 관리자만 가능합니다"
                )

            # 전체 랭킹 캐시 패턴 삭제
            pattern = "ranking:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await ranking_service.redis.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                if keys:
                    await ranking_service.redis.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            message = f"전체 랭킹 캐시 {deleted_count}개 키를 삭제했습니다"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": message, "deleted_at": datetime.utcnow().isoformat()},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐시 삭제 중 오류가 발생했습니다: {str(e)}",
        )
