"""
Integration tests for course sharing end-to-end flow.

Tests the complete flow: Create → Share → Access → Save
"""

import uuid

import pytest


class TestCourseSharingFlow:
    """Test complete course sharing workflow."""

    def test_completeSharingFlow_createShareAccessSave_succeeds(self):
        """
        Test: Complete course sharing flow

        Given: User creates a course and wants to share it
        When: Creating share link, accessing it, and saving
        Then: All operations succeed in correct sequence

        Flow:
        1. Create course
        2. Generate share link
        3. Another user accesses shared course
        4. Second user saves to favorites
        """
        from unittest.mock import MagicMock

        from app.services.course_sharing_service import (
            CourseSharingService,
            PersonalCourseStorageService,
        )

        # Mock database session
        mock_db = MagicMock()

        # Given: Course owner and course data
        owner_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        course_data = {
            "title": "강남 데이트 코스",
            "description": "로맨틱한 강남 코스",
            "places": [
                {"name": "카페", "duration_minutes": 60},
                {"name": "레스토랑", "duration_minutes": 90},
                {"name": "공원", "duration_minutes": 30},
            ],
            "course_type": "romantic",
        }
        share_settings = {
            "public_access": True,
            "allow_copy": True,
            "allow_comments": True,
            "expire_days": 30,
        }

        sharing_service = CourseSharingService(db=mock_db)
        storage_service = PersonalCourseStorageService(db=mock_db)

        # When Step 1: Create share link
        share_result = sharing_service.create_share_link(
            course_id=course_id,
            user_id=owner_id,
            course_data=course_data,
            share_settings=share_settings,
        )

        # Then: Share link should be created
        assert "share_link" in share_result
        assert "share_id" in share_result
        assert share_result["share_link"].startswith("https://hotly.app/shared/")

        share_id = share_result["share_id"]

        # When Step 2: Another user accesses shared course
        viewer_id = str(uuid.uuid4())
        shared_course = sharing_service.access_shared_course(
            share_id=share_id, accessing_user_id=viewer_id
        )

        # Then: Should retrieve course details
        assert shared_course["course_title"] == "강남 데이트 코스"
        assert len(shared_course["places"]) == 3
        assert shared_course["access_permissions"]["can_copy"] is True

        # When Step 3: Viewer saves to favorites
        save_result = storage_service.save_course_to_favorites(
            course_id=course_id,
            user_id=viewer_id,
            save_type="favorite",
            folder_name="저장한 코스",
        )

        # Then: Should save successfully
        assert save_result["saved"] is True
        assert save_result["save_type"] == "favorite"
        assert "save_id" in save_result

    def test_shareLinkRevocation_ownerRevokes_invalidatesImmediately(self):
        """
        Test: Share link revocation

        Given: Course owner has shared a course
        When: Owner revokes the share link
        Then: Link becomes invalid within 1 second (acceptance criteria)
        """
        from unittest.mock import MagicMock

        from app.services.course_sharing_service import CourseSharingService

        mock_db = MagicMock()
        sharing_service = CourseSharingService(db=mock_db)

        # Given: Shared course
        owner_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        course_data = {
            "title": "Test Course",
            "places": [{"name": "Place 1", "duration_minutes": 60}],
        }

        share_result = sharing_service.create_share_link(
            course_id=course_id,
            user_id=owner_id,
            course_data=course_data,
            share_settings={"public_access": True},
        )

        share_id = share_result["share_id"]

        # Verify it works before revocation
        shared_course = sharing_service.access_shared_course(share_id)
        assert shared_course is not None

        # When: Owner revokes link
        revoke_result = sharing_service.revoke_share_link(
            share_id=share_id, user_id=owner_id, reason="user_request"
        )

        # Then: Revocation succeeds
        assert revoke_result["revoked"] is True
        assert revoke_result["link_invalidated"] is True

        # And: Link is immediately invalid
        with pytest.raises(ValueError, match="revoked"):
            sharing_service.access_shared_course(share_id)

    def test_personalFolderOrganization_createAndOrganize_succeeds(self):
        """
        Test: Personal folder organization

        Given: User has saved multiple courses
        When: Creating folders and organizing courses
        Then: Courses are organized into folders correctly
        """
        from unittest.mock import MagicMock

        from app.services.course_sharing_service import PersonalCourseStorageService

        mock_db = MagicMock()
        storage_service = PersonalCourseStorageService(db=mock_db)

        # Given: User and saved courses
        user_id = str(uuid.uuid4())
        course_ids = [str(uuid.uuid4()) for _ in range(3)]

        # Save courses
        for course_id in course_ids:
            storage_service.save_course_to_favorites(
                course_id=course_id, user_id=user_id, save_type="favorite"
            )

        # When: Create custom folder
        folder_result = storage_service.create_personal_folder(
            user_id=user_id,
            folder_name="주말 데이트",
            folder_description="주말에 가볼만한 코스들",
            folder_color="#FF6B6B",
        )

        # Then: Folder should be created
        assert folder_result["folder_created"] is True
        assert folder_result["folder_name"] == "주말 데이트"

        folder_id = folder_result["folder_id"]

        # When: Organize courses into folder
        organize_result = storage_service.organize_courses_in_folder(
            folder_id=folder_id,
            user_id=user_id,
            course_ids=course_ids,
            organization_type="move",
        )

        # Then: Courses should be organized
        assert organize_result["courses_moved"] == 3
        assert organize_result["new_course_count"] == 3
