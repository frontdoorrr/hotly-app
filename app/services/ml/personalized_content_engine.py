"""Personalized notification content generation engine."""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import BaseLoader, Environment, Template
from sqlalchemy.orm import Session

from app.models.notification import NotificationTemplate
from app.models.notification_analytics import UserNotificationPattern

logger = logging.getLogger(__name__)


class PersonalizedContentEngine:
    """Engine for generating personalized notification content."""

    def __init__(self, db: Session) -> None:
        self.db: Session = db
        self.jinja_env = Environment(loader=BaseLoader(), autoescape=True)

        # Content personalization templates
        self.personalization_templates = {
            "greeting": {
                "morning": ["좋은 아침이에요!", "상쾌한 아침입니다!", "새로운 하루의 시작이네요!"],
                "afternoon": ["안녕하세요!", "좋은 오후입니다!", "반가워요!"],
                "evening": ["안녕하세요!", "좋은 저녁이에요!", "오늘도 수고 많으셨어요!"],
            },
            "tone": {
                "casual": {"suffix": "이에요", "emoji_density": "high"},
                "friendly": {"suffix": "입니다", "emoji_density": "medium"},
                "formal": {"suffix": "습니다", "emoji_density": "low"},
            },
            "urgency": {
                "low": {"prefix": "💡 ", "words": ["참고로", "확인해보세요"]},
                "medium": {"prefix": "⚠️ ", "words": ["알려드려요", "확인이 필요해요"]},
                "high": {"prefix": "🚨 ", "words": ["긴급", "즉시 확인"]},
            },
        }

    async def generate_personalized_notification(
        self,
        user_id: str,
        template_name: str,
        variables: Dict[str, Any],
        notification_type: str = "general",
        personalization_level: str = "medium",
    ) -> Dict[str, Any]:
        """개인화된 알림 콘텐츠 생성."""
        try:
            # Get user pattern for personalization
            user_pattern = await self._get_user_pattern(user_id)

            # Get base template
            base_template = await self._get_notification_template(template_name)
            if not base_template:
                return await self._generate_fallback_content(
                    variables, notification_type
                )

            # Apply personalization
            personalized_content = await self._apply_personalization(
                base_template,
                variables,
                user_pattern,
                notification_type,
                personalization_level,
            )

            # Generate platform-specific content
            ios_content = await self._format_for_ios(personalized_content, user_pattern)
            android_content = await self._format_for_android(
                personalized_content, user_pattern
            )

            return {
                "template_name": template_name,
                "personalization_applied": True,
                "personalization_level": personalization_level,
                "ios": ios_content,
                "android": android_content,
                "variables_used": variables,
                "user_preferences_applied": self._get_applied_preferences(user_pattern),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate personalized notification: {e}")
            return await self._generate_fallback_content(variables, notification_type)

    async def optimize_content_for_engagement(
        self, user_id: str, base_content: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """참여율 향상을 위한 콘텐츠 최적화."""
        try:
            user_pattern = await self._get_user_pattern(user_id)
            if not user_pattern:
                return base_content

            optimized_content = base_content.copy()

            # Apply engagement optimization strategies
            optimized_content = await self._apply_engagement_optimizations(
                optimized_content, user_pattern, context
            )

            # A/B testing variant selection
            optimized_content = await self._apply_ab_testing_variants(
                optimized_content, user_id
            )

            optimized_content["optimization_applied"] = True
            optimized_content["optimization_strategies"] = self._get_applied_strategies(
                user_pattern
            )

            return optimized_content

        except Exception as e:
            logger.error(f"Failed to optimize content for engagement: {e}")
            return base_content

    async def generate_contextual_content(
        self, user_id: str, notification_type: str, context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상황별 맞춤 알림 콘텐츠 생성."""
        try:
            user_pattern = await self._get_user_pattern(user_id)

            # Extract context information
            weather_context = context_data.get("weather", {})
            location_context = context_data.get("location", {})
            time_context = context_data.get("time", {})
            course_context = context_data.get("course", {})

            # Generate base content based on type
            if notification_type == "preparation_reminder":
                content = await self._generate_preparation_content(
                    user_pattern, weather_context, course_context
                )
            elif notification_type == "departure_reminder":
                content = await self._generate_departure_content(
                    user_pattern, location_context, time_context, course_context
                )
            elif notification_type == "weather_alert":
                content = await self._generate_weather_alert_content(
                    user_pattern, weather_context
                )
            elif notification_type == "traffic_alert":
                content = await self._generate_traffic_alert_content(
                    user_pattern, location_context
                )
            else:
                content = await self._generate_general_content(
                    user_pattern, notification_type, context_data
                )

            # Apply user-specific personalization
            personalized_content = await self._apply_user_personalization(
                content, user_pattern
            )

            return {
                "notification_type": notification_type,
                "content": personalized_content,
                "context_applied": True,
                "personalization_factors": self._get_personalization_factors(
                    user_pattern
                ),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate contextual content: {e}")
            return await self._generate_fallback_content(
                context_data, notification_type
            )

    async def analyze_content_performance(
        self, user_id: str, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """사용자별 알림 콘텐츠 성과 분석."""
        try:
            # This would analyze which content types/styles perform best for the user
            # For now, return mock analysis data
            user_pattern = await self._get_user_pattern(user_id)
            if not user_pattern:
                return {"status": "insufficient_data"}

            # Mock performance analysis
            return {
                "user_id": user_id,
                "analysis_period_days": time_period_days,
                "content_preferences": {
                    "emoji_usage": "medium"
                    if user_pattern.engagement_rate > 0.5
                    else "low",
                    "message_length": "short"
                    if user_pattern.avg_response_time_seconds
                    and user_pattern.avg_response_time_seconds < 60
                    else "medium",
                    "tone": "friendly"
                    if user_pattern.engagement_rate > 0.6
                    else "formal",
                    "personalization_level": "high"
                    if user_pattern.overall_engagement_score > 70
                    else "medium",
                },
                "best_performing_elements": ["시간 관련 정보 포함", "구체적인 액션 제시", "개인화된 인사말"],
                "recommendations": self._generate_content_recommendations(user_pattern),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze content performance: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_user_pattern(
        self, user_id: str
    ) -> Optional[UserNotificationPattern]:
        """사용자 알림 패턴 조회."""
        return (
            self.db.query(UserNotificationPattern)
            .filter(UserNotificationPattern.user_id == user_id)
            .first()
        )

    async def _get_notification_template(
        self, template_name: str
    ) -> Optional[NotificationTemplate]:
        """알림 템플릿 조회."""
        return (
            self.db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.name == template_name,
                NotificationTemplate.is_active.is_(True),
            )
            .first()
        )

    async def _apply_personalization(
        self,
        template: NotificationTemplate,
        variables: Dict[str, Any],
        user_pattern: Optional[UserNotificationPattern],
        notification_type: str,
        personalization_level: str,
    ) -> Dict[str, Any]:
        """템플릿에 개인화 적용."""
        personalized_vars = variables.copy()

        if user_pattern and personalization_level != "none":
            # Add personalized greeting based on time
            current_hour = datetime.now().hour
            if current_hour < 12:
                time_of_day = "morning"
            elif current_hour < 18:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"

            greeting_options = self.personalization_templates["greeting"][time_of_day]
            personalized_vars["greeting"] = random.choice(greeting_options)

            # Adjust tone based on user engagement
            if user_pattern.engagement_rate > 0.7:
                tone = "casual"
            elif user_pattern.engagement_rate > 0.4:
                tone = "friendly"
            else:
                tone = "formal"

            personalized_vars["tone_suffix"] = self.personalization_templates["tone"][
                tone
            ]["suffix"]
            personalized_vars["emoji_density"] = self.personalization_templates["tone"][
                tone
            ]["emoji_density"]

        # Render template with personalized variables
        title_template = Template(template.title_template)
        body_template = Template(template.body_template)

        return {
            "title": title_template.render(**personalized_vars),
            "body": body_template.render(**personalized_vars),
            "category": template.category,
            "priority": template.priority,
            "notification_type": template.notification_type,
        }

    async def _apply_engagement_optimizations(
        self,
        content: Dict[str, Any],
        user_pattern: UserNotificationPattern,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """참여율 향상을 위한 최적화 적용."""
        optimized = content.copy()

        # Low engagement users get shorter, more direct messages
        if user_pattern.engagement_rate < 0.3:
            optimized["title"] = self._shorten_text(optimized["title"], max_length=30)
            optimized["body"] = self._shorten_text(optimized["body"], max_length=80)
            optimized["urgency_level"] = "medium"  # More urgent to grab attention

        # High engagement users get more detailed information
        elif user_pattern.engagement_rate > 0.7:
            optimized = await self._add_contextual_details(optimized, context)
            optimized["urgency_level"] = "low"  # Less urgent, more informative

        # Add call-to-action based on user response patterns
        if user_pattern.click_rate > 0.2:
            optimized["include_cta"] = True
            optimized["cta_text"] = "자세히 보기"
        else:
            optimized["include_cta"] = False

        return optimized

    async def _apply_ab_testing_variants(
        self, content: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """A/B 테스팅 변형 적용."""
        # Simple variant selection based on user ID hash
        user_hash = hash(user_id) % 100

        if user_hash < 33:  # Variant A: Emoji-heavy
            content["variant"] = "emoji_heavy"
            content["title"] = "🎯 " + content["title"]
            content["body"] = self._add_relevant_emojis(content["body"])
        elif user_hash < 66:  # Variant B: Question format
            content["variant"] = "question_format"
            if not content["title"].endswith("?"):
                content["title"] = content["title"].rstrip("!.") + "?"
        else:  # Control group
            content["variant"] = "control"

        return content

    async def _format_for_ios(
        self, content: Dict[str, Any], user_pattern: Optional[UserNotificationPattern]
    ) -> Dict[str, Any]:
        """iOS 플랫폼용 포맷팅."""
        ios_content = {
            "title": content["title"][:60],  # iOS title limit
            "body": content["body"][:200],  # iOS body limit
            "subtitle": content.get("subtitle", ""),
            "sound": "default",
            "badge": 1,
            "category": content.get("category", "default"),
        }

        # Rich notification features for iOS
        if user_pattern and user_pattern.engagement_rate > 0.5:
            ios_content["mutable_content"] = True
            ios_content["content_available"] = True

        return ios_content

    async def _format_for_android(
        self, content: Dict[str, Any], user_pattern: Optional[UserNotificationPattern]
    ) -> Dict[str, Any]:
        """Android 플랫폼용 포맷팅."""
        android_content = {
            "title": content["title"],
            "body": content["body"],
            "icon": "notification_icon",
            "color": "#007AFF",
            "channel_id": f"channel_{content.get('notification_type', 'default')}",
            "priority": content.get("priority", "normal"),
        }

        # Android-specific features
        if content.get("include_cta", False):
            android_content["actions"] = [
                {"title": content.get("cta_text", "확인"), "action": "OPEN_APP"}
            ]

        return android_content

    async def _generate_preparation_content(
        self,
        user_pattern: Optional[UserNotificationPattern],
        weather_context: Dict[str, Any],
        course_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """데이트 준비 알림 콘텐츠 생성."""
        base_title = "내일 데이트 준비!"
        preparation_items = []

        # Weather-based preparations
        if weather_context.get("rain_probability", 0) > 50:
            preparation_items.append("우산 준비")
        if weather_context.get("temperature", 20) < 5:
            preparation_items.append("따뜻한 옷 착용")

        # Course-based preparations
        first_place = course_context.get("places", [{}])[0]
        if first_place.get("requires_reservation"):
            preparation_items.append(f"{first_place.get('name')} 예약 확인")

        body_parts = []
        if preparation_items:
            body_parts.extend(f"• {item}" for item in preparation_items[:3])

        body = "\n".join(body_parts) if body_parts else "완벽한 데이트를 위해 미리 준비해보세요!"

        return {"title": base_title, "body": body}

    async def _generate_departure_content(
        self,
        user_pattern: Optional[UserNotificationPattern],
        location_context: Dict[str, Any],
        time_context: Dict[str, Any],
        course_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """출발 알림 콘텐츠 생성."""
        departure_time = time_context.get("departure_time", "지금")
        destination = course_context.get("places", [{}])[0].get("name", "목적지")
        travel_time = time_context.get("travel_time_minutes", 30)

        title = f"{departure_time}에 출발하세요!"
        body = f"📍 {destination}까지 약 {travel_time}분 소요\n🚇 지하철 이용 권장"

        # Add traffic context if available
        if location_context.get("traffic_delay"):
            body += f"\n⚠️ 교통 지연 {location_context['traffic_delay']}분 예상"

        return {"title": title, "body": body}

    async def _generate_weather_alert_content(
        self,
        user_pattern: Optional[UserNotificationPattern],
        weather_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """날씨 알림 콘텐츠 생성."""
        weather_type = weather_context.get("type", "변화")
        severity = weather_context.get("severity", "medium")

        if severity == "high":
            title = f"🚨 {weather_type} 경보"
            body = f"심각한 {weather_type} 예보입니다. 외출 시 주의하세요."
        else:
            title = f"☔ {weather_type} 예보"
            body = f"{weather_type} 예보가 있어요. 미리 준비하세요."

        return {"title": title, "body": body}

    async def _generate_traffic_alert_content(
        self,
        user_pattern: Optional[UserNotificationPattern],
        location_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """교통 알림 콘텐츠 생성."""
        delay_minutes = location_context.get("delay_minutes", 15)
        route = location_context.get("route", "경로")

        title = "🚇 교통 지연 알림"
        body = f"{route}에서 약 {delay_minutes}분 지연 예상\n일찍 출발하시거나 대체 경로를 이용하세요."

        return {"title": title, "body": body}

    async def _generate_general_content(
        self,
        user_pattern: Optional[UserNotificationPattern],
        notification_type: str,
        context_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """일반 알림 콘텐츠 생성."""
        return {"title": f"{notification_type} 알림", "body": "새로운 정보가 있습니다."}

    async def _apply_user_personalization(
        self, content: Dict[str, str], user_pattern: Optional[UserNotificationPattern]
    ) -> Dict[str, str]:
        """사용자별 개인화 적용."""
        if not user_pattern:
            return content

        personalized = content.copy()

        # Add personal greeting for high-engagement users
        if user_pattern.engagement_rate > 0.6:
            current_hour = datetime.now().hour
            if current_hour < 12:
                greeting = "좋은 아침이에요! "
            elif current_hour < 18:
                greeting = "안녕하세요! "
            else:
                greeting = "수고하셨어요! "

            personalized["title"] = greeting + personalized["title"]

        return personalized

    async def _add_contextual_details(
        self, content: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상세 정보 추가."""
        enhanced = content.copy()

        # Add more details for engaged users
        if context.get("weather"):
            weather_detail = f"날씨: {context['weather'].get('summary', 'Unknown')}"
            enhanced["body"] = enhanced["body"] + f"\n💡 {weather_detail}"

        if context.get("time"):
            time_detail = (
                f"예상 소요시간: {context['time'].get('travel_time_minutes', 'Unknown')}분"
            )
            enhanced["body"] = enhanced["body"] + f"\n⏱️ {time_detail}"

        return enhanced

    async def _generate_fallback_content(
        self, variables: Dict[str, Any], notification_type: str
    ) -> Dict[str, Any]:
        """기본 콘텐츠 생성 (fallback)."""
        return {
            "template_name": "fallback",
            "personalization_applied": False,
            "ios": {
                "title": f"{notification_type} 알림",
                "body": "새로운 정보가 있습니다.",
            },
            "android": {
                "title": f"{notification_type} 알림",
                "body": "새로운 정보가 있습니다.",
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _shorten_text(self, text: str, max_length: int) -> str:
        """텍스트 단축."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _add_relevant_emojis(self, text: str) -> str:
        """관련 이모지 추가."""
        emoji_map = {
            "데이트": "💕",
            "출발": "🚗",
            "날씨": "🌤️",
            "비": "☔",
            "준비": "📋",
            "시간": "⏰",
        }

        for word, emoji in emoji_map.items():
            if word in text and emoji not in text:
                text = text.replace(word, f"{emoji} {word}", 1)

        return text

    def _get_applied_preferences(
        self, user_pattern: Optional[UserNotificationPattern]
    ) -> List[str]:
        """적용된 사용자 선호도 목록."""
        if not user_pattern:
            return ["default"]

        preferences = []
        if user_pattern.engagement_rate > 0.7:
            preferences.append("high_engagement_tone")
        if user_pattern.should_personalize_timing():
            preferences.append("timing_personalization")
        if user_pattern.overall_engagement_score > 50:
            preferences.append("detailed_content")

        return preferences or ["standard"]

    def _get_applied_strategies(
        self, user_pattern: UserNotificationPattern
    ) -> List[str]:
        """적용된 최적화 전략 목록."""
        strategies = []

        if user_pattern.engagement_rate < 0.3:
            strategies.extend(["content_shortening", "urgency_increase"])
        elif user_pattern.engagement_rate > 0.7:
            strategies.extend(["detail_enhancement", "contextual_enrichment"])

        if user_pattern.click_rate > 0.2:
            strategies.append("cta_inclusion")

        return strategies

    def _get_personalization_factors(
        self, user_pattern: Optional[UserNotificationPattern]
    ) -> List[str]:
        """개인화 요소 목록."""
        if not user_pattern:
            return ["time_based_greeting"]

        factors = ["time_based_greeting"]

        if user_pattern.preferred_hours:
            factors.append("timing_optimization")
        if user_pattern.engagement_rate > 0.5:
            factors.append("tone_adjustment")
        if user_pattern.type_preferences:
            factors.append("content_type_preference")

        return factors

    def _generate_content_recommendations(
        self, user_pattern: UserNotificationPattern
    ) -> List[str]:
        """콘텐츠 개선 권장사항 생성."""
        recommendations = []

        if user_pattern.engagement_rate < 0.3:
            recommendations.extend(
                ["더 간결하고 직접적인 메시지 사용", "긴급성을 나타내는 표현 추가", "명확한 행동 유도 문구 포함"]
            )
        elif user_pattern.engagement_rate > 0.7:
            recommendations.extend(
                ["상세한 컨텍스트 정보 제공", "개인화된 인사말 사용", "관련 이모지나 시각적 요소 추가"]
            )
        else:
            recommendations.extend(["현재 수준의 개인화 유지", "A/B 테스트로 추가 최적화 탐색"])

        return recommendations


def get_personalized_content_engine(db: Session) -> PersonalizedContentEngine:
    """Get personalized content engine instance."""
    return PersonalizedContentEngine(db)
