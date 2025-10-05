"""
Context Analyzer Service

Analyzes course and environmental context for notification timing optimization.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Service for analyzing context factors that affect notification timing."""

    def __init__(self) -> None:
        pass

    async def analyze_course_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze course context to determine timing adjustments.

        Args:
            context: Course context information

        Returns:
            Analysis results with recommendations
        """
        logger.info(f"Analyzing course context: {list(context.keys())}")

        analysis: Dict[str, Any] = {
            "recommended_advance_minutes": 30,
            "confidence": 0.8,
            "factors": [],
        }

        # Location-based analysis
        location = context.get("location", "").lower()
        if "강남" in location or "hongdae" in location:
            analysis["recommended_advance_minutes"] = 45
            analysis["factors"].append("busy_location")

        # Day-based analysis
        date = context.get("date", "").lower()
        if date in ["friday", "saturday"]:
            analysis["recommended_advance_minutes"] += 15
            analysis["factors"].append("weekend_traffic")

        # Course type analysis
        course_type = context.get("course_type", "").lower()
        if "restaurant" in course_type:
            analysis["factors"].append("reservation_recommended")

        # Crowd level analysis
        crowd_level = context.get("expected_crowd_level", "").lower()
        if crowd_level == "high":
            analysis["recommended_advance_minutes"] += 15
            analysis["factors"].append("high_crowd")

        return analysis

    async def analyze_user_context(
        self, user_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user-specific context factors.

        Args:
            user_id: User identifier
            context: User context information

        Returns:
            User context analysis
        """
        logger.info(f"Analyzing user context for {user_id}")

        return {
            "user_activity_level": context.get("activity_level", "normal"),
            "preferred_advance_time": 30,
            "context_factors": list(context.keys()),
        }

    async def get_timing_recommendations(
        self, course_context: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive timing recommendations based on all context.

        Args:
            course_context: Course-related context
            user_context: User-related context

        Returns:
            Timing recommendations
        """
        course_analysis = await self.analyze_course_context(course_context)
        user_analysis = await self.analyze_user_context("", user_context)

        return {
            "recommended_advance_minutes": course_analysis[
                "recommended_advance_minutes"
            ],
            "confidence": course_analysis["confidence"],
            "course_factors": course_analysis["factors"],
            "user_factors": user_analysis.get("context_factors", []),
        }
