"""
Kakao Map API integration service.

Provides geocoding, reverse geocoding, and place search functionality.
"""

import logging
from typing import Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class KakaoMapServiceError(Exception):
    """Base exception for Kakao Map service errors."""


class RateLimitError(KakaoMapServiceError):
    """Raised when API rate limit is exceeded."""


class ConfigError(KakaoMapServiceError):
    """Raised when configuration is invalid."""


class KakaoMapService:
    """
    Kakao Map API integration service.

    Provides:
    - Geocoding (address → coordinates)
    - Reverse geocoding (coordinates → address)
    - Place search by keyword
    - Location-biased search
    """

    BASE_URL = "https://dapi.kakao.com/v2/local"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        enable_cache: bool = True,
    ):
        """
        Initialize Kakao Map service.

        Args:
            api_key: Kakao REST API key (defaults to settings.KAKAO_API_KEY)
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            enable_cache: Enable result caching (future implementation)

        Raises:
            ConfigError: If API key is not configured
        """
        self.api_key = api_key or settings.KAKAO_API_KEY
        if not self.api_key:
            raise ConfigError("KAKAO_API_KEY not configured")

        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._cache: Dict[str, any] = {} if enable_cache else None

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization."""
        return {
            "Authorization": f"KakaoAK {self.api_key}",
            "KA": "sdk/1.0 os/python origin/hotly-app",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _make_request(
        self, endpoint: str, params: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Make HTTP request to Kakao API with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            RateLimitError: If rate limit is exceeded (429)
            KakaoMapServiceError: For other API errors
            TimeoutError: If request times out
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds"
                    )

                # Handle other errors
                if response.status_code != 200:
                    raise KakaoMapServiceError(
                        f"Kakao API error: {response.status_code} - {response.text}"
                    )

                return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Kakao API timeout: {e}")
            raise TimeoutError(f"Request timeout after {self.timeout}s") from e
        except httpx.HTTPError as e:
            logger.error(f"Kakao API HTTP error: {e}")
            raise KakaoMapServiceError(f"HTTP error: {e}") from e

    def address_to_coordinate(self, address: str) -> Dict[str, float]:
        """
        Convert address to coordinates (geocoding).

        Args:
            address: Korean address string

        Returns:
            Dictionary with 'latitude' and 'longitude' keys

        Raises:
            ValueError: If address is not found
            KakaoMapServiceError: For API errors
        """
        # Check cache
        if self.enable_cache and address in self._cache:
            logger.info(f"Cache hit for address: {address}")
            return self._cache[address]

        # Synchronous wrapper for async call
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, use run_until_complete
            result = loop.run_until_complete(self._address_to_coordinate_async(address))
        else:
            result = asyncio.run(self._address_to_coordinate_async(address))

        # Cache result
        if self.enable_cache:
            self._cache[address] = result

        return result

    async def _address_to_coordinate_async(self, address: str) -> Dict[str, float]:
        """Async implementation of address_to_coordinate."""
        params = {"query": address}
        data = await self._make_request("search/address.json", params)

        documents = data.get("documents", [])
        if not documents:
            raise ValueError(f"Address not found: {address}")

        # Use first result
        doc = documents[0]
        return {
            "latitude": float(doc["y"]),  # Kakao returns y=lat, x=lng
            "longitude": float(doc["x"]),
        }

    def coordinate_to_address(
        self, latitude: float, longitude: float
    ) -> Dict[str, Optional[str]]:
        """
        Convert coordinates to address (reverse geocoding).

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)

        Returns:
            Dictionary with address information:
            - road_address: Road-based address
            - jibun_address: Lot-based address

        Raises:
            KakaoMapServiceError: For API errors
        """
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            result = loop.run_until_complete(
                self._coordinate_to_address_async(latitude, longitude)
            )
        else:
            result = asyncio.run(self._coordinate_to_address_async(latitude, longitude))

        return result

    async def _coordinate_to_address_async(
        self, latitude: float, longitude: float
    ) -> Dict[str, Optional[str]]:
        """Async implementation of coordinate_to_address."""
        params = {"x": longitude, "y": latitude}  # Kakao: x=lng, y=lat
        data = await self._make_request("geo/coord2address.json", params)

        documents = data.get("documents", [])
        if not documents:
            return {"road_address": None, "jibun_address": None}

        doc = documents[0]
        result = {}

        # Road address
        road_addr = doc.get("road_address")
        if road_addr:
            result["road_address"] = road_addr.get("address_name")

        # Jibun address
        jibun_addr = doc.get("address")
        if jibun_addr:
            result["jibun_address"] = jibun_addr.get("address_name")

        return result

    def search_places_by_keyword(
        self,
        keyword: str,
        center_latitude: Optional[float] = None,
        center_longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        limit: int = 15,
    ) -> List[Dict[str, any]]:
        """
        Search places by keyword.

        Args:
            keyword: Search keyword
            center_latitude: Center point latitude for location-biased search
            center_longitude: Center point longitude for location-biased search
            radius_km: Search radius in kilometers (max 20km)
            limit: Maximum number of results (1-45)

        Returns:
            List of place dictionaries with:
            - place_name: Place name
            - address: Address
            - latitude, longitude: Coordinates
            - distance: Distance from center (if center provided)

        Raises:
            KakaoMapServiceError: For API errors
        """
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            result = loop.run_until_complete(
                self._search_places_async(
                    keyword, center_latitude, center_longitude, radius_km, limit
                )
            )
        else:
            result = asyncio.run(
                self._search_places_async(
                    keyword, center_latitude, center_longitude, radius_km, limit
                )
            )

        return result

    async def _search_places_async(
        self,
        keyword: str,
        center_latitude: Optional[float],
        center_longitude: Optional[float],
        radius_km: Optional[float],
        limit: int,
    ) -> List[Dict[str, any]]:
        """Async implementation of search_places_by_keyword."""
        params = {"query": keyword, "size": min(limit, 45)}

        # Add location bias if provided
        if center_latitude is not None and center_longitude is not None:
            params["x"] = center_longitude
            params["y"] = center_latitude

            if radius_km is not None:
                # Kakao API uses meters
                params["radius"] = int(radius_km * 1000)

        data = await self._make_request("search/keyword.json", params)

        documents = data.get("documents", [])
        results = []

        for doc in documents:
            place = {
                "place_name": doc.get("place_name"),
                "address": doc.get("address_name"),
                "latitude": float(doc.get("y")),
                "longitude": float(doc.get("x")),
            }

            # Add optional fields
            if doc.get("distance"):
                place["distance"] = float(doc.get("distance"))

            results.append(place)

        return results
