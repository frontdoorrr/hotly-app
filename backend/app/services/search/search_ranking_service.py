"""
검색 결과 랭킹 및 개인화 서비스 (Task 2-3-4)

ML 기반 스코어링과 사용자 행동 분석을 통한 개인화된 검색 랭킹 시스템
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

# from app.core.config import settings
from app.schemas.search_ranking import FeedbackType, RankingFactor, RankingFactorType

logger = logging.getLogger(__name__)


class SearchRankingService:
    """검색 랭킹 및 개인화 서비스"""

    def __init__(self, db_session, redis_client, ml_engine):
        """
        서비스 초기화

        Args:
            db_session: 데이터베이스 세션
            redis_client: Redis 클라이언트
            ml_engine: ML 엔진 (모델 추론)
        """
        self.db = db_session
        self.redis = redis_client
        self.ml_engine = ml_engine

        # 기본 랭킹 가중치
        self.default_weights = {
            "base_relevance": 0.25,
            "personalization": 0.35,
            "behavior_score": 0.20,
            "contextual": 0.15,
            "real_time": 0.05,
        }

        # 캐시 TTL 설정
        self.ranking_cache_ttl = 300  # 5분
        self.profile_cache_ttl = 3600  # 1시간

    async def rank_search_results(
        self,
        user_id: UUID,
        search_results: List[Dict[str, Any]],
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_results: Optional[int] = None,
        personalization_strength: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        검색 결과를 개인화하여 랭킹

        Args:
            user_id: 사용자 ID
            search_results: 원본 검색 결과
            query: 검색 쿼리
            context: 검색 컨텍스트
            max_results: 최대 결과 수
            personalization_strength: 개인화 강도 (0.0-1.0)

        Returns:
            랭킹된 검색 결과 리스트
        """
        start_time = time.time()
        context = context or {}

        try:
            # 1. 캐시 확인
            cache_key = self._generate_ranking_cache_key(
                user_id, search_results, query, context
            )

            if not context.get("optimization_mode", False):
                cached_result = await self._get_cached_ranking(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for ranking key: {cache_key}")
                    return cached_result

            # 2. 사용자 프로필 로드
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                logger.warning(f"No user profile found for {user_id}, using defaults")
                user_profile = self._get_default_user_profile()

            # 3. 결과 수 제한 (성능 최적화)
            if max_results and len(search_results) > max_results:
                search_results = search_results[:max_results]

            # 4. 각 결과에 대한 스코어 계산
            scored_results = []

            # 병렬 처리를 위한 배치 준비
            ml_scores = await self._calculate_ml_scores(
                user_id, search_results, query, user_profile
            )
            behavior_scores = await self._calculate_behavior_scores(
                user_id, search_results
            )
            contextual_adjustments = await self._apply_contextual_adjustments(
                search_results, context
            )

            for idx, result in enumerate(search_results):
                place_id = result.get("id") or result.get("_id")

                # 기본 관련성 점수 (Elasticsearch _score 기반)
                base_score = self._normalize_score(result.get("_score", 1.0), 0, 10)

                # ML 기반 점수
                ml_score = ml_scores.get(place_id, 0.5)

                # 개인화 점수
                personalization_score = self._calculate_personalization_score(
                    result, user_profile, personalization_strength
                )

                # 행동 기반 점수
                behavior_score = behavior_scores.get(place_id, 0.0)

                # 컨텍스트 조정
                contextual_score = contextual_adjustments.get(place_id, 1.0)

                # 실시간 조정
                real_time_adjustment = await self._get_real_time_score_adjustment(
                    user_id, place_id
                )

                # 최종 점수 계산
                ranking_factors = self._build_ranking_factors(
                    base_score,
                    ml_score,
                    personalization_score,
                    behavior_score,
                    contextual_score,
                    real_time_adjustment,
                    context.get("explain_ranking", False),
                )

                final_score = self._calculate_final_score(ranking_factors)

                # 결과 객체 구성
                scored_result = {
                    **result,
                    "original_rank": idx + 1,
                    "final_rank_score": final_score,
                    "personalization_score": personalization_score,
                    "ranking_factors": ranking_factors,
                    "confidence_score": self._calculate_confidence_score(
                        ranking_factors
                    ),
                    "ranking_source": "ml_algorithm",
                }

                scored_results.append(scored_result)

            # 5. 점수 기준 정렬
            scored_results.sort(key=lambda x: x["final_rank_score"], reverse=True)

            # 6. 다양성 주입 (선택적)
            if context.get("diversity_enabled", True):
                scored_results = await self._apply_diversity_injection(
                    scored_results, context.get("diversity_threshold", 0.3)
                )

            # 7. 최종 랭크 할당
            for idx, result in enumerate(scored_results):
                result["final_rank"] = idx + 1

            # 8. 결과 캐시 저장
            processing_time = time.time() - start_time
            if processing_time < 1.0:  # 1초 이내 처리된 결과만 캐시
                await self._cache_ranking_result(cache_key, scored_results)

            logger.info(
                f"Ranked {len(scored_results)} results for user {user_id} "
                f"in {processing_time:.3f}s"
            )

            return scored_results

        except Exception as e:
            logger.error(f"Ranking failed for user {user_id}: {str(e)}")
            # Fallback: 기본 랭킹으로 복구
            return await self._fallback_ranking(search_results)

    async def _calculate_ml_scores(
        self,
        user_id: UUID,
        search_results: List[Dict[str, Any]],
        query: Optional[str],
        user_profile: Dict[str, Any],
    ) -> Dict[str, float]:
        """ML 모델 기반 관련성 점수 계산"""
        try:
            if not self.ml_engine:
                return {result.get("id", ""): 0.5 for result in search_results}

            # 특성 벡터 생성
            feature_vectors = self._build_feature_vectors(
                search_results, query, user_profile
            )

            # ML 모델 추론 - 올바른 파라미터 사용
            prediction_scores = await self.ml_engine.predict_relevance(
                feature_vectors=feature_vectors,
                user_id=user_id,
                context={"query": query},
            )

            # 결과 매핑
            ml_scores = {}
            for i, result in enumerate(search_results):
                place_id = result.get("id", "")
                score = prediction_scores[i] if i < len(prediction_scores) else 0.5
                ml_scores[place_id] = self._normalize_score(score, 0, 1)

            return ml_scores

        except Exception as e:
            logger.error(f"ML scoring failed: {str(e)}")
            # Fallback: 균등한 점수 할당
            return {result.get("id", ""): 0.5 for result in search_results}

    async def _calculate_behavior_scores(
        self, user_id: UUID, search_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """사용자 행동 기반 점수 계산"""
        try:
            place_ids = [result.get("id") for result in search_results]
            interactions = await self._get_user_interactions(user_id, place_ids)

            behavior_scores = {}
            for result in search_results:
                place_id = result.get("id")
                interaction = interactions.get(place_id, {})

                # 상호작용 메트릭들
                view_count = interaction.get("view_count", 0)
                click_count = interaction.get("click_count", 0)
                bookmark_count = interaction.get("bookmark_count", 0)
                avg_time_spent = interaction.get("avg_time_spent", 0)
                last_interaction = interaction.get("last_interaction")

                # 점수 계산 (0.0 - 1.0 범위)
                view_score = min(view_count / 10.0, 1.0)  # 10회 이상 = 1.0
                click_score = min(click_count / 5.0, 1.0)  # 5회 이상 = 1.0
                bookmark_score = bookmark_count * 0.3  # 북마크는 강한 신호
                time_score = min(avg_time_spent / 300.0, 1.0)  # 5분 이상 = 1.0

                # 최근성 가중치
                recency_weight = 1.0
                if last_interaction:
                    days_since = (datetime.utcnow() - last_interaction).days
                    recency_weight = max(0.1, 1.0 - (days_since / 30.0))  # 30일 감소

                # 최종 행동 점수
                behavior_score = (
                    view_score * 0.2
                    + click_score * 0.3
                    + bookmark_score * 0.3
                    + time_score * 0.2
                ) * recency_weight

                behavior_scores[place_id] = min(behavior_score, 1.0)

            return behavior_scores

        except Exception as e:
            logger.error(f"Behavior scoring failed: {str(e)}")
            return {result.get("id", ""): 0.0 for result in search_results}

    def _calculate_personalization_score(
        self, result: Dict[str, Any], user_profile: Dict[str, Any], strength: float
    ) -> float:
        """개인화 점수 계산"""
        try:
            preferences = user_profile.get("preferences", {})

            # 카테고리 선호도
            category = result.get("category", "")
            category_pref = preferences.get("categories", {}).get(category, 0.5)

            # 지역 선호도
            address = result.get("address", "")
            region_pref = 0.5
            for region, pref in preferences.get("regions", {}).items():
                if region in address:
                    region_pref = pref
                    break

            # 태그 선호도
            tags = result.get("tags", [])
            tag_prefs = []
            for tag in tags:
                tag_pref = preferences.get("tags", {}).get(tag, 0.5)
                tag_prefs.append(tag_pref)

            avg_tag_pref = sum(tag_prefs) / len(tag_prefs) if tag_prefs else 0.5

            # 가격대 선호도
            price_range = result.get("price_range", 20000)
            price_pref = 0.5
            for range_key, pref in preferences.get("price_ranges", {}).items():
                if self._price_in_range(price_range, range_key):
                    price_pref = pref
                    break

            # 가중 평균
            personalization_score = (
                category_pref * 0.4
                + region_pref * 0.25
                + avg_tag_pref * 0.2
                + price_pref * 0.15
            )

            # 개인화 강도 적용
            final_score = 0.5 + (personalization_score - 0.5) * strength

            return max(0.0, min(1.0, final_score))

        except Exception as e:
            logger.error(f"Personalization scoring failed: {str(e)}")
            return 0.5

    async def _apply_contextual_adjustments(
        self, search_results: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, float]:
        """컨텍스트 기반 점수 조정"""
        try:
            adjustments = {}
            time_of_day = context.get("time_of_day", "")
            context.get("day_of_week", "")
            weather = context.get("weather", "")

            for result in search_results:
                place_id = result.get("id")
                adjustment = 1.0

                # 시간대별 조정
                category = result.get("category", "")
                if time_of_day == "morning":
                    if category == "cafe":
                        adjustment *= 1.2  # 아침에 카페 선호
                elif time_of_day == "evening":
                    if category in ["bar", "restaurant"]:
                        adjustment *= 1.1  # 저녁에 바/레스토랑 선호

                # 날씨 조정
                if weather == "rainy":
                    # 실내 장소 선호
                    indoor_categories = ["cafe", "restaurant", "shopping", "culture"]
                    if category in indoor_categories:
                        adjustment *= 1.1
                elif weather == "sunny":
                    # 야외 활동 장소 선호
                    outdoor_tags = ["야외", "테라스", "루프탑", "공원"]
                    tags = result.get("tags", [])
                    if any(tag in outdoor_tags for tag in tags):
                        adjustment *= 1.1

                # 거리 기반 조정 (근거리 선호)
                distance_km = result.get("distance_km", 5.0)
                if distance_km <= 1.0:
                    adjustment *= 1.1
                elif distance_km > 5.0:
                    adjustment *= 0.9

                adjustments[place_id] = max(0.5, min(1.5, adjustment))

            return adjustments

        except Exception as e:
            logger.error(f"Contextual adjustment failed: {str(e)}")
            return {result.get("id", ""): 1.0 for result in search_results}

    async def _get_real_time_score_adjustment(
        self, user_id: UUID, place_id: str
    ) -> float:
        """실시간 점수 조정 (최근 피드백 반영)"""
        try:
            # Redis에서 실시간 피드백 조회
            feedback_key = f"feedback:{user_id}:{place_id}"
            feedback_data = await self.redis.get(feedback_key)

            if not feedback_data:
                return 0.0

            feedback = json.loads(feedback_data)

            # 최근 1시간 내 피드백만 고려
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            recent_feedback = [
                f
                for f in feedback
                if datetime.fromisoformat(f["timestamp"]) > cutoff_time
            ]

            if not recent_feedback:
                return 0.0

            # 피드백 타입별 가중치
            feedback_weights = {
                FeedbackType.CLICK: 0.1,
                FeedbackType.VIEW: 0.05,
                FeedbackType.BOOKMARK: 0.3,
                FeedbackType.VISIT: 0.4,
                FeedbackType.SHARE: 0.2,
                FeedbackType.SKIP: -0.1,
                FeedbackType.NEGATIVE: -0.2,
            }

            total_adjustment = 0.0
            for fb in recent_feedback:
                fb_type = FeedbackType(fb["type"])
                weight = feedback_weights.get(fb_type, 0.0)
                total_adjustment += weight

            # 조정값 제한 (-0.5 ~ +0.5)
            return max(-0.5, min(0.5, total_adjustment))

        except Exception as e:
            logger.error(f"Real-time adjustment failed: {str(e)}")
            return 0.0

    def _build_ranking_factors(
        self,
        base_score: float,
        ml_score: float,
        personalization_score: float,
        behavior_score: float,
        contextual_score: float,
        real_time_adjustment: float,
        explain: bool = False,
    ) -> Dict[str, RankingFactor]:
        """랭킹 요소들 구성"""
        factors = {}

        # 가중치 가져오기 (사용자별 커스터마이징 가능)
        weights = self.default_weights.copy()

        # 기본 관련성
        factors["base_relevance"] = RankingFactor(
            factor_type=RankingFactorType.BASE_RELEVANCE,
            weight=weights["base_relevance"],
            score=base_score,
            contribution=base_score * weights["base_relevance"],
            explanation="검색어와의 기본 관련성" if explain else None,
        )

        # ML 점수
        factors["ml_score"] = RankingFactor(
            factor_type=RankingFactorType.ML_SCORE,
            weight=weights["base_relevance"] * 0.5,  # 기본 관련성과 공유
            score=ml_score,
            contribution=ml_score * weights["base_relevance"] * 0.5,
            explanation="기계학습 모델 예측 점수" if explain else None,
        )

        # 개인화
        factors["personalization"] = RankingFactor(
            factor_type=RankingFactorType.PERSONALIZATION,
            weight=weights["personalization"],
            score=personalization_score,
            contribution=personalization_score * weights["personalization"],
            explanation="개인 선호도 기반 점수" if explain else None,
        )

        # 행동 점수
        factors["behavior_score"] = RankingFactor(
            factor_type=RankingFactorType.BEHAVIOR_SCORE,
            weight=weights["behavior_score"],
            score=behavior_score,
            contribution=behavior_score * weights["behavior_score"],
            explanation="과거 행동 패턴 기반 점수" if explain else None,
        )

        # 컨텍스트 조정
        factors["contextual"] = RankingFactor(
            factor_type=RankingFactorType.CONTEXTUAL,
            weight=weights["contextual"],
            score=contextual_score,
            contribution=(contextual_score - 1.0) * weights["contextual"],
            explanation="현재 상황 기반 조정" if explain else None,
        )

        # 실시간 조정
        factors["real_time"] = RankingFactor(
            factor_type=RankingFactorType.REAL_TIME,
            weight=weights["real_time"],
            score=0.5 + real_time_adjustment,  # 중성값 0.5 기준
            contribution=real_time_adjustment * weights["real_time"],
            explanation="실시간 피드백 반영" if explain else None,
        )

        return factors

    def _calculate_final_score(self, factors: Dict[str, RankingFactor]) -> float:
        """최종 랭킹 점수 계산"""
        total_contribution = sum(factor.contribution for factor in factors.values())

        # 점수 정규화 (0.0 - 1.0 범위)
        final_score = max(0.0, min(1.0, total_contribution))

        return final_score

    def _calculate_confidence_score(self, factors: Dict[str, RankingFactor]) -> float:
        """랭킹 신뢰도 점수 계산"""
        # 각 요소의 기여도 분산을 통한 신뢰도 계산
        contributions = [factor.contribution for factor in factors.values()]

        if not contributions:
            return 0.0

        # 기여도의 표준편차가 낮을수록 신뢰도가 높음
        mean_contrib = sum(contributions) / len(contributions)
        variance = sum((c - mean_contrib) ** 2 for c in contributions) / len(
            contributions
        )
        std_dev = variance**0.5

        # 신뢰도 = 1 - 정규화된 표준편차
        confidence = max(0.0, 1.0 - (std_dev * 2))  # 2는 조정 팩터

        return min(1.0, confidence)

    async def update_ranking_by_feedback(
        self,
        user_id: UUID,
        place_id: str,
        feedback_type: FeedbackType,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """사용자 피드백을 통한 실시간 랭킹 업데이트"""
        try:
            context = context or {}

            # 피드백 데이터 구성
            feedback_data = {
                "type": feedback_type.value,
                "place_id": place_id,
                "timestamp": context.get("timestamp", datetime.utcnow().isoformat()),
                "context": context,
            }

            # Redis에 실시간 피드백 저장
            feedback_key = f"feedback:{user_id}:{place_id}"
            existing_feedback = await self.redis.get(feedback_key)

            if existing_feedback:
                feedback_list = json.loads(existing_feedback)
            else:
                feedback_list = []

            feedback_list.append(feedback_data)

            # 최근 24시간 피드백만 유지
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            feedback_list = [
                f
                for f in feedback_list
                if datetime.fromisoformat(f["timestamp"]) > cutoff_time
            ]

            # Redis 업데이트 (1시간 TTL)
            await self.redis.setex(feedback_key, 3600, json.dumps(feedback_list))

            # 관련 랭킹 캐시 무효화
            await self._invalidate_user_ranking_cache(user_id)

            # 비동기로 사용자 프로필 업데이트 (선택적)
            await self._update_user_profile_from_feedback(user_id, feedback_data)

            logger.info(
                f"Updated ranking feedback for user {user_id}, "
                f"place {place_id}, type {feedback_type.value}"
            )

        except Exception as e:
            logger.error(f"Failed to update ranking feedback: {str(e)}")

    async def learn_from_feedback(self, feedback_data: List[Dict[str, Any]]) -> None:
        """피드백 데이터로부터 모델 학습"""
        try:
            if not feedback_data:
                return

            # ML 모델 업데이트 (배치 학습)
            if self.ml_engine:
                await self.ml_engine.update_model(feedback_data)

            # 사용자 프로필 업데이트
            for feedback in feedback_data:
                user_id = feedback.get("user_id")
                if user_id:
                    await self._update_user_profile_from_feedback(
                        UUID(user_id), feedback
                    )

            logger.info(f"Learned from {len(feedback_data)} feedback samples")

        except Exception as e:
            logger.error(f"Learning from feedback failed: {str(e)}")

    # 유틸리티 메서드들

    def _generate_ranking_cache_key(
        self,
        user_id: UUID,
        search_results: List[Dict[str, Any]],
        query: Optional[str],
        context: Dict[str, Any],
    ) -> str:
        """랭킹 캐시 키 생성"""
        # 결과 ID들의 해시
        result_ids = sorted([r.get("id", "") for r in search_results])
        result_hash = hashlib.md5(
            ",".join(result_ids).encode(), usedforsecurity=False
        ).hexdigest()[
            :8
        ]  # nosec

        # 컨텍스트 해시 (시간 제외)
        context_copy = context.copy()
        context_copy.pop("time_of_search", None)
        context_hash = hashlib.md5(
            json.dumps(context_copy, sort_keys=True).encode(), usedforsecurity=False
        ).hexdigest()[
            :8
        ]  # nosec

        return f"ranking:{user_id}:{result_hash}:{context_hash}:{query or 'no_query'}"

    async def _get_cached_ranking(
        self, cache_key: str
    ) -> Optional[List[Dict[str, Any]]]:
        """캐시된 랭킹 결과 조회"""
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get failed: {str(e)}")
        return None

    async def _cache_ranking_result(
        self, cache_key: str, results: List[Dict[str, Any]]
    ) -> None:
        """랭킹 결과 캐시 저장"""
        try:
            await self.redis.setex(
                cache_key, self.ranking_cache_ttl, json.dumps(results, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set failed: {str(e)}")

    async def _get_user_profile(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """사용자 프로필 조회 (캐시된 버전)"""
        try:
            # 캐시 확인
            profile_key = f"profile:{user_id}"
            cached_profile = await self.redis.get(profile_key)

            if cached_profile:
                return json.loads(cached_profile)

            # DB 조회 및 캐시 저장
            # 실제 구현에서는 DB 쿼리 실행
            profile = {
                "preferences": {
                    "categories": {"cafe": 0.8, "restaurant": 0.6},
                    "regions": {"마포구": 0.9, "강남구": 0.3},
                    "tags": {"조용한": 0.9, "분위기좋은": 0.8},
                },
                "behavior_patterns": {
                    "distance_tolerance": 3.5,
                    "avg_session_duration": 450,
                },
                "interaction_history": {
                    "total_searches": 247,
                    "click_through_rate": 0.68,
                },
            }

            await self.redis.setex(
                profile_key, self.profile_cache_ttl, json.dumps(profile)
            )

            return profile

        except Exception as e:
            logger.error(f"Get user profile failed: {str(e)}")
            return None

    def _get_default_user_profile(self) -> Dict[str, Any]:
        """기본 사용자 프로필"""
        return {
            "preferences": {
                "categories": {},
                "regions": {},
                "tags": {},
                "price_ranges": {},
            },
            "behavior_patterns": {
                "distance_tolerance": 5.0,
                "avg_session_duration": 300,
            },
            "interaction_history": {"total_searches": 0, "click_through_rate": 0.0},
        }

    async def _get_user_interactions(
        self, user_id: UUID, place_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """사용자 상호작용 데이터 조회"""
        # 실제 구현에서는 DB에서 조회
        interactions = {}
        for place_id in place_ids:
            interactions[place_id] = {
                "view_count": 0,
                "click_count": 0,
                "bookmark_count": 0,
                "avg_time_spent": 0,
                "last_interaction": None,
            }
        return interactions

    def _build_feature_vectors(
        self,
        search_results: List[Dict[str, Any]],
        query: Optional[str],
        user_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """ML 모델용 특성 벡터 구성"""
        features = []

        for result in search_results:
            feature_vector = {
                "place_id": result.get("id"),
                "query": query or "",
                "category": result.get("category", ""),
                "rating": result.get("rating", 0.0),
                "price_range": result.get("price_range", 0),
                "distance_km": result.get("distance_km", 0.0),
                "user_category_preference": user_profile.get("preferences", {})
                .get("categories", {})
                .get(result.get("category", ""), 0.5),
                "user_avg_price_tolerance": 30000,  # 실제로는 프로필에서 계산
                "user_distance_tolerance": user_profile.get(
                    "behavior_patterns", {}
                ).get("distance_tolerance", 5.0),
            }
            features.append(feature_vector)

        return features

    def _normalize_score(self, score: float, min_val: float, max_val: float) -> float:
        """점수 정규화 (0.0 - 1.0 범위)"""
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))

    def _price_in_range(self, price: int, range_key: str) -> bool:
        """가격이 범위에 포함되는지 확인"""
        try:
            if "+" in range_key:
                min_price = int(range_key.replace("+", "").replace("원", ""))
                return price >= min_price
            elif "-" in range_key:
                parts = range_key.split("-")
                min_price = int(parts[0])
                max_price = int(parts[1]) if len(parts) > 1 else float("inf")
                return min_price <= price <= max_price
            else:
                return False
        except ValueError:
            return False

    async def _apply_diversity_injection(
        self, results: List[Dict[str, Any]], threshold: float
    ) -> List[Dict[str, Any]]:
        """다양성 주입 적용"""
        if len(results) <= 3:
            return results

        diverse_results = []
        used_categories = set()
        used_regions = set()

        # 상위 결과들을 다양성을 고려해서 선별
        for result in results:
            category = result.get("category", "")
            address = result.get("address", "")

            # 이미 선택된 카테고리나 지역인지 확인
            category_diversity = category not in used_categories
            region_diversity = not any(region in address for region in used_regions)

            # 다양성 점수 계산
            diversity_score = 0.0
            if category_diversity:
                diversity_score += 0.5
            if region_diversity:
                diversity_score += 0.5

            # 다양성 임계값 이상이거나 상위 결과는 포함
            if diversity_score >= threshold or len(diverse_results) < 3:
                diverse_results.append(result)
                used_categories.add(category)

                # 지역 추출 (간단한 로직)
                for region in ["마포구", "강남구", "종로구", "서초구"]:
                    if region in address:
                        used_regions.add(region)
                        break

        # 나머지 결과들 추가
        for result in results:
            if result not in diverse_results:
                diverse_results.append(result)

        return diverse_results

    async def _fallback_ranking(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """기본 fallback 랭킹 (에러 상황)"""
        logger.warning("Using fallback ranking algorithm")

        # 기본적인 점수 기반 정렬
        for idx, result in enumerate(search_results):
            result.update(
                {
                    "original_rank": idx + 1,
                    "final_rank": idx + 1,
                    "final_rank_score": result.get("_score", 1.0) / 10.0,
                    "personalization_score": 0.5,
                    "ranking_factors": {},
                    "confidence_score": 0.3,
                    "ranking_source": "fallback_algorithm",
                }
            )

        return search_results

    async def _invalidate_user_ranking_cache(self, user_id: UUID) -> None:
        """사용자 관련 랭킹 캐시 무효화"""
        try:
            pattern = f"ranking:{user_id}:*"
            # Redis SCAN 사용하여 패턴 매칭 키 삭제
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")

    async def _update_user_profile_from_feedback(
        self, user_id: UUID, feedback_data: Dict[str, Any]
    ) -> None:
        """피드백 데이터로 사용자 프로필 업데이트"""
        try:
            # 실제 구현에서는 점진적 학습 알고리즘 적용
            logger.info(f"Updated user profile for {user_id} from feedback")
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")

    def _get_ranking_config(self) -> Dict[str, float]:
        """현재 랭킹 설정 반환 (A/B 테스트용)"""
        return self.default_weights.copy()
