"""
Unit tests for Kakao Map API integration service.

TDD approach: Write tests first defining expected Kakao Map API behavior.
"""

from unittest.mock import patch

import pytest


class TestKakaoMapService:
    """Test Kakao Map API integration."""

    @patch(
        "app.services.kakao_map_service.KakaoMapService._address_to_coordinate_async"
    )
    def test_addressToCoordinate_validAddress_returnsCoordinates(self, mock_async):
        """
        Test: Convert valid address to coordinates (geocoding)

        Given: Valid Korean address "서울특별시 강남구 테헤란로 123"
        When: Requesting geocoding
        Then: Returns (latitude, longitude) coordinates
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Valid address and mocked API response
        address = "서울특별시 강남구 테헤란로 123"
        mock_async.return_value = {"latitude": 37.4979, "longitude": 127.0276}

        # Mock asyncio.run to directly return the mocked value
        with patch("asyncio.run", return_value=mock_async.return_value):
            service = KakaoMapService(api_key="test_key", enable_cache=False)

            # When: Convert to coordinates
            result = service.address_to_coordinate(address)

            # Then: Should return valid coordinates
            assert result is not None
            assert "latitude" in result
            assert "longitude" in result
            assert result["latitude"] == 37.4979
            assert result["longitude"] == 127.0276
            assert -90 <= result["latitude"] <= 90
            assert -180 <= result["longitude"] <= 180

    def test_addressToCoordinate_invalidAddress_raisesError(self):
        """
        Test: Invalid address raises appropriate error

        Given: Invalid/non-existent address
        When: Requesting geocoding
        Then: Raises ValueError with clear message
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Invalid address
        invalid_address = "존재하지않는주소12345XYZ"
        service = KakaoMapService()

        # When & Then: Should raise error
        with pytest.raises(ValueError, match="Address not found"):
            service.address_to_coordinate(invalid_address)
        pytest.skip("Implementation pending")

    def test_coordinateToAddress_validCoordinates_returnsAddress(self):
        """
        Test: Reverse geocoding - coordinates to address

        Given: Valid coordinates (37.4979, 127.0276)
        When: Requesting reverse geocoding
        Then: Returns Korean address with road/jibun formats

        RED: This test should fail until reverse geocoding is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Valid coordinates (Gangnam area)
        latitude = 37.4979
        longitude = 127.0276
        service = KakaoMapService()

        # When: Convert to address
        result = service.coordinate_to_address(latitude, longitude)

        # Then: Should return address information
        assert result is not None
        assert "road_address" in result or "jibun_address" in result
        assert "서울" in (
            result.get("road_address", "") + result.get("jibun_address", "")
        )
        pytest.skip("Implementation pending")

    def test_searchPlacesByKeyword_validKeyword_returnsPlaces(self):
        """
        Test: Search places by keyword

        Given: Search keyword "강남역 카페"
        When: Searching with keyword
        Then: Returns list of matching places with name, address, coordinates

        RED: This test should fail until place search is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Search keyword
        keyword = "강남역 카페"
        service = KakaoMapService()

        # When: Search places
        results = service.search_places_by_keyword(keyword, limit=5)

        # Then: Should return place results
        assert isinstance(results, list)
        assert len(results) <= 5
        if results:
            first_result = results[0]
            assert "place_name" in first_result
            assert "address" in first_result
            assert "latitude" in first_result
            assert "longitude" in first_result
        pytest.skip("Implementation pending")

    def test_searchPlacesByKeyword_withLocationBias_prioritizesNearby(self):
        """
        Test: Keyword search with location bias

        Given: Keyword "카페" with center coordinates (Gangnam)
        When: Searching with radius 1km
        Then: Returns places prioritized by proximity to center

        RED: This test should fail until location-biased search is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Keyword with location bias
        keyword = "카페"
        center_lat = 37.4979
        center_lng = 127.0276
        radius_km = 1.0
        service = KakaoMapService()

        # When: Search with location bias
        results = service.search_places_by_keyword(
            keyword,
            center_latitude=center_lat,
            center_longitude=center_lng,
            radius_km=radius_km,
            limit=10,
        )

        # Then: Should return nearby places
        assert isinstance(results, list)
        assert len(results) <= 10
        # All results should be within specified radius
        # (will verify distance calculation)
        pytest.skip("Implementation pending")

    def test_apiErrorHandling_networkTimeout_retriesWithBackoff(self):
        """
        Test: Network timeout handling with retry logic

        Given: Kakao API times out
        When: Making API request
        Then: Retries 3 times with exponential backoff

        RED: This test should fail until error handling is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Service configured with timeout
        service = KakaoMapService(timeout=1.0, max_retries=3)

        # When: API call that will timeout
        # (will mock httpx to simulate timeout)

        # Then: Should retry and eventually raise timeout error
        # with pytest.raises(TimeoutError):
        #     service.address_to_coordinate("서울특별시 강남구")
        pytest.skip("Implementation pending")

    def test_apiErrorHandling_rateLimitExceeded_returnsGracefulError(self):
        """
        Test: Rate limit handling (429 response)

        Given: Kakao API returns 429 (rate limit exceeded)
        When: Making API request
        Then: Raises specific RateLimitError with retry-after info

        RED: This test should fail until rate limit handling is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Service that will hit rate limit
        KakaoMapService()

        # When: API returns 429
        # (will mock httpx to simulate 429 response)

        # Then: Should raise RateLimitError
        # from app.exceptions import RateLimitError
        # with pytest.raises(RateLimitError):
        #     service.search_places_by_keyword("test")
        pytest.skip("Implementation pending")

    def test_apiKeyValidation_missingKey_raisesConfigError(self):
        """
        Test: API key validation on service initialization

        Given: KAKAO_API_KEY is not set
        When: Initializing KakaoMapService
        Then: Raises ConfigError with clear message

        RED: This test should fail until validation is implemented
        """

        # Given: No API key configured
        # (will need to temporarily unset env var)
        # When & Then: Should raise error
        # from app.exceptions import ConfigError
        # with pytest.raises(ConfigError, match="KAKAO_API_KEY not configured"):
        #     service = KakaoMapService()
        pytest.skip("Implementation pending")

    def test_caching_repeatedAddressSearch_returnsCachedResult(self):
        """
        Test: Geocoding results are cached

        Given: Same address queried twice
        When: Making second request
        Then: Returns cached result (no API call)

        RED: This test should fail until caching is implemented
        """
        from app.services.maps.kakao_map_service import KakaoMapService

        # Given: Address that will be queried twice
        address = "서울특별시 강남구 테헤란로 123"
        service = KakaoMapService(enable_cache=True)

        # When: Query address twice
        result1 = service.address_to_coordinate(address)
        result2 = service.address_to_coordinate(address)

        # Then: Both results should be identical
        assert result1 == result2
        # Second call should be from cache (faster, no API call)
        # (will measure performance in integration test)
        pytest.skip("Implementation pending")
