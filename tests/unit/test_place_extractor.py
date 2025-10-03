"""Test place information extraction and structuring logic."""


import pytest

from app.schemas.ai import AnalysisConfidence, GeminiResponse, PlaceAnalysisResult
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType
from app.schemas.place import ExtractionConfidence, PlaceExtractionResult
from app.services.place_extractor import PlaceExtractor


class TestPlaceExtractor:
    """Test cases for PlaceExtractor service."""

    @pytest.fixture
    def extractor(self):
        """Create PlaceExtractor instance."""
        return PlaceExtractor()

    @pytest.fixture
    def sample_gemini_response(self):
        """Sample Gemini response for testing."""
        return GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Gangnam Korean BBQ",
                    address="123 Teheran-ro, Gangnam-gu, Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                    description="Premium Korean BBQ restaurant",
                ),
                PlaceAnalysisResult(
                    name="Blue Bottle Coffee",
                    address="Hongdae, Seoul",
                    category="cafe",
                    confidence=AnalysisConfidence.MEDIUM,
                    description="Specialty coffee shop",
                ),
            ],
            overall_confidence=AnalysisConfidence.HIGH,
            processing_time=1.2,
        )

    @pytest.mark.asyncio
    async def test_extract_and_structure_places_success(
        self, extractor, sample_gemini_response
    ):
        """Test successful place extraction and structuring."""
        # Given
        content = ExtractedContent(
            url="https://www.instagram.com/p/ABC123/",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(
                title="Great food in Seoul",
                description="Amazing Korean BBQ and coffee",
                hashtags=["#food", "#seoul"],
            ),
        )

        # When
        result = await extractor.extract_and_structure_places(
            content, sample_gemini_response
        )

        # Then
        assert isinstance(result, PlaceExtractionResult)
        assert len(result.places) == 2
        assert result.total_places_found == 2
        assert result.confidence_score >= 0.7  # High confidence

        # Check first place
        place1 = result.places[0]
        assert place1.name == "Gangnam Korean BBQ"
        assert place1.category == "restaurant"
        assert place1.confidence == ExtractionConfidence.HIGH
        assert place1.structured_address is not None

        # Check second place
        place2 = result.places[1]
        assert place2.name == "Blue Bottle Coffee"
        assert place2.category == "cafe"
        assert place2.confidence == ExtractionConfidence.MEDIUM

    @pytest.mark.asyncio
    async def test_extract_places_with_validation_errors(self, extractor):
        """Test extraction with validation errors in place data."""
        # Given
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="",  # Invalid empty name
                    address="Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Valid Place",
                    address="Seoul",
                    category="invalid_category",  # Invalid category
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Another Valid Place",
                    address="Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                ),
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, gemini_response)

        # Then
        # Should only include valid places
        assert len(result.places) == 1
        assert result.places[0].name == "Another Valid Place"
        assert len(result.validation_errors) == 2
        assert result.total_places_found == 3  # Original count
        assert result.places_validated == 1

    @pytest.mark.asyncio
    async def test_address_structuring_and_normalization(self, extractor):
        """Test address structuring and normalization logic."""
        # Given
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Test Restaurant",
                    address="   123 Teheran-ro, Gangnam-gu, Seoul, South Korea   ",  # Extra whitespace
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Test Cafe",
                    address="Hongdae",  # Incomplete address
                    category="cafe",
                    confidence=AnalysisConfidence.MEDIUM,
                ),
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, gemini_response)

        # Then
        place1 = result.places[0]
        assert (
            place1.structured_address.full_address
            == "123 Teheran-ro, Gangnam-gu, Seoul, South Korea"
        )
        assert place1.structured_address.district == "Gangnam-gu"
        assert place1.structured_address.city == "Seoul"
        assert place1.structured_address.country == "South Korea"

        place2 = result.places[1]
        assert place2.structured_address.district == "Hongdae"
        assert place2.structured_address.completeness_score < 0.5  # Incomplete

    @pytest.mark.asyncio
    async def test_confidence_scoring_algorithm(self, extractor):
        """Test confidence scoring algorithm."""
        # Given different confidence scenarios
        test_cases = [
            {
                "gemini_confidence": AnalysisConfidence.HIGH,
                "address_quality": "complete",  # Full address
                "name_clarity": "high",  # Clear business name
                "expected_min_score": 0.8,
            },
            {
                "gemini_confidence": AnalysisConfidence.MEDIUM,
                "address_quality": "partial",  # Only district
                "name_clarity": "medium",  # Some ambiguity
                "expected_min_score": 0.5,
            },
            {
                "gemini_confidence": AnalysisConfidence.LOW,
                "address_quality": "incomplete",  # Vague location
                "name_clarity": "low",  # Unclear name
                "expected_min_score": 0.2,
            },
        ]

        for case in test_cases:
            # Create test response
            address = {
                "complete": "123 Main St, Gangnam-gu, Seoul, South Korea",
                "partial": "Gangnam, Seoul",
                "incomplete": "Seoul",
            }[case["address_quality"]]

            name = {
                "high": "Jungsik Restaurant",
                "medium": "Korean Place",
                "low": "Some restaurant",
            }[case["name_clarity"]]

            gemini_response = GeminiResponse(
                places=[
                    PlaceAnalysisResult(
                        name=name,
                        address=address,
                        category="restaurant",
                        confidence=case["gemini_confidence"],
                    )
                ],
                overall_confidence=case["gemini_confidence"],
            )

            content = ExtractedContent(
                url="test",
                platform=PlatformType.INSTAGRAM,
                metadata=ContentMetadata(title="Test"),
            )

            # When
            result = await extractor.extract_and_structure_places(
                content, gemini_response
            )

            # Then
            assert result.confidence_score >= case["expected_min_score"]

    @pytest.mark.asyncio
    async def test_duplicate_place_detection(self, extractor):
        """Test detection and handling of duplicate places."""
        # Given response with duplicate places
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Korean BBQ Restaurant",
                    address="Gangnam, Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Korean BBQ",  # Similar name
                    address="Gangnam-gu, Seoul",  # Similar address
                    category="restaurant",
                    confidence=AnalysisConfidence.MEDIUM,
                ),
                PlaceAnalysisResult(
                    name="Different Place",
                    address="Hongdae, Seoul",
                    category="cafe",
                    confidence=AnalysisConfidence.HIGH,
                ),
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, gemini_response)

        # Then
        # Should detect and handle duplicates
        assert len(result.places) == 2  # One duplicate removed
        assert result.duplicates_removed == 1
        assert any(place.name == "Korean BBQ Restaurant" for place in result.places)
        assert any(place.name == "Different Place" for place in result.places)

    @pytest.mark.asyncio
    async def test_category_normalization(self, extractor):
        """Test category normalization and validation."""
        # Given
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Test Place 1",
                    category="RESTAURANT",  # Uppercase
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Test Place 2",
                    category="Korean Restaurant",  # Non-standard
                    confidence=AnalysisConfidence.HIGH,
                ),
                PlaceAnalysisResult(
                    name="Test Place 3",
                    category="cafe",  # Valid
                    confidence=AnalysisConfidence.HIGH,
                ),
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, gemini_response)

        # Then
        place1 = next(p for p in result.places if p.name == "Test Place 1")
        assert place1.category == "restaurant"  # Normalized to lowercase

        place2 = next(p for p in result.places if p.name == "Test Place 2")
        assert place2.category == "restaurant"  # Mapped to standard category

        place3 = next(p for p in result.places if p.name == "Test Place 3")
        assert place3.category == "cafe"  # Already valid

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, extractor):
        """Test handling of empty Gemini responses."""
        # Given
        empty_response = GeminiResponse(
            places=[], overall_confidence=AnalysisConfidence.HIGH
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, empty_response)

        # Then
        assert len(result.places) == 0
        assert result.total_places_found == 0
        assert result.confidence_score >= 0.9  # High confidence in finding no places

    @pytest.mark.asyncio
    async def test_data_quality_metrics(self, extractor):
        """Test data quality metrics calculation."""
        # Given
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Complete Place",
                    address="123 Main St, Gangnam-gu, Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                    description="Full description",
                ),
                PlaceAnalysisResult(
                    name="Incomplete Place",
                    address="Seoul",  # Incomplete address
                    category="cafe",
                    confidence=AnalysisConfidence.LOW
                    # No description
                ),
            ],
            overall_confidence=AnalysisConfidence.MEDIUM,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        result = await extractor.extract_and_structure_places(content, gemini_response)

        # Then
        assert result.data_quality_score > 0
        assert result.data_quality_score < 1.0  # Not perfect due to incomplete data

        # Check individual place quality scores
        complete_place = next(p for p in result.places if p.name == "Complete Place")
        incomplete_place = next(
            p for p in result.places if p.name == "Incomplete Place"
        )

        assert complete_place.data_quality_score > incomplete_place.data_quality_score

    @pytest.mark.asyncio
    async def test_performance_requirements(self, extractor):
        """Test that extraction meets performance requirements."""
        # Given large response (simulate processing overhead)
        large_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name=f"Place {i}",
                    address=f"Address {i}, Seoul",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                )
                for i in range(10)  # 10 places to process
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        # When
        import time

        start_time = time.time()
        result = await extractor.extract_and_structure_places(content, large_response)
        processing_time = time.time() - start_time

        # Then
        # Should process quickly (under 1 second for 10 places)
        assert processing_time < 1.0
        assert len(result.places) == 10
        assert result.processing_time_ms is not None
        assert result.processing_time_ms < 1000  # Under 1 second
