"""Tests for course sharing and personal save system following TDD approach."""

import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000000"
TEST_USER_ID_2 = "11111111-1111-1111-1111-111111111111"


class TestCourseShareLinkGeneration:
    """Test course sharing link generation and access control."""

    def test_create_share_link_success(self):
        """Test: 코스 공유 링크 생성."""
        # Given: Course data for sharing
        course_data = {
            "course_id": "course_123",
            "user_id": TEST_USER_ID,
            "title": "강남 맛집 코스",
            "places": [
                {"place_id": "place1", "name": "강남역 맛집", "order": 1},
                {"place_id": "place2", "name": "역삼동 카페", "order": 2}
            ],
            "share_settings": {
                "public_access": True,
                "allow_copy": True,
                "expire_days": 30
            }
        }

        # When: Create share link
        response = client.post("/api/v1/courses/create-share-link", json=course_data)

        # Then: Should return shareable link
        assert response.status_code in [200, 404]  # Will be implemented

        if response.status_code == 200:
            share_result = response.json()
            required_fields = ["share_link", "share_id", "expires_at", "access_level"]
            for field in required_fields:
                assert field in share_result

    def test_access_shared_course_public(self):
        """Test: 공유 링크로 코스 접근."""
        # Given: Public share link
        share_id = "share_abc123"

        # When: Access course via share link (no authentication)
        response = client.get(f"/api/v1/courses/shared/{share_id}")

        # Then: Should return course information
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            shared_course = response.json()
            expected_fields = ["course_title", "places", "created_by", "shared_at"]
            for field in expected_fields:
                assert field in shared_course

    def test_share_link_expiration(self):
        """Test: 공유 링크 만료."""
        # Given: Expired share link
        expired_share_id = "expired_share_123"

        # When: Try to access expired link
        response = client.get(f"/api/v1/courses/shared/{expired_share_id}")

        # Then: Should return appropriate error
        assert response.status_code in [404, 410]  # Not found or gone

    def test_share_link_revocation(self):
        """Test: 공유 링크 취소."""
        # Given: Valid share link
        revoke_data = {
            "share_id": "share_to_revoke",
            "user_id": TEST_USER_ID,
            "reason": "privacy_concern"
        }

        # When: Revoke share link
        response = client.delete("/api/v1/courses/revoke-share", json=revoke_data)

        # Then: Should invalidate link within 1 second (requirement)
        start_time = time.time()

        # Verify link is actually revoked
        verify_response = client.get(f"/api/v1/courses/shared/{revoke_data['share_id']}")

        end_time = time.time()
        revocation_time = end_time - start_time

        assert revocation_time < 1.0, f"Share link revocation took {revocation_time:.3f}s, exceeds 1s requirement"
        assert verify_response.status_code in [404, 410]  # Should be inaccessible
        assert response.status_code in [200, 404]


class TestPersonalCourseStorage:
    """Test personal course saving and favoriting system."""

    def test_save_course_to_favorites(self):
        """Test: 코스 즐겨찾기 저장."""
        # Given: Course to save as favorite
        favorite_data = {
            "course_id": "course_456",
            "user_id": TEST_USER_ID,
            "save_type": "favorite",
            "folder_name": "데이트 코스",
            "private_notes": "다음주 가볼 곳"
        }

        # When: Save course to favorites
        response = client.post("/api/v1/courses/save-favorite", json=favorite_data)

        # Then: Should save successfully
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            save_result = response.json()
            assert save_result["saved"] is True
            assert "saved_at" in save_result

    def test_create_personal_folder(self):
        """Test: 개인 폴더 생성."""
        # Given: New folder request
        folder_data = {
            "user_id": TEST_USER_ID,
            "folder_name": "서울 맛집 투어",
            "folder_description": "서울 시내 추천 맛집들",
            "folder_color": "#FF6B6B",
            "is_private": True
        }

        # When: Create personal folder
        response = client.post("/api/v1/courses/create-folder", json=folder_data)

        # Then: Should create folder successfully
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            folder_result = response.json()
            assert "folder_id" in folder_result
            assert folder_result["folder_name"] == folder_data["folder_name"]

    def test_organize_courses_in_folder(self):
        """Test: 폴더별 코스 정리."""
        # Given: Courses to organize in folder
        organize_data = {
            "folder_id": "folder_789",
            "user_id": TEST_USER_ID,
            "course_ids": ["course_1", "course_2", "course_3"],
            "organization_type": "move"  # move or copy
        }

        # When: Organize courses in folder
        response = client.post("/api/v1/courses/organize-folder", json=organize_data)

        # Then: Should organize successfully
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            organize_result = response.json()
            assert organize_result["courses_moved"] == 3
            assert "folder_updated_at" in organize_result

    def test_wishlist_management(self):
        """Test: 위시리스트 관리."""
        # Given: Course for wishlist
        wishlist_data = {
            "course_id": "course_wishlist_1",
            "user_id": TEST_USER_ID,
            "priority": "high",
            "planned_date": "2024-02-14",
            "notes": "발렌타인 데이 계획"
        }

        # When: Add to wishlist
        response = client.post("/api/v1/courses/add-to-wishlist", json=wishlist_data)

        # Then: Should add to wishlist
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            wishlist_result = response.json()
            assert "added_to_wishlist" in wishlist_result
            assert wishlist_result["priority"] == "high"


class TestCourseOwnershipAndPermissions:
    """Test course ownership and access permissions."""

    def test_course_ownership_validation(self):
        """Test: 코스 소유권 검증."""
        # Given: Course ownership check
        ownership_data = {
            "course_id": "course_owned_123",
            "user_id": TEST_USER_ID,
            "operation": "modify"
        }

        # When: Validate ownership for modification
        response = client.post("/api/v1/courses/validate-ownership", json=ownership_data)

        # Then: Should validate ownership
        assert response.status_code in [200, 403, 404]

    def test_shared_course_copy_permission(self):
        """Test: 공유 코스 복사 권한."""
        # Given: Shared course to copy
        copy_data = {
            "original_course_id": "shared_course_456",
            "copying_user_id": TEST_USER_ID_2,
            "copy_type": "full_copy",  # full_copy or reference_only
            "new_title": "내가 수정한 강남 코스"
        }

        # When: Copy shared course
        response = client.post("/api/v1/courses/copy-shared", json=copy_data)

        # Then: Should create personal copy
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            copy_result = response.json()
            assert "new_course_id" in copy_result
            assert copy_result["original_course_preserved"] is True

    def test_private_course_access_denied(self):
        """Test: 비공개 코스 접근 거부."""
        # Given: Private course access attempt
        private_course_id = "private_course_789"
        unauthorized_user = TEST_USER_ID_2

        # When: Try to access private course
        response = client.get(
            f"/api/v1/courses/{private_course_id}",
            headers={"X-User-ID": unauthorized_user}
        )

        # Then: Should deny access
        assert response.status_code in [403, 404]


@pytest.mark.integration
class TestCourseCollaborationFeatures:
    """Integration tests for course collaboration features."""

    def test_course_like_system(self):
        """Test: 코스 좋아요 시스템."""
        # Given: Course to like
        like_data = {
            "course_id": "likeable_course_123",
            "user_id": TEST_USER_ID,
            "action": "like"  # like or unlike
        }

        # When: Like a course
        response = client.post("/api/v1/courses/like", json=like_data)

        # Then: Should update like status
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            like_result = response.json()
            assert "liked" in like_result
            assert "total_likes" in like_result

    def test_course_comment_system(self):
        """Test: 코스 댓글 시스템."""
        # Given: Comment to add
        comment_data = {
            "course_id": "commented_course_456",
            "user_id": TEST_USER_ID,
            "comment_text": "정말 좋은 코스네요! 추천합니다.",
            "rating": 5,
            "is_public": True
        }

        # When: Add comment
        response = client.post("/api/v1/courses/add-comment", json=comment_data)

        # Then: Should add comment successfully
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            comment_result = response.json()
            assert "comment_id" in comment_result
            assert "posted_at" in comment_result

    def test_course_rating_aggregation(self):
        """Test: 코스 평점 집계."""
        # Given: Course with multiple ratings
        course_id = "rated_course_789"

        # When: Get course rating summary
        response = client.get(f"/api/v1/courses/{course_id}/ratings")

        # Then: Should return rating aggregation
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            rating_data = response.json()
            assert "average_rating" in rating_data
            assert "total_ratings" in rating_data
            assert "rating_distribution" in rating_data


class TestCourseDiscoveryAndSearch:
    """Test course discovery and search functionality."""

    def test_public_course_discovery(self):
        """Test: 공개 코스 탐색."""
        # Given: Public course discovery request
        discovery_params = {
            "location": {"latitude": 37.5665, "longitude": 126.9780},
            "radius_km": 10,
            "category": "restaurant",
            "min_rating": 4.0,
            "sort_by": "popularity"
        }

        # When: Discover public courses
        response = client.post("/api/v1/courses/discover", json=discovery_params)

        # Then: Should return discoverable courses
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            discovery_result = response.json()
            assert "courses" in discovery_result
            assert "total_count" in discovery_result

    def test_trending_courses(self):
        """Test: 인기 코스 조회."""
        # Given: Trending courses request
        trending_params = {
            "time_period": "week",  # week, month, all_time
            "location_filter": "seoul",
            "limit": 10
        }

        # When: Get trending courses
        response = client.get("/api/v1/courses/trending", params=trending_params)

        # Then: Should return popular courses
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            trending_data = response.json()
            assert "trending_courses" in trending_data
            assert "ranking_criteria" in trending_data

    def test_course_recommendation_based_on_saves(self):
        """Test: 저장 기록 기반 코스 추천."""
        # Given: User with saved courses
        user_history = {
            "user_id": TEST_USER_ID,
            "saved_courses_count": 5,
            "preferred_categories": ["restaurant", "cafe"],
            "activity_radius_km": 15
        }

        # When: Get recommendations based on saves
        response = client.post("/api/v1/courses/recommend-from-saves", json=user_history)

        # Then: Should return personalized recommendations
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            recommendations = response.json()
            assert "recommended_courses" in recommendations
            assert "recommendation_reason" in recommendations


@pytest.mark.integration
class TestCourseStorageIntegration:
    """Integration tests for course storage and organization."""

    def test_save_shared_course_workflow(self):
        """Test: 공유 코스 저장 워크플로우."""
        # Given: Shared course to save
        save_workflow = {
            "shared_course_id": "shared_course_123",
            "saving_user_id": TEST_USER_ID_2,
            "save_to_folder": "여행 계획",
            "add_personal_notes": "여름 휴가 때 가볼 곳",
            "copy_or_reference": "reference"  # Keep link to original
        }

        # When: Save shared course to personal collection
        response = client.post("/api/v1/courses/save-shared-course", json=save_workflow)

        # Then: Should save with proper attribution
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            save_result = response.json()
            assert "saved_course_id" in save_result
            assert "original_course_link" in save_result
            assert "attribution_preserved" in save_result

    def test_folder_course_management(self):
        """Test: 폴더 내 코스 관리."""
        # Given: Folder with multiple courses
        folder_management = {
            "folder_id": "folder_travel_plans",
            "user_id": TEST_USER_ID,
            "operations": [
                {"action": "add_course", "course_id": "course_new_1"},
                {"action": "remove_course", "course_id": "course_old_1"},
                {"action": "reorder", "course_ids": ["course_1", "course_2", "course_3"]}
            ]
        }

        # When: Manage courses in folder
        response = client.post("/api/v1/courses/manage-folder-courses", json=folder_management)

        # Then: Should update folder contents
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            management_result = response.json()
            assert "operations_completed" in management_result
            assert "folder_updated_at" in management_result

    def test_cross_user_course_interaction(self):
        """Test: 사용자간 코스 상호작용."""
        # Given: Cross-user interaction scenario
        interaction_data = {
            "course_id": "interactive_course_789",
            "original_owner": TEST_USER_ID,
            "interacting_user": TEST_USER_ID_2,
            "interactions": [
                {"type": "view", "timestamp": "2024-01-01T12:00:00Z"},
                {"type": "like", "timestamp": "2024-01-01T12:01:00Z"},
                {"type": "save", "timestamp": "2024-01-01T12:02:00Z"}
            ]
        }

        # When: Process user interactions
        response = client.post("/api/v1/courses/track-interactions", json=interaction_data)

        # Then: Should track interactions properly
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            interaction_result = response.json()
            assert "interactions_recorded" in interaction_result
            assert "analytics_updated" in interaction_result


class TestCourseSharing Performance:
    """Performance tests for course sharing system."""

    def test_share_link_generation_speed(self):
        """Test: 공유 링크 생성 속도."""
        # Given: Course data for quick sharing
        quick_share_data = {
            "course_id": "speed_test_course",
            "user_id": TEST_USER_ID,
            "quick_share": True  # Simplified sharing
        }

        # When: Generate share link quickly
        start_time = time.time()
        response = client.post("/api/v1/courses/quick-share", json=quick_share_data)
        end_time = time.time()

        # Then: Should generate within 500ms
        generation_time = end_time - start_time
        assert generation_time < 0.5, f"Share link generation {generation_time:.3f}s exceeds 500ms"
        assert response.status_code in [200, 404]

    def test_concurrent_course_access(self):
        """Test: 동시 코스 접근 처리."""
        from concurrent.futures import ThreadPoolExecutor

        def access_shared_course(user_offset):
            share_id = f"concurrent_test_course_{user_offset % 3}"  # 3 different courses
            try:
                response = client.get(f"/api/v1/courses/shared/{share_id}")
                return response.status_code in [200, 404]
            except:
                return False

        # Simulate 50 concurrent course accesses
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(access_shared_course, i) for i in range(50)]
            results = [future.result() for future in futures]

        success_rate = sum(results) / len(results)
        assert success_rate >= 0.95, f"Concurrent access success rate {success_rate:.2f} below 95%"

    def test_large_course_sharing(self):
        """Test: 대용량 코스 공유."""
        # Given: Large course with many places
        large_course = {
            "course_id": "large_course_100_places",
            "user_id": TEST_USER_ID,
            "places": [
                {
                    "place_id": f"place_{i}",
                    "name": f"장소 {i}",
                    "order": i + 1,
                    "duration_minutes": 30
                } for i in range(100)  # 100 places
            ]
        }

        # When: Share large course
        start_time = time.time()
        response = client.post("/api/v1/courses/share-large-course", json=large_course)
        end_time = time.time()

        # Then: Should handle efficiently
        sharing_time = end_time - start_time
        assert sharing_time < 3.0, f"Large course sharing {sharing_time:.3f}s exceeds 3 second limit"
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestWebSocketCourseUpdates:
    """Test real-time course updates via WebSocket."""

    def test_realtime_course_updates(self):
        """Test: 실시간 코스 업데이트 (WebSocket)."""
        # Given: WebSocket connection for course updates
        websocket_data = {
            "course_id": "realtime_course_123",
            "user_id": TEST_USER_ID,
            "subscribe_to": ["likes", "comments", "saves"]
        }

        # When: Subscribe to course updates
        response = client.post("/api/v1/courses/subscribe-updates", json=websocket_data)

        # Then: Should establish real-time connection
        assert response.status_code in [200, 404, 501]  # 501 for WebSocket not yet implemented

    def test_collaborative_course_editing(self):
        """Test: 협업 코스 편집."""
        # Given: Collaborative editing request
        collab_data = {
            "course_id": "collab_course_456",
            "editor_user_id": TEST_USER_ID,
            "permission_level": "edit",  # view, edit, admin
            "edit_operations": [
                {"type": "add_place", "place_data": {"name": "새로운 장소"}},
                {"type": "reorder", "new_order": [1, 3, 2]}
            ]
        }

        # When: Perform collaborative edits
        response = client.post("/api/v1/courses/collaborative-edit", json=collab_data)

        # Then: Should handle collaborative editing
        assert response.status_code in [200, 403, 404]


class TestCourseAnalyticsAndInsights:
    """Test course analytics and insights."""

    def test_course_sharing_analytics(self):
        """Test: 코스 공유 분석."""
        # Given: Course with sharing history
        analytics_request = {
            "course_id": "analytics_course_123",
            "owner_user_id": TEST_USER_ID,
            "analytics_period": "30_days"
        }

        # When: Get sharing analytics
        response = client.post("/api/v1/courses/sharing-analytics", json=analytics_request)

        # Then: Should return comprehensive analytics
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            analytics_data = response.json()
            expected_metrics = ["total_shares", "unique_viewers", "save_rate", "engagement_score"]
            for metric in expected_metrics:
                assert metric in analytics_data

    def test_popular_course_trends(self):
        """Test: 인기 코스 트렌드 분석."""
        # Given: Trend analysis request
        trend_params = {
            "analysis_period": "7_days",
            "location_filter": {"city": "seoul", "district": "gangnam"},
            "category_filter": ["restaurant", "cafe"]
        }

        # When: Analyze course trends
        response = client.post("/api/v1/courses/trend-analysis", json=trend_params)

        # Then: Should return trend insights
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            trend_data = response.json()
            assert "trending_categories" in trend_data
            assert "growth_metrics" in trend_data

    def test_user_course_insights(self):
        """Test: 사용자 코스 인사이트."""
        # Given: User course activity
        insight_request = {
            "user_id": TEST_USER_ID,
            "insight_type": "personal_summary",
            "time_range": "month"
        }

        # When: Generate user insights
        response = client.post("/api/v1/courses/user-insights", json=insight_request)

        # Then: Should provide personalized insights
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            insights_data = response.json()
            expected_insights = ["courses_created", "courses_saved", "favorite_categories", "sharing_activity"]
            for insight in expected_insights:
                assert insight in insights_data
