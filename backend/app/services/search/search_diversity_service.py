"""
검색 결과 다양성 보장 서비스 (Task 2-3-4)

검색 결과의 다양성을 보장하여 사용자가 균형잡힌 옵션을 볼 수 있도록 지원
- 카테고리 다양성 보장
- 가격대 균형 조정
- 지역별 분산
- 유사도 기반 중복 제거
- 개인화와 다양성의 균형 조절
"""

import logging
import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SearchDiversityService:
    """검색 결과 다양성 보장 서비스"""

    def __init__(self):
        """서비스 초기화"""
        # 다양성 설정
        self.diversity_weights = {
            "category": 0.3,  # 카테고리 다양성
            "price_range": 0.2,  # 가격대 다양성
            "location": 0.25,  # 지역 다양성
            "rating": 0.15,  # 평점 분산
            "features": 0.1,  # 특성 다양성
        }

        # 다양성 임계값
        self.diversity_threshold = 0.7  # 0-1, 높을수록 더 다양함
        self.similarity_threshold = 0.8  # 유사도 임계값

        # TF-IDF 벡터화 (특성 유사도 계산용)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100, stop_words="english", ngram_range=(1, 2)
        )

    async def ensure_diversity(
        self,
        search_results: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None,
        diversity_factor: float = 0.5,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        검색 결과의 다양성을 보장하여 재정렬

        Args:
            search_results: 원본 검색 결과
            user_preferences: 사용자 선호도
            diversity_factor: 다양성 강도 (0.0-1.0)
            max_results: 최대 결과 수

        Returns:
            다양성이 보장된 검색 결과
        """
        try:
            if not search_results:
                return []

            if len(search_results) <= 3:  # 적은 결과는 그대로 반환
                return search_results[:max_results] if max_results else search_results

            logger.info(f"Ensuring diversity for {len(search_results)} results")

            # 1. 결과 분석 및 클러스터링
            result_clusters = self._analyze_result_clusters(search_results)

            # 2. 다양성 점수 계산
            diversity_scores = self._calculate_diversity_scores(
                search_results, result_clusters
            )

            # 3. 개인화 점수와 다양성 점수 균형 조정
            balanced_results = self._balance_personalization_and_diversity(
                search_results, diversity_scores, user_preferences, diversity_factor
            )

            # 4. 유사한 결과 제거
            deduplicated_results = await self._remove_similar_results(balanced_results)

            # 5. 카테고리별 균형 조정
            balanced_by_category = self._balance_by_categories(
                deduplicated_results, user_preferences
            )

            # 6. 최종 다양성 검증 및 조정
            final_results = self._final_diversity_check(
                balanced_by_category, user_preferences
            )

            # 결과 수 제한
            if max_results:
                final_results = final_results[:max_results]

            logger.info(f"Diversity ensured: {len(final_results)} results returned")

            return final_results

        except Exception as e:
            logger.error(f"Failed to ensure diversity: {e}")
            return search_results[:max_results] if max_results else search_results

    def _analyze_result_clusters(
        self, search_results: List[Dict[str, Any]]
    ) -> Dict[str, List[int]]:
        """검색 결과를 클러스터별로 분석"""
        clusters = {
            "categories": defaultdict(list),
            "price_ranges": defaultdict(list),
            "regions": defaultdict(list),
            "ratings": defaultdict(list),
        }

        for i, result in enumerate(search_results):
            # 카테고리별 클러스터링
            category = result.get("category", "unknown")
            clusters["categories"][category].append(i)

            # 가격대별 클러스터링
            price_range = result.get("price_range", 0)
            price_cluster = self._get_price_cluster(price_range)
            clusters["price_ranges"][price_cluster].append(i)

            # 지역별 클러스터링
            region = result.get("region", result.get("address", "unknown"))
            region_cluster = self._get_region_cluster(region)
            clusters["regions"][region_cluster].append(i)

            # 평점별 클러스터링
            rating = result.get("rating", 0)
            rating_cluster = self._get_rating_cluster(rating)
            clusters["ratings"][rating_cluster].append(i)

        return clusters

    def _calculate_diversity_scores(
        self,
        search_results: List[Dict[str, Any]],
        result_clusters: Dict[str, List[int]],
    ) -> List[float]:
        """각 결과의 다양성 점수 계산"""
        diversity_scores = []
        total_results = len(search_results)

        for i, result in enumerate(search_results):
            score = 0.0

            # 카테고리 다양성
            category = result.get("category", "unknown")
            category_frequency = len(result_clusters["categories"].get(category, []))
            category_diversity = 1.0 - (category_frequency / total_results)
            score += self.diversity_weights["category"] * category_diversity

            # 가격대 다양성
            price_range = result.get("price_range", 0)
            price_cluster = self._get_price_cluster(price_range)
            price_frequency = len(
                result_clusters["price_ranges"].get(price_cluster, [])
            )
            price_diversity = 1.0 - (price_frequency / total_results)
            score += self.diversity_weights["price_range"] * price_diversity

            # 지역 다양성
            region = result.get("region", result.get("address", "unknown"))
            region_cluster = self._get_region_cluster(region)
            region_frequency = len(result_clusters["regions"].get(region_cluster, []))
            region_diversity = 1.0 - (region_frequency / total_results)
            score += self.diversity_weights["location"] * region_diversity

            # 평점 다양성
            rating = result.get("rating", 0)
            rating_cluster = self._get_rating_cluster(rating)
            rating_frequency = len(result_clusters["ratings"].get(rating_cluster, []))
            rating_diversity = 1.0 - (rating_frequency / total_results)
            score += self.diversity_weights["rating"] * rating_diversity

            # 특성 다양성 (태그/키워드 기반)
            feature_diversity = self._calculate_feature_diversity(
                result, search_results
            )
            score += self.diversity_weights["features"] * feature_diversity

            diversity_scores.append(min(1.0, max(0.0, score)))

        return diversity_scores

    def _balance_personalization_and_diversity(
        self,
        search_results: List[Dict[str, Any]],
        diversity_scores: List[float],
        user_preferences: Optional[Dict[str, Any]],
        diversity_factor: float,
    ) -> List[Dict[str, Any]]:
        """개인화 점수와 다양성 점수의 균형 조정"""
        balanced_results = []

        for i, result in enumerate(search_results):
            # 기존 개인화 점수
            personalization_score = result.get("personalization_score", 0.5)

            # 다양성 점수
            diversity_score = diversity_scores[i]

            # 가중 평균으로 최종 점수 계산
            final_score = (
                1 - diversity_factor
            ) * personalization_score + diversity_factor * diversity_score

            # 사용자 선호도 고려 조정
            if user_preferences:
                preference_adjustment = self._calculate_preference_adjustment(
                    result, user_preferences
                )
                final_score *= preference_adjustment

            result_copy = result.copy()
            result_copy["diversity_score"] = diversity_score
            result_copy["balanced_score"] = final_score

            balanced_results.append(result_copy)

        # 균형 점수로 정렬
        balanced_results.sort(key=lambda x: x["balanced_score"], reverse=True)

        return balanced_results

    async def _remove_similar_results(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """유사한 결과 제거"""
        if len(search_results) <= 1:
            return search_results

        try:
            # 텍스트 특성 추출
            text_features = []
            for result in search_results:
                # 이름, 주소, 태그 등을 결합
                text = " ".join(
                    [
                        result.get("name", ""),
                        result.get("address", ""),
                        " ".join(result.get("tags", [])),
                        result.get("description", ""),
                    ]
                ).strip()
                text_features.append(text if text else "unknown")

            # TF-IDF 벡터화
            if len(set(text_features)) > 1:  # 유니크한 텍스트가 있을 때만
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
                similarity_matrix = cosine_similarity(tfidf_matrix)
            else:
                similarity_matrix = np.zeros((len(search_results), len(search_results)))

            # 중복 제거 로직
            unique_results = []
            used_indices = set()

            for i, result in enumerate(search_results):
                if i in used_indices:
                    continue

                unique_results.append(result)
                used_indices.add(i)

                # 유사한 결과들을 제외 목록에 추가
                for j in range(i + 1, len(search_results)):
                    if (
                        j not in used_indices
                        and similarity_matrix[i][j] > self.similarity_threshold
                    ):
                        used_indices.add(j)

            logger.info(
                f"Removed {len(search_results) - len(unique_results)} similar results"
            )

            return unique_results

        except Exception as e:
            logger.error(f"Failed to remove similar results: {e}")
            return search_results

    def _balance_by_categories(
        self,
        search_results: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """카테고리별 균형 조정"""
        if len(search_results) <= 5:
            return search_results

        # 카테고리별 그룹핑
        category_groups = defaultdict(list)
        for result in search_results:
            category = result.get("category", "unknown")
            category_groups[category].append(result)

        # 사용자 선호도 기반 카테고리 가중치
        category_weights = self._get_category_weights(user_preferences)

        # 카테고리별 할당량 계산
        total_results = len(search_results)
        category_quotas = self._calculate_category_quotas(
            category_groups, category_weights, total_results
        )

        # 할당량에 따라 결과 선택
        balanced_results = []
        for category, quota in category_quotas.items():
            if category in category_groups:
                # 해당 카테고리의 최고 점수 결과들 선택
                category_results = sorted(
                    category_groups[category],
                    key=lambda x: x.get("balanced_score", 0),
                    reverse=True,
                )
                balanced_results.extend(category_results[:quota])

        # 점수 순으로 최종 정렬
        balanced_results.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)

        return balanced_results

    def _final_diversity_check(
        self,
        search_results: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """최종 다양성 검증 및 조정"""
        if len(search_results) <= 3:
            return search_results

        # 다양성 메트릭 계산
        diversity_metrics = self._calculate_diversity_metrics(search_results)

        # 다양성이 부족한 경우 조정
        if diversity_metrics["overall_diversity"] < self.diversity_threshold:
            logger.info("Diversity below threshold, applying adjustments")
            return self._apply_diversity_adjustments(search_results, diversity_metrics)

        return search_results

    def _get_price_cluster(self, price_range: int) -> str:
        """가격대를 클러스터로 분류"""
        if price_range <= 1:
            return "budget"
        elif price_range <= 2:
            return "affordable"
        elif price_range <= 3:
            return "moderate"
        elif price_range <= 4:
            return "expensive"
        else:
            return "luxury"

    def _get_region_cluster(self, region: str) -> str:
        """지역을 클러스터로 분류"""
        if not region or region == "unknown":
            return "unknown"

        # 주요 지역별 클러스터링
        region_lower = region.lower()

        if any(area in region_lower for area in ["강남", "gangnam", "역삼", "삼성"]):
            return "gangnam"
        elif any(area in region_lower for area in ["홍대", "hongdae", "상수", "합정"]):
            return "hongdae"
        elif any(area in region_lower for area in ["명동", "myeongdong", "중구"]):
            return "jung_gu"
        elif any(area in region_lower for area in ["건대", "konkuk", "광진"]):
            return "gwangjin"
        elif any(area in region_lower for area in ["신촌", "sinchon", "이대", "서대문"]):
            return "seodaemun"
        else:
            return "other"

    def _get_rating_cluster(self, rating: float) -> str:
        """평점을 클러스터로 분류"""
        if rating >= 4.5:
            return "excellent"
        elif rating >= 4.0:
            return "very_good"
        elif rating >= 3.5:
            return "good"
        elif rating >= 3.0:
            return "average"
        else:
            return "below_average"

    def _calculate_feature_diversity(
        self, result: Dict[str, Any], all_results: List[Dict[str, Any]]
    ) -> float:
        """특성 다양성 계산"""
        result_tags = set(result.get("tags", []))
        if not result_tags:
            return 0.5  # 중간값

        # 전체 결과에서 해당 태그들의 빈도 계산
        all_tags = []
        for r in all_results:
            all_tags.extend(r.get("tags", []))

        if not all_tags:
            return 0.5

        tag_counter = Counter(all_tags)
        total_tags = len(all_tags)

        # 태그별 희소성 계산 (빈도가 낮을수록 다양성이 높음)
        diversity_score = 0.0
        for tag in result_tags:
            tag_frequency = tag_counter.get(tag, 1)
            tag_diversity = 1.0 - (tag_frequency / total_tags)
            diversity_score += tag_diversity

        return min(1.0, diversity_score / len(result_tags) if result_tags else 0.5)

    def _calculate_preference_adjustment(
        self, result: Dict[str, Any], user_preferences: Dict[str, Any]
    ) -> float:
        """사용자 선호도 기반 조정값 계산"""
        adjustment = 1.0

        # 카테고리 선호도
        category_prefs = user_preferences.get("category_preferences", {})
        result_category = result.get("category", "unknown")
        if result_category in category_prefs:
            category_weight = category_prefs[result_category]
            adjustment *= 0.8 + 0.4 * category_weight  # 0.8 ~ 1.2 범위

        # 지역 선호도
        region_prefs = user_preferences.get("region_preferences", {})
        result_region = result.get("region", "unknown")
        region_cluster = self._get_region_cluster(result_region)
        if region_cluster in region_prefs:
            region_weight = region_prefs[region_cluster]
            adjustment *= 0.9 + 0.2 * region_weight  # 0.9 ~ 1.1 범위

        # 가격 선호도
        price_pref = user_preferences.get("price_preference", 2.5)  # 기본값 중간
        result_price = result.get("price_range", 2.5)
        price_diff = abs(result_price - price_pref)
        price_adjustment = max(0.7, 1.0 - price_diff * 0.1)  # 차이가 클수록 감소
        adjustment *= price_adjustment

        return min(1.5, max(0.5, adjustment))  # 0.5 ~ 1.5 범위로 제한

    def _get_category_weights(
        self, user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """카테고리 가중치 계산"""
        if not user_preferences:
            return {}

        category_prefs = user_preferences.get("category_preferences", {})
        if not category_prefs:
            return {}

        # 선호도를 가중치로 정규화
        total_preference = sum(category_prefs.values())
        if total_preference == 0:
            return {}

        return {
            category: pref / total_preference
            for category, pref in category_prefs.items()
        }

    def _calculate_category_quotas(
        self,
        category_groups: Dict[str, List[Dict[str, Any]]],
        category_weights: Dict[str, float],
        total_results: int,
    ) -> Dict[str, int]:
        """카테고리별 할당량 계산"""
        quotas = {}
        remaining_results = total_results
        categories = list(category_groups.keys())

        # 가중치가 있는 카테고리 먼저 처리
        weighted_categories = [cat for cat in categories if cat in category_weights]
        unweighted_categories = [
            cat for cat in categories if cat not in category_weights
        ]

        # 가중치 기반 할당
        for category in weighted_categories:
            weight = category_weights[category]
            available_items = len(category_groups[category])

            # 가중치와 사용 가능한 아이템 수를 고려한 할당
            quota = min(available_items, max(1, int(total_results * weight)))

            quotas[category] = quota
            remaining_results -= quota

        # 가중치가 없는 카테고리는 균등 분배
        if unweighted_categories and remaining_results > 0:
            per_category = max(1, remaining_results // len(unweighted_categories))
            remainder = remaining_results % len(unweighted_categories)

            for i, category in enumerate(unweighted_categories):
                available_items = len(category_groups[category])
                quota = min(available_items, per_category)

                # 나머지를 앞쪽 카테고리에 분배
                if i < remainder:
                    quota = min(available_items, quota + 1)

                quotas[category] = quota

        return quotas

    def _calculate_diversity_metrics(
        self, search_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """다양성 메트릭 계산"""
        if not search_results:
            return {"overall_diversity": 0.0}

        # 카테고리 분포
        categories = [r.get("category", "unknown") for r in search_results]
        category_diversity = self._calculate_shannon_diversity(categories)

        # 가격대 분포
        price_ranges = [
            self._get_price_cluster(r.get("price_range", 0)) for r in search_results
        ]
        price_diversity = self._calculate_shannon_diversity(price_ranges)

        # 지역 분포
        regions = [
            self._get_region_cluster(r.get("region", "")) for r in search_results
        ]
        region_diversity = self._calculate_shannon_diversity(regions)

        # 평점 분포
        ratings = [self._get_rating_cluster(r.get("rating", 0)) for r in search_results]
        rating_diversity = self._calculate_shannon_diversity(ratings)

        # 전체 다양성 (가중 평균)
        overall_diversity = (
            0.3 * category_diversity
            + 0.25 * region_diversity
            + 0.2 * price_diversity
            + 0.25 * rating_diversity
        )

        return {
            "overall_diversity": overall_diversity,
            "category_diversity": category_diversity,
            "price_diversity": price_diversity,
            "region_diversity": region_diversity,
            "rating_diversity": rating_diversity,
        }

    def _calculate_shannon_diversity(self, items: List[str]) -> float:
        """Shannon 다양성 지수 계산"""
        if not items:
            return 0.0

        counter = Counter(items)
        total = len(items)

        if total <= 1:
            return 0.0

        shannon_index = 0.0
        for count in counter.values():
            if count > 0:
                proportion = count / total
                shannon_index -= proportion * math.log2(proportion)

        # 최대 다양성으로 정규화 (0-1 범위)
        max_diversity = math.log2(len(counter))
        return shannon_index / max_diversity if max_diversity > 0 else 0.0

    def _apply_diversity_adjustments(
        self, search_results: List[Dict[str, Any]], diversity_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """다양성 조정 적용"""
        if len(search_results) <= 3:
            return search_results

        adjusted_results = search_results.copy()

        # 다양성이 낮은 차원 식별
        low_diversity_dimensions = []
        if diversity_metrics.get("category_diversity", 0) < 0.5:
            low_diversity_dimensions.append("category")
        if diversity_metrics.get("region_diversity", 0) < 0.5:
            low_diversity_dimensions.append("region")
        if diversity_metrics.get("price_diversity", 0) < 0.5:
            low_diversity_dimensions.append("price")

        if not low_diversity_dimensions:
            return adjusted_results

        # 차원별 조정 적용
        for dimension in low_diversity_dimensions:
            adjusted_results = self._adjust_dimension_diversity(
                adjusted_results, dimension
            )

        return adjusted_results

    def _adjust_dimension_diversity(
        self, search_results: List[Dict[str, Any]], dimension: str
    ) -> List[Dict[str, Any]]:
        """특정 차원의 다양성 조정"""
        if dimension == "category":
            return self._adjust_category_diversity(search_results)
        elif dimension == "region":
            return self._adjust_region_diversity(search_results)
        elif dimension == "price":
            return self._adjust_price_diversity(search_results)

        return search_results

    def _adjust_category_diversity(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """카테고리 다양성 조정"""
        category_groups = defaultdict(list)
        for i, result in enumerate(search_results):
            category = result.get("category", "unknown")
            category_groups[category].append((i, result))

        # 과도하게 많은 카테고리의 결과 수 제한
        max_per_category = max(2, len(search_results) // len(category_groups))
        adjusted_results = []

        for category, items in category_groups.items():
            # 점수 순으로 정렬하여 상위 결과만 선택
            items.sort(key=lambda x: x[1].get("balanced_score", 0), reverse=True)
            selected_items = items[:max_per_category]
            adjusted_results.extend([item[1] for item in selected_items])

        # 점수 순으로 재정렬
        adjusted_results.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)
        return adjusted_results

    def _adjust_region_diversity(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """지역 다양성 조정"""
        region_groups = defaultdict(list)
        for result in search_results:
            region = self._get_region_cluster(result.get("region", ""))
            region_groups[region].append(result)

        # 지역별 균등 분배
        target_per_region = max(1, len(search_results) // len(region_groups))
        adjusted_results = []

        for region, items in region_groups.items():
            items.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)
            adjusted_results.extend(items[:target_per_region])

        adjusted_results.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)
        return adjusted_results

    def _adjust_price_diversity(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """가격대 다양성 조정"""
        price_groups = defaultdict(list)
        for result in search_results:
            price_cluster = self._get_price_cluster(result.get("price_range", 0))
            price_groups[price_cluster].append(result)

        # 가격대별 균등 분배
        target_per_price = max(1, len(search_results) // len(price_groups))
        adjusted_results = []

        for price_cluster, items in price_groups.items():
            items.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)
            adjusted_results.extend(items[:target_per_price])

        adjusted_results.sort(key=lambda x: x.get("balanced_score", 0), reverse=True)
        return adjusted_results
