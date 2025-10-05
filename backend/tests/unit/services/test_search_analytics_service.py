"""
검색 분석 서비스 테스트 코드 (Task 2-3-5)

TDD Red Phase: 검색 성능 분석 및 대시보드 데이터 제공 시스템 테스트
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.search.search_analytics_service import SearchAnalyticsService


class TestSearchAnalyticsService:
    """검색 분석 서비스 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_redis = AsyncMock()
        self.mock_db = Mock()

        # 테스트 분석 데이터
        self.sample_analytics_data = {
            "total_searches": 1250,
            "unique_users": 340,
            "avg_response_time": 185.5,
            "cache_hit_rate": 0.72,
            "popular_queries": [
                {"query": "홍대 맛집", "count": 89, "trend": "up"},
                {"query": "강남 카페", "count": 67, "trend": "stable"},
                {"query": "이태원 바", "count": 45, "trend": "down"},
            ],
        }

    async def test_search_performance_metrics_collection(self) -> None:
        """
        Given: 검색 서비스의 성능 데이터
        When: 성능 메트릭을 수집함
        Then: 응답시간, 처리량, 에러율 등을 정확히 측정함
        """
        # Given: 분석 서비스 초기화
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock performance data
        performance_samples = [
            {"response_time": 150, "cache_hit": True, "error": False},
            {"response_time": 220, "cache_hit": False, "error": False},
            {"response_time": 180, "cache_hit": True, "error": False},
            {"response_time": 0, "cache_hit": False, "error": True},
        ]

        # When: 성능 데이터 기록
        for sample in performance_samples:
            await analytics_service.record_search_performance(
                user_id=self.test_user_id,
                query="테스트 검색",
                response_time_ms=sample["response_time"],
                cache_hit=sample["cache_hit"],
                error_occurred=sample["error"],
                result_count=10,
            )

        # When: 성능 메트릭 계산
        metrics = await analytics_service.get_performance_metrics(time_period_hours=24)

        # Then: 정확한 성능 메트릭 반환
        assert "avg_response_time" in metrics
        assert "error_rate" in metrics
        assert "cache_hit_rate" in metrics
        assert "total_searches" in metrics
        assert "searches_per_hour" in metrics

        # 평균 응답시간 계산 (에러 제외)
        expected_avg = (150 + 220 + 180) / 3  # 183.33
        assert abs(metrics["avg_response_time"] - expected_avg) < 1.0

    async def test_search_trend_analysis(self) -> None:
        """
        Given: 시계열 검색 데이터
        When: 검색 트렌드를 분석함
        Then: 증가/감소/안정 트렌드를 식별함
        """
        # Given: 트렌드 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_trend_analysis=True,
        )

        # Mock time series data (최근 7일)
        trend_data = {
            "홍대 맛집": [15, 18, 22, 25, 28, 32, 35],  # 증가 트렌드
            "강남 카페": [20, 19, 21, 20, 22, 21, 20],  # 안정 트렌드
            "이태원 바": [30, 28, 25, 22, 20, 18, 15],  # 감소 트렌드
        }

        with patch.object(analytics_service, "_get_search_time_series") as mock_series:
            mock_series.return_value = trend_data

            # When: 트렌드 분석 수행
            trends = await analytics_service.analyze_search_trends(
                period_days=7, top_queries=10
            )

            # Then: 트렌드 분류 정확성 확인
            trend_dict = {item["query"]: item["trend"] for item in trends}

            assert trend_dict["홍대 맛집"] == "increasing"
            assert trend_dict["강남 카페"] == "stable"
            assert trend_dict["이태원 바"] == "decreasing"

            # 트렌드 강도 확인
            hongdae_item = next(item for item in trends if item["query"] == "홍대 맛집")
            assert hongdae_item["trend_strength"] > 0.5  # 강한 증가 트렌드

    async def test_user_engagement_analysis(self) -> None:
        """
        Given: 사용자 검색 및 상호작용 데이터
        When: 사용자 참여도를 분석함
        Then: 클릭률, 전환율, 세션 지속시간 등을 측정함
        """
        # Given: 참여도 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock user engagement data
        engagement_data = [
            {
                "user_id": str(uuid4()),
                "searches": 5,
                "clicks": 3,
                "bookmarks": 1,
                "visits": 1,
                "session_duration": 420,  # 7분
            },
            {
                "user_id": str(uuid4()),
                "searches": 8,
                "clicks": 6,
                "bookmarks": 2,
                "visits": 2,
                "session_duration": 680,  # 11분
            },
        ]

        with patch.object(
            analytics_service, "_get_user_engagement_data"
        ) as mock_engagement:
            mock_engagement.return_value = engagement_data

            # When: 참여도 분석
            engagement_metrics = await analytics_service.analyze_user_engagement(
                time_period_days=7
            )

            # Then: 참여도 메트릭 확인
            assert "avg_click_through_rate" in engagement_metrics
            assert "avg_conversion_rate" in engagement_metrics
            assert "avg_session_duration" in engagement_metrics
            assert "user_retention_rate" in engagement_metrics

            # 평균 클릭률 계산: (3+6)/(5+8) = 9/13 ≈ 0.69
            assert abs(engagement_metrics["avg_click_through_rate"] - 0.69) < 0.01

    async def test_search_result_quality_analysis(self) -> None:
        """
        Given: 검색 결과와 사용자 피드백
        When: 검색 품질을 분석함
        Then: 관련성, 만족도, 개선점을 제시함
        """
        # Given: 품질 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock quality metrics
        quality_data = [
            {
                "query": "홍대 맛집",
                "results_count": 15,
                "clicks": 8,
                "zero_results": False,
                "user_satisfaction": 4.2,
                "relevance_score": 0.85,
            },
            {
                "query": "특이한 검색어",
                "results_count": 0,
                "clicks": 0,
                "zero_results": True,
                "user_satisfaction": 1.0,
                "relevance_score": 0.0,
            },
        ]

        with patch.object(
            analytics_service, "_get_search_quality_data"
        ) as mock_quality:
            mock_quality.return_value = quality_data

            # When: 품질 분석
            quality_report = await analytics_service.analyze_search_quality(
                time_period_days=30
            )

            # Then: 품질 메트릭 확인
            assert "avg_relevance_score" in quality_report
            assert "zero_results_rate" in quality_report
            assert "user_satisfaction_score" in quality_report
            assert "improvement_suggestions" in quality_report

            # 제로 결과율: 1/2 = 50%
            assert quality_report["zero_results_rate"] == 0.5

            # 개선 제안 존재 확인
            assert len(quality_report["improvement_suggestions"]) > 0

    async def test_search_personalization_effectiveness(self) -> None:
        """
        Given: 개인화된 검색과 일반 검색의 비교 데이터
        When: 개인화 효과를 분석함
        Then: 개인화로 인한 성능 향상을 정량화함
        """
        # Given: 개인화 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_ab_testing=True,
        )

        # Mock A/B testing data
        ab_test_data = {
            "personalized_group": {
                "users": 500,
                "avg_click_rate": 0.75,
                "avg_conversion_rate": 0.42,
                "avg_session_duration": 380,
                "user_satisfaction": 4.3,
            },
            "control_group": {
                "users": 500,
                "avg_click_rate": 0.58,
                "avg_conversion_rate": 0.31,
                "avg_session_duration": 290,
                "user_satisfaction": 3.8,
            },
        }

        with patch.object(analytics_service, "_get_ab_test_data") as mock_ab:
            mock_ab.return_value = ab_test_data

            # When: 개인화 효과 분석
            personalization_report = (
                await analytics_service.analyze_personalization_effectiveness(
                    experiment_id="search_personalization_v2"
                )
            )

            # Then: 개인화 효과 확인
            assert "click_rate_improvement" in personalization_report
            assert "conversion_rate_improvement" in personalization_report
            assert "statistical_significance" in personalization_report

            # 클릭률 개선: (0.75 - 0.58) / 0.58 ≈ 0.29 (29% 개선)
            click_improvement = personalization_report["click_rate_improvement"]
            assert abs(click_improvement - 0.29) < 0.01

    async def test_search_anomaly_detection(self) -> None:
        """
        Given: 검색 패턴의 이상 데이터
        When: 이상 탐지를 수행함
        Then: 비정상적인 검색 패턴을 식별하고 알림함
        """
        # Given: 이상 탐지 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_anomaly_detection=True,
        )

        # Mock normal and anomalous patterns
        search_patterns = [
            {"timestamp": datetime.utcnow() - timedelta(hours=i), "count": 50 + i * 2}
            for i in range(24)  # 정상 패턴
        ]

        # 이상 패턴 추가 (갑작스러운 급증)
        search_patterns.append({"timestamp": datetime.utcnow(), "count": 500})  # 10배 급증

        with patch.object(
            analytics_service, "_get_hourly_search_counts"
        ) as mock_counts:
            mock_counts.return_value = search_patterns

            # When: 이상 탐지
            anomalies = await analytics_service.detect_search_anomalies(
                sensitivity=0.05  # 5% 임계값
            )

            # Then: 이상 패턴 탐지 확인
            assert len(anomalies) > 0
            latest_anomaly = anomalies[0]
            assert latest_anomaly["type"] == "sudden_spike"
            assert latest_anomaly["severity"] == "high"
            assert latest_anomaly["count"] == 500

    async def test_search_geography_analysis(self) -> None:
        """
        Given: 지역별 검색 데이터
        When: 지리적 검색 패턴을 분석함
        Then: 지역별 선호도와 트렌드를 파악함
        """
        # Given: 지리 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock geographic search data
        geo_data = [
            {"region": "강남구", "searches": 350, "popular_category": "cafe"},
            {"region": "마포구", "searches": 280, "popular_category": "restaurant"},
            {"region": "종로구", "searches": 220, "popular_category": "culture"},
        ]

        with patch.object(analytics_service, "_get_geographic_search_data") as mock_geo:
            mock_geo.return_value = geo_data

            # When: 지리적 분석
            geo_analysis = await analytics_service.analyze_geographic_patterns()

            # Then: 지역별 분석 결과 확인
            assert "top_regions" in geo_analysis
            assert "regional_preferences" in geo_analysis
            assert "geographic_trends" in geo_analysis

            # 상위 지역 확인
            top_region = geo_analysis["top_regions"][0]
            assert top_region["region"] == "강남구"
            assert top_region["searches"] == 350

    async def test_real_time_dashboard_data(self) -> None:
        """
        Given: 실시간 검색 활동
        When: 대시보드 데이터를 생성함
        Then: 실시간 메트릭과 시각화 데이터를 제공함
        """
        # Given: 실시간 대시보드 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            real_time_enabled=True,
        )

        # Mock real-time data
        self.mock_redis.get.return_value = json.dumps(
            {
                "current_active_users": 145,
                "searches_last_hour": 89,
                "avg_response_time": 167,
                "top_queries_now": ["홍대 맛집", "강남 카페", "명동 쇼핑"],
            }
        )

        # When: 실시간 대시보드 데이터 조회
        dashboard_data = await analytics_service.get_real_time_dashboard()

        # Then: 실시간 메트릭 확인
        assert "current_metrics" in dashboard_data
        assert "active_users" in dashboard_data["current_metrics"]
        assert "recent_activity" in dashboard_data
        assert "live_trends" in dashboard_data
        assert "system_health" in dashboard_data

        # 현재 활성 사용자 확인
        assert dashboard_data["current_metrics"]["active_users"] == 145

    async def test_search_conversion_funnel_analysis(self) -> None:
        """
        Given: 검색-클릭-방문-전환의 단계별 데이터
        When: 전환 퍼널을 분석함
        Then: 각 단계의 전환율과 이탈 지점을 파악함
        """
        # Given: 퍼널 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock funnel data
        funnel_data = {
            "searches": 1000,
            "clicks": 680,
            "detail_views": 420,
            "bookmarks": 250,
            "visits": 120,
        }

        with patch.object(
            analytics_service, "_get_conversion_funnel_data"
        ) as mock_funnel:
            mock_funnel.return_value = funnel_data

            # When: 퍼널 분석
            funnel_analysis = await analytics_service.analyze_conversion_funnel(
                time_period_days=30
            )

            # Then: 전환율 계산 확인
            assert "search_to_click_rate" in funnel_analysis
            assert "click_to_view_rate" in funnel_analysis
            assert "view_to_bookmark_rate" in funnel_analysis
            assert "bookmark_to_visit_rate" in funnel_analysis

            # 검색-클릭 전환율: 680/1000 = 68%
            assert funnel_analysis["search_to_click_rate"] == 0.68

    async def test_search_analytics_export(self) -> None:
        """
        Given: 분석 대시보드의 모든 메트릭
        When: 분석 데이터를 내보내기함
        Then: 구조화된 리포트를 생성함
        """
        # Given: 분석 내보내기 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # When: 분석 리포트 생성
        report = await analytics_service.generate_analytics_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            include_trends=True,
            include_user_segments=True,
            format="detailed",
        )

        # Then: 완전한 리포트 구조 확인
        assert "report_metadata" in report
        assert "executive_summary" in report
        assert "performance_metrics" in report
        assert "trend_analysis" in report
        assert "user_engagement" in report
        assert "search_quality" in report
        assert "recommendations" in report

        # 메타데이터 확인
        assert report["report_metadata"]["period_days"] == 30
        assert "generated_at" in report["report_metadata"]

    async def test_search_ab_test_analysis(self) -> None:
        """
        Given: A/B 테스트 실험 데이터
        When: 실험 결과를 분석함
        Then: 통계적 유의성과 비즈니스 임팩트를 측정함
        """
        # Given: A/B 테스트 분석 서비스
        analytics_service = SearchAnalyticsService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_ab_testing=True,
        )

        # Mock A/B test results
        experiment_data = {
            "experiment_id": "search_ui_redesign",
            "variant_a": {
                "users": 1000,
                "conversions": 180,
                "avg_engagement": 3.2,
                "revenue": 45000,
            },
            "variant_b": {
                "users": 1000,
                "conversions": 220,
                "avg_engagement": 3.8,
                "revenue": 55000,
            },
        }

        with patch.object(analytics_service, "_get_experiment_data") as mock_experiment:
            mock_experiment.return_value = experiment_data

            # When: A/B 테스트 결과 분석
            test_results = await analytics_service.analyze_ab_test(
                experiment_id="search_ui_redesign"
            )

            # Then: 통계적 분석 결과 확인
            assert "conversion_rate_a" in test_results
            assert "conversion_rate_b" in test_results
            assert "statistical_significance" in test_results
            assert "confidence_interval" in test_results
            assert "recommendation" in test_results

            # 전환율 계산: A=18%, B=22%
            assert test_results["conversion_rate_a"] == 0.18
            assert test_results["conversion_rate_b"] == 0.22
