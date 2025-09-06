"""Tests for tag management service."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.place import Place
from app.services.tag_service import TagService
from app.utils.tag_normalizer import TagNormalizer


class TestTagNormalizer:
    """Test tag normalization utilities."""

    def test_normalize_single_tag_success(self):
        """Test successful tag normalization."""
        # Given: Various raw tags
        test_cases = [
            ("  카페  ", "카페"),
            ("CAFE", "커피"),  # Synonym normalization
            ("커피숍", "커피"),
            ("맛집!@#", "맛집"),
            ("Restaurant", "음식"),
        ]

        for raw_tag, expected in test_cases:
            # When: Normalize tag
            result = TagNormalizer.normalize_tag(raw_tag)

            # Then: Should return normalized version
            assert result == expected

    def test_normalize_tag_rejection(self):
        """Test tag rejection for invalid inputs."""
        # Given: Invalid tags
        invalid_tags = ["", "   ", "가", "a", "매우긴태그이름입니다정말길어요", "의", "the"]

        for invalid_tag in invalid_tags:
            # When: Normalize invalid tag
            result = TagNormalizer.normalize_tag(invalid_tag)

            # Then: Should return empty string
            assert result == ""

    def test_normalize_tags_list(self):
        """Test normalizing list of tags."""
        # Given: Mixed tag list
        raw_tags = ["카페", "CAFE", "  음식점  ", "", "커피숍", "카페"]  # Include duplicates

        # When: Normalize tag list
        result = TagNormalizer.normalize_tags(raw_tags)

        # Then: Should return unique normalized tags
        expected = ["카페", "커피", "음식"]  # Note: "카페" and "CAFE" both normalize to "커피"
        assert len(result) == len(set(result))  # No duplicates
        assert "커피" in result
        assert "음식" in result

    def test_extract_tags_from_text(self):
        """Test tag extraction from text content."""
        # Given: Text with potential tags
        text = "스타벅스는 커피가 맛있는 카페입니다. 조용하고 데이트하기 좋은 곳이에요."

        # When: Extract tags
        result = TagNormalizer.extract_tags_from_text(text, max_tags=5)

        # Then: Should extract relevant tags
        assert "커피" in result
        assert "데이트" in result
        assert len(result) <= 5

    def test_suggest_similar_tags(self):
        """Test similar tag suggestions."""
        # Given: Input tag and existing tags
        existing_tags = ["커피", "카페라떼", "아메리카노", "음식", "맛집"]
        input_tag = "커피숍"

        # When: Get similar tag suggestions
        result = TagNormalizer.suggest_similar_tags(input_tag, existing_tags)

        # Then: Should suggest similar tags
        assert len(result) <= 5
        if result:
            assert any("커피" in tag for tag in result)

    def test_categorize_tags(self):
        """Test tag categorization."""
        # Given: Mixed tags
        tags = ["커피", "데이트", "조용", "저렴", "실내", "맛집"]

        # When: Categorize tags
        result = TagNormalizer.categorize_tags(tags)

        # Then: Should group tags by category
        assert isinstance(result, dict)
        assert "장소타입" in result
        assert "분위기" in result
        assert "대상" in result


class TestTagService:
    """Test tag management service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def tag_service(self, mock_db):
        """Create tag service instance."""
        return TagService(mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()

    @pytest.fixture
    def sample_place_id(self):
        """Sample place ID for testing."""
        return uuid4()

    def test_validate_and_normalize_tags_success(self, tag_service):
        """Test successful tag validation and normalization."""
        # Given: Mixed quality tags
        raw_tags = ["  카페  ", "COFFEE", "음식점", "", "커피숍", "카페"]

        # When: Validate and normalize
        result = tag_service.validate_and_normalize_tags(raw_tags)

        # Then: Should return validation results
        assert "normalized_tags" in result
        assert "warnings" in result
        assert "rejected_tags" in result
        assert len(result["normalized_tags"]) > 0

    def test_validate_tags_with_rejections(self, tag_service):
        """Test tag validation with rejected tags."""
        # Given: Tags with invalid entries
        raw_tags = ["", "가", "매우긴태그이름입니다정말길어요너무길다", "좋은태그"]

        # When: Validate tags
        result = tag_service.validate_and_normalize_tags(raw_tags)

        # Then: Should reject invalid tags
        assert len(result["rejected_tags"]) > 0
        assert len(result["warnings"]) > 0

    def test_add_tags_to_place_success(
        self, tag_service, mock_db, sample_place_id, sample_user_id
    ):
        """Test adding tags to place."""
        # Given: Mock place and tags
        mock_place = Mock(spec=Place)
        mock_place.tags = ["기존태그"]
        mock_place.add_tag = Mock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_place

        tags_to_add = ["새태그", "커피"]

        # When: Add tags to place
        result = tag_service.add_tags_to_place(
            place_id=sample_place_id, user_id=sample_user_id, tags=tags_to_add
        )

        # Then: Should add normalized tags
        assert isinstance(result, list)
        mock_db.commit.assert_called_once()

    def test_add_tags_place_not_found(
        self, tag_service, mock_db, sample_place_id, sample_user_id
    ):
        """Test adding tags to non-existent place."""
        # Given: No place found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # When/Then: Should raise error
        with pytest.raises(ValueError, match="not found or access denied"):
            tag_service.add_tags_to_place(
                place_id=sample_place_id, user_id=sample_user_id, tags=["태그"]
            )

    def test_remove_tags_from_place(
        self, tag_service, mock_db, sample_place_id, sample_user_id
    ):
        """Test removing tags from place."""
        # Given: Mock place with tags
        mock_place = Mock(spec=Place)
        mock_place.remove_tag = Mock(return_value=True)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_place

        tags_to_remove = ["기존태그"]

        # When: Remove tags
        result = tag_service.remove_tags_from_place(
            place_id=sample_place_id, user_id=sample_user_id, tags=tags_to_remove
        )

        # Then: Should remove tags
        assert isinstance(result, list)
        mock_db.commit.assert_called_once()

    def test_suggest_tags_for_place(self, tag_service, sample_user_id):
        """Test tag suggestions for place."""
        # Given: Place information
        place_name = "스타벅스 강남점"
        place_description = "커피가 맛있는 조용한 카페"

        # When: Get tag suggestions
        result = tag_service.suggest_tags_for_place(
            place_name=place_name,
            place_description=place_description,
            user_id=sample_user_id,
            max_suggestions=5,
        )

        # Then: Should suggest relevant tags
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_get_tag_suggestions_with_query(self, tag_service, mock_db, sample_user_id):
        """Test tag autocomplete suggestions."""
        # Given: Mock database with tag statistics
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            Mock(tag="커피", count=10),
            Mock(tag="커피숍", count=5),
        ]

        # When: Get suggestions for query
        result = tag_service.get_tag_suggestions(
            query="커", user_id=sample_user_id, limit=10
        )

        # Then: Should return matching suggestions
        assert isinstance(result, list)

    def test_get_tag_statistics(self, tag_service, mock_db, sample_user_id):
        """Test tag statistics calculation."""
        # Given: Mock places with tags
        mock_places = [
            Mock(tags=["커피", "조용"]),
            Mock(tags=["음식", "커피"]),
            Mock(tags=["데이트", "커피"]),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_places

        # When: Get tag statistics
        result = tag_service.get_tag_statistics(user_id=sample_user_id)

        # Then: Should return comprehensive statistics
        assert "total_unique_tags" in result
        assert "total_tag_usage" in result
        assert "most_used_tags" in result
        assert "tag_categories" in result
        assert "average_tags_per_place" in result

    def test_merge_duplicate_tags(self, tag_service, mock_db, sample_user_id):
        """Test merging duplicate/similar tags."""
        # Given: Mock tag data with potential duplicates
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            Mock(tag="커피", count=10),
            Mock(tag="cafe", count=3),  # Should merge with "커피"
            Mock(tag="음식", count=8),
        ]

        mock_places = [
            Mock(tags=["커피", "cafe"], save=Mock()),
            Mock(tags=["음식"], save=Mock()),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_places

        # When: Merge duplicate tags
        result = tag_service.merge_duplicate_tags(user_id=sample_user_id)

        # Then: Should return merge summary
        assert "merges_performed" in result
        assert "operations" in result
        assert isinstance(result["operations"], list)

    def test_get_trending_tags(self, tag_service, mock_db):
        """Test trending tags calculation."""
        # Given: Mock recent tag data
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            Mock(tag="신상카페", recent_count=5),
            Mock(tag="힙한곳", recent_count=3),
        ]

        # When: Get trending tags
        result = tag_service.get_trending_tags(days=7, limit=5)

        # Then: Should return trending analysis
        assert isinstance(result, list)
