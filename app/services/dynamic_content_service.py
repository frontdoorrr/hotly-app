"""Dynamic content generation service for personalized onboarding."""

import logging
import random
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DynamicContentGenerator:
    """Generator for dynamic, personalized onboarding content."""

    def __init__(self, db: Session):
        self.db = db
        self.content_templates = self._load_content_templates()
        self.personalization_rules = self._load_personalization_rules()

    def _load_content_templates(self) -> Dict[str, Any]:
        """Load content templates for dynamic generation."""
        return {
            "welcome_messages": {
                "base_templates": [
                    "안녕하세요! {app_name}에 오신 것을 환영합니다.",
                    "{user_name}님, 반갑습니다! 특별한 장소 발견을 시작해보세요.",
                    "환영합니다! 당신만의 핫플레이스를 찾아드릴게요.",
                    "어서 오세요! 맞춤형 장소 추천을 준비했습니다.",
                ],
                "personalized_templates": {
                    "tech_savvy": [
                        "개발자분들이 선택한 {app_name}입니다. 효율적인 설정을 시작하겠습니다.",
                        "빠른 설정으로 바로 시작하시겠어요? 고급 옵션도 준비되어 있습니다.",
                        "API 같은 직관적인 설정으로 개인화를 진행합니다.",
                    ],
                    "casual_user": [
                        "처음이시죠? 차근차근 안내해드릴게요. 걱정하지 마세요!",
                        "쉽고 간단한 몇 단계로 설정을 완료하겠습니다.",
                        "편안하게 따라오시면 됩니다. 모든 과정을 자세히 설명드려요.",
                    ],
                    "visual_learner": [
                        "시각적 가이드와 함께 설정을 시작하겠습니다.",
                        "이미지와 예시로 쉽게 이해할 수 있게 도와드릴게요.",
                        "직관적인 화면으로 설정 과정을 보여드리겠습니다.",
                    ],
                },
                "context_variables": [
                    "app_name",
                    "user_name",
                    "time_of_day",
                    "device_type",
                    "referral_source",
                    "user_segment",
                    "current_weather",
                ],
            },
            "step_descriptions": {
                "category_selection": {
                    "base": "관심있는 장소 유형을 선택해주세요.",
                    "personalized": {
                        "tech_savvy": "API 엔드포인트처럼 명확한 카테고리를 선택하세요. (2-5개 권장)",
                        "casual_user": "어떤 종류의 장소를 좋아하시나요? 천천히 골라보세요. 나중에 변경할 수 있어요.",
                        "visual_learner": "아래 이미지를 보고 마음에 드는 장소 유형을 선택해보세요.",
                        "goal_oriented": "맞춤 추천의 정확도를 높이기 위해 선호하는 카테고리를 선택하세요.",
                        "social_user": "친구들과 함께 가고 싶은 장소 유형을 선택해보세요!",
                    },
                },
                "preference_setup": {
                    "base": "세부 취향을 설정해주세요.",
                    "personalized": {
                        "tech_savvy": "알고리즘 최적화를 위한 추가 파라미터를 설정합니다.",
                        "casual_user": "몇 가지만 더 알려주시면 더 좋은 추천을 받으실 수 있어요.",
                        "visual_learner": "선호하는 분위기와 스타일을 이미지로 확인하며 설정해보세요.",
                        "goal_oriented": "목표 달성을 위한 최적의 설정을 구성합니다.",
                        "social_user": "친구들과 공유할 때 도움이 될 설정들을 해보세요.",
                    },
                },
            },
            "progress_messages": {
                "encouragement": [
                    "잘하고 계세요! 조금만 더 하면 완료됩니다.",
                    "훌륭해요! 이제 {completion_percentage}% 완료되었습니다.",
                    "순조롭게 진행되고 있어요. 계속해주세요!",
                    "아주 좋습니다! 거의 다 왔어요.",
                ],
                "milestones": {
                    "25": "첫 번째 단계 완료! 좋은 시작이에요.",
                    "50": "절반 완료! 이제 절반만 더 하면 됩니다.",
                    "75": "거의 다 했어요! 마지막 단계만 남았습니다.",
                    "100": "완료! 이제 개인화된 추천을 받을 수 있습니다.",
                },
            },
            "help_content": {
                "contextual_tips": {
                    "category_selection": [
                        "💡 팁: 처음에는 2-3개 정도 선택하시고, 나중에 더 추가할 수 있어요.",
                        "💡 도움말: 자주 가는 장소 유형을 우선 선택해보세요.",
                        "💡 가이드: 다양한 카테고리를 선택하면 더 폭넓은 추천을 받을 수 있어요.",
                    ],
                    "preference_setup": [
                        "💡 팁: 평소 선호하는 분위기나 스타일을 생각해보세요.",
                        "💡 도움말: 확실하지 않은 항목은 기본값으로 두어도 괜찮아요.",
                        "💡 가이드: 설정은 언제든 프로필에서 변경할 수 있습니다.",
                    ],
                },
                "troubleshooting": {
                    "common_issues": {
                        "slow_loading": "네트워크가 느린 경우, 잠시 기다려주시거나 새로고침을 해보세요.",
                        "selection_error": "선택이 안 되는 경우, 다른 옵션을 먼저 선택한 후 다시 시도해보세요.",
                        "navigation_stuck": "단계 이동이 안 되면, 필수 항목들이 모두 선택되었는지 확인해주세요.",
                    }
                },
            },
            "completion_messages": {
                "success": [
                    "🎉 축하합니다! 설정이 완료되었습니다.",
                    "✨ 완성! 이제 개인화된 추천을 받아보세요.",
                    "🚀 준비 완료! 특별한 장소들을 발견할 시간입니다.",
                    "🎯 설정 완료! 맞춤형 서비스가 시작됩니다.",
                ],
                "next_steps": {
                    "immediate": [
                        "바로 첫 번째 추천을 확인해보세요!",
                        "주변의 인기 장소들을 둘러보시겠어요?",
                        "친구를 초대해서 함께 즐겨보세요.",
                    ],
                    "exploratory": [
                        "설정을 더 세밀하게 조정하고 싶으시면 프로필로 가세요.",
                        "다양한 기능들을 차근차근 살펴보세요.",
                        "궁금한 점이 있으면 언제든 도움말을 확인하세요.",
                    ],
                },
            },
        }

    def _load_personalization_rules(self) -> Dict[str, Any]:
        """Load personalization rules for content adaptation."""
        return {
            "tone_mapping": {
                "tech_savvy": "professional",
                "casual_user": "friendly",
                "visual_learner": "descriptive",
                "goal_oriented": "direct",
                "social_user": "enthusiastic",
            },
            "content_length": {
                "tech_savvy": "concise",
                "casual_user": "detailed",
                "visual_learner": "moderate",
                "goal_oriented": "brief",
                "social_user": "engaging",
            },
            "emoji_usage": {
                "tech_savvy": "minimal",
                "casual_user": "moderate",
                "visual_learner": "frequent",
                "goal_oriented": "minimal",
                "social_user": "frequent",
            },
            "urgency_level": {
                "tech_savvy": "low",
                "casual_user": "low",
                "visual_learner": "medium",
                "goal_oriented": "high",
                "social_user": "medium",
            },
        }

    def generate_personalized_content(
        self, content_type: str, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized content based on user segment and context."""
        try:
            content_result = {
                "content_type": content_type,
                "user_segment": user_segment,
                "context": context,
                "generated_content": {},
                "personalization_applied": [],
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Generate content based on type
            if content_type == "welcome_message":
                content_result["generated_content"] = self._generate_welcome_message(
                    user_segment, context
                )
            elif content_type == "step_description":
                content_result["generated_content"] = self._generate_step_description(
                    user_segment, context
                )
            elif content_type == "progress_message":
                content_result["generated_content"] = self._generate_progress_message(
                    user_segment, context
                )
            elif content_type == "help_content":
                content_result["generated_content"] = self._generate_help_content(
                    user_segment, context
                )
            elif content_type == "completion_message":
                content_result["generated_content"] = self._generate_completion_message(
                    user_segment, context
                )
            else:
                logger.warning(f"Unknown content type: {content_type}")
                return content_result

            # Apply personalization rules
            content_result = self._apply_personalization_rules(
                content_result, user_segment
            )

            logger.info(f"Generated personalized {content_type} for {user_segment}")
            return content_result

        except Exception as e:
            logger.error(f"Error generating personalized content: {e}")
            return self._get_fallback_content(content_type, context)

    def _generate_welcome_message(
        self, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized welcome message."""
        templates = self.content_templates["welcome_messages"]

        # Select template based on segment
        if user_segment in templates["personalized_templates"]:
            segment_templates = templates["personalized_templates"][user_segment]
            base_message = random.choice(segment_templates)
        else:
            base_message = random.choice(templates["base_templates"])

        # Apply context variables
        personalized_message = self._apply_context_variables(base_message, context)

        return {
            "message": personalized_message,
            "tone": self.personalization_rules["tone_mapping"].get(
                user_segment, "friendly"
            ),
            "length": self.personalization_rules["content_length"].get(
                user_segment, "moderate"
            ),
            "urgency": self.personalization_rules["urgency_level"].get(
                user_segment, "low"
            ),
        }

    def _generate_step_description(
        self, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized step description."""
        step_name = context.get("step_name", "unknown")
        step_templates = self.content_templates["step_descriptions"].get(step_name, {})

        if user_segment in step_templates.get("personalized", {}):
            description = step_templates["personalized"][user_segment]
        else:
            description = step_templates.get("base", "다음 단계를 완료해주세요.")

        # Add contextual enhancements
        if context.get("has_errors"):
            description += " 이전 오류를 수정하고 진행해주세요."
        elif context.get("is_retry"):
            description += " 다시 시도해보시겠어요?"

        return {
            "description": description,
            "estimated_time": self._estimate_step_time(step_name, user_segment),
            "difficulty_level": self._get_step_difficulty(step_name, user_segment),
            "help_available": True,
        }

    def _generate_progress_message(
        self, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized progress message."""
        completion_percentage = context.get("completion_percentage", 0)
        templates = self.content_templates["progress_messages"]

        # Check for milestone messages
        milestone_key = str(completion_percentage)
        if milestone_key in templates["milestones"]:
            message = templates["milestones"][milestone_key]
        else:
            # Use encouragement message
            message = random.choice(templates["encouragement"])

        # Apply context variables
        message = message.format(
            completion_percentage=completion_percentage,
            remaining_steps=context.get("remaining_steps", 0),
            estimated_time=context.get("estimated_completion_time", "2분"),
        )

        return {
            "message": message,
            "show_progress_bar": True,
            "completion_percentage": completion_percentage,
            "celebration_level": self._get_celebration_level(completion_percentage),
            "next_step_preview": context.get("next_step_name"),
        }

    def _generate_help_content(
        self, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized help content."""
        current_step = context.get("current_step", "unknown")
        issue_type = context.get("issue_type", "general")

        help_templates = self.content_templates["help_content"]

        # Get contextual tips
        contextual_tips = help_templates["contextual_tips"].get(current_step, [])
        selected_tip = (
            random.choice(contextual_tips)
            if contextual_tips
            else "도움이 필요하시면 언제든 문의해주세요."
        )

        # Get troubleshooting info if specific issue
        troubleshooting_info = ""
        if issue_type in help_templates["troubleshooting"]["common_issues"]:
            troubleshooting_info = help_templates["troubleshooting"]["common_issues"][
                issue_type
            ]

        # Personalize help content based on segment
        if user_segment == "tech_savvy":
            additional_info = (
                "고급 설정이나 API 문서를 확인하시려면 설정 메뉴를 참조하세요."
            )
        elif user_segment == "casual_user":
            additional_info = "걱정하지 마세요. 천천히 진행하시면 됩니다. 도움이 더 필요하면 채팅으로 문의해주세요."
        else:
            additional_info = "추가 도움이 필요하시면 고객지원팀에 연락해주세요."

        return {
            "contextual_tip": selected_tip,
            "troubleshooting_info": troubleshooting_info,
            "additional_info": additional_info,
            "contact_support": True,
            "help_priority": "high" if issue_type != "general" else "medium",
        }

    def _generate_completion_message(
        self, user_segment: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized completion message."""
        templates = self.content_templates["completion_messages"]

        # Select success message
        success_message = random.choice(templates["success"])

        # Select next steps based on segment
        if user_segment in ["tech_savvy", "goal_oriented"]:
            next_steps = templates["next_steps"]["immediate"]
        else:
            next_steps = templates["next_steps"]["exploratory"]

        selected_next_step = random.choice(next_steps)

        # Add personalized touches
        personalized_elements = {}
        if user_segment == "social_user":
            personalized_elements["sharing_encouragement"] = "친구들과 공유해보세요!"
        elif user_segment == "visual_learner":
            personalized_elements["visual_celebration"] = True

        return {
            "success_message": success_message,
            "next_step_suggestion": selected_next_step,
            "completion_time": context.get("total_time_seconds", 0),
            "achievement_unlocked": True,
            "personalized_elements": personalized_elements,
            "user_satisfaction_survey": context.get("completion_percentage", 0) == 100,
        }

    def _apply_context_variables(
        self, message_template: str, context: Dict[str, Any]
    ) -> str:
        """Apply context variables to message template."""
        try:
            # Default context values
            default_context = {
                "app_name": "핫플레이스",
                "user_name": "사용자",
                "time_of_day": self._get_time_of_day(),
                "device_type": "모바일",
                "referral_source": "직접 방문",
                "current_weather": "좋은",
            }

            # Merge with provided context
            full_context = {**default_context, **context}

            # Apply formatting
            return message_template.format(**full_context)

        except KeyError as e:
            logger.warning(f"Missing context variable {e}, using original message")
            return message_template
        except Exception as e:
            logger.error(f"Error applying context variables: {e}")
            return message_template

    def _apply_personalization_rules(
        self, content_result: Dict[str, Any], user_segment: str
    ) -> Dict[str, Any]:
        """Apply personalization rules to generated content."""
        try:
            rules = self.personalization_rules
            applied_rules = []

            # Apply emoji usage rules
            emoji_usage = rules["emoji_usage"].get(user_segment, "moderate")
            if emoji_usage == "minimal":
                # Remove most emojis
                content_result = self._reduce_emojis(content_result)
                applied_rules.append("reduced_emojis")
            elif emoji_usage == "frequent":
                # Add more emojis
                content_result = self._enhance_emojis(content_result)
                applied_rules.append("enhanced_emojis")

            # Apply content length rules
            content_length = rules["content_length"].get(user_segment, "moderate")
            if content_length == "concise":
                content_result = self._make_concise(content_result)
                applied_rules.append("made_concise")
            elif content_length == "detailed":
                content_result = self._add_detail(content_result)
                applied_rules.append("added_detail")

            # Apply urgency rules
            urgency_level = rules["urgency_level"].get(user_segment, "low")
            if urgency_level == "high":
                content_result = self._add_urgency(content_result)
                applied_rules.append("added_urgency")

            content_result["personalization_applied"] = applied_rules
            return content_result

        except Exception as e:
            logger.error(f"Error applying personalization rules: {e}")
            return content_result

    def _estimate_step_time(self, step_name: str, user_segment: str) -> int:
        """Estimate time to complete step based on user segment."""
        base_times = {
            "category_selection": 60,
            "preference_setup": 90,
            "sample_guide": 45,
            "completion": 30,
        }

        base_time = base_times.get(step_name, 60)

        # Adjust based on user segment
        multipliers = {
            "tech_savvy": 0.7,
            "casual_user": 1.3,
            "visual_learner": 1.1,
            "goal_oriented": 0.8,
            "social_user": 1.0,
        }

        multiplier = multipliers.get(user_segment, 1.0)
        return int(base_time * multiplier)

    def _get_step_difficulty(self, step_name: str, user_segment: str) -> str:
        """Get step difficulty level for user segment."""
        base_difficulties = {
            "category_selection": "easy",
            "preference_setup": "medium",
            "sample_guide": "easy",
            "completion": "easy",
        }

        base_difficulty = base_difficulties.get(step_name, "medium")

        # Adjust based on user segment
        if user_segment == "tech_savvy":
            return "easy" if base_difficulty != "hard" else "medium"
        elif user_segment == "casual_user":
            return (
                "hard"
                if base_difficulty == "hard"
                else "medium" if base_difficulty == "medium" else "easy"
            )
        else:
            return base_difficulty

    def _get_celebration_level(self, completion_percentage: int) -> str:
        """Get celebration level based on completion percentage."""
        if completion_percentage >= 100:
            return "high"
        elif completion_percentage >= 75:
            return "medium"
        elif completion_percentage >= 50:
            return "low"
        else:
            return "minimal"

    def _get_time_of_day(self) -> str:
        """Get time of day greeting."""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 18:
            return "afternoon"
        else:
            return "evening"

    def _reduce_emojis(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce emoji usage in content."""
        # Simple emoji reduction (in production, would use more sophisticated filtering)
        for key, value in content_result.get("generated_content", {}).items():
            if isinstance(value, str):
                # Remove some emojis but keep essential ones
                value = value.replace("🎉", "").replace("✨", "").replace("🚀", "")
                content_result["generated_content"][key] = value
        return content_result

    def _enhance_emojis(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance emoji usage in content."""
        # Add more emojis where appropriate
        for key, value in content_result.get("generated_content", {}).items():
            if isinstance(value, str) and key in ["message", "description"]:
                if "완료" in value and "🎉" not in value:
                    value = f"🎉 {value}"
                elif "시작" in value and "🚀" not in value:
                    value = f"🚀 {value}"
                content_result["generated_content"][key] = value
        return content_result

    def _make_concise(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Make content more concise."""
        # Simplify messages for tech-savvy users
        for key, value in content_result.get("generated_content", {}).items():
            if isinstance(value, str):
                # Remove redundant phrases
                value = (
                    value.replace("천천히 ", "")
                    .replace("걱정하지 마세요", "")
                    .replace("차근차근 ", "")
                )
                content_result["generated_content"][key] = value
        return content_result

    def _add_detail(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add more detail to content."""
        # Add helpful details for casual users
        for key, value in content_result.get("generated_content", {}).items():
            if isinstance(value, str) and key in ["description"]:
                if "선택" in value:
                    value += " (나중에 변경할 수 있습니다)"
                content_result["generated_content"][key] = value
        return content_result

    def _add_urgency(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add urgency to content."""
        # Add time-sensitive language for goal-oriented users
        for key, value in content_result.get("generated_content", {}).items():
            if isinstance(value, str) and key in ["message", "description"]:
                if "완료" in value:
                    value = value.replace("완료", "빠른 완료")
                elif "시작" in value:
                    value = value.replace("시작", "즉시 시작")
                content_result["generated_content"][key] = value
        return content_result

    def _get_fallback_content(
        self, content_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get fallback content when generation fails."""
        fallback_messages = {
            "welcome_message": "안녕하세요! 환영합니다.",
            "step_description": "다음 단계를 완료해주세요.",
            "progress_message": "진행 중입니다...",
            "help_content": "도움이 필요하시면 문의해주세요.",
            "completion_message": "완료되었습니다!",
        }

        return {
            "content_type": content_type,
            "user_segment": "default",
            "context": context,
            "generated_content": {
                "message": fallback_messages.get(
                    content_type, "콘텐츠를 준비 중입니다."
                )
            },
            "personalization_applied": [],
            "fallback_used": True,
            "generated_at": datetime.utcnow().isoformat(),
        }
