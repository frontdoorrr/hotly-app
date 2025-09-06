"""Tests for LLM-based place category classification."""

from unittest.mock import Mock

import pytest

from app.models.place import PlaceCategory
from app.schemas.place import PlaceCreate
from app.services.ai.interfaces.classifier_interface import AIClassifierInterface
from app.services.place_classification_service import (
    PlaceClassificationService,
)


class TestPlaceClassifier:
    """Test LLM-based category classification system."""

    @pytest.fixture
    def mock_ai_classifier(self) -> Mock:
        """Create mock AI classifier interface."""
        mock = Mock(spec=AIClassifierInterface)
        return mock

    @pytest.fixture
    def classification_service(self, mock_ai_classifier) -> PlaceClassificationService:
        """Create classification service with mock AI classifier."""
        return PlaceClassificationService(ai_classifier=mock_ai_classifier)

    @pytest.mark.asyncio
    async def test_cafe_classification_success(
        self, classification_service, mock_ai_classifier
    ):
        """Test successful cafe classification."""
        # Given: Mock AI classifier returns cafe result
        mock_ai_classifier.classify_place.return_value = {
            "category": "cafe",
            "confidence": 0.92,
            "reasoning": "커피 전문점 키워드가 명확함",
        }

        place_data = PlaceCreate(
            name="스타벅스 강남점",
            description="커피 전문점, 라떼 맛집",
            keywords=["커피", "라떼", "카페"],
        )

        # When: Classify place
        result = await classification_service.classify_place(place_data)

        # Then: Should return cafe category
        assert result.predicted_category == PlaceCategory.CAFE
        assert result.confidence == 0.92
        assert result.reasoning == "커피 전문점 키워드가 명확함"
        assert result.needs_manual_review is False

        # Verify AI classifier was called correctly
        mock_ai_classifier.classify_place.assert_called_once()
        call_args = mock_ai_classifier.classify_place.call_args[0][0]
        assert call_args.name == "스타벅스 강남점"

    @pytest.mark.asyncio
    async def test_restaurant_classification(
        self, classification_service, mock_ai_classifier
    ):
        """Test restaurant classification."""
        # Given: Mock AI classifier returns restaurant result
        mock_ai_classifier.classify_place.return_value = {
            "category": "restaurant",
            "confidence": 0.88,
            "reasoning": "음식점 관련 키워드가 명확함",
        }

        place_data = PlaceCreate(
            name="한정식집 고궁",
            description="전통 한식, 정갈한 상차림",
            keywords=["한식", "정식", "전통음식"],
        )

        # When: Classify place
        result = await classification_service.classify_place(place_data)

        # Then: Should return restaurant category
        assert result.predicted_category == PlaceCategory.RESTAURANT
        assert result.confidence == 0.88

    @pytest.mark.asyncio
    async def test_low_confidence_manual_review(
        self, classification_service, mock_ai_classifier
    ):
        """Test low confidence requiring manual review."""
        # Given: Mock AI returns low confidence
        mock_ai_classifier.classify_place.return_value = {
            "category": "other",
            "confidence": 0.45,
            "reasoning": "정보가 부족하여 명확한 분류 어려움",
        }

        place_data = PlaceCreate(
            name="알 수 없는 장소",
            description="",
            keywords=[],
        )

        # When: Classify place
        result = await classification_service.classify_place(place_data)

        # Then: Should require manual review
        assert result.needs_manual_review is True
        assert result.confidence < 0.70

    @pytest.mark.asyncio
    async def test_ai_service_fallback(
        self, classification_service, mock_ai_classifier
    ):
        """Test fallback when AI service is unavailable."""
        # Given: AI classifier is unavailable
        mock_ai_classifier.is_available.return_value = False

        place_data = PlaceCreate(
            name="스타벅스 테스트점",
            description="커피 전문점",
            keywords=["커피", "카페"],
        )

        # When: Classify place
        result = await classification_service.classify_place(place_data)

        # Then: Should use fallback classification
        assert (
            result.predicted_category == PlaceCategory.CAFE
        )  # Heuristic classification
        assert result.confidence == 0.30  # Low confidence
        assert result.needs_manual_review is True
        assert "AI 서비스 이용 불가" in result.reasoning

    @pytest.mark.asyncio
    async def test_batch_classification(
        self, classification_service, mock_ai_classifier
    ):
        """Test batch classification with concurrency control."""
        # Given: Multiple places and mock AI responses
        places = [
            PlaceCreate(name=f"카페{i}", description="커피숍", keywords=["커피"])
            for i in range(5)
        ]

        mock_ai_classifier.classify_place.return_value = {
            "category": "cafe",
            "confidence": 0.85,
            "reasoning": "커피 관련 키워드",
        }

        # When: Classify batch
        results = await classification_service.classify_places_batch(places)

        # Then: Should return results for all places
        assert len(results) == 5
        assert all(
            result.predicted_category == PlaceCategory.CAFE for result in results
        )

    def test_confidence_threshold_setting(self, classification_service):
        """Test confidence threshold adjustment."""
        # Given: Classification service
        # When: Set confidence threshold
        classification_service.set_confidence_threshold(0.85)

        # Then: Threshold should be updated
        assert classification_service.confidence_threshold == 0.85

    @pytest.mark.asyncio
    async def test_classify_and_update_place(
        self, classification_service, mock_ai_classifier
    ):
        """Test classification with auto-update functionality."""
        # Given: High confidence classification
        mock_ai_classifier.classify_place.return_value = {
            "category": "cafe",
            "confidence": 0.92,
            "reasoning": "명확한 카페 키워드",
        }

        place_data = PlaceCreate(
            name="투썸플레이스",
            description="커피 체인점",
            keywords=["커피", "라떼"],
            category=PlaceCategory.OTHER,  # Initial category
        )

        # When: Classify with auto-update
        result = await classification_service.classify_and_update_place(
            place_data, auto_update=True
        )

        # Then: Should update place category
        assert result.predicted_category == PlaceCategory.CAFE
        assert place_data.category == PlaceCategory.CAFE  # Should be auto-updated
