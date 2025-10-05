"""
검색 피드백 학습 서비스 (Task 2-3-4)

사용자의 검색 및 상호작용 피드백을 수집하고 ML 모델을 지속적으로 개선
- 클릭, 북마크, 방문 등의 피드백 수집
- 온라인 학습을 통한 실시간 모델 업데이트
- 사용자 선호도 프로필 동적 조정
- 피드백 품질 평가 및 필터링
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.cache import CacheService
from app.models.search_preference import SearchHistory, UserSearchPattern
from app.schemas.search_ranking import FeedbackType
from app.services.ml.ml_engine import MLEngine

logger = logging.getLogger(__name__)


class SearchFeedbackService:
    """검색 피드백 학습 서비스"""

    def __init__(
        self, db: AsyncSession, cache_service: CacheService, ml_engine: MLEngine
    ):
        """서비스 초기화"""
        self.db = db
        self.cache = cache_service
        self.ml_engine = ml_engine

        # 피드백 처리 설정
        self.batch_size = 50  # 배치 학습 크기
        self.learning_threshold = 10  # 최소 피드백 수
        self.feedback_window_hours = 24  # 피드백 수집 윈도우

        # 피드백 가중치 매핑
        self.feedback_weights = {
            FeedbackType.CLICK: 0.7,
            FeedbackType.VIEW: 0.3,
            FeedbackType.BOOKMARK: 0.9,
            FeedbackType.VISIT: 0.95,
            FeedbackType.SHARE: 0.85,
            FeedbackType.SKIP: 0.1,
            FeedbackType.NEGATIVE: 0.05,
        }

    async def collect_search_feedback(
        self,
        user_id: UUID,
        search_session_id: str,
        place_id: UUID,
        feedback_type: FeedbackType,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        검색 결과에 대한 사용자 피드백 수집

        Args:
            user_id: 사용자 ID
            search_session_id: 검색 세션 ID
            place_id: 장소 ID
            feedback_type: 피드백 타입
            context: 피드백 컨텍스트
            metadata: 추가 메타데이터

        Returns:
            수집 성공 여부
        """
        try:
            timestamp = datetime.utcnow()

            # 피드백 데이터 구성
            feedback_data = {
                "user_id": str(user_id),
                "search_session_id": search_session_id,
                "place_id": str(place_id),
                "feedback_type": feedback_type.value,
                "timestamp": timestamp.isoformat(),
                "context": context or {},
                "metadata": metadata or {},
            }

            # 즉시 캐시에 저장 (빠른 수집)
            feedback_key = f"search_feedback:{user_id}:{timestamp.timestamp()}"
            await self.cache.set(feedback_key, feedback_data, ttl=86400)  # 24시간

            # 비동기 배치 처리를 위한 큐에 추가
            await self._add_to_processing_queue(feedback_data)

            # 검색 히스토리 업데이트
            await self._update_search_history(
                user_id, search_session_id, place_id, feedback_type, context
            )

            logger.info(
                f"Collected {feedback_type.value} feedback from user {user_id} "
                f"for place {place_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to collect search feedback: {e}")
            return False

    async def process_feedback_batch(
        self, user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        배치 피드백 처리 및 모델 업데이트

        Args:
            user_id: 특정 사용자 피드백만 처리 (None이면 전체)

        Returns:
            처리 결과 통계
        """
        try:
            # 처리할 피드백 수집
            feedback_batch = await self._collect_feedback_batch(user_id)

            if len(feedback_batch) < self.learning_threshold:
                logger.info(
                    f"Insufficient feedback for learning: {len(feedback_batch)}"
                )
                return {"processed": 0, "learned": False}

            # 피드백 데이터를 학습 데이터로 변환
            training_data = await self._convert_feedback_to_training_data(
                feedback_batch
            )

            # ML 모델 업데이트
            model_updated = await self.ml_engine.update_model(training_data)

            # 사용자 프로필 업데이트
            profile_updates = 0
            if user_id:
                updated = await self._update_user_profile_from_feedback(
                    user_id, feedback_batch
                )
                if updated:
                    profile_updates = 1
            else:
                # 모든 사용자 프로필 업데이트
                user_ids = list(set(fb["user_id"] for fb in feedback_batch))
                for uid_str in user_ids:
                    uid = UUID(uid_str)
                    user_feedback = [
                        fb for fb in feedback_batch if fb["user_id"] == uid_str
                    ]
                    updated = await self._update_user_profile_from_feedback(
                        uid, user_feedback
                    )
                    if updated:
                        profile_updates += 1

            # 처리된 피드백 정리
            await self._cleanup_processed_feedback(feedback_batch)

            result = {
                "processed": len(feedback_batch),
                "learned": model_updated,
                "profile_updates": profile_updates,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Processed feedback batch: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to process feedback batch: {e}")
            return {"error": str(e)}

    async def analyze_feedback_patterns(
        self, user_id: UUID, days: int = 7
    ) -> Dict[str, Any]:
        """
        사용자 피드백 패턴 분석

        Args:
            user_id: 사용자 ID
            days: 분석 기간 (일)

        Returns:
            피드백 패턴 분석 결과
        """
        try:
            # 피드백 패턴 캐시 확인
            cache_key = f"feedback_patterns:{user_id}:{days}"
            cached_patterns = await self.cache.get(cache_key)
            if cached_patterns:
                return cached_patterns

            # 최근 피드백 데이터 수집
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            feedback_data = await self._get_user_feedback_history(
                user_id, start_time, end_time
            )

            if not feedback_data:
                return {"error": "No feedback data found"}

            # 패턴 분석
            patterns = {
                "total_interactions": len(feedback_data),
                "feedback_distribution": self._analyze_feedback_distribution(
                    feedback_data
                ),
                "interaction_quality": self._calculate_interaction_quality(
                    feedback_data
                ),
                "temporal_patterns": self._analyze_temporal_patterns(feedback_data),
                "category_preferences": await self._analyze_category_preferences(
                    feedback_data
                ),
                "search_success_rate": self._calculate_search_success_rate(
                    feedback_data
                ),
                "engagement_score": self._calculate_engagement_score(feedback_data),
            }

            # 캐시에 저장
            await self.cache.set(cache_key, patterns, ttl=3600)  # 1시간

            return patterns

        except Exception as e:
            logger.error(f"Failed to analyze feedback patterns: {e}")
            return {"error": str(e)}

    async def get_personalization_insights(self, user_id: UUID) -> Dict[str, Any]:
        """
        개인화 인사이트 생성

        Args:
            user_id: 사용자 ID

        Returns:
            개인화 인사이트
        """
        try:
            # 사용자 검색 패턴 조회
            search_pattern = await self._get_user_search_pattern(user_id)

            # 피드백 패턴 분석
            feedback_patterns = await self.analyze_feedback_patterns(user_id, days=30)

            # 개인화 점수 계산
            personalization_score = await self._calculate_personalization_score(
                user_id, search_pattern, feedback_patterns
            )

            # 추천 개선사항
            improvements = await self._suggest_personalization_improvements(
                user_id, feedback_patterns
            )

            insights = {
                "user_id": str(user_id),
                "personalization_score": personalization_score,
                "search_preferences": search_pattern,
                "feedback_summary": feedback_patterns,
                "improvement_suggestions": improvements,
                "last_updated": datetime.utcnow().isoformat(),
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to generate personalization insights: {e}")
            return {"error": str(e)}

    async def _add_to_processing_queue(self, feedback_data: Dict[str, Any]):
        """피드백을 처리 큐에 추가"""
        queue_key = "search_feedback_queue"
        queue_data = await self.cache.get(queue_key) or []
        queue_data.append(feedback_data)

        # 큐 크기 제한 (메모리 관리)
        if len(queue_data) > 1000:
            queue_data = queue_data[-1000:]

        await self.cache.set(queue_key, queue_data, ttl=86400)

    async def _collect_feedback_batch(
        self, user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """처리할 피드백 배치 수집"""
        queue_key = "search_feedback_queue"
        queue_data = await self.cache.get(queue_key) or []

        if user_id:
            # 특정 사용자 피드백만 필터링
            user_feedback = [
                fb for fb in queue_data if fb.get("user_id") == str(user_id)
            ]
            return user_feedback[: self.batch_size]

        # 전체 피드백에서 배치 크기만큼 가져오기
        return queue_data[: self.batch_size]

    async def _convert_feedback_to_training_data(
        self, feedback_batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """피드백을 ML 훈련 데이터로 변환"""
        training_data = []

        for feedback in feedback_batch:
            try:
                # 피드백 타입을 점수로 변환
                feedback_type = FeedbackType(feedback["feedback_type"])
                score = self.feedback_weights.get(feedback_type, 0.5)

                # 컨텍스트 정보에서 특성 추출
                features = await self._extract_features_from_feedback(feedback)

                training_sample = {
                    "features": features,
                    "label": score,
                    "user_id": feedback["user_id"],
                    "timestamp": feedback["timestamp"],
                    "metadata": feedback.get("metadata", {}),
                }

                training_data.append(training_sample)

            except Exception as e:
                logger.warning(f"Failed to convert feedback to training data: {e}")
                continue

        return training_data

    async def _extract_features_from_feedback(
        self, feedback: Dict[str, Any]
    ) -> Dict[str, float]:
        """피드백에서 ML 특성 추출"""
        features = {
            "rating": 0.0,
            "distance": 0.0,
            "popularity": 0.0,
            "price_range": 0.0,
            "category_match": 0.0,
            "tag_match": 0.0,
            "visit_frequency": 0.0,
            "recent_activity": 0.0,
            "time_context": 0.0,
            "location_context": 0.0,
        }

        context = feedback.get("context", {})
        feedback.get("metadata", {})

        # 컨텍스트에서 특성 값 추출
        if "place_rating" in context:
            features["rating"] = float(context["place_rating"])

        if "distance_km" in context:
            features["distance"] = float(context["distance_km"])

        if "popularity_score" in context:
            features["popularity"] = float(context["popularity_score"])

        if "price_range" in context:
            features["price_range"] = float(context["price_range"])

        # 시간 컨텍스트
        if "hour" in context:
            hour = int(context["hour"])
            features["time_context"] = self._encode_time_context(hour)

        # 위치 컨텍스트
        if "location_type" in context:
            features["location_context"] = self._encode_location_context(
                context["location_type"]
            )

        return features

    def _encode_time_context(self, hour: int) -> float:
        """시간을 컨텍스트 특성으로 인코딩"""
        if 9 <= hour <= 11:  # 오전
            return 0.8
        elif 12 <= hour <= 14:  # 점심
            return 1.0
        elif 18 <= hour <= 21:  # 저녁
            return 0.9
        else:
            return 0.5

    def _encode_location_context(self, location_type: str) -> float:
        """위치 타입을 컨텍스트 특성으로 인코딩"""
        encoding_map = {
            "work": 0.7,
            "home": 0.8,
            "travel": 0.9,
            "entertainment": 1.0,
            "unknown": 0.5,
        }
        return encoding_map.get(location_type, 0.5)

    async def _update_search_history(
        self,
        user_id: UUID,
        search_session_id: str,
        place_id: UUID,
        feedback_type: FeedbackType,
        context: Optional[Dict[str, Any]] = None,
    ):
        """검색 히스토리 업데이트"""
        try:
            # 검색 히스토리 조회
            result = await self.db.execute(
                select(SearchHistory).where(
                    and_(
                        SearchHistory.user_id == user_id,
                        SearchHistory.session_id == search_session_id,
                    )
                )
            )
            search_history = result.scalar_one_or_none()

            if search_history:
                # 클릭한 결과 추가
                clicked_results = search_history.clicked_results or []
                if str(place_id) not in clicked_results:
                    clicked_results.append(str(place_id))
                    search_history.clicked_results = clicked_results

                # 체류 시간 업데이트
                if context and "dwell_time" in context:
                    search_history.dwell_time_seconds = context["dwell_time"]

                await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update search history: {e}")

    async def _update_user_profile_from_feedback(
        self, user_id: UUID, feedback_batch: List[Dict[str, Any]]
    ) -> bool:
        """피드백을 기반으로 사용자 프로필 업데이트"""
        try:
            if not feedback_batch:
                return False

            # 피드백 패턴 분석
            positive_feedback = [
                fb
                for fb in feedback_batch
                if FeedbackType(fb["feedback_type"])
                in [
                    FeedbackType.CLICK,
                    FeedbackType.BOOKMARK,
                    FeedbackType.VISIT,
                    FeedbackType.SHARE,
                ]
            ]

            if not positive_feedback:
                return False

            # 카테고리 선호도 업데이트
            category_preferences = {}
            for feedback in positive_feedback:
                context = feedback.get("context", {})
                if "category" in context:
                    category = context["category"]
                    category_preferences[category] = (
                        category_preferences.get(category, 0) + 1
                    )

            # 사용자 검색 패턴 조회 또는 생성
            result = await self.db.execute(
                select(UserSearchPattern).where(UserSearchPattern.user_id == user_id)
            )
            search_pattern = result.scalar_one_or_none()

            if not search_pattern:
                # 새로운 패턴 생성
                search_pattern = UserSearchPattern(
                    user_id=user_id,
                    analysis_period_start=datetime.utcnow() - timedelta(days=30),
                    analysis_period_end=datetime.utcnow(),
                    category_preferences=category_preferences,
                    total_searches=len(feedback_batch),
                )
                self.db.add(search_pattern)
            else:
                # 기존 패턴 업데이트
                current_prefs = search_pattern.category_preferences or {}
                for category, count in category_preferences.items():
                    current_prefs[category] = current_prefs.get(category, 0) + count

                search_pattern.category_preferences = current_prefs
                search_pattern.last_updated = datetime.utcnow()

            await self.db.commit()

            # 캐시 무효화
            await self.cache.delete(f"user_profile:{user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to update user profile from feedback: {e}")
            return False

    def _analyze_feedback_distribution(
        self, feedback_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """피드백 분포 분석"""
        distribution = {}
        for feedback in feedback_data:
            feedback_type = feedback.get("feedback_type", "unknown")
            distribution[feedback_type] = distribution.get(feedback_type, 0) + 1

        return distribution

    def _calculate_interaction_quality(
        self, feedback_data: List[Dict[str, Any]]
    ) -> float:
        """상호작용 품질 계산"""
        if not feedback_data:
            return 0.0

        total_score = 0.0
        for feedback in feedback_data:
            feedback_type = FeedbackType(feedback.get("feedback_type", "view"))
            total_score += self.feedback_weights.get(feedback_type, 0.5)

        return total_score / len(feedback_data)

    def _analyze_temporal_patterns(
        self, feedback_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """시간적 패턴 분석"""
        hourly_distribution = {}
        daily_distribution = {}

        for feedback in feedback_data:
            try:
                timestamp = datetime.fromisoformat(feedback["timestamp"])
                hour = timestamp.hour
                day = timestamp.strftime("%A")

                hourly_distribution[str(hour)] = (
                    hourly_distribution.get(str(hour), 0) + 1
                )
                daily_distribution[day] = daily_distribution.get(day, 0) + 1

            except Exception:
                continue

        return {
            "hourly_distribution": hourly_distribution,
            "daily_distribution": daily_distribution,
        }

    async def _analyze_category_preferences(
        self, feedback_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """카테고리 선호도 분석"""
        category_scores = {}

        for feedback in feedback_data:
            context = feedback.get("context", {})
            category = context.get("category")

            if category:
                feedback_type = FeedbackType(feedback.get("feedback_type", "view"))
                score = self.feedback_weights.get(feedback_type, 0.5)

                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)

        # 평균 점수 계산
        category_preferences = {}
        for category, scores in category_scores.items():
            category_preferences[category] = sum(scores) / len(scores)

        return category_preferences

    def _calculate_search_success_rate(
        self, feedback_data: List[Dict[str, Any]]
    ) -> float:
        """검색 성공률 계산"""
        if not feedback_data:
            return 0.0

        positive_interactions = sum(
            1
            for feedback in feedback_data
            if FeedbackType(feedback.get("feedback_type", "view"))
            in [
                FeedbackType.CLICK,
                FeedbackType.BOOKMARK,
                FeedbackType.VISIT,
                FeedbackType.SHARE,
            ]
        )

        return positive_interactions / len(feedback_data)

    def _calculate_engagement_score(self, feedback_data: List[Dict[str, Any]]) -> float:
        """참여도 점수 계산"""
        if not feedback_data:
            return 0.0

        engagement_weights = {
            FeedbackType.VIEW: 1.0,
            FeedbackType.CLICK: 2.0,
            FeedbackType.BOOKMARK: 4.0,
            FeedbackType.VISIT: 5.0,
            FeedbackType.SHARE: 3.0,
            FeedbackType.SKIP: -1.0,
            FeedbackType.NEGATIVE: -2.0,
        }

        total_score = 0.0
        for feedback in feedback_data:
            feedback_type = FeedbackType(feedback.get("feedback_type", "view"))
            total_score += engagement_weights.get(feedback_type, 0.0)

        return max(0.0, total_score / len(feedback_data))

    async def _get_user_feedback_history(
        self, user_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """사용자 피드백 히스토리 조회"""
        # 캐시에서 피드백 데이터 조회
        feedback_keys = await self.cache.get(f"feedback_keys:{user_id}") or []
        feedback_data = []

        for key in feedback_keys:
            data = await self.cache.get(key)
            if data:
                try:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    if start_time <= timestamp <= end_time:
                        feedback_data.append(data)
                except Exception:
                    continue

        return feedback_data

    async def _get_user_search_pattern(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """사용자 검색 패턴 조회"""
        try:
            result = await self.db.execute(
                select(UserSearchPattern).where(UserSearchPattern.user_id == user_id)
            )
            search_pattern = result.scalar_one_or_none()

            if search_pattern:
                return {
                    "category_preferences": search_pattern.category_preferences,
                    "region_preferences": search_pattern.region_preferences,
                    "preferred_sort_fields": search_pattern.preferred_sort_fields,
                    "average_query_length": search_pattern.average_query_length,
                    "click_through_rate": search_pattern.click_through_rate,
                    "overall_satisfaction_score": search_pattern.overall_satisfaction_score,
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get user search pattern: {e}")
            return None

    async def _calculate_personalization_score(
        self,
        user_id: UUID,
        search_pattern: Optional[Dict[str, Any]],
        feedback_patterns: Dict[str, Any],
    ) -> float:
        """개인화 점수 계산"""
        if not search_pattern or not feedback_patterns:
            return 0.0

        # 기본 점수 (검색 패턴 기반)
        base_score = search_pattern.get("overall_satisfaction_score", 0.5)

        # 피드백 품질 점수
        quality_score = feedback_patterns.get("interaction_quality", 0.5)

        # 참여도 점수
        engagement_score = feedback_patterns.get("engagement_score", 0.5)

        # 검색 성공률 점수
        success_score = feedback_patterns.get("search_success_rate", 0.5)

        # 가중 평균으로 최종 점수 계산
        personalization_score = (
            0.3 * base_score
            + 0.25 * quality_score
            + 0.25 * engagement_score
            + 0.2 * success_score
        )

        return min(1.0, max(0.0, personalization_score))

    async def _suggest_personalization_improvements(
        self, user_id: UUID, feedback_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """개인화 개선사항 제안"""
        improvements = []

        # 상호작용 품질이 낮은 경우
        if feedback_patterns.get("interaction_quality", 0.5) < 0.3:
            improvements.append(
                {
                    "type": "interaction_quality",
                    "description": "검색 결과의 관련성을 높이기 위한 필터 조정이 필요합니다.",
                    "action": "사용자 선호도 프로필 재조정",
                    "priority": "high",
                }
            )

        # 검색 성공률이 낮은 경우
        if feedback_patterns.get("search_success_rate", 0.5) < 0.4:
            improvements.append(
                {
                    "type": "search_success",
                    "description": "검색 결과에 만족하지 않는 경우가 많습니다.",
                    "action": "검색 알고리즘 가중치 재조정",
                    "priority": "high",
                }
            )

        # 참여도가 낮은 경우
        if feedback_patterns.get("engagement_score", 0.5) < 0.3:
            improvements.append(
                {
                    "type": "engagement",
                    "description": "검색 결과와의 상호작용이 부족합니다.",
                    "action": "결과 다양성 증가 및 추천 알고리즘 개선",
                    "priority": "medium",
                }
            )

        return improvements

    async def _cleanup_processed_feedback(self, feedback_batch: List[Dict[str, Any]]):
        """처리된 피드백 정리"""
        try:
            queue_key = "search_feedback_queue"
            queue_data = await self.cache.get(queue_key) or []

            # 처리된 피드백 제거
            processed_timestamps = set(fb["timestamp"] for fb in feedback_batch)
            remaining_data = [
                fb
                for fb in queue_data
                if fb.get("timestamp") not in processed_timestamps
            ]

            await self.cache.set(queue_key, remaining_data, ttl=86400)

        except Exception as e:
            logger.error(f"Failed to cleanup processed feedback: {e}")
