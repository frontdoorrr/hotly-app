"""Test cases for notification template service functionality."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.models.notification import NotificationType
from app.schemas.notification import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
)
from app.services.notification_template_service import NotificationTemplateService


class TestNotificationTemplateService:
    """Test cases for NotificationTemplateService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def template_service(self, mock_db):
        """Create NotificationTemplateService instance."""
        with patch.object(NotificationTemplateService, "_initialize_default_templates"):
            return NotificationTemplateService(db=mock_db)

    @pytest.fixture
    def sample_template_data(self):
        """Sample template creation data."""
        return NotificationTemplateCreate(
            name="test_template",
            description="Test template for unit testing",
            title_template="Welcome {user_name}!",
            body_template="Hi {user_name}, welcome to {app_name}!",
            notification_type=NotificationType.ONBOARDING.value,
            category="welcome",
            priority="normal",
            required_variables=["user_name", "app_name"],
            optional_variables=["user_email"],
            default_data={"app_name": "HotlyApp"},
        )

    def test_create_template_success(self, template_service, sample_template_data):
        """Test successful template creation."""
        # Given
        mock_template = Mock()
        mock_template.id = uuid4()
        mock_template.name = sample_template_data.name

        template_service.db.add = Mock()
        template_service.db.commit = Mock()
        template_service.db.refresh = Mock()

        with patch(
            "app.services.notification_template_service.NotificationTemplate",
            return_value=mock_template,
        ):
            with patch(
                "app.schemas.notification.NotificationTemplateResponse"
            ) as mock_response:
                mock_response.from_orm.return_value = Mock(
                    id=mock_template.id, name=mock_template.name
                )

                # When
                result = template_service.create_template(sample_template_data)

        # Then
        template_service.db.add.assert_called_once_with(mock_template)
        template_service.db.commit.assert_called_once()
        template_service.db.refresh.assert_called_once_with(mock_template)
        assert result.id == mock_template.id

    def test_create_template_failure(self, template_service, sample_template_data):
        """Test template creation failure."""
        # Given
        template_service.db.add.side_effect = Exception("Database error")
        template_service.db.rollback = Mock()

        # When & Then
        with pytest.raises(Exception, match="Database error"):
            template_service.create_template(sample_template_data)

        template_service.db.rollback.assert_called_once()

    def test_get_template_by_id_success(self, template_service):
        """Test successful template retrieval by ID."""
        # Given
        template_id = str(uuid4())
        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "test_template"

        template_service.db.query().filter().first.return_value = mock_template

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(
                id=template_id, name="test_template"
            )

            # When
            result = template_service.get_template_by_id(template_id)

        # Then
        assert result is not None
        assert result.id == template_id
        mock_response.from_orm.assert_called_once_with(mock_template)

    def test_get_template_by_id_not_found(self, template_service):
        """Test template retrieval by ID when not found."""
        # Given
        template_id = str(uuid4())
        template_service.db.query().filter().first.return_value = None

        # When
        result = template_service.get_template_by_id(template_id)

        # Then
        assert result is None

    def test_get_template_by_name_success(self, template_service):
        """Test successful template retrieval by name."""
        # Given
        template_name = "welcome_template"
        mock_template = Mock()
        mock_template.name = template_name
        mock_template.id = uuid4()

        template_service.db.query().filter().first.return_value = mock_template

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(
                name=template_name, id=mock_template.id
            )

            # When
            result = template_service.get_template_by_name(template_name)

        # Then
        assert result is not None
        assert result.name == template_name

    def test_get_template_by_name_not_found(self, template_service):
        """Test template retrieval by name when not found."""
        # Given
        template_name = "nonexistent_template"
        template_service.db.query().filter().first.return_value = None

        # When
        result = template_service.get_template_by_name(template_name)

        # Then
        assert result is None

    def test_get_templates_by_type_success(self, template_service):
        """Test getting templates by notification type."""
        # Given
        notification_type = NotificationType.ONBOARDING.value
        mock_templates = [
            Mock(id=uuid4(), notification_type=notification_type, is_active=True),
            Mock(id=uuid4(), notification_type=notification_type, is_active=True),
        ]

        template_service.db.query().filter().all.return_value = mock_templates

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.side_effect = lambda t: Mock(
                id=t.id, notification_type=t.notification_type
            )

            # When
            result = template_service.get_templates_by_type(notification_type)

        # Then
        assert len(result) == 2
        for template in result:
            assert template.notification_type == notification_type

    def test_list_templates_with_filters(self, template_service):
        """Test listing templates with various filters."""
        # Given
        mock_templates = [
            Mock(
                id=uuid4(),
                notification_type="onboarding",
                category="welcome",
                is_active=True,
            ),
            Mock(
                id=uuid4(),
                notification_type="onboarding",
                category="progress",
                is_active=True,
            ),
        ]

        template_service.db.query().filter().offset().limit().all.return_value = (
            mock_templates
        )

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.side_effect = lambda t: Mock(
                id=t.id, category=t.category
            )

            # When
            result = template_service.list_templates(
                notification_type="onboarding",
                category="welcome",
                is_active=True,
                skip=0,
                limit=10,
            )

        # Then
        assert len(result) == 2

    def test_update_template_success(self, template_service):
        """Test successful template update."""
        # Given
        template_id = str(uuid4())
        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "original_template"

        template_service.db.query().filter().first.return_value = mock_template
        template_service.db.commit = Mock()
        template_service.db.refresh = Mock()

        template_update = NotificationTemplateUpdate(
            description="Updated description",
            title_template="Updated title for {user_name}",
            priority="high",
        )

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(
                id=template_id, name="original_template"
            )

            # When
            result = template_service.update_template(template_id, template_update)

        # Then
        assert result is not None
        assert mock_template.description == "Updated description"
        assert mock_template.title_template == "Updated title for {user_name}"
        assert mock_template.priority == "high"
        assert mock_template.updated_at is not None
        template_service.db.commit.assert_called_once()

    def test_update_template_not_found(self, template_service):
        """Test updating non-existent template."""
        # Given
        template_id = str(uuid4())
        template_service.db.query().filter().first.return_value = None

        template_update = NotificationTemplateUpdate(description="Updated description")

        # When
        result = template_service.update_template(template_id, template_update)

        # Then
        assert result is None

    def test_delete_template_success(self, template_service):
        """Test successful template deletion."""
        # Given
        template_id = str(uuid4())
        mock_template = Mock()
        mock_template.name = "template_to_delete"

        template_service.db.query().filter().first.return_value = mock_template
        template_service.db.delete = Mock()
        template_service.db.commit = Mock()

        # When
        result = template_service.delete_template(template_id)

        # Then
        assert result is True
        template_service.db.delete.assert_called_once_with(mock_template)
        template_service.db.commit.assert_called_once()

    def test_delete_template_not_found(self, template_service):
        """Test deleting non-existent template."""
        # Given
        template_id = str(uuid4())
        template_service.db.query().filter().first.return_value = None

        # When
        result = template_service.delete_template(template_id)

        # Then
        assert result is False

    def test_render_template_success(self, template_service):
        """Test successful template rendering."""
        # Given
        template_name = "welcome_template"
        mock_template = Mock()
        mock_template.name = template_name
        mock_template.title_template = "Welcome {user_name} to {app_name}!"
        mock_template.body_template = "Hi {user_name}, enjoy using {app_name}."
        mock_template.notification_type = "onboarding"
        mock_template.category = "welcome"
        mock_template.priority = "normal"
        mock_template.required_variables = ["user_name", "app_name"]
        mock_template.default_data = {"app_name": "HotlyApp"}

        template_service.get_template_by_name = Mock(return_value=mock_template)

        variables = {"user_name": "John Doe", "user_email": "john@example.com"}

        # When
        result = template_service.render_template(template_name, variables)

        # Then
        assert result["title"] == "Welcome John Doe to HotlyApp!"
        assert result["body"] == "Hi John Doe, enjoy using HotlyApp."
        assert result["notification_type"] == "onboarding"
        assert result["category"] == "welcome"
        assert result["priority"] == "normal"
        assert result["data"]["user_name"] == "John Doe"
        assert result["data"]["app_name"] == "HotlyApp"
        assert result["data"]["user_email"] == "john@example.com"

    def test_render_template_not_found(self, template_service):
        """Test rendering non-existent template."""
        # Given
        template_name = "nonexistent_template"
        template_service.get_template_by_name = Mock(return_value=None)

        # When & Then
        with pytest.raises(
            ValueError, match="Template 'nonexistent_template' not found"
        ):
            template_service.render_template(template_name, {})

    def test_render_template_missing_required_variables(self, template_service):
        """Test rendering template with missing required variables."""
        # Given
        template_name = "welcome_template"
        mock_template = Mock()
        mock_template.required_variables = ["user_name", "app_name"]
        mock_template.default_data = {}

        template_service.get_template_by_name = Mock(return_value=mock_template)

        variables = {"user_name": "John"}  # Missing app_name

        # When & Then
        with pytest.raises(ValueError, match="Missing required variables"):
            template_service.render_template(template_name, variables)

    def test_get_template_variables_success(self, template_service):
        """Test getting template variable requirements."""
        # Given
        template_name = "test_template"
        mock_template = Mock()
        mock_template.name = template_name
        mock_template.required_variables = ["user_name", "app_name"]
        mock_template.optional_variables = ["user_email", "user_phone"]
        mock_template.default_data = {"app_name": "HotlyApp"}
        mock_template.notification_type = "onboarding"
        mock_template.category = "welcome"

        template_service.get_template_by_name = Mock(return_value=mock_template)

        # When
        result = template_service.get_template_variables(template_name)

        # Then
        assert result["template_name"] == template_name
        assert result["required_variables"] == ["user_name", "app_name"]
        assert result["optional_variables"] == ["user_email", "user_phone"]
        assert result["default_data"] == {"app_name": "HotlyApp"}
        assert result["notification_type"] == "onboarding"
        assert result["category"] == "welcome"

    def test_get_template_variables_not_found(self, template_service):
        """Test getting variables for non-existent template."""
        # Given
        template_name = "nonexistent_template"
        template_service.get_template_by_name = Mock(return_value=None)

        # When
        result = template_service.get_template_variables(template_name)

        # Then
        assert "error" in result
        assert "not found" in result["error"]

    def test_initialize_default_templates(self, template_service):
        """Test initialization of default templates."""
        # Given
        template_service.get_template_by_name = Mock(
            return_value=None
        )  # No existing templates
        template_service.create_template = Mock()

        # When
        template_service._initialize_default_templates()

        # Then
        # Should create multiple default templates
        assert template_service.create_template.call_count >= 5

        # Check that various template types are created
        call_args_list = template_service.create_template.call_args_list
        template_names = [call[0][0].name for call in call_args_list]

        expected_templates = [
            "onboarding_welcome",
            "place_recommendation",
            "social_like_received",
            "reminder_visit_place",
        ]

        for expected in expected_templates:
            assert expected in template_names


@pytest.mark.integration
class TestNotificationTemplateServiceIntegration:
    """Integration tests for notification template service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def template_service(self, mock_db):
        """Create template service for integration testing."""
        with patch.object(NotificationTemplateService, "_initialize_default_templates"):
            return NotificationTemplateService(db=mock_db)

    def test_complete_template_lifecycle_e2e(self, template_service):
        """Test complete template lifecycle end-to-end."""
        # Given
        template_data = NotificationTemplateCreate(
            name="integration_test_template",
            description="Integration test template",
            title_template="Hello {user_name}!",
            body_template="Welcome to {app_name}, {user_name}. Your {item_type} is ready!",
            notification_type=NotificationType.GENERAL.value,
            category="integration",
            required_variables=["user_name", "app_name", "item_type"],
            default_data={"app_name": "HotlyApp"},
        )

        # Mock database operations
        mock_template = Mock()
        mock_template.id = uuid4()
        mock_template.name = template_data.name

        template_service.db.add = Mock()
        template_service.db.commit = Mock()
        template_service.db.refresh = Mock()
        template_service.db.delete = Mock()

        # When - Step 1: Create template
        with patch(
            "app.services.notification_template_service.NotificationTemplate",
            return_value=mock_template,
        ):
            with patch(
                "app.schemas.notification.NotificationTemplateResponse"
            ) as mock_response:
                mock_response.from_orm.return_value = Mock(
                    id=mock_template.id,
                    name=mock_template.name,
                    title_template=template_data.title_template,
                    body_template=template_data.body_template,
                    required_variables=template_data.required_variables,
                    default_data=template_data.default_data,
                )

                created_template = template_service.create_template(template_data)

        # When - Step 2: Get template by name
        template_service.db.query().filter().first.return_value = mock_template
        retrieved_template = template_service.get_template_by_name(template_data.name)

        # When - Step 3: Render template
        variables = {"user_name": "Alice Johnson", "item_type": "reservation"}

        template_service.get_template_by_name = Mock(return_value=created_template)
        rendered = template_service.render_template(template_data.name, variables)

        # When - Step 4: Update template
        template_service.db.query().filter().first.return_value = mock_template

        update_data = NotificationTemplateUpdate(
            description="Updated integration test template", priority="high"
        )

        updated_template = template_service.update_template(
            str(mock_template.id), update_data
        )

        # When - Step 5: List templates
        template_service.db.query().filter().offset().limit().all.return_value = [
            mock_template
        ]

        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(
                id=mock_template.id, name=mock_template.name
            )
            templates_list = template_service.list_templates(category="integration")

        # When - Step 6: Delete template
        success = template_service.delete_template(str(mock_template.id))

        # Then
        assert created_template.name == template_data.name
        assert retrieved_template is not None
        assert rendered["title"] == "Hello Alice Johnson!"
        assert (
            rendered["body"]
            == "Welcome to HotlyApp, Alice Johnson. Your reservation is ready!"
        )
        assert updated_template is not None
        assert len(templates_list) == 1
        assert success is True

        # Verify database operations
        template_service.db.add.assert_called()
        template_service.db.commit.assert_called()
        template_service.db.delete.assert_called_with(mock_template)

    def test_template_rendering_with_edge_cases(self, template_service):
        """Test template rendering with various edge cases."""
        # Given
        complex_template = Mock()
        complex_template.name = "complex_template"
        complex_template.title_template = "🎉 {greeting} {user_name}!"
        complex_template.body_template = "Your {item_count} {item_type}(s) from {location} {status}. Total: ${total_amount:.2f}"
        complex_template.notification_type = "complex"
        complex_template.category = "test"
        complex_template.priority = "normal"
        complex_template.required_variables = [
            "greeting",
            "user_name",
            "item_count",
            "item_type",
            "location",
            "status",
            "total_amount",
        ]
        complex_template.default_data = {
            "greeting": "Hello",
            "status": "are ready",
            "currency": "USD",
        }

        template_service.get_template_by_name = Mock(return_value=complex_template)

        # Test Cases
        test_cases = [
            {
                "name": "Basic rendering with all variables",
                "variables": {
                    "user_name": "김철수",
                    "item_count": "3",
                    "item_type": "pizza",
                    "location": "강남점",
                    "total_amount": "45000",
                },
                "expected_title": "🎉 Hello 김철수!",
                "expected_body": "Your 3 pizza(s) from 강남점 are ready. Total: $45000.00",
            },
            {
                "name": "Rendering with numeric formatting",
                "variables": {
                    "user_name": "Jane",
                    "item_count": "1",
                    "item_type": "burger",
                    "location": "downtown",
                    "total_amount": "15.99",
                },
                "expected_title": "🎉 Hello Jane!",
                "expected_body": "Your 1 burger(s) from downtown are ready. Total: $15.99",
            },
        ]

        for test_case in test_cases:
            # When
            result = template_service.render_template(
                "complex_template", test_case["variables"]
            )

            # Then
            assert (
                result["title"] == test_case["expected_title"]
            ), f"Failed for: {test_case['name']}"
            assert (
                result["body"] == test_case["expected_body"]
            ), f"Failed for: {test_case['name']}"
            assert result["data"]["greeting"] == "Hello"  # From default_data
            assert result["data"]["status"] == "are ready"  # From default_data

    def test_template_management_with_filtering_and_pagination(self, template_service):
        """Test template management with advanced filtering and pagination."""
        # Given
        mock_templates = []
        template_types = ["onboarding", "recommendation", "social", "reminder"]
        categories = ["welcome", "progress", "like", "visit"]

        for i in range(20):
            mock_template = Mock()
            mock_template.id = uuid4()
            mock_template.name = f"template_{i}"
            mock_template.notification_type = template_types[i % len(template_types)]
            mock_template.category = categories[i % len(categories)]
            mock_template.is_active = i % 3 != 0  # Some inactive templates
            mock_templates.append(mock_template)

        # Mock different query results for different filters
        def mock_query_side_effect(*args, **kwargs):
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query

            # Simulate filtering logic
            filtered_templates = [
                t
                for t in mock_templates
                if (
                    args
                    and args[0] == "onboarding"
                    and t.notification_type == "onboarding"
                )
                or not args
            ][
                :10
            ]  # Simulate limit

            mock_query.all.return_value = filtered_templates
            return mock_query

        template_service.db.query.side_effect = mock_query_side_effect

        # When - Test different filtering scenarios
        with patch(
            "app.schemas.notification.NotificationTemplateResponse"
        ) as mock_response:
            mock_response.from_orm.side_effect = lambda t: Mock(
                id=t.id,
                name=t.name,
                notification_type=t.notification_type,
                category=t.category,
            )

            # Test 1: List all templates with pagination
            all_templates = template_service.list_templates(skip=0, limit=10)

            # Test 2: List by notification type
            onboarding_templates = template_service.list_templates(
                notification_type="onboarding"
            )

            # Test 3: List active templates only
            active_templates = template_service.list_templates(is_active=True)

        # Then
        assert len(all_templates) <= 10  # Pagination limit
        assert all(
            [
                t.notification_type == "onboarding"
                for t in onboarding_templates
                if hasattr(t, "notification_type")
            ]
        )
        assert len(active_templates) <= 10
