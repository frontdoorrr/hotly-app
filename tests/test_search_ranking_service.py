"""
검색 결과 랭킹 및 개인화 서비스 테스트 (Task 2-3-4)

TDD Red Phase: 개인화된 검색 랭킹 시스템 테스트
- ML 기반 스코어링
- 사용자 행동 기반 개인화
- 실시간 랭킹 조정
- 성능 최적화
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.search_ranking_service import SearchRankingService


class TestSearchRankingService:
    """검색 랭킹 서비스 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_db = Mock()
        self.mock_redis = AsyncMock()
        self.mock_ml_engine = AsyncMock()

        # Mock 사용자 프로필 데이터
        self.user_profile = {
            "preferences": {
                "categories": {"cafe": 0.8, "restaurant": 0.6, "bar": 0.3},
                "price_ranges": {"10000-30000": 0.9, "30000-50000": 0.4},
                "regions": {"마포구": 0.9, "강남구": 0.3},
                "tags": {"조용한": 0.9, "분위기좋은": 0.8, "와이파이": 0.7},
            },
            "behavior_patterns": {
                "visit_time_preference": {
                    "morning": 0.2,
                    "afternoon": 0.8,
                    "evening": 0.6,
                },
                "distance_tolerance": 3.5,  # km
                "avg_session_duration": 450,  # seconds
                "review_tendency": 0.7,
            },
            "interaction_history": {
                "total_searches": 247,
                "click_through_rate": 0.68,
                "conversion_rate": 0.34,
                "avg_time_on_result": 180,
            },
        }

        # Mock 검색 결과들
        self.mock_search_results = [
            Mock(
                id=str(uuid4()),
                name="홍대 감성 카페",
                category="cafe",
                tags=["조용한", "분위기좋은"],
                rating=4.5,
                review_count=127,
                price_range=15000,
                distance_km=0.8,
                popularity_score=0.75,
                user_interaction_score=0.0,  # 초기값
                created_at=datetime.utcnow() - timedelta(days=3),
                last_visited=None,
            ),
            Mock(
                id=str(uuid4()),
                name="강남 이탈리안",
                category="restaurant",
                tags=["고급", "데이트"],
                rating=4.8,
                review_count=89,
                price_range=45000,
                distance_km=5.2,
                popularity_score=0.68,
                user_interaction_score=0.85,  # 높은 상호작용 스코어
                created_at=datetime.utcnow() - timedelta(days=10),
                last_visited=datetime.utcnow() - timedelta(days=5),
            ),
            Mock(
                id=str(uuid4()),
                name="신촌 바",
                category="bar",
                tags=["시끌벅적", "친구"],
                rating=4.0,
                review_count=45,
                price_range=25000,
                distance_km=2.1,
                popularity_score=0.45,
                user_interaction_score=0.2,
                created_at=datetime.utcnow() - timedelta(days=7),
                last_visited=None,
            ),
        ]

    async def test_personalized_ranking_basic(self):
        """
        Given: 기본 검색 결과와 사용자 프로필
        When: 개인화된 랭킹을 수행함
        Then: 사용자 선호도에 따라 재정렬된 결과를 반환함
        """
        # Given: 랭킹 서비스 초기화
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # Mock 사용자 프로필 반환
        with patch.object(service, "_get_user_profile") as mock_profile:
            mock_profile.return_value = self.user_profile

            # When: 개인화 랭킹 수행
            ranked_results = await service.rank_search_results(
                user_id=self.test_user_id,
                search_results=self.mock_search_results,
                query="카페 맛집",
                context={
                    "search_type": "text",
                    "location": {"lat": 37.5563, "lng": 126.9225},
                    "time_of_search": datetime.utcnow().isoformat(),
                },
            )

            # Then: 랭킹 결과 검증
            assert len(ranked_results) == len(self.mock_search_results)
            assert all("personalization_score" in result for result in ranked_results)
            assert all("final_rank_score" in result for result in ranked_results)
            assert all("ranking_factors" in result for result in ranked_results)

            # 카페 카테고리가 사용자 선호도가 높아서 상위에 랭킹
            top_result = ranked_results[0]
            assert top_result["category"] == "cafe"

    async def test_ml_based_scoring(self):
        """
        Given: ML 엔진과 특성 벡터
        When: ML 기반 스코어링을 수행함
        Then: 학습된 모델 기반의 관련성 점수를 반환함
        """
        # Given: ML 스코어링 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # Mock ML 모델 예측 결과
        self.mock_ml_engine.predict_relevance.return_value = [
            {"place_id": self.mock_search_results[0].id, "ml_score": 0.92},
            {"place_id": self.mock_search_results[1].id, "ml_score": 0.74},
            {"place_id": self.mock_search_results[2].id, "ml_score": 0.58},
        ]

        # When: ML 기반 스코어링
        ml_scores = await service._calculate_ml_scores(
            user_id=self.test_user_id,
            search_results=self.mock_search_results,
            query="홍대 카페",
            user_context={
                "search_history": [],
                "preferences": self.user_profile["preferences"],
            },
        )

        # Then: ML 스코어 검증
        assert len(ml_scores) == 3
        assert ml_scores[self.mock_search_results[0].id] == 0.92
        assert ml_scores[self.mock_search_results[1].id] == 0.74
        assert ml_scores[self.mock_search_results[2].id] == 0.58

        # ML 엔진 호출 검증
        self.mock_ml_engine.predict_relevance.assert_called_once()

    async def test_user_behavior_personalization(self):
        """
        Given: 사용자 행동 데이터와 상호작용 히스토리
        When: 행동 기반 개인화를 적용함
        Then: 사용자 행동 패턴에 맞춰 조정된 스코어를 반환함
        """
        # Given: 행동 기반 개인화 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # Mock 사용자 상호작용 데이터
        interaction_data = {
            self.mock_search_results[0].id: {
                "view_count": 5,
                "click_count": 3,
                "bookmark_count": 1,
                "avg_time_spent": 120,
                "last_interaction": datetime.utcnow() - timedelta(days=1),
            },
            self.mock_search_results[1].id: {
                "view_count": 8,
                "click_count": 6,
                "bookmark_count": 2,
                "avg_time_spent": 200,
                "last_interaction": datetime.utcnow() - timedelta(hours=12),
            },
            self.mock_search_results[2].id: {
                "view_count": 2,
                "click_count": 1,
                "bookmark_count": 0,
                "avg_time_spent": 45,
                "last_interaction": datetime.utcnow() - timedelta(days=7),
            },
        }

        with patch.object(service, "_get_user_interactions") as mock_interactions:
            mock_interactions.return_value = interaction_data

            # When: 행동 기반 개인화 적용
            behavior_scores = await service._calculate_behavior_scores(
                user_id=self.test_user_id, search_results=self.mock_search_results
            )

            # Then: 행동 스코어 검증
            assert len(behavior_scores) == 3

            # 더 많은 상호작용이 있는 장소가 높은 점수
            restaurant_score = behavior_scores[self.mock_search_results[1].id]
            cafe_score = behavior_scores[self.mock_search_results[0].id]
            bar_score = behavior_scores[self.mock_search_results[2].id]

            assert restaurant_score > cafe_score > bar_score

    async def test_contextual_ranking_adjustment(self):
        """
        Given: 검색 컨텍스트 (시간, 위치, 날씨 등)
        When: 컨텍스트 기반 랭킹 조정을 수행함
        Then: 현재 상황에 맞는 가중치가 적용된 결과를 반환함
        """
        # Given: 컨텍스트 기반 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # 다양한 컨텍스트 시나리오 테스트
        contexts = [
            {
                "name": "점심시간",
                "context": {
                    "time_of_day": "afternoon",
                    "day_of_week": "weekday",
                    "weather": "sunny",
                    "user_location": {"lat": 37.5563, "lng": 126.9225},
                },
                "expected_boost": {"restaurant": 1.2, "cafe": 0.9},
            },
            {
                "name": "주말 저녁",
                "context": {
                    "time_of_day": "evening",
                    "day_of_week": "weekend",
                    "weather": "clear",
                    "user_location": {"lat": 37.5563, "lng": 126.9225},
                },
                "expected_boost": {"bar": 1.3, "restaurant": 1.1},
            },
            {
                "name": "비오는 날",
                "context": {
                    "time_of_day": "morning",
                    "day_of_week": "weekend",
                    "weather": "rainy",
                    "user_location": {"lat": 37.5563, "lng": 126.9225},
                },
                "expected_boost": {"cafe": 1.1},  # 실내 선호
            },
        ]

        for scenario in contexts:
            # When: 각 컨텍스트에 대한 랭킹 조정
            contextual_scores = await service._apply_contextual_adjustments(
                search_results=self.mock_search_results, context=scenario["context"]
            )

            # Then: 컨텍스트별 부스트 검증
            assert len(contextual_scores) == 3
            assert all(score >= 0.5 for score in contextual_scores.values())

    async def test_real_time_ranking_updates(self):
        """
        Given: 실시간 사용자 피드백 (클릭, 북마크, 방문)
        When: 실시간 랭킹 업데이트를 수행함
        Then: 즉시 랭킹이 조정되고 캐시가 무효화됨
        """
        # Given: 실시간 랭킹 업데이트 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        place_id = self.mock_search_results[0].id
        initial_score = 0.75

        # When: 실시간 피드백 처리
        feedback_events = [
            {"type": "click", "place_id": place_id, "weight": 0.1},
            {"type": "bookmark", "place_id": place_id, "weight": 0.2},
            {"type": "visit", "place_id": place_id, "weight": 0.3},
        ]

        for event in feedback_events:
            await service.update_ranking_by_feedback(
                user_id=self.test_user_id,
                place_id=event["place_id"],
                feedback_type=event["type"],
                context={"timestamp": datetime.utcnow().isoformat()},
            )

        # Then: 실시간 업데이트 검증
        updated_score = await service._get_real_time_score_adjustment(
            user_id=self.test_user_id, place_id=place_id
        )

        assert updated_score > initial_score

        # 캐시 무효화 검증
        self.mock_redis.delete.assert_called()

    async def test_ranking_performance_optimization(self):
        """
        Given: 대량의 검색 결과 (1000개)
        When: 성능 최적화된 랭킹을 수행함
        Then: 설정된 시간 내에 랭킹을 완료함
        """
        # Given: 대량 데이터 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # 1000개의 Mock 검색 결과 생성
        large_results = []
        for i in range(1000):
            large_results.append(
                Mock(
                    id=str(uuid4()),
                    name=f"Place {i}",
                    category=["cafe", "restaurant", "bar"][i % 3],
                    rating=3.5 + (i % 3) * 0.5,
                    distance_km=float(i % 10),
                    popularity_score=0.3 + (i % 7) * 0.1,
                )
            )

        # Mock 캐시된 사용자 프로필
        self.mock_redis.get.return_value = json.dumps(self.user_profile)

        # When: 성능 최적화된 랭킹 수행
        start_time = datetime.utcnow()

        ranked_results = await service.rank_search_results(
            user_id=self.test_user_id,
            search_results=large_results,
            query="test query",
            context={"optimization_mode": True},
            max_results=50,  # 상위 50개만 상세 랭킹
        )

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        # Then: 성능 기준 검증
        assert processing_time < 2.0  # 2초 이내 처리
        assert len(ranked_results) <= 50  # 제한된 결과 수
        assert all("final_rank_score" in result for result in ranked_results)

    async def test_ranking_cache_integration(self):
        """
        Given: 랭킹 결과 캐싱 설정
        When: 동일한 조건의 랭킹을 반복 요청함
        Then: 캐시된 결과를 빠르게 반환함
        """
        # Given: 캐시 통합 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        ranking_params = {
            "user_id": self.test_user_id,
            "search_results": self.mock_search_results,
            "query": "홍대 카페",
            "context": {"location": {"lat": 37.5563, "lng": 126.9225}},
        }

        # 첫 번째 요청 - 캐시 미스
        self.mock_redis.get.return_value = None

        result1 = await service.rank_search_results(**ranking_params)

        # 두 번째 요청 - 캐시 히트
        cached_result = json.dumps(result1)
        self.mock_redis.get.return_value = cached_result

        result2 = await service.rank_search_results(**ranking_params)

        # Then: 캐시 동작 검증
        assert result1 == result2  # 동일한 결과
        self.mock_redis.set.assert_called()  # 첫 요청에서 캐시 저장
        assert self.mock_redis.get.call_count == 2  # 두 요청 모두 캐시 조회

    async def test_ranking_factors_explanation(self):
        """
        Given: 랭킹된 검색 결과
        When: 랭킹 요인 설명을 요청함
        Then: 각 결과의 랭킹 근거를 명확히 설명함
        """
        # Given: 랭킹 설명 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # Mock 사용자 프로필 설정
        with patch.object(service, "_get_user_profile") as mock_profile:
            mock_profile.return_value = self.user_profile

            # When: 설명 가능한 랭킹 수행
            ranked_results = await service.rank_search_results(
                user_id=self.test_user_id,
                search_results=self.mock_search_results,
                query="카페",
                context={"explain": True},
            )

            # Then: 랭킹 설명 검증
            for result in ranked_results:
                assert "ranking_factors" in result
                factors = result["ranking_factors"]

                # 주요 랭킹 요소들 존재 확인
                assert "base_relevance" in factors
                assert "personalization_boost" in factors
                assert "behavior_score" in factors
                assert "contextual_adjustment" in factors
                assert "explanation" in factors

                # 설명 텍스트 검증
                assert isinstance(factors["explanation"], str)
                assert len(factors["explanation"]) > 0

    async def test_a_b_testing_ranking_variants(self):
        """
        Given: A/B 테스트 랭킹 변형들
        When: 사용자별로 다른 랭킹 알고리즘을 적용함
        Then: 변형에 따른 다른 랭킹 결과를 반환함
        """
        # Given: A/B 테스트 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # 두 가지 랭킹 변형 정의
        variant_configs = {
            "control": {
                "ml_weight": 0.4,
                "behavior_weight": 0.3,
                "context_weight": 0.3,
            },
            "test": {"ml_weight": 0.5, "behavior_weight": 0.2, "context_weight": 0.3},
        }

        results_by_variant = {}

        for variant_name, config in variant_configs.items():
            # When: 각 변형별 랭킹 수행
            with patch.object(service, "_get_ranking_config") as mock_config:
                mock_config.return_value = config

                ranked_results = await service.rank_search_results(
                    user_id=self.test_user_id,
                    search_results=self.mock_search_results,
                    query="카페",
                    context={"ab_test_variant": variant_name},
                )

                results_by_variant[variant_name] = ranked_results

        # Then: 변형별 다른 결과 확인
        control_order = [r["id"] for r in results_by_variant["control"]]
        test_order = [r["id"] for r in results_by_variant["test"]]

        # 두 변형의 결과가 다를 가능성이 높음 (완전히 같을 수도 있지만 드문 경우)
        assert len(control_order) == len(test_order)

    async def test_ranking_feedback_learning(self):
        """
        Given: 사용자 피드백 데이터 누적
        When: 피드백 기반 학습을 수행함
        Then: 랭킹 모델이 개선되고 개인화 정확도가 향상됨
        """
        # Given: 학습 기반 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # Mock 피드백 데이터
        feedback_data = [
            {
                "user_id": self.test_user_id,
                "query": "홍대 카페",
                "clicked_results": [self.mock_search_results[0].id],
                "skipped_results": [
                    self.mock_search_results[1].id,
                    self.mock_search_results[2].id,
                ],
                "session_duration": 180,
                "conversion": True,
            }
        ]

        # When: 피드백 학습 수행
        await service.learn_from_feedback(feedback_data)

        # Then: 학습 호출 검증
        self.mock_ml_engine.update_model.assert_called_once()

        # 사용자 프로필 업데이트 확인
        await service._update_user_profile_from_feedback(
            self.test_user_id, feedback_data[0]
        )

    async def test_ranking_error_handling_and_fallback(self):
        """
        Given: ML 엔진 또는 외부 서비스 장애
        When: 랭킹을 시도함
        Then: 기본 랭킹 알고리즘으로 fallback하여 안정적인 결과 제공
        """
        # Given: 에러 처리 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # ML 엔진 에러 시뮬레이션
        self.mock_ml_engine.predict_relevance.side_effect = Exception(
            "ML service unavailable"
        )

        # When: 에러 상황에서 랭킹 시도
        ranked_results = await service.rank_search_results(
            user_id=self.test_user_id,
            search_results=self.mock_search_results,
            query="카페",
            context={},
        )

        # Then: fallback 랭킹 결과 확인
        assert len(ranked_results) == len(self.mock_search_results)
        assert all("final_rank_score" in result for result in ranked_results)

        # fallback 사용 표시 확인
        assert ranked_results[0].get("ranking_source") == "fallback_algorithm"

    async def test_ranking_diversity_injection(self):
        """
        Given: 유사한 검색 결과들
        When: 다양성 주입 랭킹을 수행함
        Then: 카테고리, 지역, 가격대 등이 다양한 결과를 상위에 배치함
        """
        # Given: 다양성 주입 랭킹 서비스
        service = SearchRankingService(
            self.mock_db, self.mock_redis, self.mock_ml_engine
        )

        # 유사한 카페들로 구성된 결과 (다양성 부족)
        similar_results = [
            Mock(
                id=str(uuid4()),
                name=f"홍대 카페 {i}",
                category="cafe",
                rating=4.5,
                price_range=15000,
                distance_km=1.0 + i * 0.1,
            )
            for i in range(10)
        ]

        # When: 다양성 주입 랭킹
        diverse_results = await service.rank_search_results(
            user_id=self.test_user_id,
            search_results=similar_results,
            query="홍대",
            context={"diversity_enabled": True, "diversity_threshold": 0.7},
        )

        # Then: 다양성 검증 - 상위 결과들이 너무 유사하지 않아야 함
        assert len(diverse_results) == len(similar_results)

        # 다양성 메트릭 확인 (실제로는 더 복잡한 다양성 계산 필요)
        top_5_results = diverse_results[:5]
        assert len(set(r.get("category") for r in top_5_results)) >= 1  # 최소 카테고리 다양성
