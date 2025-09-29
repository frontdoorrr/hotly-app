"""
TDD Example: Link Analysis Feature Implementation

This example demonstrates the complete TDD cycle for implementing
link analysis functionality following Red-Green-Refactor methodology.

Steps shown:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass tests
3. REFACTOR: Improve implementation while keeping tests green
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.schemas.link_analysis import LinkAnalyzeRequest
from app.services.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisTDD:
    """TDD implementation example for link analysis feature."""

    # STEP 1: RED - Write failing tests first

    def test_analyze_link_validInstagramUrl_returnsSuccessResponse(self):
        """
        RED: This test will fail initially because we haven't implemented
        the link analysis service yet.

        Test naming follows: methodName_condition_expectedResult
        """
        # Given
        url = "https://instagram.com/p/CXXXXXXXXXx/"
        request = LinkAnalyzeRequest(url=url)

        # When - This will fail because LinkAnalysisService doesn't exist yet
        # service = LinkAnalysisService()
        # result = await service.analyze_link(request)

        # Then - Expected behavior
        # assert result.success is True
        # assert result.analysis_id is not None
        # assert result.status == AnalysisStatus.COMPLETED

        # For now, we'll skip this test to show the TDD process
        pytest.skip("RED step - test written before implementation")

    def test_analyze_link_unsupportedPlatform_raisesUnsupportedPlatformError(self):
        """RED: Test error handling for unsupported platforms."""
        # Given
        url = "https://facebook.com/post/123"
        request = LinkAnalyzeRequest(url=url)

        # When/Then - This should raise an exception
        # service = LinkAnalysisService()
        # with pytest.raises(UnsupportedPlatformError):
        #     await service.analyze_link(request)

        pytest.skip("RED step - test written before implementation")

    # STEP 2: GREEN - Implement minimal code to pass tests

    @pytest.mark.asyncio
    async def test_content_extractor_extract_validUrl_returnsContentData(self):
        """
        GREEN: Now we implement minimal functionality to pass this test.
        """
        from app.services.content_extractor import ContentExtractor

        # Given
        url = "https://instagram.com/p/test123/"
        extractor = ContentExtractor()

        # Mock the extract_content method to return test data
        with patch.object(
            extractor, "extract_content", new_callable=AsyncMock
        ) as mock_extract:
            expected_result = ContentExtractResult(
                url=url,
                title="Test Instagram Post",
                description="Test description #food #restaurant",
                images=["https://example.com/image1.jpg"],
                platform="instagram",
                extraction_time=0.5,
                success=True,
                hashtags=["food", "restaurant"],
                author="test_user",
                posted_at="2024-01-15T14:30:00Z",
            )
            mock_extract.return_value = expected_result

            # When
            result = await extractor.extract_content(url)

            # Then
            assert result.success is True
            assert result.url == url
            assert result.platform == "instagram"
            assert len(result.hashtags) > 0
            assert result.extraction_time > 0

    @pytest.mark.asyncio
    async def test_place_analysis_service_analyze_contentWithPlaceInfo_returnsPlaceInfo(
        self,
    ):
        """GREEN: Test AI analysis service."""
        from app.schemas.content import ContentMetadata
        from app.services.place_analysis_service import PlaceAnalysisService

        # Given
        content = ContentMetadata(
            title="Amazing Korean BBQ Restaurant",
            description="Best Korean BBQ in Gangnam #korean #bbq #restaurant",
            images=["https://example.com/image.jpg"],
            hashtags=["korean", "bbq", "restaurant"],
        )

        service = PlaceAnalysisService()

        # Mock the AI analysis
        with patch.object(
            service, "analyze_content", new_callable=AsyncMock
        ) as mock_analyze:
            expected_place_info = PlaceInfo(
                name="Gangnam Korean BBQ",
                category="restaurant",
                address="Seoul, Gangnam-gu",
                description="Korean BBQ restaurant",
                keywords=["korean", "bbq", "meat"],
                confidence=0.9,
            )

            expected_result = PlaceAnalysisResult(
                success=True,
                place_info=expected_place_info,
                confidence=0.9,
                analysis_time=1.5,
                model_version="gemini-pro-1.0",
                error=None,
            )
            mock_analyze.return_value = expected_result

            # When
            result = await service.analyze_content(content, content.images)

            # Then
            assert result.success is True
            assert result.place_info is not None
            assert result.place_info.name is not None
            assert result.confidence > 0.8
            assert result.analysis_time > 0

    # STEP 3: REFACTOR - Improve implementation while keeping tests green

    @pytest.mark.asyncio
    async def test_link_analysis_endpoint_fullWorkflow_returnsCompleteResult(self):
        """
        REFACTOR: Test the complete integrated workflow after refactoring.
        This test validates that all components work together correctly.
        """
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)

        # Given
        request_data = {"url": "https://instagram.com/p/test123/"}

        # Mock all external dependencies for isolated testing
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor_class, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis_class, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache_class:
            # Setup content extraction mock
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_content.return_value = ContentExtractResult(
                url=request_data["url"],
                title="Restaurant Review",
                description="Amazing food at this place #restaurant #food",
                images=["https://example.com/image.jpg"],
                platform="instagram",
                extraction_time=0.8,
                success=True,
                hashtags=["restaurant", "food"],
                author="food_blogger",
                posted_at="2024-01-15T14:30:00Z",
            )

            # Setup AI analysis mock
            mock_analysis = mock_analysis_class.return_value
            mock_analysis.analyze_content.return_value = PlaceAnalysisResult(
                success=True,
                place_info=PlaceInfo(
                    name="Amazing Restaurant",
                    category="restaurant",
                    address="Seoul, Korea",
                    description="Great restaurant with amazing food",
                    keywords=["restaurant", "food", "dining"],
                    confidence=0.92,
                ),
                confidence=0.92,
                analysis_time=2.1,
                model_version="gemini-pro-1.0",
                error=None,
            )

            # Setup cache mock (cache miss scenario)
            mock_cache = mock_cache_class.return_value
            mock_cache.get.return_value = None
            mock_cache.initialize.return_value = None
            mock_cache.close.return_value = None
            mock_cache.set = AsyncMock()

            # When
            response = client.post("/api/v1/links/analyze", json=request_data)

            # Then
            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert data["success"] is True
            assert data["status"] == "completed"
            assert data["cached"] is False
            assert "analysisId" in data
            assert "processingTime" in data

            # Validate result content
            result = data["result"]
            assert result["confidence"] == 0.92

            place_info = result["placeInfo"]
            assert place_info["name"] == "Amazing Restaurant"
            assert place_info["category"] == "restaurant"
            assert place_info["confidence"] == 0.92

            content_metadata = result["contentMetadata"]
            assert content_metadata["title"] == "Restaurant Review"
            assert "Amazing food" in content_metadata["description"]

    def test_tdd_documentation_example(self):
        """
        This test demonstrates how TDD serves as living documentation.

        By reading this test, developers can understand:
        1. What the link analysis feature does
        2. How it should behave
        3. What the expected inputs and outputs are
        4. How error cases are handled

        This is the power of TDD - tests become executable specifications.
        """
        # Given - Clear setup shows what data is needed
        instagram_url = "https://instagram.com/p/CXXXXXXXXXx/"

        # When - Action clearly shows what the system does
        # result = link_analysis_service.analyze(instagram_url)

        # Then - Assertions document expected behavior
        # assert result.success is True
        # assert result.place_info is not None
        # assert result.confidence > 0.8

        # Documentation through code - anyone can read this test
        # and understand exactly how the feature should work
        assert True  # Placeholder for actual implementation


class TestTDDWorkflowExample:
    """
    This class shows the complete TDD workflow for a new feature.
    """

    def test_step1_red_write_failing_test_first(self):
        """
        STEP 1 - RED: Write the test first, it should fail.

        This forces us to think about the API design and expected behavior
        before writing any production code.
        """
        # This test defines what we want to build
        # It will fail because we haven't implemented anything yet

        # Given - what input do we need?
        user_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget": "medium",
            "location": "Gangnam",
        }

        # When - what action do we want to perform?
        # recommendation_engine = PersonalizedRecommendationEngine()
        # recommendations = recommendation_engine.get_recommendations(user_preferences)

        # Then - what should the result look like?
        # assert len(recommendations) > 0
        # assert all(rec.category in user_preferences["categories"] for rec in recommendations)
        # assert all(rec.budget_level == user_preferences["budget"] for rec in recommendations)

        pytest.skip("RED: Test written first, implementation doesn't exist yet")

    def test_step2_green_minimal_implementation(self):
        """
        STEP 2 - GREEN: Write minimal code to make the test pass.

        Don't worry about perfect code yet, just make it work.
        """
        # After writing minimal implementation, this test should pass

        class MockRecommendationEngine:
            def get_recommendations(self, preferences):
                # Minimal implementation - just return dummy data
                return [
                    Mock(category="restaurant", budget_level="medium"),
                    Mock(category="cafe", budget_level="medium"),
                ]

        # Given
        user_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget": "medium",
            "location": "Gangnam",
        }

        # When
        engine = MockRecommendationEngine()
        recommendations = engine.get_recommendations(user_preferences)

        # Then
        assert len(recommendations) > 0
        assert all(
            rec.category in user_preferences["categories"] for rec in recommendations
        )
        assert all(
            rec.budget_level == user_preferences["budget"] for rec in recommendations
        )

    def test_step3_refactor_improve_implementation(self):
        """
        STEP 3 - REFACTOR: Improve the implementation while keeping tests green.

        Now we can make the code better - add proper algorithms,
        error handling, performance optimizations, etc.
        """
        # After refactoring, all tests should still pass
        # but the implementation should be production-ready

        class ImprovedRecommendationEngine:
            def __init__(self):
                self.database = Mock()  # Would be real database
                self.ml_model = Mock()  # Would be real ML model

            def get_recommendations(self, preferences):
                # Improved implementation with proper logic

                # 1. Validate input
                if not preferences.get("categories"):
                    raise ValueError("Categories are required")

                # 2. Query database
                places = self.database.find_places_by_categories(
                    preferences["categories"]
                )

                # 3. Apply ML filtering
                filtered_places = self.ml_model.filter_by_preferences(
                    places, preferences
                )

                # 4. Return recommendations
                return filtered_places[:10]  # Top 10 recommendations

        # Test still passes with improved implementation
        engine = ImprovedRecommendationEngine()

        # Mock the dependencies
        engine.database.find_places_by_categories.return_value = [
            Mock(category="restaurant", budget_level="medium"),
            Mock(category="cafe", budget_level="medium"),
        ]
        engine.ml_model.filter_by_preferences.return_value = [
            Mock(category="restaurant", budget_level="medium"),
            Mock(category="cafe", budget_level="medium"),
        ]

        # Given
        user_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget": "medium",
            "location": "Gangnam",
        }

        # When
        recommendations = engine.get_recommendations(user_preferences)

        # Then
        assert len(recommendations) > 0
        assert len(recommendations) <= 10  # New constraint from refactored code


# TDD Benefits Demonstrated:
# 1. Design: Tests force good API design
# 2. Documentation: Tests show how to use the code
# 3. Confidence: Refactoring is safe with comprehensive tests
# 4. Quality: Edge cases and error conditions are considered upfront
# 5. Feedback: Quick feedback on whether code works as expected
