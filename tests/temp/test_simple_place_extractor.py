#!/usr/bin/env python3
"""Simple test script for place extractor."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas.ai import AnalysisConfidence, GeminiResponse, PlaceAnalysisResult
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType
from app.services.places.place_extractor import PlaceExtractor


async def test_place_extractor():
    """Test place extractor functionality."""
    print("Testing PlaceExtractor...")

    extractor = PlaceExtractor()

    # Test 1: Basic place extraction
    print("\n1. Testing basic place extraction:")
    try:
        content = ExtractedContent(
            url="https://www.instagram.com/p/ABC123/",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(
                title="Great Korean BBQ in Gangnam",
                description="Amazing Korean BBQ restaurant in Gangnam",
                hashtags=["#koreanbbq", "#gangnam", "#seoul"],
            ),
        )

        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Gangnam Korean BBQ",
                    address="123 Teheran-ro, Gangnam-gu, Seoul, South Korea",
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                    description="Premium Korean BBQ restaurant",
                )
            ],
            overall_confidence=AnalysisConfidence.HIGH,
            processing_time=1.2,
        )

        result = await extractor.extract_and_structure_places(content, gemini_response)

        print(f"✅ Basic extraction completed:")
        print(f"   Found {len(result.places)} place(s)")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Data quality: {result.data_quality_score:.3f}")
        print(f"   Processing time: {result.processing_time_ms:.1f}ms")

        if result.places:
            place = result.places[0]
            print(f"   Place: {place.name}")
            print(f"   Category: {place.category}")
            print(
                f"   Address completeness: {place.structured_address.completeness_score:.2f}"
            )
            print(f"   Keywords: {place.keywords}")

    except Exception as e:
        print(f"❌ Basic extraction failed: {e}")

    # Test 2: Multiple places with duplicates
    print("\n2. Testing duplicate removal:")
    try:
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
                    name="Blue Bottle Coffee",
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

        result = await extractor.extract_and_structure_places(content, gemini_response)

        print(f"✅ Duplicate removal test:")
        print(f"   Original places: {result.total_places_found}")
        print(f"   After deduplication: {len(result.places)}")
        print(f"   Duplicates removed: {result.duplicates_removed}")

        for place in result.places:
            print(f"   - {place.name} ({place.category})")

    except Exception as e:
        print(f"❌ Duplicate removal test failed: {e}")

    # Test 3: Address structuring
    print("\n3. Testing address structuring:")
    try:
        gemini_response = GeminiResponse(
            places=[
                PlaceAnalysisResult(
                    name="Test Restaurant",
                    address="   123 Teheran-ro, Gangnam-gu, Seoul, South Korea   ",  # Extra whitespace
                    category="restaurant",
                    confidence=AnalysisConfidence.HIGH,
                )
            ],
            overall_confidence=AnalysisConfidence.HIGH,
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        result = await extractor.extract_and_structure_places(content, gemini_response)

        if result.places:
            addr = result.places[0].structured_address
            print(f"✅ Address structuring:")
            print(f"   Full: {addr.full_address}")
            print(f"   District: {addr.district}")
            print(f"   City: {addr.city}")
            print(f"   Country: {addr.country}")
            print(f"   Completeness: {addr.completeness_score:.2f}")

    except Exception as e:
        print(f"❌ Address structuring test failed: {e}")

    # Test 4: Category normalization
    print("\n4. Testing category normalization:")
    try:
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
                    category="invalid_category",  # Invalid
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

        result = await extractor.extract_and_structure_places(content, gemini_response)

        print(f"✅ Category normalization:")
        for place in result.places:
            print(f"   {place.name}: {place.original_category} → {place.category}")

        print(f"   Validation errors: {len(result.validation_errors)}")
        for error in result.validation_errors:
            print(f"   - {error}")

    except Exception as e:
        print(f"❌ Category normalization test failed: {e}")

    # Test 5: Empty response handling
    print("\n5. Testing empty response:")
    try:
        empty_response = GeminiResponse(
            places=[], overall_confidence=AnalysisConfidence.HIGH
        )

        content = ExtractedContent(
            url="test",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(title="Test"),
        )

        result = await extractor.extract_and_structure_places(content, empty_response)

        print(f"✅ Empty response handling:")
        print(f"   Places found: {len(result.places)}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Data quality: {result.data_quality_score:.3f}")

    except Exception as e:
        print(f"❌ Empty response test failed: {e}")

    print("\n🎉 All place extractor tests completed!")


if __name__ == "__main__":
    asyncio.run(test_place_extractor())
