"""Test cases for A/B testing service (TDD Red phase)."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.notification_analytics import (
    ABTestCohort,
    InteractionType,
    NotificationInteraction,
    NotificationLog,
    UserABTestAssignment,
)
from app.services.ab_testing_service import ABTestingService


class TestABTestingService:
    """Test suite for A/B testing service."""

    def setup_method(self):
        """Setup test dependencies."""
        self.test_user_id = str(uuid4())
        self.test_name = "notification_timing_test"

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_variants(self):
        """Sample A/B test variants."""
        return [
            {"type": "control", "timing_adjustment": 0},  # Control
            {"type": "optimized", "timing_adjustment": -30},  # 30 min earlier
            {"type": "personalized", "timing_adjustment": "ml_based"},  # ML-based
        ]

    async def test_create_notification_ab_test_success(self, mock_db, sample_variants):
        """
        Given: 유효한 테스트 설정과 변형들
        When: create_notification_ab_test 호출
        Then: A/B 테스트 코호트들이 생성됨
        """
        # Given
        service = ABTestingService(mock_db)
        test_description = "Testing notification timing optimization"
        traffic_split = [0.4, 0.3, 0.3]  # Control gets more traffic

        # When
        cohorts = await service.create_notification_ab_test(
            self.test_name, test_description, sample_variants, traffic_split
        )

        # Then
        assert len(cohorts) == 3
        assert cohorts[0].is_control is True  # First variant is control
        assert cohorts[1].is_control is False
        assert cohorts[2].is_control is False
        assert cohorts[0].traffic_allocation == 0.4
        assert cohorts[1].traffic_allocation == 0.3
        assert cohorts[2].traffic_allocation == 0.3
        mock_db.commit.assert_called_once()

    async def test_create_notification_ab_test_invalid_traffic_split(
        self, mock_db, sample_variants
    ):
        """
        Given: 트래픽 분할 비율이 1.0을 초과함
        When: create_notification_ab_test 호출
        Then: ValueError 발생
        """
        # Given
        service = ABTestingService(mock_db)
        invalid_traffic_split = [0.6, 0.3, 0.3]  # Sums to 1.2

        # When & Then
        with pytest.raises(ValueError, match="Traffic split must sum to 1.0"):
            await service.create_notification_ab_test(
                self.test_name, "Test", sample_variants, invalid_traffic_split
            )

    async def test_assign_user_to_test_new_assignment(self, mock_db):
        """
        Given: 사용자가 아직 테스트에 할당되지 않음
        When: assign_user_to_test 호출
        Then: 사용자를 결정론적으로 코호트에 할당
        """
        # Given
        service = ABTestingService(mock_db)

        # Mock existing assignment query (no existing assignment)
        mock_query_assignment = Mock()
        mock_query_assignment.join.return_value.filter.return_value.first.return_value = (
            None
        )

        # Mock cohorts query
        mock_cohorts = [
            Mock(
                id=str(uuid4()),
                cohort_name="test_variant_A",
                traffic_allocation=0.5,
                is_active=True,
            ),
            Mock(
                id=str(uuid4()),
                cohort_name="test_variant_B",
                traffic_allocation=0.5,
                is_active=True,
            ),
        ]
        mock_query_cohorts = Mock()
        mock_query_cohorts.filter.return_value.all.return_value = mock_cohorts

        def query_side_effect(*args):
            if args[0] == UserABTestAssignment:
                return mock_query_assignment
            elif args[0] == ABTestCohort:
                return mock_query_cohorts

        mock_db.query.side_effect = query_side_effect

        # When
        assignment = await service.assign_user_to_test(
            self.test_user_id, self.test_name
        )

        # Then
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert assignment.user_id == self.test_user_id
        assert assignment.assignment_method == "deterministic_hash"

    async def test_assign_user_to_test_existing_assignment(self, mock_db):
        """
        Given: 사용자가 이미 테스트에 할당됨
        When: assign_user_to_test 호출
        Then: 기존 할당을 반환
        """
        # Given
        service = ABTestingService(mock_db)
        existing_assignment = Mock(
            user_id=self.test_user_id,
            cohort_id=str(uuid4()),
            assignment_method="deterministic_hash",
        )

        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.first.return_value = (
            existing_assignment
        )
        mock_db.query.return_value = mock_query

        # When
        result = await service.assign_user_to_test(self.test_user_id, self.test_name)

        # Then
        assert result == existing_assignment
        mock_db.add.assert_not_called()  # Should not create new assignment

    async def test_get_user_test_variant_with_assignment(self, mock_db):
        """
        Given: 사용자가 A/B 테스트에 할당됨
        When: get_user_test_variant 호출
        Then: 사용자의 변형 설정 반환
        """
        # Given
        service = ABTestingService(mock_db)
        mock_cohort = Mock(
            cohort_name="test_variant_B",
            variant_config={"timing_adjustment": -30},
            is_control=False,
        )
        mock_assignment = Mock(
            cohort=mock_cohort,
            assigned_at=datetime.utcnow(),
        )

        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.first.return_value = (
            mock_assignment
        )
        mock_db.query.return_value = mock_query

        # When
        variant = await service.get_user_test_variant(self.test_user_id, self.test_name)

        # Then
        assert variant["cohort_name"] == "test_variant_B"
        assert variant["variant_config"]["timing_adjustment"] == -30
        assert variant["is_control"] is False

    async def test_get_user_test_variant_no_assignment(self, mock_db):
        """
        Given: 사용자가 테스트에 할당되지 않음
        When: get_user_test_variant 호출
        Then: 자동으로 할당하고 변형 설정 반환
        """
        # Given
        service = ABTestingService(mock_db)
        service.assign_user_to_test = AsyncMock(
            return_value=Mock(
                cohort=Mock(
                    cohort_name="test_variant_A",
                    variant_config={"type": "control"},
                    is_control=True,
                ),
                assigned_at=datetime.utcnow(),
            )
        )

        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # When
        variant = await service.get_user_test_variant(self.test_user_id, self.test_name)

        # Then
        service.assign_user_to_test.assert_called_once_with(
            self.test_user_id, self.test_name
        )
        assert variant["cohort_name"] == "test_variant_A"
        assert variant["is_control"] is True

    async def test_analyze_ab_test_results_with_data(self, mock_db):
        """
        Given: A/B 테스트에 충분한 사용자 데이터가 있음
        When: analyze_ab_test_results 호출
        Then: 상세한 분석 결과 반환
        """
        # Given
        service = ABTestingService(mock_db)

        # Mock cohorts
        mock_cohorts = [
            Mock(id="cohort1", cohort_name="control", is_control=True),
            Mock(id="cohort2", cohort_name="treatment", is_control=False),
        ]

        # Mock assignments
        mock_assignments = [
            [Mock(user_id="user1"), Mock(user_id="user2")],  # Control group
            [Mock(user_id="user3"), Mock(user_id="user4")],  # Treatment group
        ]

        # Mock notification logs
        mock_logs = [
            [Mock(id="log1"), Mock(id="log2")],  # Control logs
            [Mock(id="log3"), Mock(id="log4")],  # Treatment logs
        ]

        # Mock interactions
        mock_interactions = [
            [Mock(interaction_type=InteractionType.OPENED)],  # Control: 1 open out of 2
            [
                Mock(interaction_type=InteractionType.OPENED),
                Mock(interaction_type=InteractionType.CLICKED),
            ],  # Treatment: 2 interactions out of 2
        ]

        def setup_queries(*args):
            if args[0] == ABTestCohort:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=mock_cohorts)))
                )
            elif args[0] == UserABTestAssignment:
                call_count = getattr(setup_queries, "assignment_call_count", 0)
                setup_queries.assignment_call_count = call_count + 1
                return Mock(
                    filter=Mock(
                        return_value=Mock(
                            all=Mock(return_value=mock_assignments[call_count % 2])
                        )
                    )
                )
            elif args[0] == NotificationLog:
                call_count = getattr(setup_queries, "log_call_count", 0)
                setup_queries.log_call_count = call_count + 1
                return Mock(
                    filter=Mock(
                        return_value=Mock(
                            all=Mock(return_value=mock_logs[call_count % 2])
                        )
                    )
                )
            elif args[0] == NotificationInteraction:
                call_count = getattr(setup_queries, "interaction_call_count", 0)
                setup_queries.interaction_call_count = call_count + 1
                return Mock(
                    filter=Mock(
                        return_value=Mock(
                            all=Mock(return_value=mock_interactions[call_count % 2])
                        )
                    )
                )

        mock_db.query.side_effect = setup_queries

        service._calculate_statistical_significance = AsyncMock(
            return_value={
                "has_significance": True,
                "results": {"treatment": {"is_significant": True, "lift": 0.5}},
            }
        )
        service._determine_test_winner = AsyncMock(return_value="treatment")

        # When
        results = await service.analyze_ab_test_results(self.test_name, 30)

        # Then
        assert results.test_name == self.test_name
        assert len(results.cohort_results) == 2
        assert results.winner == "treatment"
        assert results.statistical_significance["has_significance"] is True

    async def test_end_ab_test_success(self, mock_db):
        """
        Given: 활성 A/B 테스트가 있음
        When: end_ab_test 호출 with 승자 지정
        Then: 테스트가 종료되고 승자가 마킹됨
        """
        # Given
        service = ABTestingService(mock_db)
        winner_cohort = "test_variant_B"

        mock_cohorts = [
            Mock(cohort_name="test_variant_A", is_active=True),
            Mock(cohort_name="test_variant_B", is_active=True),
        ]

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_cohorts
        mock_db.query.return_value = mock_query

        # When
        success = await service.end_ab_test(self.test_name, winner_cohort)

        # Then
        assert success is True
        # All cohorts should be marked inactive
        for cohort in mock_cohorts:
            assert cohort.is_active is False
            assert cohort.ended_at is not None

        # Winner should be marked
        assert mock_cohorts[1].is_winner is True
        assert (
            not hasattr(mock_cohorts[0], "is_winner")
            or mock_cohorts[0].is_winner is not True
        )
        mock_db.commit.assert_called_once()

    async def test_get_active_tests_for_user(self, mock_db):
        """
        Given: 사용자가 여러 활성 A/B 테스트에 참여 중
        When: get_active_tests_for_user 호출
        Then: 활성 테스트 목록 반환
        """
        # Given
        service = ABTestingService(mock_db)

        mock_assignments = [
            Mock(
                cohort=Mock(
                    test_name="timing_test",
                    cohort_name="timing_variant_A",
                    variant_config={"timing_adjustment": 0},
                    is_control=True,
                ),
                assigned_at=datetime.utcnow(),
            ),
            Mock(
                cohort=Mock(
                    test_name="content_test",
                    cohort_name="content_variant_B",
                    variant_config={"emoji_usage": "high"},
                    is_control=False,
                ),
                assigned_at=datetime.utcnow(),
            ),
        ]

        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = (
            mock_assignments
        )
        mock_db.query.return_value = mock_query

        # When
        active_tests = await service.get_active_tests_for_user(self.test_user_id)

        # Then
        assert len(active_tests) == 2
        assert active_tests[0]["test_name"] == "timing_test"
        assert active_tests[1]["test_name"] == "content_test"
        assert active_tests[0]["is_control"] is True
        assert active_tests[1]["is_control"] is False

    @patch("app.services.ab_testing_service.chi2_contingency")
    @patch("app.services.ab_testing_service.np")
    async def test_calculate_statistical_significance_with_scipy(
        self, mock_np, mock_chi2, mock_db
    ):
        """
        Given: scipy가 사용 가능하고 충분한 데이터가 있음
        When: _calculate_statistical_significance 호출
        Then: 통계적 유의성 결과 계산
        """
        # Given
        service = ABTestingService(mock_db)

        control_metrics = {
            "total_opens": 50,
            "total_clicks": 20,
            "total_notifications": 100,
            "engagement_rate": 0.7,
        }

        cohort_results = [
            {
                "cohort_name": "control",
                "is_control": True,
                "metrics": control_metrics,
            },
            {
                "cohort_name": "treatment",
                "is_control": False,
                "metrics": {
                    "total_opens": 60,
                    "total_clicks": 30,
                    "total_notifications": 100,
                    "engagement_rate": 0.9,
                },
            },
        ]

        # Mock scipy functions
        mock_chi2.return_value = (
            5.23,
            0.02,
            1,
            [[45, 25], [55, 35]],
        )  # Significant result
        mock_np.array.return_value = [[50, 30], [60, 30]]

        # When
        with patch(
            "app.services.ab_testing_service.scipy.stats.chi2_contingency", mock_chi2
        ):
            with patch("app.services.ab_testing_service.np.array", mock_np.array):
                results = await service._calculate_statistical_significance(
                    cohort_results, control_metrics
                )

        # Then
        assert results["has_significance"] is True
        assert "treatment" in results["results"]
        assert results["results"]["treatment"]["is_significant"] is True
        assert results["results"]["treatment"]["p_value"] == 0.02
        assert results["results"]["treatment"]["lift"] > 0  # Treatment performs better

    async def test_calculate_statistical_significance_no_scipy(self, mock_db):
        """
        Given: scipy가 사용 불가능함
        When: _calculate_statistical_significance 호출
        Then: 통계 라이브러리 미사용 결과 반환
        """
        # Given
        service = ABTestingService(mock_db)

        with patch("app.services.ab_testing_service.scipy", side_effect=ImportError):
            # When
            results = await service._calculate_statistical_significance([], {})

            # Then
            assert results["has_significance"] is False
            assert results["reason"] == "Statistical library not available"

    async def test_determine_test_winner_with_significance(self, mock_db):
        """
        Given: 통계적으로 유의한 결과가 있음
        When: _determine_test_winner 호출
        Then: 최고 성능의 통계적으로 유의한 변형을 승자로 선택
        """
        # Given
        service = ABTestingService(mock_db)

        cohort_results = [
            {
                "cohort_name": "control",
                "is_control": True,
                "metrics": {"engagement_rate": 0.6},
            },
            {
                "cohort_name": "treatment_a",
                "is_control": False,
                "metrics": {"engagement_rate": 0.7},
            },
            {
                "cohort_name": "treatment_b",
                "is_control": False,
                "metrics": {"engagement_rate": 0.8},
            },
        ]

        statistical_results = {
            "has_significance": True,
            "results": {
                "treatment_a": {"is_significant": True},
                "treatment_b": {"is_significant": True},
            },
        }

        # When
        winner = await service._determine_test_winner(
            cohort_results, statistical_results
        )

        # Then
        assert winner == "treatment_b"  # Highest engagement rate

    async def test_determine_test_winner_no_significance(self, mock_db):
        """
        Given: 통계적으로 유의하지 않은 결과
        When: _determine_test_winner 호출
        Then: 승자 없음 반환
        """
        # Given
        service = ABTestingService(mock_db)

        cohort_results = [
            {
                "cohort_name": "control",
                "is_control": True,
                "metrics": {"engagement_rate": 0.6},
            },
            {
                "cohort_name": "treatment",
                "is_control": False,
                "metrics": {"engagement_rate": 0.65},
            },
        ]

        statistical_results = {"has_significance": False}

        # When
        winner = await service._determine_test_winner(
            cohort_results, statistical_results
        )

        # Then
        assert winner is None
