"""Sample places and guide services."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class SamplePlacesService:
    """Service for managing sample places and recommendations."""

    def __init__(self, db_session=None):
        self.db = db_session

    def get_sample_places(
        self, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get sample places for user exploration."""
        sample_places = [
            {
                "id": str(uuid4()),
                "name": "샘플 레스토랑",
                "category": "restaurant",
                "description": "맛있는 음식을 제공하는 레스토랑",
                "rating": 4.5,
                "price_level": 2,
                "location": {"latitude": 37.5665, "longitude": 126.9780},
                "tags": ["맛집", "분위기좋은"],
                "image_url": "https://example.com/image.jpg",
            },
            {
                "id": str(uuid4()),
                "name": "샘플 카페",
                "category": "cafe",
                "description": "편안한 분위기의 카페",
                "rating": 4.2,
                "price_level": 1,
                "location": {"latitude": 37.5665, "longitude": 126.9780},
                "tags": ["조용한", "커피맛집"],
                "image_url": "https://example.com/cafe.jpg",
            },
        ]

        if category:
            sample_places = [p for p in sample_places if p["category"] == category]

        return sample_places[:limit]

    def get_recommended_samples(
        self, user_preferences: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommended sample places based on user preferences."""
        all_samples = self.get_sample_places()

        # Simple recommendation based on category preferences
        preferred_categories = user_preferences.get("categories", [])
        if preferred_categories:
            recommended = [
                p for p in all_samples if p["category"] in preferred_categories
            ]
        else:
            recommended = all_samples

        return recommended[:limit]


class GuideService:
    """Service for providing user guides and tutorials."""

    def __init__(self, db_session=None):
        self.db = db_session

    def get_onboarding_guide(
        self, user_id: str, step: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get onboarding guide steps."""
        guide_steps = [
            {
                "step": 1,
                "title": "환영합니다!",
                "description": "hotly 앱에 오신 것을 환영합니다.",
                "action": "next",
                "content": "맛집과 핫플레이스를 발견하고 코스를 만들어보세요.",
            },
            {
                "step": 2,
                "title": "취향 설정",
                "description": "당신의 취향을 설정해주세요.",
                "action": "preferences",
                "content": "더 나은 추천을 위해 선호하는 카테고리를 선택하세요.",
            },
            {
                "step": 3,
                "title": "장소 탐색",
                "description": "주변 장소를 탐색해보세요.",
                "action": "explore",
                "content": "지도에서 관심 있는 장소를 찾아보세요.",
            },
        ]

        if step is not None:
            guide_steps = [s for s in guide_steps if s["step"] == step]

        return {
            "user_id": user_id,
            "guide_steps": guide_steps,
            "total_steps": len(guide_steps),
            "current_step": step or 1,
        }

    def get_feature_guide(self, feature_name: str) -> Dict[str, Any]:
        """Get guide for specific feature."""
        feature_guides = {
            "place_save": {
                "title": "장소 저장하기",
                "description": "마음에 드는 장소를 저장하는 방법",
                "steps": [
                    "장소 상세 페이지에서 하트 아이콘을 탭하세요",
                    "저장된 장소는 '내 장소'에서 확인할 수 있습니다",
                ],
            },
            "course_create": {
                "title": "코스 만들기",
                "description": "여러 장소를 연결하여 코스를 만드는 방법",
                "steps": [
                    "지도에서 장소들을 선택하세요",
                    "코스 순서를 정하고 저장하세요",
                    "친구들과 코스를 공유해보세요",
                ],
            },
        }

        return feature_guides.get(
            feature_name,
            {
                "title": "기능 가이드",
                "description": "해당 기능에 대한 가이드가 준비 중입니다.",
                "steps": [],
            },
        )


class FirstCourseGuideService:
    """Service for first course creation guide."""

    def __init__(self, db_session=None):
        self.db = db_session

    def start_first_course_guide(self, user_id: str) -> Dict[str, Any]:
        """Start the first course creation guide."""
        return {
            "user_id": user_id,
            "guide_id": str(uuid4()),
            "status": "started",
            "current_step": 1,
            "total_steps": 4,
            "steps": [
                {
                    "step": 1,
                    "title": "첫 번째 장소 선택",
                    "description": "시작점이 될 장소를 선택하세요",
                    "action": "select_start_place",
                },
                {
                    "step": 2,
                    "title": "두 번째 장소 추가",
                    "description": "다음으로 방문할 장소를 추가하세요",
                    "action": "add_next_place",
                },
                {
                    "step": 3,
                    "title": "코스 순서 확인",
                    "description": "장소 순서를 확인하고 조정하세요",
                    "action": "arrange_order",
                },
                {
                    "step": 4,
                    "title": "코스 완성",
                    "description": "코스에 이름을 지어주고 저장하세요",
                    "action": "save_course",
                },
            ],
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_guide_progress(self, user_id: str, guide_id: str) -> Dict[str, Any]:
        """Get progress of first course guide."""
        # In a real implementation, this would fetch from database
        return {
            "user_id": user_id,
            "guide_id": guide_id,
            "status": "in_progress",
            "current_step": 2,
            "total_steps": 4,
            "completion_percentage": 50.0,
            "next_action": "add_next_place",
        }

    def complete_guide_step(
        self, user_id: str, guide_id: str, step: int, step_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete a guide step."""
        return {
            "user_id": user_id,
            "guide_id": guide_id,
            "completed_step": step,
            "next_step": step + 1 if step < 4 else None,
            "status": "completed" if step >= 4 else "in_progress",
            "step_result": step_data,
            "completed_at": datetime.utcnow().isoformat(),
        }

    def get_sample_course(self) -> Dict[str, Any]:
        """Get a sample course for demonstration."""
        return {
            "course_id": str(uuid4()),
            "name": "강남 맛집 투어",
            "description": "강남 지역의 인기 맛집들을 둘러보는 코스",
            "places": [
                {
                    "order": 1,
                    "place_name": "유명 레스토랑",
                    "category": "restaurant",
                    "estimated_time": 90,
                },
                {
                    "order": 2,
                    "place_name": "디저트 카페",
                    "category": "cafe",
                    "estimated_time": 60,
                },
            ],
            "total_duration": 150,
            "difficulty": "easy",
            "created_at": datetime.utcnow().isoformat(),
        }
