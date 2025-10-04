"""Notification template service for managing reusable notification content."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.notification import NotificationTemplate, NotificationType
from app.schemas.notification import (
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
)

logger = logging.getLogger(__name__)


class NotificationTemplateService:
    """Service for managing notification templates."""

    def __init__(self, db: Session):
        """Initialize notification template service with database session."""
        self.db = db
        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        """Initialize default notification templates."""
        default_templates = [
            {
                "name": "onboarding_welcome",
                "description": "환영 온보딩 알림",
                "title_template": "🎉 {app_name}에 오신 것을 환영합니다!",
                "body_template": "{user_name}님, 첫 번째 맛집 탐험을 시작해보세요!",
                "notification_type": NotificationType.ONBOARDING.value,
                "category": "welcome",
                "required_variables": ["app_name", "user_name"],
                "default_data": {"action_url": "/onboarding/step1"},
            },
            {
                "name": "onboarding_step_complete",
                "description": "온보딩 단계 완료 알림",
                "title_template": "✅ {step_name} 완료!",
                "body_template": "다음 단계로 이동하여 취향 설정을 완료해주세요.",
                "notification_type": NotificationType.ONBOARDING.value,
                "category": "progress",
                "required_variables": ["step_name"],
                "default_data": {"action_url": "/onboarding/next"},
            },
            {
                "name": "place_recommendation",
                "description": "장소 추천 알림",
                "title_template": "🍽️ {location_name} 근처 맛집 추천",
                "body_template": "{user_name}님의 취향에 맞는 {category} {place_count}곳을 찾았어요!",
                "notification_type": NotificationType.PLACE_RECOMMENDATION.value,
                "category": "recommendation",
                "required_variables": [
                    "location_name",
                    "user_name",
                    "category",
                    "place_count",
                ],
                "default_data": {"action_url": "/places/recommendations"},
            },
            {
                "name": "course_recommendation",
                "description": "코스 추천 알림",
                "title_template": "🗺️ {theme} 테마 코스 추천",
                "body_template": "{user_name}님을 위한 {duration} 코스를 준비했어요!",
                "notification_type": NotificationType.COURSE_RECOMMENDATION.value,
                "category": "recommendation",
                "required_variables": ["theme", "user_name", "duration"],
                "default_data": {"action_url": "/courses/recommendations"},
            },
            {
                "name": "social_like_received",
                "description": "좋아요 받음 알림",
                "title_template": "💖 좋아요를 받았어요!",
                "body_template": "{liker_name}님이 '{place_name}' 장소에 좋아요를 눌렀어요.",
                "notification_type": NotificationType.SOCIAL_ACTIVITY.value,
                "category": "like",
                "required_variables": ["liker_name", "place_name"],
                "default_data": {"action_url": "/social/activity"},
            },
            {
                "name": "social_comment_received",
                "description": "댓글 받음 알림",
                "title_template": "💬 새로운 댓글이 있어요!",
                "body_template": "{commenter_name}님이 '{place_name}'에 댓글을 남겼어요.",
                "notification_type": NotificationType.SOCIAL_ACTIVITY.value,
                "category": "comment",
                "required_variables": ["commenter_name", "place_name"],
                "default_data": {"action_url": "/social/comments"},
            },
            {
                "name": "reminder_visit_place",
                "description": "장소 방문 리마인더",
                "title_template": "📍 {place_name} 방문 계획",
                "body_template": "저장하신 '{place_name}'을 방문할 시간이에요!",
                "notification_type": NotificationType.REMINDER.value,
                "category": "visit",
                "required_variables": ["place_name"],
                "default_data": {"action_url": "/reminders"},
            },
            {
                "name": "promotional_weekend_special",
                "description": "주말 특가 프로모션",
                "title_template": "🎁 주말 특가 이벤트",
                "body_template": "이번 주말 {discount_rate}% 할인 혜택을 놓치지 마세요!",
                "notification_type": NotificationType.PROMOTIONAL.value,
                "category": "discount",
                "required_variables": ["discount_rate"],
                "default_data": {"action_url": "/events/weekend-special"},
            },
            {
                "name": "system_update_available",
                "description": "시스템 업데이트 알림",
                "title_template": "🔄 앱 업데이트 알림",
                "body_template": "새로운 기능이 추가된 {version} 버전이 출시되었어요!",
                "notification_type": NotificationType.SYSTEM_UPDATE.value,
                "category": "update",
                "required_variables": ["version"],
                "default_data": {"action_url": "/app/update"},
            },
        ]

        for template_data in default_templates:
            if not self.get_template_by_name(template_data["name"]):
                self.create_template(NotificationTemplateCreate(**template_data))

    def create_template(
        self, template_data: NotificationTemplateCreate
    ) -> NotificationTemplateResponse:
        """Create a new notification template."""
        try:
            template = NotificationTemplate(
                name=template_data.name,
                description=template_data.description,
                title_template=template_data.title_template,
                body_template=template_data.body_template,
                notification_type=template_data.notification_type,
                category=template_data.category,
                priority=template_data.priority,
                required_variables=template_data.required_variables,
                optional_variables=template_data.optional_variables,
                default_data=template_data.default_data or {},
                is_active=template_data.is_active,
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Created notification template: {template.name}")

            return NotificationTemplateResponse.from_orm(template)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification template: {e}")
            raise

    def get_template_by_id(
        self, template_id: str
    ) -> Optional[NotificationTemplateResponse]:
        """Get notification template by ID."""
        try:
            template = (
                self.db.query(NotificationTemplate)
                .filter(NotificationTemplate.id == template_id)
                .first()
            )

            if template:
                return NotificationTemplateResponse.from_orm(template)
            return None

        except Exception as e:
            logger.error(
                f"Failed to get notification template by ID {template_id}: {e}"
            )
            return None

    def get_template_by_name(
        self, template_name: str
    ) -> Optional[NotificationTemplateResponse]:
        """Get notification template by name."""
        try:
            template = (
                self.db.query(NotificationTemplate)
                .filter(NotificationTemplate.name == template_name)
                .first()
            )

            if template:
                return NotificationTemplateResponse.from_orm(template)
            return None

        except Exception as e:
            logger.error(
                f"Failed to get notification template by name {template_name}: {e}"
            )
            return None

    def get_templates_by_type(
        self, notification_type: str
    ) -> List[NotificationTemplateResponse]:
        """Get notification templates by type."""
        try:
            templates = (
                self.db.query(NotificationTemplate)
                .filter(
                    NotificationTemplate.notification_type == notification_type,
                    NotificationTemplate.is_active == True,
                )
                .all()
            )

            return [
                NotificationTemplateResponse.from_orm(template)
                for template in templates
            ]

        except Exception as e:
            logger.error(f"Failed to get templates by type {notification_type}: {e}")
            return []

    def list_templates(
        self,
        notification_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[NotificationTemplateResponse]:
        """List notification templates with optional filters."""
        try:
            query = self.db.query(NotificationTemplate)

            if notification_type:
                query = query.filter(
                    NotificationTemplate.notification_type == notification_type
                )

            if category:
                query = query.filter(NotificationTemplate.category == category)

            if is_active is not None:
                query = query.filter(NotificationTemplate.is_active == is_active)

            templates = query.offset(skip).limit(limit).all()

            return [
                NotificationTemplateResponse.from_orm(template)
                for template in templates
            ]

        except Exception as e:
            logger.error(f"Failed to list notification templates: {e}")
            return []

    def update_template(
        self, template_id: str, template_update: NotificationTemplateUpdate
    ) -> Optional[NotificationTemplateResponse]:
        """Update notification template."""
        try:
            template = (
                self.db.query(NotificationTemplate)
                .filter(NotificationTemplate.id == template_id)
                .first()
            )

            if not template:
                return None

            update_data = template_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(template, field, value)

            template.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Updated notification template: {template.name}")

            return NotificationTemplateResponse.from_orm(template)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update notification template {template_id}: {e}")
            return None

    def delete_template(self, template_id: str) -> bool:
        """Delete notification template."""
        try:
            template = (
                self.db.query(NotificationTemplate)
                .filter(NotificationTemplate.id == template_id)
                .first()
            )

            if not template:
                return False

            self.db.delete(template)
            self.db.commit()

            logger.info(f"Deleted notification template: {template.name}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete notification template {template_id}: {e}")
            return False

    def render_template(
        self, template_name: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render notification template with provided variables."""
        try:
            template = self.get_template_by_name(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")

            # Validate required variables
            missing_vars = []
            for required_var in template.required_variables:
                if required_var not in variables:
                    missing_vars.append(required_var)

            if missing_vars:
                raise ValueError(f"Missing required variables: {missing_vars}")

            # Merge default data with provided data
            combined_variables = {**template.default_data, **variables}

            # Render templates
            title = template.title_template.format(**combined_variables)
            body = template.body_template.format(**combined_variables)

            return {
                "title": title,
                "body": body,
                "notification_type": template.notification_type,
                "category": template.category,
                "priority": template.priority,
                "data": combined_variables,
            }

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def get_template_variables(self, template_name: str) -> Dict[str, Any]:
        """Get template variable requirements."""
        try:
            template = self.get_template_by_name(template_name)
            if not template:
                return {"error": f"Template '{template_name}' not found"}

            return {
                "template_name": template.name,
                "required_variables": template.required_variables,
                "optional_variables": template.optional_variables,
                "default_data": template.default_data,
                "notification_type": template.notification_type,
                "category": template.category,
            }

        except Exception as e:
            logger.error(f"Failed to get template variables for {template_name}: {e}")
            return {"error": str(e)}


# Factory function for dependency injection
def get_notification_template_service(
    db: Session = Depends(get_db),
) -> NotificationTemplateService:
    """Get notification template service instance."""
    return NotificationTemplateService(db)
