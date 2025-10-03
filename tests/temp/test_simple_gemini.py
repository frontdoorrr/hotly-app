#!/usr/bin/env python3
"""Simple test script for Gemini analyzer."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas.ai import PlaceAnalysisRequest
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType
from app.services.ai.gemini_analyzer_v2 import GeminiAnalyzerV2


async def test_gemini_analyzer():
    """Test Gemini analyzer functionality."""
    print("Testing GeminiAnalyzerV2...")

    analyzer = GeminiAnalyzerV2()

    # Test 1: Basic content extraction
    print("\n1. Testing basic place analysis:")
    try:
        content = ExtractedContent(
            url="https://www.instagram.com/p/ABC123/",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(
                title="Amazing Korean BBQ in Gangnam",
                description="Just had the best Korean BBQ at this place in Gangnam! The beef was incredible and the service was amazing. Located near Gangnam Station. #koreanbbq #gangnam #seoul #restaurant",
                images=["https://instagram.com/image1.jpg"],
                location="Gangnam, Seoul",
                hashtags=["#koreanbbq", "#gangnam", "#seoul", "#restaurant"],
            ),
        )

        result = await analyzer.analyze_place_content_extracted(content)

        print(f"✅ Analysis completed successfully:")
        print(f"   Found {len(result.places)} place(s)")
        print(f"   Overall confidence: {result.overall_confidence.value}")
        print(f"   Processing time: {result.processing_time:.3f}s")

        for i, place in enumerate(result.places):
            print(f"   Place {i+1}:")
            print(f"     Name: {place.name}")
            print(f"     Category: {place.category}")
            print(f"     Confidence: {place.confidence.value}")
            print(f"     Address: {place.address}")

    except Exception as e:
        print(f"❌ Basic analysis failed: {e}")

    # Test 2: Multiple places
    print("\n2. Testing multiple place detection:")
    try:
        content = ExtractedContent(
            url="https://blog.naver.com/user/post",
            platform=PlatformType.NAVER_BLOG,
            metadata=ContentMetadata(
                title="Hongdae Food Tour",
                description="Today we visited 3 great places: First, amazing pasta at Italian Corner restaurant, then coffee at Blue Bottle Coffee, and finally drinks at Rooftop Bar with great city view.",
                images=["https://blog.image.jpg"],
                hashtags=["#hongdae", "#food", "#tour"],
            ),
        )

        result = await analyzer.analyze_place_content_extracted(content)

        print(f"✅ Multiple place analysis:")
        print(f"   Found {len(result.places)} place(s)")
        for place in result.places:
            print(f"     - {place.name} ({place.category})")

    except Exception as e:
        print(f"❌ Multiple place analysis failed: {e}")

    # Test 3: No places found
    print("\n3. Testing no places scenario:")
    try:
        content = ExtractedContent(
            url="https://www.instagram.com/p/ABC123/",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(
                title="My daily routine",
                description="Morning workout and meditation. Feeling great today! #wellness #motivation",
                images=["https://instagram.com/image1.jpg"],
                hashtags=["#wellness", "#motivation"],
            ),
        )

        result = await analyzer.analyze_place_content_extracted(content)

        print(f"✅ No places scenario:")
        print(f"   Found {len(result.places)} place(s) (expected: 0)")
        print(f"   Confidence: {result.overall_confidence.value}")

    except Exception as e:
        print(f"❌ No places analysis failed: {e}")

    # Test 4: Legacy compatibility
    print("\n4. Testing legacy method compatibility:")
    try:
        request = PlaceAnalysisRequest(
            content_text="Dinner at Jungsik Restaurant in Gangnam",
            content_description="Amazing fine dining experience",
            hashtags=["#jungsik", "#finedining"],
            platform="instagram",
        )

        result = await analyzer.analyze_place_content(request)

        print(f"✅ Legacy method:")
        print(f"   Place name: {result.name}")
        print(f"   Category: {result.category.value}")
        print(f"   Score: {result.recommendation_score}")

    except Exception as e:
        print(f"❌ Legacy method failed: {e}")

    # Test 5: Confidence filtering
    print("\n5. Testing confidence filtering:")
    try:
        content = ExtractedContent(
            url="https://www.instagram.com/p/ABC123/",
            platform=PlatformType.INSTAGRAM,
            metadata=ContentMetadata(
                title="Korean BBQ",
                description="Good food somewhere in Seoul",
                hashtags=["#food"],
            ),
        )

        # Test with different confidence levels
        for min_conf in ["low", "medium", "high"]:
            result = await analyzer.analyze_place_content_extracted(
                content, min_confidence=min_conf
            )
            print(f"   Min confidence '{min_conf}': {len(result.places)} place(s)")

    except Exception as e:
        print(f"❌ Confidence filtering failed: {e}")

    print("\n🎉 All Gemini analyzer tests completed!")


if __name__ == "__main__":
    asyncio.run(test_gemini_analyzer())
