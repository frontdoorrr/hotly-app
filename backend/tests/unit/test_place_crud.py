"""
Unit tests for Place CRUD operations with geographical and filtering capabilities.

Follows TDD methodology with comprehensive coverage of place management functionality.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session
from tests.utils.test_helpers import MockFactory, TestDataBuilder

from app.crud.place import place as place_crud
from app.models.place import Place, PlaceCategory, PlaceStatus
from app.schemas.place import PlaceCreate, PlaceListRequest, PlaceUpdate


class TestPlaceCRUDOperations:
    """Test basic CRUD operations for places."""

    def test_create_with_user_validInput_createsPlace(self, mock_db_session):
        """Test place creation with user association."""
        # Given
        user_id = uuid4()
        place_data = TestDataBuilder().with_cafe_content().build_place_create()

        # When
        result = place_crud.create_with_user(
            mock_db_session, obj_in=place_data, user_id=user_id
        )

        # Then
        assert result is not None
        assert result.user_id == user_id
        assert result.name == place_data.name
        assert result.category == place_data.category
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_with_user_coordinatesProvided_setsCoordinates(
        self, mock_db_session
    ):
        """Test place creation with geographical coordinates."""
        # Given
        user_id = uuid4()
        place_data = PlaceCreate(
            name="Test Restaurant",
            category=PlaceCategory.RESTAURANT,
            latitude=37.5665,
            longitude=126.9780,
        )

        # When
        with patch.object(Place, "set_coordinates") as mock_set_coords:
            result = place_crud.create_with_user(
                mock_db_session, obj_in=place_data, user_id=user_id
            )

        # Then
        mock_set_coords.assert_called_once_with(37.5665, 126.9780)

    def test_get_by_user_existingPlace_returnsPlace(self, mock_db_session):
        """Test retrieving place by user and place ID."""
        # Given
        user_id = uuid4()
        place_id = uuid4()
        expected_place = MockFactory.create_place_model(
            user_id=user_id, place_id=place_id
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            expected_place
        )

        # When
        result = place_crud.get_by_user(
            mock_db_session, user_id=user_id, place_id=place_id
        )

        # Then
        assert result == expected_place
        mock_db_session.query.assert_called_once_with(Place)

    def test_get_by_user_nonExistingPlace_returnsNone(self, mock_db_session):
        """Test retrieving non-existing place returns None."""
        # Given
        user_id = uuid4()
        place_id = uuid4()

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # When
        result = place_crud.get_by_user(
            mock_db_session, user_id=user_id, place_id=place_id
        )

        # Then
        assert result is None

    def test_get_multi_by_user_withPagination_returnsPagedResults(
        self, mock_db_session
    ):
        """Test retrieving multiple places with pagination."""
        # Given
        user_id = uuid4()
        expected_places = [MockFactory.create_place_model() for _ in range(5)]

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            expected_places
        )

        # When
        result = place_crud.get_multi_by_user(
            mock_db_session, user_id=user_id, limit=10, skip=0
        )

        # Then
        assert len(result) == 5
        assert result == expected_places
        mock_query.filter.assert_called_once()
        mock_query.filter.return_value.offset.assert_called_once_with(0)
        mock_query.filter.return_value.offset.return_value.limit.assert_called_once_with(
            10
        )

    def test_update_existingPlace_updatesSuccessfully(self, mock_db_session):
        """Test updating existing place."""
        # Given
        place_id = uuid4()
        place_update = PlaceUpdate(
            name="Updated Restaurant", category=PlaceCategory.RESTAURANT
        )
        existing_place = MockFactory.create_place_model(place_id=place_id)

        # When
        result = place_crud.update(
            mock_db_session, db_obj=existing_place, obj_in=place_update
        )

        # Then
        assert result.name == "Updated Restaurant"
        assert result.category == PlaceCategory.RESTAURANT
        mock_db_session.add.assert_called_once_with(existing_place)
        mock_db_session.commit.assert_called_once()


class TestPlaceFiltersAndSearch:
    """Test place filtering and search functionality."""

    def test_get_list_with_filters_categoryFilter_appliesFilter(self, mock_db_session):
        """Test filtering places by category."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(category=PlaceCategory.RESTAURANT, page=1, size=20)

        expected_places = [
            MockFactory.create_place_model(category=PlaceCategory.RESTAURANT)
        ]
        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            expected_places
        )
        mock_query.filter.return_value.count.return_value = 1

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        assert len(result) == 1
        assert total == 1
        assert result[0].category == PlaceCategory.RESTAURANT

    def test_get_list_with_filters_statusFilter_appliesFilter(self, mock_db_session):
        """Test filtering places by status."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(status=PlaceStatus.ACTIVE, page=1, size=20)

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_query.filter.return_value.count.return_value = 0

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        mock_query.filter.assert_called()

    def test_get_list_with_filters_tagsFilter_appliesOverlapFilter(
        self, mock_db_session
    ):
        """Test filtering places by tags with overlap operation."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(tags=["korean", "bbq"], page=1, size=20)

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_query.filter.return_value.count.return_value = 0

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        mock_query.filter.assert_called()

    def test_get_list_with_filters_geographicalSearch_appliesDistanceFilter(
        self, mock_db_session
    ):
        """Test geographical search with distance filtering."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(
            latitude=37.5665, longitude=126.9780, radius_km=5.0, page=1, size=20
        )

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_query.filter.return_value.filter.return_value.order_by.return_value.count.return_value = (
            0
        )

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        # Should apply distance filter and order by distance
        mock_query.filter.assert_called()

    def test_get_list_with_filters_searchQuery_appliesFullTextSearch(
        self, mock_db_session
    ):
        """Test full-text search functionality."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(
            search_query="korean restaurant gangnam", page=1, size=20
        )

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_query.filter.return_value.filter.return_value.count.return_value = 0

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        mock_query.filter.assert_called()

    def test_get_list_with_filters_combinedFilters_appliesAllFilters(
        self, mock_db_session
    ):
        """Test applying multiple filters simultaneously."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(
            category=PlaceCategory.RESTAURANT,
            status=PlaceStatus.ACTIVE,
            tags=["korean"],
            search_query="bbq",
            latitude=37.5665,
            longitude=126.9780,
            radius_km=2.0,
            page=1,
            size=10,
        )

        mock_query = mock_db_session.query.return_value
        # Chain the mock calls
        filtered_query = (
            mock_query.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value
        )
        filtered_query.offset.return_value.limit.return_value.all.return_value = []
        filtered_query.count.return_value = 0

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        assert len(result) == 0
        assert total == 0


class TestPlaceSpecialOperations:
    """Test special place operations like duplicate detection and statistics."""

    def test_get_nearby_places_withinRadius_returnsDistanceOrdered(
        self, mock_db_session
    ):
        """Test retrieving nearby places within radius."""
        # Given
        user_id = uuid4()
        latitude, longitude, radius_km = 37.5665, 126.9780, 5.0
        nearby_places = [MockFactory.create_place_model() for _ in range(3)]

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            nearby_places
        )

        # When
        result = place_crud.get_nearby_places(
            mock_db_session,
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=50,
        )

        # Then
        assert len(result) == 3
        assert result == nearby_places
        mock_db_session.query.assert_called_with(Place)

    def test_search_by_text_withQuery_returnsTextSearchResults(self, mock_db_session):
        """Test full-text search for places."""
        # Given
        user_id = uuid4()
        search_query = "korean bbq restaurant"
        expected_places = [MockFactory.create_place_model() for _ in range(2)]

        mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            expected_places
        )

        # When
        result = place_crud.search_by_text(
            mock_db_session, user_id=user_id, query=search_query, limit=20
        )

        # Then
        assert len(result) == 2
        assert result == expected_places

    def test_search_by_text_withCategoryFilter_appliesCategoryFilter(
        self, mock_db_session
    ):
        """Test text search with category filtering."""
        # Given
        user_id = uuid4()
        search_query = "korean restaurant"
        category = PlaceCategory.RESTAURANT
        expected_places = [MockFactory.create_place_model(category=category)]

        mock_db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            expected_places
        )

        # When
        result = place_crud.search_by_text(
            mock_db_session,
            user_id=user_id,
            query=search_query,
            category=category,
            limit=20,
        )

        # Then
        assert len(result) == 1
        assert result[0].category == category


class TestPlaceGeographicalOperations:
    """Test geographical operations and PostGIS functionality."""

    @patch("app.crud.place.ST_DWithin")
    @patch("app.crud.place.ST_GeogFromText")
    @patch("app.crud.place.ST_Distance")
    def test_geographical_search_withCoordinates_appliesDistanceFilter(
        self, mock_distance, mock_geog, mock_dwithin, mock_db_session
    ):
        """Test geographical search functionality using PostGIS operations."""
        # Given
        user_id = uuid4()
        request = PlaceListRequest(
            latitude=37.5665, longitude=126.9780, radius_km=5.0, page=1, size=20
        )

        nearby_places = [MockFactory.create_place_model() for _ in range(3)]
        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            nearby_places
        )
        mock_query.filter.return_value.filter.return_value.order_by.return_value.count.return_value = (
            3
        )

        # When
        result, total = place_crud.get_list_with_filters(
            mock_db_session, request=request, user_id=user_id
        )

        # Then
        assert len(result) == 3
        assert total == 3
        mock_geog.assert_called_once_with(
            f"POINT({request.longitude} {request.latitude})"
        )
        mock_dwithin.assert_called_once()
        mock_distance.assert_called_once()

    def test_coordinate_setting_validCoordinates_setsCorrectly(self, mock_db_session):
        """Test setting coordinates on place creation."""
        # Given
        user_id = uuid4()
        latitude, longitude = 37.5665, 126.9780
        place_data = PlaceCreate(
            name="Test Place", latitude=latitude, longitude=longitude
        )

        # When
        with patch.object(Place, "set_coordinates") as mock_set_coords:
            place_crud.create_with_user(
                mock_db_session, obj_in=place_data, user_id=user_id
            )

        # Then
        mock_set_coords.assert_called_once_with(latitude, longitude)


class TestPlaceValidationAndErrorHandling:
    """Test validation and error handling scenarios."""

    def test_create_with_user_invalidLatitude_raisesValidationError(
        self, mock_db_session
    ):
        """Test place creation with invalid latitude raises validation error."""
        # Given
        user_id = uuid4()
        invalid_place = PlaceCreate(
            name="Test Place", latitude=91.0, longitude=126.9780  # Invalid: > 90
        )

        # When/Then
        with pytest.raises(Exception):  # Could be ValidationError or similar
            place_crud.create_with_user(
                mock_db_session, obj_in=invalid_place, user_id=user_id
            )

    def test_create_with_user_invalidLongitude_raisesValidationError(
        self, mock_db_session
    ):
        """Test place creation with invalid longitude raises validation error."""
        # Given
        user_id = uuid4()
        invalid_place = PlaceCreate(
            name="Test Place", latitude=37.5665, longitude=181.0  # Invalid: > 180
        )

        # When/Then
        with pytest.raises(Exception):  # Could be ValidationError or similar
            place_crud.create_with_user(
                mock_db_session, obj_in=invalid_place, user_id=user_id
            )

    def test_get_by_user_databaseError_handlesGracefully(self, mock_db_session):
        """Test database error handling in place retrieval."""
        # Given
        user_id = uuid4()
        place_id = uuid4()

        mock_db_session.query.side_effect = Exception("Database connection error")

        # When/Then
        with pytest.raises(Exception):
            place_crud.get_by_user(mock_db_session, user_id=user_id, place_id=place_id)

    def test_update_nonExistentPlace_handlesGracefully(self, mock_db_session):
        """Test updating non-existent place handles gracefully."""
        # Given
        place_update = PlaceUpdate(name="Updated Name")
        non_existent_place = None

        # When/Then
        with pytest.raises(AttributeError):  # Will fail trying to update None object
            place_crud.update(
                mock_db_session, db_obj=non_existent_place, obj_in=place_update
            )


# Test fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = Mock(spec=Session)

    # Setup common mock returns
    mock_query = Mock()
    session.query.return_value = mock_query

    # Chain mocking for query operations
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    mock_query.count.return_value = 0

    return session


@pytest.fixture
def sample_place_create():
    """Sample place creation data."""
    return TestDataBuilder().with_korean_bbq_content().build_place_create()


@pytest.fixture
def sample_places_list():
    """Sample list of places for testing."""
    return [MockFactory.create_place_model() for _ in range(10)]
