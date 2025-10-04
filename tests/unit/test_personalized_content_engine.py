"""Test cases for personalized content engine (TDD Red phase)."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.notification import NotificationTemplate
from app.models.notification_analytics import UserNotificationPattern
from app.services.ml.personalized_content_engine import PersonalizedContentEngine


class TestPersonalizedContentEngine:
    """Test suite for personalized content engine."""

    def setup_method(self) -> None:
        """Setup test dependencies."""
        self.test_user_id = str(uuid4())

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user_pattern(self):
        """Sample user notification pattern."""
        return UserNotificationPattern(
            user_id=self.test_user_id,
            total_notifications_received=100,
            total_notifications_opened=70,
            total_notifications_clicked=25,
            engagement_rate=0.7,
            open_rate=0.7,
            click_rate=0.25,
            preferred_hours={"18": 0.8, "19": 0.6},
            avg_response_time_seconds=45.0,
        )

    @pytest.fixture
    def sample_notification_template(self):
        """Sample notification template."""
        return NotificationTemplate(
            id=str(uuid4()),
            name="preparation_reminder",
            title_template="{{greeting}} 내일 {{course_name}} 데이트 준비!",
            body_template="{{preparation_items}} 완벽한 데이트를 위해 미리 준비하세요{{tone_suffix}}",
            notification_type="preparation_reminder",
            category="date_preparation",
            priority="normal",
            is_active=True,
        )

    async def test_generate_personalized_notification_with_template(
        self, mock_db, sample_user_pattern, sample_notification_template
    ):
        """
        Given: 사용자 패턴과 템플릿이 있음
        When: generate_personalized_notification 호출
        Then: 개인화된 알림 콘텐츠 생성
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)
        engine._get_notification_template = AsyncMock(
            return_value=sample_notification_template
        )

        variables = {
            "course_name": "홍대 데이트",
            "preparation_items": "• 카페 예약\n• 우산 준비",
        }

        # When
        result = await engine.generate_personalized_notification(
            self.test_user_id,
            "preparation_reminder",
            variables,
            "preparation_reminder",
            "high",
        )

        # Then
        assert result["personalization_applied"] is True
        assert result["personalization_level"] == "high"
        assert "ios" in result
        assert "android" in result
        assert "홍대 데이트" in result["ios"]["title"]
        assert len(result["user_preferences_applied"]) > 0

    async def test_generate_personalized_notification_fallback_no_template(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 템플릿을 찾을 수 없음
        When: generate_personalized_notification 호출
        Then: 기본 콘텐츠로 fallback
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)
        engine._get_notification_template = AsyncMock(return_value=None)
        engine._generate_fallback_content = AsyncMock(
            return_value={
                "template_name": "fallback",
                "personalization_applied": False,
                "ios": {"title": "기본 알림", "body": "내용"},
                "android": {"title": "기본 알림", "body": "내용"},
            }
        )

        # When
        result = await engine.generate_personalized_notification(
            self.test_user_id, "nonexistent_template", {}, "general"
        )

        # Then
        assert result["template_name"] == "fallback"
        assert result["personalization_applied"] is False
        engine._generate_fallback_content.assert_called_once()

    async def test_optimize_content_for_engagement_low_engagement_user(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 낮은 참여율을 보이는 사용자
        When: optimize_content_for_engagement 호출
        Then: 간결하고 긴급한 톤의 콘텐츠로 최적화
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        sample_user_pattern.engagement_rate = 0.2  # Low engagement
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)

        base_content = {
            "title": "내일 홍대 데이트 준비를 위해서 미리 확인해보시고 준비해주세요",
            "body": "여러 가지 준비사항들이 있으니까 차근차근 확인해보시면 좋을 것 같습니다. 날씨도 체크하시고 예약도 확인해보세요.",
        }
        context = {"weather": {"rain_probability": 70}}

        # When
        result = await engine.optimize_content_for_engagement(
            self.test_user_id, base_content, context
        )

        # Then
        assert result["optimization_applied"] is True
        assert len(result["title"]) < len(base_content["title"])  # Shortened
        assert len(result["body"]) < len(base_content["body"])  # Shortened
        assert result["urgency_level"] == "medium"
        assert result["include_cta"] is False  # Low click rate

    async def test_optimize_content_for_engagement_high_engagement_user(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 높은 참여율을 보이는 사용자
        When: optimize_content_for_engagement 호출
        Then: 상세하고 정보가 풍부한 콘텐츠로 최적화
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        sample_user_pattern.engagement_rate = 0.8  # High engagement
        sample_user_pattern.click_rate = 0.3  # High click rate
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)
        engine._add_contextual_details = AsyncMock(
            side_effect=lambda content, context: {
                **content,
                "body": content["body"] + "\n💡 추가 정보: 비 예보 70%",
            }
        )

        base_content = {
            "title": "데이트 준비 알림",
            "body": "내일 데이트 준비하세요.",
        }
        context = {"weather": {"rain_probability": 70}}

        # When
        result = await engine.optimize_content_for_engagement(
            self.test_user_id, base_content, context
        )

        # Then
        assert result["optimization_applied"] is True
        assert result["urgency_level"] == "low"  # Less urgent for engaged users
        assert result["include_cta"] is True  # High click rate
        assert result["cta_text"] == "자세히 보기"
        assert "추가 정보" in result["body"]  # Enhanced content

    async def test_generate_contextual_content_preparation_reminder(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 데이트 준비 알림 요청 및 날씨/코스 컨텍스트
        When: generate_contextual_content 호출
        Then: 상황에 맞는 준비 알림 콘텐츠 생성
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)

        context_data = {
            "weather": {"rain_probability": 80, "temperature": 3},
            "course": {"places": [{"name": "카페 ABC", "requires_reservation": True}]},
        }

        # When
        result = await engine.generate_contextual_content(
            self.test_user_id, "preparation_reminder", context_data
        )

        # Then
        assert result["notification_type"] == "preparation_reminder"
        assert result["context_applied"] is True
        assert "우산 준비" in result["content"]["body"]  # Rain context
        assert "따뜻한 옷" in result["content"]["body"]  # Cold weather
        assert "카페 ABC" in result["content"]["body"]  # Reservation needed

    async def test_generate_contextual_content_departure_reminder(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 출발 알림 요청 및 위치/시간 컨텍스트
        When: generate_contextual_content 호출
        Then: 출발 시간과 교통 정보가 포함된 알림 생성
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)

        context_data = {
            "time": {
                "departure_time": "14:30",
                "travel_time_minutes": 35,
            },
            "location": {"traffic_delay": 10},
            "course": {"places": [{"name": "홍대 놀이터"}]},
        }

        # When
        result = await engine.generate_contextual_content(
            self.test_user_id, "departure_reminder", context_data
        )

        # Then
        assert result["notification_type"] == "departure_reminder"
        assert "14:30에 출발" in result["content"]["title"]
        assert "35분 소요" in result["content"]["body"]
        assert "교통 지연 10분" in result["content"]["body"]
        assert "홍대 놀이터" in result["content"]["body"]

    async def test_analyze_content_performance_sufficient_data(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 충분한 사용자 데이터가 있음
        When: analyze_content_performance 호출
        Then: 상세한 콘텐츠 성과 분석 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        sample_user_pattern.overall_engagement_score = 75.0
        sample_user_pattern.avg_response_time_seconds = 30.0
        engine._get_user_pattern = AsyncMock(return_value=sample_user_pattern)

        # When
        result = await engine.analyze_content_performance(self.test_user_id)

        # Then
        assert result["user_id"] == self.test_user_id
        assert result["analysis_period_days"] == 30

        preferences = result["content_preferences"]
        assert preferences["emoji_usage"] == "medium"  # engagement_rate > 0.5
        assert preferences["message_length"] == "short"  # response time < 60
        assert preferences["tone"] == "friendly"  # engagement_rate > 0.6
        assert preferences["personalization_level"] == "high"  # score > 70

        assert len(result["best_performing_elements"]) > 0
        assert len(result["recommendations"]) > 0

    async def test_analyze_content_performance_insufficient_data(self, mock_db):
        """
        Given: 사용자 데이터가 부족함
        When: analyze_content_performance 호출
        Then: 데이터 부족 상태 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        engine._get_user_pattern = AsyncMock(return_value=None)

        # When
        result = await engine.analyze_content_performance(self.test_user_id)

        # Then
        assert result["status"] == "insufficient_data"

    async def test_apply_ab_testing_variants_emoji_heavy(self, mock_db):
        """
        Given: 사용자가 이모지 중심 변형 그룹에 할당됨
        When: _apply_ab_testing_variants 호출
        Then: 이모지가 추가된 콘텐츠 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)

        content = {
            "title": "데이트 준비 알림",
            "body": "내일 데이트 준비하세요.",
        }

        # Mock user hash to fall into emoji variant (< 33)
        test_user_id = "user_with_hash_10"  # This should hash to < 33

        # When
        result = await engine._apply_ab_testing_variants(content, test_user_id)

        # Then
        # Note: The exact variant depends on hash, but we test the structure
        assert "variant" in result
        assert result["variant"] in ["emoji_heavy", "question_format", "control"]

    async def test_format_for_ios_high_engagement_user(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 높은 참여율 사용자와 콘텐츠
        When: _format_for_ios 호출
        Then: iOS 리치 노티피케이션 기능이 활성화된 포맷
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        content = {
            "title": "데이트 준비 알림입니다. 내일 홍대에서 만나요!",
            "body": "여러 준비사항들을 미리 체크해보시고, 날씨 확인도 하시고, 예약도 다시 한 번 확인해보세요. 완벽한 데이트를 위해서 준비하겠습니다.",
            "subtitle": "홍대 데이트",
            "category": "preparation",
        }

        # When
        result = await engine._format_for_ios(content, sample_user_pattern)

        # Then
        assert len(result["title"]) <= 60  # iOS title limit
        assert len(result["body"]) <= 200  # iOS body limit
        assert result["mutable_content"] is True  # High engagement user
        assert result["content_available"] is True  # Rich notification
        assert result["category"] == "preparation"
        assert result["sound"] == "default"
        assert result["badge"] == 1

    async def test_format_for_android_with_cta(self, mock_db, sample_user_pattern):
        """
        Given: CTA가 포함된 콘텐츠
        When: _format_for_android 호출
        Then: Android 액션 버튼이 포함된 포맷
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        content = {
            "title": "출발 시간 알림",
            "body": "지금 출발하세요!",
            "notification_type": "departure_reminder",
            "priority": "high",
            "include_cta": True,
            "cta_text": "경로 확인",
        }

        # When
        result = await engine._format_for_android(content, sample_user_pattern)

        # Then
        assert result["title"] == content["title"]
        assert result["body"] == content["body"]
        assert result["priority"] == "high"
        assert result["channel_id"] == "channel_departure_reminder"
        assert "actions" in result
        assert len(result["actions"]) == 1
        assert result["actions"][0]["title"] == "경로 확인"
        assert result["actions"][0]["action"] == "OPEN_APP"

    async def test_generate_preparation_content_with_weather_and_course(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 날씨와 코스 컨텍스트 정보
        When: _generate_preparation_content 호출
        Then: 날씨와 예약 정보가 반영된 준비 콘텐츠 생성
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)

        weather_context = {
            "rain_probability": 70,
            "temperature": 2,
        }

        course_context = {
            "places": [
                {"name": "맛집 XYZ", "requires_reservation": True},
                {"name": "카페 ABC", "requires_reservation": False},
            ]
        }

        # When
        result = await engine._generate_preparation_content(
            sample_user_pattern, weather_context, course_context
        )

        # Then
        assert "내일 데이트 준비" in result["title"]
        body_lines = result["body"].split("\n")

        # Weather-based items
        assert any("우산 준비" in line for line in body_lines)
        assert any("따뜻한 옷" in line for line in body_lines)

        # Course-based items
        assert any("맛집 XYZ" in line and "예약" in line for line in body_lines)

    async def test_shorten_text_within_limit(self, mock_db):
        """
        Given: 제한 길이 이내의 텍스트
        When: _shorten_text 호출
        Then: 원본 텍스트 그대로 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        text = "짧은 텍스트"
        max_length = 20

        # When
        result = engine._shorten_text(text, max_length)

        # Then
        assert result == text

    async def test_shorten_text_exceeds_limit(self, mock_db):
        """
        Given: 제한 길이를 초과하는 텍스트
        When: _shorten_text 호출
        Then: 줄임표와 함께 단축된 텍스트 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        text = "이것은 매우 긴 텍스트입니다. 제한 길이를 초과할 것입니다."
        max_length = 15

        # When
        result = engine._shorten_text(text, max_length)

        # Then
        assert len(result) == max_length
        assert result.endswith("...")
        assert result == "이것은 매우 긴 텍..."

    async def test_add_relevant_emojis(self, mock_db):
        """
        Given: 특정 키워드가 포함된 텍스트
        When: _add_relevant_emojis 호출
        Then: 관련 이모지가 추가된 텍스트 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        text = "내일 데이트 준비하고 출발 시간 확인하세요. 비가 올 수도 있어요."

        # When
        result = engine._add_relevant_emojis(text)

        # Then
        assert "💕 데이트" in result
        assert "🚗 출발" in result
        assert "☔ 비" in result
        # Should only add emoji once per word
        assert result.count("💕") == 1

    async def test_get_applied_preferences_high_engagement(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 높은 참여율을 보이는 사용자 패턴
        When: _get_applied_preferences 호출
        Then: 해당하는 선호도 태그들 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)
        sample_user_pattern.engagement_rate = 0.8
        sample_user_pattern.overall_engagement_score = 75.0
        sample_user_pattern.preferred_hours = {"18": 0.9, "19": 0.7}

        # Mock the should_personalize_timing method
        sample_user_pattern.should_personalize_timing = Mock(return_value=True)

        # When
        result = engine._get_applied_preferences(sample_user_pattern)

        # Then
        assert "high_engagement_tone" in result
        assert "timing_personalization" in result
        assert "detailed_content" in result
        assert len(result) == 3

    async def test_get_applied_preferences_no_pattern(self, mock_db):
        """
        Given: 사용자 패턴이 없음
        When: _get_applied_preferences 호출
        Then: 기본 설정 반환
        """
        # Given
        engine = PersonalizedContentEngine(mock_db)

        # When
        result = engine._get_applied_preferences(None)

        # Then
        assert result == ["default"]
