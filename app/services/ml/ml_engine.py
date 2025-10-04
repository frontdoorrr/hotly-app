"""
머신러닝 엔진 서비스 (Task 2-3-4)

개인화된 검색 랭킹을 위한 ML 모델 서비스
- 사용자 행동 기반 선호도 예측
- 컨텍스트 기반 관련도 스코어링
- 온라인 학습을 통한 모델 개선
"""

import logging
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.core.cache import CacheService

logger = logging.getLogger(__name__)


class MLEngine:
    """머신러닝 엔진"""

    def __init__(self, cache_service: CacheService):
        """ML 엔진 초기화"""
        self.cache = cache_service

        # 모델 초기화
        self.relevance_model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.personalization_model = SGDRegressor(alpha=0.01, random_state=42)

        # 특성 스케일러
        self.scaler = StandardScaler()

        # 모델 상태
        self.is_trained = False
        self.last_training = None
        self.model_version = "1.0.0"

        # 캐시 TTL
        self.model_cache_ttl = 3600  # 1시간
        self.prediction_cache_ttl = 300  # 5분

    async def predict_relevance(
        self,
        feature_vectors: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        """
        검색 결과의 관련도 점수 예측

        Args:
            feature_vectors: 특성 벡터 리스트
            user_id: 사용자 ID (개인화용)
            context: 검색 컨텍스트

        Returns:
            관련도 점수 리스트 (0.0 ~ 1.0)
        """
        try:
            if not feature_vectors:
                return []

            # 캐시 확인
            cache_key = f"ml:predictions:{hash(str(feature_vectors))}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            # 모델이 훈련되지 않았다면 기본 스코어 반환
            if not self.is_trained:
                logger.warning("ML model not trained, returning default scores")
                return await self._get_default_scores(feature_vectors)

            # 특성 벡터를 numpy 배열로 변환
            features = self._convert_features_to_array(feature_vectors)

            # 특성 스케일링
            if hasattr(self.scaler, "mean_"):
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features

            # 관련도 예측
            base_scores = self.relevance_model.predict(features_scaled)

            # 개인화 점수 추가
            if user_id and hasattr(self, "personalization_model"):
                personalization_scores = await self._predict_personalization(
                    features_scaled, user_id, context
                )
                # 가중 평균으로 최종 점수 계산
                final_scores = 0.7 * base_scores + 0.3 * personalization_scores
            else:
                final_scores = base_scores

            # 0-1 범위로 정규화
            normalized_scores = self._normalize_scores(final_scores)

            # 결과 캐싱
            await self.cache.set(
                cache_key, normalized_scores.tolist(), ttl=self.prediction_cache_ttl
            )

            return normalized_scores.tolist()

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return await self._get_default_scores(feature_vectors)

    async def update_model(self, feedback_data: List[Dict[str, Any]]) -> bool:
        """
        사용자 피드백을 기반으로 모델 업데이트

        Args:
            feedback_data: 피드백 데이터 리스트

        Returns:
            업데이트 성공 여부
        """
        try:
            if not feedback_data:
                return False

            # 피드백 데이터를 훈련 데이터로 변환
            training_data = self._prepare_training_data(feedback_data)

            if not training_data:
                logger.warning("No valid training data from feedback")
                return False

            # 온라인 학습 수행
            success = await self._perform_online_learning(training_data)

            if success:
                self.last_training = datetime.utcnow()
                logger.info(f"Model updated with {len(training_data)} samples")

                # 모델 캐시 무효화
                await self._invalidate_model_cache()

            return success

        except Exception as e:
            logger.error(f"Model update failed: {e}")
            return False

    async def train_initial_model(self, historical_data: List[Dict[str, Any]]) -> bool:
        """
        초기 모델 훈련

        Args:
            historical_data: 과거 데이터

        Returns:
            훈련 성공 여부
        """
        try:
            if not historical_data:
                logger.warning("No historical data for initial training")
                return False

            # 훈련 데이터 준비
            X, y = self._prepare_training_features_and_labels(historical_data)

            if len(X) < 10:  # 최소 데이터 요구사항
                logger.warning("Insufficient data for training")
                return False

            # 데이터 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 특성 스케일링
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # 관련도 모델 훈련
            self.relevance_model.fit(X_train_scaled, y_train)

            # 개인화 모델 훈련
            self.personalization_model.fit(X_train_scaled, y_train)

            # 모델 평가
            y_pred = self.relevance_model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            logger.info(f"Model trained - MSE: {mse:.4f}, R2: {r2:.4f}")

            self.is_trained = True
            self.last_training = datetime.utcnow()

            # 모델 저장
            await self._save_model()

            return True

        except Exception as e:
            logger.error(f"Initial training failed: {e}")
            return False

    async def get_model_metrics(self) -> Dict[str, Any]:
        """모델 성능 지표 반환"""
        try:
            metrics = {
                "is_trained": self.is_trained,
                "last_training": self.last_training.isoformat()
                if self.last_training
                else None,
                "model_version": self.model_version,
                "feature_importance": {},
                "prediction_cache_hit_rate": 0.0,
            }

            # 특성 중요도 (Random Forest)
            if self.is_trained and hasattr(
                self.relevance_model, "feature_importances_"
            ):
                feature_names = self._get_feature_names()
                importance_scores = self.relevance_model.feature_importances_

                metrics["feature_importance"] = {
                    name: float(score)
                    for name, score in zip(feature_names, importance_scores)
                }

            # 캐시 히트율 계산
            cache_stats = await self.cache.get_stats()
            if cache_stats:
                metrics["prediction_cache_hit_rate"] = cache_stats.get("hit_rate", 0.0)

            return metrics

        except Exception as e:
            logger.error(f"Failed to get model metrics: {e}")
            return {"error": str(e)}

    async def _predict_personalization(
        self,
        features: np.ndarray,
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """개인화 점수 예측"""
        try:
            # 사용자별 가중치 조회
            user_weights = await self._get_user_personalization_weights(user_id)

            # 컨텍스트 기반 조정
            if context:
                context_adjustment = self._calculate_context_adjustment(context)
                user_weights = self._apply_context_to_weights(
                    user_weights, context_adjustment
                )

            # 개인화 점수 계산
            personalization_scores = self.personalization_model.predict(features)

            # 사용자 가중치 적용
            adjusted_scores = personalization_scores * user_weights.get(
                "global_factor", 1.0
            )

            return adjusted_scores

        except Exception as e:
            logger.error(f"Personalization prediction failed: {e}")
            return np.ones(len(features)) * 0.5

    async def _get_default_scores(
        self, feature_vectors: List[Dict[str, Any]]
    ) -> List[float]:
        """기본 스코어 반환 (모델이 훈련되지 않은 경우)"""
        default_scores = []

        for features in feature_vectors:
            # 간단한 휴리스틱 기반 스코어링
            score = 0.5  # 기본값

            # 평점이 높으면 스코어 증가
            if "rating" in features and features["rating"]:
                score += min(features["rating"] / 5.0 * 0.3, 0.3)

            # 거리가 가까우면 스코어 증가
            if "distance" in features and features["distance"]:
                distance_score = max(0, 1.0 - features["distance"] / 10000)  # 10km 기준
                score += distance_score * 0.2

            # 인기도 반영
            if "popularity" in features and features["popularity"]:
                score += min(features["popularity"] / 100.0 * 0.2, 0.2)

            default_scores.append(min(score, 1.0))

        return default_scores

    def _convert_features_to_array(
        self, feature_vectors: List[Dict[str, Any]]
    ) -> np.ndarray:
        """특성 벡터를 numpy 배열로 변환"""
        feature_names = self._get_feature_names()
        features_array = []

        for features in feature_vectors:
            feature_row = []
            for name in feature_names:
                value = features.get(name, 0.0)
                if isinstance(value, (int, float)):
                    feature_row.append(float(value))
                else:
                    feature_row.append(0.0)
            features_array.append(feature_row)

        return np.array(features_array)

    def _get_feature_names(self) -> List[str]:
        """특성 이름 리스트 반환"""
        return [
            "rating",
            "distance",
            "popularity",
            "price_range",
            "category_match",
            "tag_match",
            "visit_frequency",
            "recent_activity",
            "time_context",
            "location_context",
        ]

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """점수를 0-1 범위로 정규화"""
        if len(scores) == 0:
            return scores

        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            return np.ones_like(scores) * 0.5

        normalized = (scores - min_score) / (max_score - min_score)
        return np.clip(normalized, 0.0, 1.0)

    def _prepare_training_data(
        self, feedback_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """피드백 데이터를 훈련 데이터로 변환"""
        training_data = []

        for feedback in feedback_data:
            try:
                # 피드백을 점수로 변환
                feedback_score = self._convert_feedback_to_score(feedback)

                training_sample = {
                    "features": feedback.get("features", {}),
                    "label": feedback_score,
                    "user_id": feedback.get("user_id"),
                    "timestamp": feedback.get("timestamp", datetime.utcnow()),
                }

                training_data.append(training_sample)

            except Exception as e:
                logger.warning(f"Failed to convert feedback to training data: {e}")
                continue

        return training_data

    def _convert_feedback_to_score(self, feedback: Dict[str, Any]) -> float:
        """피드백을 점수로 변환"""
        feedback_type = feedback.get("type", "view")

        score_mapping = {
            "click": 0.7,
            "view": 0.3,
            "bookmark": 0.9,
            "visit": 0.95,
            "share": 0.85,
            "skip": 0.1,
            "negative": 0.05,
        }

        base_score = score_mapping.get(feedback_type, 0.5)

        # 체류 시간 고려
        if "dwell_time" in feedback:
            dwell_multiplier = min(feedback["dwell_time"] / 30.0, 2.0)  # 30초 기준
            base_score *= dwell_multiplier

        # 평점 고려
        if "rating" in feedback:
            rating_score = feedback["rating"] / 5.0
            base_score = 0.7 * base_score + 0.3 * rating_score

        return min(base_score, 1.0)

    def _prepare_training_features_and_labels(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """훈련용 특성과 라벨 준비"""
        features = []
        labels = []

        for item in data:
            try:
                feature_vector = self._convert_features_to_array(
                    [item.get("features", {})]
                )
                if len(feature_vector) > 0:
                    features.extend(feature_vector)
                    labels.append(item.get("label", 0.5))
            except Exception as e:
                logger.warning(f"Failed to prepare training sample: {e}")
                continue

        return np.array(features), np.array(labels)

    async def _perform_online_learning(
        self, training_data: List[Dict[str, Any]]
    ) -> bool:
        """온라인 학습 수행"""
        try:
            X, y = self._prepare_training_features_and_labels(training_data)

            if len(X) == 0:
                return False

            # 특성 스케일링
            if hasattr(self.scaler, "mean_"):
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X

            # SGD 모델로 온라인 학습
            self.personalization_model.partial_fit(X_scaled, y)

            return True

        except Exception as e:
            logger.error(f"Online learning failed: {e}")
            return False

    async def _get_user_personalization_weights(
        self, user_id: UUID
    ) -> Dict[str, float]:
        """사용자별 개인화 가중치 조회"""
        cache_key = f"ml:user_weights:{user_id}"

        # 캐시에서 조회
        cached_weights = await self.cache.get(cache_key)
        if cached_weights:
            return cached_weights

        # 기본 가중치 반환
        default_weights = {
            "global_factor": 1.0,
            "category_preference": 1.0,
            "location_preference": 1.0,
            "price_preference": 1.0,
            "time_preference": 1.0,
        }

        # 캐시에 저장
        await self.cache.set(cache_key, default_weights, ttl=self.model_cache_ttl)

        return default_weights

    def _calculate_context_adjustment(
        self, context: Dict[str, Any]
    ) -> Dict[str, float]:
        """컨텍스트 기반 조정값 계산"""
        adjustment = {}

        # 시간 컨텍스트
        if "hour" in context:
            hour = context["hour"]
            if 9 <= hour <= 11:  # 오전
                adjustment["morning_boost"] = 1.1
            elif 12 <= hour <= 14:  # 점심
                adjustment["lunch_boost"] = 1.2
            elif 18 <= hour <= 21:  # 저녁
                adjustment["dinner_boost"] = 1.15

        # 날씨 컨텍스트
        if "weather" in context:
            weather = context["weather"]
            if weather in ["rain", "snow"]:
                adjustment["indoor_boost"] = 1.3
            elif weather == "sunny":
                adjustment["outdoor_boost"] = 1.1

        # 위치 컨텍스트
        if "location_type" in context:
            location_type = context["location_type"]
            if location_type == "work":
                adjustment["work_lunch_boost"] = 1.2
            elif location_type == "home":
                adjustment["nearby_boost"] = 1.1

        return adjustment

    def _apply_context_to_weights(
        self, weights: Dict[str, float], adjustment: Dict[str, float]
    ) -> Dict[str, float]:
        """컨텍스트 조정을 가중치에 적용"""
        adjusted_weights = weights.copy()

        # 글로벌 팩터에 조정값 적용
        global_adjustment = 1.0
        for key, value in adjustment.items():
            global_adjustment *= value

        adjusted_weights["global_factor"] *= global_adjustment

        return adjusted_weights

    async def _save_model(self):
        """모델을 캐시에 저장"""
        try:
            model_data = {
                "relevance_model": pickle.dumps(self.relevance_model),
                "personalization_model": pickle.dumps(self.personalization_model),
                "scaler": pickle.dumps(self.scaler),
                "is_trained": self.is_trained,
                "last_training": self.last_training.isoformat()
                if self.last_training
                else None,
                "model_version": self.model_version,
            }

            await self.cache.set(
                "ml:model:current", model_data, ttl=self.model_cache_ttl
            )

        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    async def _load_model(self):
        """캐시에서 모델 로드"""
        try:
            model_data = await self.cache.get("ml:model:current")
            if not model_data:
                return False

            self.relevance_model = pickle.loads(model_data["relevance_model"])
            self.personalization_model = pickle.loads(
                model_data["personalization_model"]
            )
            self.scaler = pickle.loads(model_data["scaler"])
            self.is_trained = model_data["is_trained"]
            self.model_version = model_data["model_version"]

            if model_data["last_training"]:
                self.last_training = datetime.fromisoformat(model_data["last_training"])

            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    async def _invalidate_model_cache(self):
        """모델 캐시 무효화"""
        try:
            # 예측 캐시 삭제
            await self.cache.delete_pattern("ml:predictions:*")

            # 사용자 가중치 캐시 삭제
            await self.cache.delete_pattern("ml:user_weights:*")

        except Exception as e:
            logger.error(f"Failed to invalidate model cache: {e}")


# 전역 ML 엔진 인스턴스
_ml_engine: Optional[MLEngine] = None


async def get_ml_engine() -> MLEngine:
    """ML 엔진 인스턴스 반환"""
    global _ml_engine

    if _ml_engine is None:
        from app.core.cache import get_cache_service

        cache_service = await get_cache_service()
        _ml_engine = MLEngine(cache_service)

        # 저장된 모델 로드 시도
        await _ml_engine._load_model()

    return _ml_engine


def get_ml_engine_sync() -> MLEngine:
    """동기식 ML 엔진 반환 (테스트용)"""
    global _ml_engine

    if _ml_engine is None:
        from app.core.cache import get_cache_service_sync

        # 동기식 캐시 서비스 사용
        cache_service = get_cache_service_sync()
        _ml_engine = MLEngine(cache_service)

    return _ml_engine
