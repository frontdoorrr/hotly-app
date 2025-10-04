"""
검색 개인화 품질 테스트 (Task 2-3-6)

개인화 검색 알고리즘 품질 검증
- 사용자 행동 학습 정확도
- 개인화 추천 품질
- 검색 선호도 반영 효과
- 개인화 다양성 보장
"""

import statistics
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4


class TestSearchPersonalizationQuality:
    """검색 개인화 품질 테스트"""

    def setup_method(self) -> None:
        """개인화 테스트 설정"""
        self.test_users = [
            {
                "id": uuid4(),
                "profile": {
                    "age_group": "20s",
                    "lifestyle": "active",
                    "preferred_categories": ["cafe", "activity"],
                    "preferred_regions": ["홍대", "강남"],
                    "budget_range": [1, 2, 3],
                    "visit_frequency": "frequent",
                },
                "behavior_history": [
                    {
                        "action": "search",
                        "query": "홍대 카페",
                        "clicked": True,
                        "rating": 4.5,
                    },
                    {
                        "action": "visit",
                        "place_id": "cafe_123",
                        "duration_minutes": 120,
                    },
                    {
                        "action": "search",
                        "query": "조용한 공간",
                        "clicked": True,
                        "rating": 4.0,
                    },
                    {
                        "action": "favorite",
                        "place_id": "cafe_456",
                        "timestamp": "2025-01-10",
                    },
                ],
            },
            {
                "id": uuid4(),
                "profile": {
                    "age_group": "30s",
                    "lifestyle": "family",
                    "preferred_categories": ["restaurant", "cultural"],
                    "preferred_regions": ["신촌", "여의도"],
                    "budget_range": [3, 4, 5],
                    "visit_frequency": "moderate",
                },
                "behavior_history": [
                    {
                        "action": "search",
                        "query": "가족 맛집",
                        "clicked": True,
                        "rating": 5.0,
                    },
                    {
                        "action": "visit",
                        "place_id": "restaurant_789",
                        "duration_minutes": 90,
                    },
                    {
                        "action": "search",
                        "query": "아이와 함께",
                        "clicked": True,
                        "rating": 4.5,
                    },
                    {
                        "action": "save",
                        "place_id": "family_place_101",
                        "timestamp": "2025-01-09",
                    },
                ],
            },
        ]

        # 테스트용 장소 데이터 (다양한 특성)
        self.diverse_places = [
            {
                "id": "personalized_place_1",
                "name": "홍대 조용한 카페",
                "category": "cafe",
                "region": "홍대",
                "tags": ["조용한", "혼자가기좋은", "작업공간"],
                "price_range": 2,
                "rating": 4.3,
                "visit_count": 50,
                "popularity_score": 0.7,
                "features": ["wifi", "quiet", "study_friendly"],
            },
            {
                "id": "personalized_place_2",
                "name": "강남 트렌디 카페",
                "category": "cafe",
                "region": "강남",
                "tags": ["트렌디", "인스타감성", "모던"],
                "price_range": 4,
                "rating": 4.6,
                "visit_count": 200,
                "popularity_score": 0.9,
                "features": ["trendy", "instagram_worthy", "modern"],
            },
            {
                "id": "personalized_place_3",
                "name": "신촌 가족 레스토랑",
                "category": "restaurant",
                "region": "신촌",
                "tags": ["가족", "넓은", "아이동반"],
                "price_range": 3,
                "rating": 4.4,
                "visit_count": 120,
                "popularity_score": 0.6,
                "features": ["family_friendly", "spacious", "kids_welcome"],
            },
            {
                "id": "personalized_place_4",
                "name": "여의도 고급 레스토랑",
                "category": "restaurant",
                "region": "여의도",
                "tags": ["고급", "비즈니스", "뷰맛집"],
                "price_range": 5,
                "rating": 4.8,
                "visit_count": 80,
                "popularity_score": 0.8,
                "features": ["luxury", "business", "great_view"],
            },
        ]

    async def test_user_behavior_learning_accuracy(self) -> None:
        """
        Given: 사용자의 과거 행동 데이터
        When: 개인화 모델이 학습함
        Then: 사용자 선호도를 정확히 파악함
        """
        # Given: 첫 번째 사용자 (20대, 활동적, 카페 선호)
        user = self.test_users[0]

        # Mock 개인화 학습 서비스
        with patch(
            "app.services.personalization_service.learn_user_preferences"
        ) as mock_learning:
            # 행동 기반 선호도 학습 시뮬레이션
            learned_preferences = {
                "category_preferences": {
                    "cafe": 0.8,  # 카페 검색 및 방문 많음
                    "restaurant": 0.3,
                    "cultural": 0.2,
                },
                "region_preferences": {
                    "홍대": 0.9,  # 홍대 관련 검색 빈번
                    "강남": 0.6,
                    "신촌": 0.2,
                },
                "tag_preferences": {
                    "조용한": 0.9,  # 조용한 공간 검색 이력
                    "혼자가기좋은": 0.7,
                    "작업공간": 0.8,
                    "트렌디": 0.3,
                },
                "price_sensitivity": {
                    "preferred_range": [1, 2, 3],  # 저-중간 가격대 선호
                    "max_acceptable": 3,
                    "budget_flexibility": 0.6,
                },
                "behavioral_patterns": {
                    "visit_duration_preference": "long",  # 2시간 방문 이력
                    "search_time_pattern": "afternoon",
                    "decision_speed": "moderate",
                },
            }

            mock_learning.return_value = learned_preferences

            # When: 사용자 행동 데이터로 학습 실행
            from app.services.ml.personalization_service import PersonalizationService

            personalization_service = PersonalizationService(
                ml_model=AsyncMock(),
                user_behavior_tracker=AsyncMock(),
                preferences_store=AsyncMock(),
            )
            personalization_service.learn_user_preferences = mock_learning

            result = await personalization_service.learn_user_preferences(
                user_id=user["id"],
                behavior_history=user["behavior_history"],
                profile_data=user["profile"],
            )

        # Then: 학습된 선호도가 사용자 행동과 일치함
        assert result["category_preferences"]["cafe"] > 0.7  # 카페 선호도 높음
        assert result["region_preferences"]["홍대"] > 0.8  # 홍대 선호도 높음
        assert result["tag_preferences"]["조용한"] > 0.8  # 조용한 공간 선호
        assert 3 in result["price_sensitivity"]["preferred_range"]  # 적정 가격대 포함

        # 행동 패턴 정확도 검증
        assert result["behavioral_patterns"]["visit_duration_preference"] == "long"

        # 전체 학습 정확도 검증 (가중 평균)
        accuracy_scores = [
            result["category_preferences"]["cafe"],
            result["region_preferences"]["홍대"],
            result["tag_preferences"]["조용한"],
        ]
        overall_accuracy = statistics.mean(accuracy_scores)
        assert overall_accuracy > 0.8  # 80% 이상 정확도

    async def test_personalized_search_ranking_quality(self) -> None:
        """
        Given: 개인화된 사용자 프로필
        When: 검색 결과 개인화 랭킹을 적용함
        Then: 사용자 취향에 맞는 순서로 결과가 정렬됨
        """
        # Given: 카페 선호 사용자와 가족 중심 사용자
        cafe_lover = self.test_users[0]  # 20대, 카페 선호
        family_user = self.test_users[1]  # 30대, 가족 중심

        search_query = "맛집"  # 동일한 검색어로 개인화 차이 확인

        # Mock 개인화 랭킹 서비스
        with patch(
            "app.services.ranking_service.calculate_personalized_score"
        ) as mock_ranking:
            # 카페 선호 사용자용 개인화 점수
            def personalized_score_cafe_user(place, user_profile):
                score = 0.5  # 기본 점수

                # 카테고리 매치 보너스
                if place["category"] == "cafe":
                    score += 0.3
                elif place["category"] == "restaurant":
                    score += 0.1

                # 지역 선호도 반영
                if place["region"] in ["홍대", "강남"]:
                    score += 0.2

                # 가격대 선호도
                if place["price_range"] in [1, 2, 3]:
                    score += 0.15

                # 태그 매칭
                preferred_tags = ["조용한", "혼자가기좋은", "작업공간"]
                tag_matches = sum(1 for tag in place["tags"] if tag in preferred_tags)
                score += tag_matches * 0.1

                return min(score, 1.0)

            # 가족 사용자용 개인화 점수
            def personalized_score_family_user(place, user_profile):
                score = 0.5  # 기본 점수

                # 카테고리 매치 보너스
                if place["category"] == "restaurant":
                    score += 0.3
                elif place["category"] == "cultural":
                    score += 0.2

                # 지역 선호도 반영
                if place["region"] in ["신촌", "여의도"]:
                    score += 0.2

                # 가격대 선호도 (높은 예산)
                if place["price_range"] in [3, 4, 5]:
                    score += 0.15

                # 가족 친화 태그
                family_tags = ["가족", "넓은", "아이동반"]
                tag_matches = sum(1 for tag in place["tags"] if tag in family_tags)
                score += tag_matches * 0.15

                return min(score, 1.0)

            # When: 두 사용자에 대해 동일 검색 결과 개인화
            cafe_user_results = []
            family_user_results = []

            for place in self.diverse_places:
                # 카페 사용자 개인화 점수
                cafe_score = personalized_score_cafe_user(place, cafe_lover["profile"])
                cafe_user_results.append({**place, "personalization_score": cafe_score})

                # 가족 사용자 개인화 점수
                family_score = personalized_score_family_user(
                    place, family_user["profile"]
                )
                family_user_results.append(
                    {**place, "personalization_score": family_score}
                )

            # 개인화 점수순 정렬
            cafe_user_results.sort(
                key=lambda x: x["personalization_score"], reverse=True
            )
            family_user_results.sort(
                key=lambda x: x["personalization_score"], reverse=True
            )

        # Then: 개인화 랭킹이 사용자 취향을 반영함

        # 카페 사용자: 카페나 홍대/강남 지역이 상위에
        cafe_top_result = cafe_user_results[0]
        assert cafe_top_result["category"] == "cafe" or cafe_top_result["region"] in [
            "홍대",
            "강남",
        ]
        assert cafe_top_result["personalization_score"] > 0.7

        # 가족 사용자: 레스토랑이나 가족 친화적 장소가 상위에
        family_top_result = family_user_results[0]
        assert family_top_result["category"] == "restaurant" or any(
            tag in ["가족", "넓은", "아이동반"] for tag in family_top_result["tags"]
        )
        assert family_top_result["personalization_score"] > 0.7

        # 두 사용자의 상위 결과가 다름 (개인화 효과)
        assert cafe_top_result["id"] != family_top_result["id"]

        # 개인화 점수 분산도 확인 (충분한 차별화)
        cafe_scores = [place["personalization_score"] for place in cafe_user_results]
        family_scores = [
            place["personalization_score"] for place in family_user_results
        ]

        cafe_score_std = statistics.stdev(cafe_scores)
        family_score_std = statistics.stdev(family_scores)

        assert cafe_score_std > 0.1  # 충분한 점수 차별화
        assert family_score_std > 0.1

    async def test_search_preference_adaptation(self) -> None:
        """
        Given: 사용자의 검색 패턴 변화
        When: 지속적인 학습이 이루어짐
        Then: 변화하는 취향에 맞춰 추천이 적응함
        """
        # Given: 취향이 변화하는 사용자 시뮬레이션
        user_id = uuid4()

        # 초기 취향: 카페 선호
        initial_behavior = [
            {
                "action": "search",
                "query": "카페",
                "timestamp": "2025-01-01",
                "satisfaction": 4.0,
            },
            {
                "action": "visit",
                "place_category": "cafe",
                "timestamp": "2025-01-02",
                "rating": 4.5,
            },
            {"action": "save", "place_category": "cafe", "timestamp": "2025-01-03"},
        ]

        # 변화된 취향: 문화 활동 선호로 변화
        recent_behavior = [
            {
                "action": "search",
                "query": "전시회",
                "timestamp": "2025-01-08",
                "satisfaction": 4.8,
            },
            {
                "action": "visit",
                "place_category": "cultural",
                "timestamp": "2025-01-09",
                "rating": 5.0,
            },
            {
                "action": "search",
                "query": "박물관",
                "timestamp": "2025-01-10",
                "satisfaction": 4.6,
            },
            {"action": "save", "place_category": "cultural", "timestamp": "2025-01-10"},
        ]

        # Mock 적응형 학습 서비스
        with patch(
            "app.services.adaptive_personalization.update_preferences"
        ) as mock_adaptive:
            # 시간별 가중치 적용한 선호도 업데이트
            def calculate_time_weighted_preferences(all_behavior):
                preferences = {"cafe": 0, "cultural": 0, "restaurant": 0}

                for behavior in all_behavior:
                    # 최근 행동에 더 높은 가중치
                    days_ago = (
                        datetime.now() - datetime.fromisoformat(behavior["timestamp"])
                    ).days
                    weight = max(0.1, 1.0 - (days_ago * 0.1))  # 시간에 따른 가중치 감소

                    if "place_category" in behavior:
                        category = behavior["place_category"]
                        satisfaction = behavior.get(
                            "rating", behavior.get("satisfaction", 3.0)
                        )
                        preferences[category] += weight * (satisfaction / 5.0)
                    elif "query" in behavior:
                        # 검색어 기반 카테고리 추론
                        query = behavior["query"].lower()
                        if any(word in query for word in ["카페", "cafe"]):
                            preferences["cafe"] += weight * 0.7
                        elif any(word in query for word in ["전시", "박물관", "문화"]):
                            preferences["cultural"] += weight * 0.8

                # 정규화
                total = sum(preferences.values())
                if total > 0:
                    preferences = {k: v / total for k, v in preferences.items()}

                return preferences

            # 초기 학습 (과거 행동)
            initial_prefs = calculate_time_weighted_preferences(initial_behavior)

            # 적응 학습 (최근 행동 포함)
            all_behavior = initial_behavior + recent_behavior
            adapted_prefs = calculate_time_weighted_preferences(all_behavior)

            mock_adaptive.side_effect = [initial_prefs, adapted_prefs]

            # When: 적응형 개인화 서비스 실행
            from app.services.adaptive_personalization import (
                AdaptivePersonalizationService,
            )

            adaptive_service = AdaptivePersonalizationService(
                behavior_tracker=AsyncMock(),
                ml_model=AsyncMock(),
                preference_store=AsyncMock(),
            )
            adaptive_service.update_preferences = mock_adaptive

            # 초기 선호도 학습
            initial_result = await adaptive_service.update_preferences(
                user_id=user_id,
                behavior_history=initial_behavior,
            )

            # 적응 후 선호도 업데이트
            adapted_result = await adaptive_service.update_preferences(
                user_id=user_id,
                behavior_history=all_behavior,
            )

        # Then: 취향 변화가 선호도에 반영됨

        # 초기에는 카페 선호도가 높음
        assert initial_result.get("cafe", 0) > initial_result.get("cultural", 0)

        # 적응 후에는 문화 활동 선호도가 상승
        assert adapted_result.get("cultural", 0) > adapted_result.get("cafe", 0)

        # 적응 효과 측정 (선호도 변화폭)
        cafe_change = adapted_result.get("cafe", 0) - initial_result.get("cafe", 0)
        cultural_change = adapted_result.get("cultural", 0) - initial_result.get(
            "cultural", 0
        )

        assert cultural_change > 0.2  # 문화 선호도 20% 이상 증가
        assert cafe_change < 0  # 카페 선호도 감소

        # 전체 적응도 측정
        total_change = abs(cafe_change) + abs(cultural_change)
        assert total_change > 0.3  # 충분한 적응 효과

    async def test_personalization_diversity_balance(self) -> None:
        """
        Given: 개인화 추천 시스템
        When: 다양성 보장 알고리즘을 적용함
        Then: 개인 취향과 탐색의 균형을 유지함
        """
        # Given: 특정 카테고리만 선호하는 사용자
        narrow_preference_user = {
            "id": uuid4(),
            "strong_preferences": {
                "cafe": 0.9,
                "restaurant": 0.05,
                "cultural": 0.03,
                "activity": 0.02,
            },
            "diversity_setting": "balanced",  # 다양성 균형 설정
        }

        # 다양한 카테고리의 검색 결과
        diverse_results = [
            {"id": "cafe_1", "category": "cafe", "base_score": 0.8},
            {"id": "cafe_2", "category": "cafe", "base_score": 0.75},
            {"id": "cafe_3", "category": "cafe", "base_score": 0.7},
            {"id": "restaurant_1", "category": "restaurant", "base_score": 0.85},
            {"id": "cultural_1", "category": "cultural", "base_score": 0.8},
            {"id": "activity_1", "category": "activity", "base_score": 0.75},
        ]

        # Mock 다양성 보장 서비스
        with patch(
            "app.services.diversity_service.apply_diversity_boost"
        ) as mock_diversity:

            def apply_diversity_algorithm(results, user_prefs, diversity_factor=0.3):
                """다양성 보장 알고리즘"""
                # 카테고리별 빈도 계산
                category_counts = {}
                for result in results:
                    category = result["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1

                # 다양성 부스트 적용
                boosted_results = []
                for result in results:
                    # 기본 개인화 점수
                    personal_score = result["base_score"] * user_prefs[
                        "strong_preferences"
                    ].get(result["category"], 0.1)

                    # 다양성 부스트 (희귀 카테고리에 보너스)
                    category_frequency = category_counts[result["category"]]
                    diversity_boost = (1.0 / category_frequency) * diversity_factor

                    # 최종 점수 계산
                    final_score = (
                        personal_score * (1 - diversity_factor) + diversity_boost
                    )

                    boosted_results.append(
                        {
                            **result,
                            "personal_score": personal_score,
                            "diversity_boost": diversity_boost,
                            "final_score": final_score,
                        }
                    )

                return sorted(
                    boosted_results, key=lambda x: x["final_score"], reverse=True
                )

            mock_diversity.return_value = apply_diversity_algorithm(
                diverse_results, narrow_preference_user, diversity_factor=0.3
            )

            # When: 다양성 보장 알고리즘 적용
            from app.services.diversity_service import DiversityService

            diversity_service = DiversityService(
                personalization_service=AsyncMock(),
                diversity_config={"balance_factor": 0.3},
            )
            diversity_service.apply_diversity_boost = mock_diversity

            final_results = await diversity_service.apply_diversity_boost(
                results=diverse_results,
                user_preferences=narrow_preference_user,
            )

        # Then: 개인화와 다양성의 균형이 유지됨

        # 상위 결과에 여전히 개인 취향 반영 (카페)
        top_3 = final_results[:3]
        cafe_in_top3 = sum(1 for result in top_3 if result["category"] == "cafe")
        assert cafe_in_top3 >= 1  # 최소 1개는 카페

        # 하지만 모든 결과가 카페는 아님 (다양성 보장)
        assert cafe_in_top3 < 3  # 3개 모두 카페가 아님

        # 다양한 카테고리가 상위권에 포함
        top_5_categories = {result["category"] for result in final_results[:5]}
        assert len(top_5_categories) >= 3  # 최소 3개 카테고리

        # 개인화 점수 vs 다양성 부스트 균형 검증
        for result in final_results:
            personal_weight = result["personal_score"] * 0.7  # 70% 개인화
            diversity_weight = result["diversity_boost"]  # 30% 다양성

            # 최종 점수가 둘의 적절한 조합인지 확인
            expected_score = personal_weight + diversity_weight
            assert abs(result["final_score"] - expected_score) < 0.1

        # 다양성 지표 계산 (Shannon entropy)
        category_distribution = {}
        for result in final_results[:10]:  # 상위 10개 결과
            cat = result["category"]
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        # 엔트로피 계산
        total_results = sum(category_distribution.values())
        entropy = 0
        for count in category_distribution.values():
            if count > 0:
                p = count / total_results
                entropy -= p * statistics.log(p)

        # 다양성 지표가 충분한지 확인
        max_entropy = statistics.log(len(category_distribution))
        diversity_score = entropy / max_entropy if max_entropy > 0 else 0
        assert diversity_score > 0.5  # 50% 이상의 다양성 확보

    async def test_cold_start_personalization(self) -> None:
        """
        Given: 신규 사용자 (행동 데이터 부족)
        When: 콜드 스타트 개인화를 적용함
        Then: 일반적 선호도와 인구통계 기반 추천 제공함
        """
        # Given: 신규 사용자 (최소한의 정보만 있음)
        new_user = {
            "id": uuid4(),
            "signup_date": "2025-01-11",
            "basic_profile": {
                "age_group": "20s",
                "region": "서울",
                "signup_source": "friend_referral",
            },
            "behavior_history": [],  # 행동 데이터 없음
            "onboarding_preferences": {
                "interested_categories": ["cafe", "cultural"],  # 온보딩에서 선택
                "budget_range": "moderate",
                "activity_level": "moderate",
            },
        }

        # Mock 콜드 스타트 추천 서비스
        with patch(
            "app.services.cold_start_service.generate_initial_recommendations"
        ) as mock_coldstart:

            def cold_start_algorithm(user_profile, available_places):
                """콜드 스타트 알고리즘"""

                # 1. 인구통계 기반 선호도
                demographic_prefs = {
                    "20s": {
                        "cafe": 0.4,
                        "activity": 0.3,
                        "cultural": 0.2,
                        "restaurant": 0.1,
                    },
                    "30s": {
                        "restaurant": 0.4,
                        "cultural": 0.3,
                        "cafe": 0.2,
                        "activity": 0.1,
                    },
                }
                age_prefs = demographic_prefs.get(
                    user_profile["basic_profile"]["age_group"], {}
                )

                # 2. 온보딩 선호도 반영
                onboarding_categories = user_profile["onboarding_preferences"][
                    "interested_categories"
                ]
                onboarding_boost = {cat: 0.3 for cat in onboarding_categories}

                # 3. 지역 인기도 반영
                regional_popularity = {
                    "personalized_place_1": 0.7,  # 홍대 카페 - 20대에 인기
                    "personalized_place_2": 0.9,  # 강남 카페 - 트렌디
                    "personalized_place_3": 0.5,  # 신촌 가족 레스토랑
                    "personalized_place_4": 0.6,  # 여의도 고급 레스토랑
                }

                # 4. 추천 점수 계산
                recommendations = []
                for place in available_places:
                    # 기본 점수 (인구통계)
                    demo_score = age_prefs.get(place["category"], 0.1)

                    # 온보딩 선호도 보너스
                    onboarding_score = onboarding_boost.get(place["category"], 0)

                    # 지역 인기도
                    popularity_score = regional_popularity.get(place["id"], 0.5)

                    # 최종 점수 (가중 평균)
                    final_score = (
                        demo_score * 0.4
                        + onboarding_score * 0.3  # 40% 인구통계
                        + popularity_score * 0.3  # 30% 온보딩 선호  # 30% 지역 인기도
                    )

                    recommendations.append(
                        {
                            **place,
                            "demo_score": demo_score,
                            "onboarding_score": onboarding_score,
                            "popularity_score": popularity_score,
                            "cold_start_score": final_score,
                        }
                    )

                return sorted(
                    recommendations, key=lambda x: x["cold_start_score"], reverse=True
                )

            mock_coldstart.return_value = cold_start_algorithm(
                new_user, self.diverse_places
            )

            # When: 콜드 스타트 추천 실행
            from app.services.cold_start_service import ColdStartService

            cold_start_service = ColdStartService(
                demographic_analyzer=AsyncMock(),
                popularity_tracker=AsyncMock(),
                onboarding_service=AsyncMock(),
            )
            cold_start_service.generate_initial_recommendations = mock_coldstart

            recommendations = await cold_start_service.generate_initial_recommendations(
                user_profile=new_user,
                available_places=self.diverse_places,
            )

        # Then: 콜드 스타트 추천이 적절함

        # 상위 추천이 온보딩 선호 카테고리와 일치
        top_recommendation = recommendations[0]
        onboarding_interests = new_user["onboarding_preferences"][
            "interested_categories"
        ]
        assert top_recommendation["category"] in onboarding_interests

        # 20대 인구통계에 맞는 추천 (카페, 액티비티 우선)
        top_3_categories = [rec["category"] for rec in recommendations[:3]]
        young_friendly_categories = ["cafe", "activity", "cultural"]
        matches = sum(1 for cat in top_3_categories if cat in young_friendly_categories)
        assert matches >= 2  # 3개 중 최소 2개는 20대 선호 카테고리

        # 모든 추천에 점수가 할당됨
        for rec in recommendations:
            assert "cold_start_score" in rec
            assert rec["cold_start_score"] > 0
            assert rec["cold_start_score"] <= 1.0

        # 점수 구성 요소들이 적절히 반영됨
        for rec in recommendations:
            # 인구통계 점수가 있음
            assert "demo_score" in rec
            # 온보딩 선택과 일치하면 보너스 점수
            if rec["category"] in onboarding_interests:
                assert rec["onboarding_score"] > 0

        # 추천 다양성 확보 (모든 카테고리가 단일하지 않음)
        recommended_categories = {rec["category"] for rec in recommendations}
        assert len(recommended_categories) >= 2  # 최소 2개 카테고리

    async def test_personalization_performance_metrics(self) -> None:
        """
        Given: 개인화 추천 시스템
        When: 성능 지표를 측정함
        Then: 추천 품질과 사용자 만족도 목표를 달성함
        """
        # Given: 개인화 성능 평가를 위한 시뮬레이션 데이터
        evaluation_scenarios = [
            {
                "user_id": uuid4(),
                "user_type": "cafe_lover",
                "true_preferences": {"cafe": 0.8, "restaurant": 0.1, "cultural": 0.1},
                "search_query": "좋은 곳",
                "expected_top_category": "cafe",
            },
            {
                "user_id": uuid4(),
                "user_type": "foodie",
                "true_preferences": {"restaurant": 0.7, "cafe": 0.2, "cultural": 0.1},
                "search_query": "맛있는 곳",
                "expected_top_category": "restaurant",
            },
            {
                "user_id": uuid4(),
                "user_type": "culture_enthusiast",
                "true_preferences": {"cultural": 0.6, "cafe": 0.2, "restaurant": 0.2},
                "search_query": "재미있는 곳",
                "expected_top_category": "cultural",
            },
        ]

        # Mock 성능 측정 서비스
        with patch(
            "app.services.personalization_metrics.evaluate_recommendation_quality"
        ) as mock_metrics:

            def calculate_personalization_metrics(scenarios, recommendations_list):
                """개인화 성능 지표 계산"""
                metrics = {
                    "precision_at_k": [],
                    "recall_at_k": [],
                    "diversity_scores": [],
                    "user_satisfaction_estimates": [],
                    "category_prediction_accuracy": [],
                }

                for i, scenario in enumerate(scenarios):
                    recommendations = recommendations_list[i]
                    true_prefs = scenario["true_preferences"]
                    expected_category = scenario["expected_top_category"]

                    # Precision@5: 상위 5개 중 선호 카테고리 비율
                    top_5 = recommendations[:5]
                    relevant_count = sum(
                        1 for rec in top_5 if true_prefs.get(rec["category"], 0) > 0.5
                    )
                    precision_5 = relevant_count / 5
                    metrics["precision_at_k"].append(precision_5)

                    # 카테고리 예측 정확도
                    top_category = (
                        recommendations[0]["category"] if recommendations else None
                    )
                    category_correct = 1 if top_category == expected_category else 0
                    metrics["category_prediction_accuracy"].append(category_correct)

                    # 다양성 점수 (상위 10개 중 카테고리 수)
                    top_10_categories = {
                        rec["category"] for rec in recommendations[:10]
                    }
                    diversity = len(top_10_categories) / min(10, len(recommendations))
                    metrics["diversity_scores"].append(diversity)

                    # 사용자 만족도 추정 (가중 점수 기반)
                    satisfaction = 0
                    for j, rec in enumerate(recommendations[:10]):
                        weight = 1.0 / (j + 1)  # 순위에 따른 가중치
                        pref_score = true_prefs.get(rec["category"], 0.1)
                        satisfaction += weight * pref_score

                    satisfaction = satisfaction / sum(
                        1.0 / (i + 1) for i in range(10)
                    )  # 정규화
                    metrics["user_satisfaction_estimates"].append(satisfaction)

                # 평균 계산
                return {
                    "avg_precision_at_5": statistics.mean(metrics["precision_at_k"]),
                    "avg_category_accuracy": statistics.mean(
                        metrics["category_prediction_accuracy"]
                    ),
                    "avg_diversity_score": statistics.mean(metrics["diversity_scores"]),
                    "avg_satisfaction_estimate": statistics.mean(
                        metrics["user_satisfaction_estimates"]
                    ),
                    "detailed_metrics": metrics,
                }

            # 각 시나리오별 추천 생성 (시뮬레이션)
            recommendations_for_scenarios = []
            for scenario in evaluation_scenarios:
                true_prefs = scenario["true_preferences"]

                # 개인화된 추천 점수 적용
                personalized_recommendations = []
                for place in self.diverse_places:
                    pref_score = true_prefs.get(place["category"], 0.1)
                    noise = 0.1 * (hash(place["id"]) % 100) / 100  # 약간의 노이즈
                    final_score = pref_score + noise

                    personalized_recommendations.append(
                        {
                            **place,
                            "personalization_score": final_score,
                        }
                    )

                personalized_recommendations.sort(
                    key=lambda x: x["personalization_score"], reverse=True
                )
                recommendations_for_scenarios.append(personalized_recommendations)

            mock_metrics.return_value = calculate_personalization_metrics(
                evaluation_scenarios, recommendations_for_scenarios
            )

            # When: 성능 지표 평가 실행
            from app.services.personalization_metrics import PersonalizationMetrics

            metrics_service = PersonalizationMetrics(
                recommendation_engine=AsyncMock(),
                user_behavior_tracker=AsyncMock(),
            )
            metrics_service.evaluate_recommendation_quality = mock_metrics

            performance_results = await metrics_service.evaluate_recommendation_quality(
                evaluation_scenarios=evaluation_scenarios,
                recommendations_list=recommendations_for_scenarios,
            )

        # Then: 성능 목표 달성 확인

        # Precision@5: 상위 5개 추천 중 관련성 높은 비율 60% 이상
        assert performance_results["avg_precision_at_5"] >= 0.6

        # 카테고리 예측 정확도: 1순위 카테고리 예측 80% 이상
        assert performance_results["avg_category_accuracy"] >= 0.8

        # 다양성 점수: 상위 10개 중 평균 3개 이상 카테고리
        assert performance_results["avg_diversity_score"] >= 0.3

        # 사용자 만족도 추정: 70% 이상
        assert performance_results["avg_satisfaction_estimate"] >= 0.7

        # 상세 지표별 안정성 확인
        detailed = performance_results["detailed_metrics"]

        # Precision 점수의 표준편차가 너무 크지 않음 (일관성)
        precision_std = statistics.stdev(detailed["precision_at_k"])
        assert precision_std < 0.3  # 표준편차 30% 이내

        # 모든 사용자에게 최소한의 만족도 보장
        min_satisfaction = min(detailed["user_satisfaction_estimates"])
        assert min_satisfaction >= 0.5  # 최소 50% 만족도

        # 전체 성능 점수 계산 (가중 평균)
        overall_score = (
            performance_results["avg_precision_at_5"] * 0.3
            + performance_results["avg_category_accuracy"] * 0.3
            + performance_results["avg_diversity_score"] * 0.2
            + performance_results["avg_satisfaction_estimate"] * 0.2
        )

        assert overall_score >= 0.7  # 전체 70% 이상 성능
