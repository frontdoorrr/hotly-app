"""
Travel Time Calculator Service

Calculates travel time between locations considering various factors.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TravelTimeCalculator:
    """Service for calculating travel times between locations."""

    def __init__(self) -> None:
        self.default_travel_time: int = 30  # Default 30 minutes
        self.cache: Dict[str, int] = {}  # Simple in-memory cache

    async def calculate(
        self,
        destination_place_id: str,
        arrival_time: datetime,
        origin_coordinates: Optional[Tuple[float, float]] = None,
        transport_method: str = "walking",
    ) -> int:
        """
        Calculate travel time to destination.

        Args:
            destination_place_id: ID of destination place
            arrival_time: Expected arrival time
            origin_coordinates: Starting point coordinates (lat, lng)
            transport_method: Transportation method

        Returns:
            Travel time in minutes
        """
        try:
            # Create cache key
            cache_key = f"{destination_place_id}_{transport_method}_{arrival_time.hour}"

            # Check cache first
            if cache_key in self.cache:
                logger.debug(f"Using cached travel time for {destination_place_id}")
                return self.cache[cache_key]

            # For now, return mock travel times based on transport method
            # In real implementation, this would call external APIs
            travel_times: Dict[str, int] = {
                "walking": 45,
                "driving": 25,
                "transit": 35,
                "bicycle": 20,
            }

            calculated_time: int = travel_times.get(
                transport_method, self.default_travel_time
            )

            # Adjust for rush hour
            if self._is_rush_hour(arrival_time):
                if transport_method in ["driving", "transit"]:
                    calculated_time = int(
                        calculated_time * 1.5
                    )  # 50% longer during rush hour

            # Cache the result
            self.cache[cache_key] = calculated_time

            logger.info(
                f"Calculated travel time to {destination_place_id}: {calculated_time} minutes"
            )
            return calculated_time

        except Exception as e:
            logger.error(f"Failed to calculate travel time: {e}")
            return self.default_travel_time

    def _is_rush_hour(self, dt: datetime) -> bool:
        """Check if time is during rush hour."""
        hour: int = dt.hour
        weekday: int = dt.weekday()

        # Weekday rush hours: 7-9 AM and 6-8 PM
        if weekday < 5:  # Monday to Friday
            return (7 <= hour <= 9) or (18 <= hour <= 20)

        return False

    async def get_route_info(
        self, destination_place_id: str, transport_method: str = "walking"
    ) -> Dict[str, Any]:
        """
        Get detailed route information.

        Args:
            destination_place_id: ID of destination place
            transport_method: Transportation method

        Returns:
            Route information with distance, time, instructions
        """
        try:
            # Mock route information
            # In real implementation, this would call mapping APIs

            base_info: Dict[str, Dict[str, Any]] = {
                "walking": {
                    "distance_km": 2.5,
                    "duration_minutes": 45,
                    "steps": [
                        "Head north on Main St",
                        "Turn right on Oak Ave",
                        "Destination will be on the left",
                    ],
                },
                "driving": {
                    "distance_km": 8.2,
                    "duration_minutes": 25,
                    "steps": [
                        "Take Highway 101 North",
                        "Exit at Downtown",
                        "Turn left on First St",
                    ],
                },
                "transit": {
                    "distance_km": 12.1,
                    "duration_minutes": 35,
                    "steps": [
                        "Walk to Metro Station",
                        "Take Line 2 to Downtown",
                        "Walk 5 minutes to destination",
                    ],
                },
            }

            info = base_info.get(transport_method, base_info["walking"])

            return {
                "destination_place_id": destination_place_id,
                "transport_method": transport_method,
                "total_duration_minutes": int(info["duration_minutes"]),
                "total_distance_km": float(info["distance_km"]),
                "route_steps": list(info["steps"]),
                "calculated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get route info: {e}")
            return {
                "destination_place_id": destination_place_id,
                "transport_method": transport_method,
                "total_duration_minutes": self.default_travel_time,
                "error": str(e),
            }
