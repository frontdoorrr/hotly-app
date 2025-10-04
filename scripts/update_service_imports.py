#!/usr/bin/env python3
"""
Script to update import paths after services reorganization.

This script updates all imports from:
  from app.services.service_name import ...

To:
  from app.services.category.service_name import ...
"""

import re
from pathlib import Path
from typing import Dict

# Mapping of service files to their new categories
SERVICE_MAPPING: Dict[str, str] = {
    # Notifications (10 files)
    "notification_service": "notifications",
    "notification_scheduler": "notifications",
    "notification_settings_service": "notifications",
    "notification_template_service": "notifications",
    "notification_history_service": "notifications",
    "notification_analytics_service": "notifications",
    "personalized_notification_service": "notifications",
    "ml_notification_optimizer": "notifications",
    "fcm_service": "notifications",
    # Search (12 files)
    "search_service": "search",
    "search_analytics_service": "search",
    "search_cache_service": "search",
    "search_diversity_service": "search",
    "search_feedback_service": "search",
    "search_history_service": "search",
    "search_optimization_service": "search",
    "search_performance_service": "search",
    "search_ranking_service": "search",
    "autocomplete_service": "search",
    "favorite_searches_service": "search",
    "search_schemas": "search",
    # Places (8 files)
    "place_analysis_service": "places",
    "place_classification_service": "places",
    "place_classifier": "places",
    "place_extractor": "places",
    "duplicate_detector": "places",
    "category_classifier": "places",
    "content_extractor": "places",
    # Courses (5 files)
    "course_optimizer": "courses",
    "course_generator_service": "courses",
    "course_recommender": "courses",
    "course_sharing_service": "courses",
    # Maps (7 files)
    "map_service": "maps",
    "kakao_map_service": "maps",
    "location_service": "maps",
    "geo_service": "maps",
    "route_calculator": "maps",
    "travel_time_calculator": "maps",
    # ML (10 files)
    "ml_engine": "ml",
    "ml_timing_model": "ml",
    "personalization_engine": "ml",
    "personalization_service": "ml",
    "personalized_content_engine": "ml",
    "user_behavior_analytics_service": "ml",
    "user_engagement_analyzer": "ml",
    "real_time_analyzer": "ml",
    "context_analyzer": "ml",
    # Monitoring (7 files)
    "performance_service": "monitoring",
    "performance_metrics_service": "monitoring",
    "performance_monitoring_service": "monitoring",
    "logging_service": "monitoring",
    "cache_manager": "monitoring",
    "redis_queue": "monitoring",
    # Auth (7 files)
    "firebase_auth_service": "auth",
    "supabase_auth_service": "auth",
    "onboarding_service": "auth",
    "user_data_service": "auth",
    "user_preference_service": "auth",
    "preference_service": "auth",
    # Ranking (6 files)
    "filter_service": "ranking",
    "advanced_filter_service": "ranking",
    "sort_service": "ranking",
    "realtime_ranking_service": "ranking",
    "ranking_experiment_service": "ranking",
    # Experiments (2 files)
    "ab_testing_service": "experiments",
    # Content (5 files)
    "dynamic_content_service": "content",
    "cdn_service": "content",
    "progressive_loading_service": "content",
    "sample_guide_service": "content",
    # Utils (3 files)
    "feedback_service": "utils",
    "tag_service": "utils",
}


def update_imports_in_file(file_path: Path) -> int:
    """Update import statements in a single file."""
    if not file_path.exists():
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = 0

    # Pattern 1: from app.services.service_name import ...
    for service_name, category in SERVICE_MAPPING.items():
        # Match: from app.services.service_name import ...
        pattern1 = rf"from app\.services\.{service_name} import"
        replacement1 = f"from app.services.{category}.{service_name} import"

        if re.search(pattern1, content):
            content = re.sub(pattern1, replacement1, content)
            changes += 1

        # Match: import app.services.service_name
        pattern2 = rf"import app\.services\.{service_name}\b"
        replacement2 = f"import app.services.{category}.{service_name}"

        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            changes += 1

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Updated {changes} imports in: {file_path}")
        return changes

    return 0


def main():
    """Main function to update all imports."""
    project_root = Path(__file__).parent.parent

    # Directories to scan
    directories = [
        project_root / "app",
        project_root / "tests",
    ]

    total_files = 0
    total_changes = 0

    print("🔄 Updating service import paths...")
    print("=" * 60)

    for directory in directories:
        if not directory.exists():
            continue

        # Find all Python files
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            changes = update_imports_in_file(py_file)
            if changes > 0:
                total_files += 1
                total_changes += changes

    print("=" * 60)
    print(f"✨ Complete! Updated {total_changes} imports in {total_files} files")


if __name__ == "__main__":
    main()
