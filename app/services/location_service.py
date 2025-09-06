"""Real-time location tracking and routing service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.place import Place
from app.utils.distance_calculator import DistanceCalculator

logger = logging.getLogger(__name__)


class LocationService:
    """Service for real-time location tracking and route optimization."""

    def __init__(self, db: Session):
        self.db = db
        self.distance_calculator = DistanceCalculator()
        self.location_cache = {}  # In-memory cache for frequently accessed locations

    async def calculate_route_info(
        self, waypoints: List[Dict[str, Any]], travel_mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Calculate route information for multiple waypoints.

        Args:
            waypoints: List of waypoint coordinates with names
            travel_mode: Transportation mode (driving, walking, transit)

        Returns:
            Route information with distances and durations
        """
        try:
            if len(waypoints) < 2:
                raise ValueError("Route must have at least 2 waypoints")

            total_distance = 0.0
            estimated_duration = 0.0
            waypoint_distances = []

            # Calculate distances between consecutive waypoints
            for i in range(len(waypoints) - 1):
                start = waypoints[i]
                end = waypoints[i + 1]

                distance_km = self.distance_calculator.haversine_distance(
                    start["latitude"],
                    start["longitude"],
                    end["latitude"],
                    end["longitude"],
                )

                # Estimate duration based on travel mode
                duration_minutes = self._estimate_travel_time(distance_km, travel_mode)

                waypoint_distances.append(
                    {
                        "from": start.get("name", f"Point {i+1}"),
                        "to": end.get("name", f"Point {i+2}"),
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": round(duration_minutes, 1),
                    }
                )

                total_distance += distance_km
                estimated_duration += duration_minutes

            route_info = {
                "total_distance_km": round(total_distance, 2),
                "estimated_duration_minutes": round(estimated_duration, 1),
                "waypoint_count": len(waypoints),
                "waypoint_distances": waypoint_distances,
                "travel_mode": travel_mode,
                "calculated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Route calculated: {total_distance:.2f}km, {estimated_duration:.1f}min"
            )
            return route_info

        except Exception as e:
            logger.error(f"Error calculating route info: {e}")
            raise

    async def get_google_directions(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> Dict[str, Any]:
        """
        Get directions using Google Maps API.

        Args:
            origin_lat, origin_lng: Starting coordinates
            dest_lat, dest_lng: Destination coordinates
            mode: Travel mode

        Returns:
            Google Maps directions response
        """
        try:
            # Cache key for directions
            cache_key = (
                f"directions_{origin_lat}_{origin_lng}_{dest_lat}_{dest_lng}_{mode}"
            )

            # Check cache first
            if cache_key in self.location_cache:
                cached_result = self.location_cache[cache_key]
                if (
                    datetime.utcnow() - cached_result["cached_at"]
                ).seconds < 3600:  # 1 hour cache
                    logger.info("Returning cached directions")
                    return cached_result["data"]

            # In production, this would call actual Google Maps API
            # For now, return simulated response
            mock_directions = {
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "distance": {"value": 5000, "text": "5.0 km"},
                                "duration": {"value": 900, "text": "15 mins"},
                                "start_location": {
                                    "lat": origin_lat,
                                    "lng": origin_lng,
                                },
                                "end_location": {"lat": dest_lat, "lng": dest_lng},
                            }
                        ],
                        "overview_polyline": {"points": "mock_encoded_polyline"},
                        "summary": "테헤란로 via 강남대로",
                    }
                ],
                "geocoded_waypoints": [
                    {"geocoder_status": "OK", "place_id": "mock_place_id_1"},
                    {"geocoder_status": "OK", "place_id": "mock_place_id_2"},
                ],
            }

            # Cache the result
            self.location_cache[cache_key] = {
                "data": mock_directions,
                "cached_at": datetime.utcnow(),
            }

            logger.info(f"Google directions calculated for {mode} mode")
            return mock_directions

        except Exception as e:
            logger.error(f"Error getting Google directions: {e}")
            raise

    def update_user_location(
        self,
        user_id: UUID,
        latitude: float,
        longitude: float,
        accuracy_meters: int,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Update user's current location.

        Args:
            user_id: User identifier
            latitude, longitude: Current coordinates
            accuracy_meters: GPS accuracy
            timestamp: Location timestamp

        Returns:
            Location update confirmation with nearby place updates
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Validate coordinates
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Invalid coordinates")

            # Store location update (would save to database in production)
            location_data = {
                "user_id": str(user_id),
                "latitude": latitude,
                "longitude": longitude,
                "accuracy_meters": accuracy_meters,
                "timestamp": timestamp.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Calculate distances to user's saved places
            nearby_updates = self._calculate_distances_to_saved_places(
                user_id, latitude, longitude
            )

            result = {
                "location_updated": True,
                "current_location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy_meters": accuracy_meters,
                },
                "nearby_places_updated": len(nearby_updates),
                "next_update_recommended_seconds": self._calculate_update_interval(
                    accuracy_meters
                ),
            }

            logger.info(f"Location updated for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error updating user location: {e}")
            raise

    def optimize_route_order(
        self,
        places: List[Dict[str, Any]],
        start_location: Dict[str, float],
        optimization_goal: str = "shortest_time",
    ) -> Dict[str, Any]:
        """
        Optimize visit order for multiple places using TSP algorithm.

        Args:
            places: List of places to visit
            start_location: Starting point
            optimization_goal: Optimization criteria

        Returns:
            Optimized route order and metrics
        """
        try:
            if len(places) <= 1:
                return {
                    "optimized_order": [
                        p.get("place_id", i) for i, p in enumerate(places)
                    ],
                    "total_distance_km": 0.0,
                    "estimated_duration_minutes": 0.0,
                }

            # Simple nearest neighbor heuristic for TSP
            # In production, would use more sophisticated algorithms

            current_location = start_location
            unvisited = places.copy()
            route_order = []
            total_distance = 0.0
            total_duration = 0.0

            while unvisited:
                # Find nearest unvisited place
                nearest_place = None
                min_distance = float("inf")
                nearest_index = -1

                for i, place in enumerate(unvisited):
                    distance = self.distance_calculator.haversine_distance(
                        current_location["latitude"],
                        current_location["longitude"],
                        place["latitude"],
                        place["longitude"],
                    )

                    if distance < min_distance:
                        min_distance = distance
                        nearest_place = place
                        nearest_index = i

                # Add nearest place to route
                route_order.append(nearest_place.get("place_id", nearest_index))
                total_distance += min_distance

                # Estimate travel time
                travel_time = self._estimate_travel_time(min_distance, "driving")
                visit_time = nearest_place.get(
                    "visit_duration", 30
                )  # Default 30 minutes
                total_duration += travel_time + visit_time

                # Update current location and remove from unvisited
                current_location = {
                    "latitude": nearest_place["latitude"],
                    "longitude": nearest_place["longitude"],
                }
                unvisited.pop(nearest_index)

            optimized_route = {
                "optimized_order": route_order,
                "total_distance_km": round(total_distance, 2),
                "estimated_duration_minutes": round(total_duration, 1),
                "optimization_method": "nearest_neighbor",
                "efficiency_score": self._calculate_efficiency_score(
                    total_distance, len(places)
                ),
            }

            logger.info(
                f"Route optimized: {len(places)} places, {total_distance:.2f}km"
            )
            return optimized_route

        except Exception as e:
            logger.error(f"Error optimizing route: {e}")
            raise

    def calculate_eta(
        self,
        current_location: Dict[str, float],
        destination: Dict[str, float],
        travel_mode: str = "driving",
    ) -> Dict[str, Any]:
        """
        Calculate estimated time of arrival.

        Args:
            current_location: Current coordinates
            destination: Destination coordinates
            travel_mode: Transportation mode

        Returns:
            ETA information with real-time updates
        """
        try:
            distance_km = self.distance_calculator.haversine_distance(
                current_location["latitude"],
                current_location["longitude"],
                destination["latitude"],
                destination["longitude"],
            )

            duration_minutes = self._estimate_travel_time(distance_km, travel_mode)
            arrival_time = datetime.utcnow() + timedelta(minutes=duration_minutes)

            eta_info = {
                "remaining_distance_km": round(distance_km, 2),
                "estimated_duration_minutes": round(duration_minutes, 1),
                "estimated_arrival_time": arrival_time.isoformat(),
                "travel_mode": travel_mode,
                "confidence": self._calculate_eta_confidence(distance_km, travel_mode),
                "last_updated": datetime.utcnow().isoformat(),
            }

            logger.info(f"ETA calculated: {duration_minutes:.1f}min to destination")
            return eta_info

        except Exception as e:
            logger.error(f"Error calculating ETA: {e}")
            raise

    def _calculate_distances_to_saved_places(
        self, user_id: UUID, user_lat: float, user_lng: float
    ) -> List[Dict[str, Any]]:
        """Calculate distances from current location to user's saved places."""
        try:
            # Get user's active places
            places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.latitude.isnot(None),
                    Place.longitude.isnot(None),
                )
                .limit(50)
                .all()
            )  # Limit for performance

            distance_updates = []

            for place in places:
                distance = self.distance_calculator.haversine_distance(
                    user_lat, user_lng, place.latitude, place.longitude
                )

                distance_updates.append(
                    {
                        "place_id": str(place.id),
                        "place_name": place.name,
                        "distance_km": round(distance, 2),
                        "is_nearby": distance <= 1.0,  # Within 1km
                        "walking_minutes": round(
                            distance * 12, 1
                        ),  # Rough walking time
                    }
                )

            return distance_updates

        except Exception as e:
            logger.error(f"Error calculating distances to saved places: {e}")
            return []

    def _estimate_travel_time(self, distance_km: float, travel_mode: str) -> float:
        """Estimate travel time based on distance and mode."""
        # Average speeds by travel mode (km/h)
        mode_speeds = {
            "walking": 5.0,
            "bicycling": 15.0,
            "driving": 30.0,  # Urban driving with traffic
            "transit": 20.0,  # Public transportation
        }

        speed = mode_speeds.get(travel_mode, 30.0)
        duration_hours = distance_km / speed
        duration_minutes = duration_hours * 60

        # Add buffer time for stops, traffic, etc.
        if travel_mode == "driving":
            duration_minutes *= 1.3  # 30% buffer for traffic
        elif travel_mode == "transit":
            duration_minutes *= 1.5  # 50% buffer for connections/waiting

        return duration_minutes

    def _calculate_update_interval(self, accuracy_meters: int) -> int:
        """Calculate recommended location update interval based on accuracy."""
        if accuracy_meters <= 10:
            return 30  # High accuracy: update every 30 seconds
        elif accuracy_meters <= 50:
            return 60  # Medium accuracy: update every minute
        else:
            return 120  # Low accuracy: update every 2 minutes

    def _calculate_efficiency_score(
        self, total_distance: float, place_count: int
    ) -> float:
        """Calculate route efficiency score."""
        if place_count <= 1:
            return 1.0

        # Calculate theoretical minimum distance (straight line to all places)
        # This is a simplified efficiency metric
        theoretical_min = place_count * 2.0  # Assume 2km average between places
        efficiency = (
            min(theoretical_min / total_distance, 1.0) if total_distance > 0 else 0
        )

        return round(efficiency, 3)

    def _calculate_eta_confidence(self, distance_km: float, travel_mode: str) -> float:
        """Calculate confidence in ETA prediction."""
        # Confidence decreases with distance and varies by travel mode
        base_confidence = 0.9

        # Distance factor
        distance_penalty = min(
            distance_km / 50, 0.3
        )  # Max 30% penalty for long distances

        # Travel mode factor
        mode_reliability = {
            "walking": 0.95,
            "driving": 0.7,  # Traffic variability
            "transit": 0.6,  # Schedule variability
            "bicycling": 0.8,
        }

        mode_factor = mode_reliability.get(travel_mode, 0.7)
        final_confidence = (base_confidence - distance_penalty) * mode_factor

        return round(max(final_confidence, 0.1), 3)  # Minimum 10% confidence


class GoogleMapsService:
    """Service for Google Maps API integration."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock_api_key"  # Would use real API key
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        alternatives: bool = False,
    ) -> Dict[str, Any]:
        """
        Get directions from Google Maps API.

        Args:
            origin: Origin address or coordinates
            destination: Destination address or coordinates
            mode: Travel mode
            alternatives: Whether to return alternative routes

        Returns:
            Google Maps directions response
        """
        try:
            # Mock Google Maps API response for development
            # In production, would make actual API call

            mock_response = {
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "distance": {"value": 8500, "text": "8.5 km"},
                                "duration": {"value": 1200, "text": "20 mins"},
                                "start_address": "강남역, 서울",
                                "end_address": "명동역, 서울",
                                "steps": [
                                    {
                                        "distance": {"value": 2000, "text": "2.0 km"},
                                        "duration": {"value": 300, "text": "5 mins"},
                                        "html_instructions": "Head north on 테헤란로",
                                        "polyline": {
                                            "points": "mock_polyline_segment_1"
                                        },
                                    },
                                    {
                                        "distance": {"value": 6500, "text": "6.5 km"},
                                        "duration": {"value": 900, "text": "15 mins"},
                                        "html_instructions": "Continue on 을지로 toward 명동",
                                        "polyline": {
                                            "points": "mock_polyline_segment_2"
                                        },
                                    },
                                ],
                            }
                        ],
                        "overview_polyline": {"points": "mock_overview_polyline"},
                        "summary": "테헤란로/을지로",
                        "warnings": [],
                        "waypoint_order": [],
                    }
                ],
            }

            logger.info(f"Google directions: {origin} → {destination}")
            return mock_response

        except Exception as e:
            logger.error(f"Error getting Google directions: {e}")
            raise

    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Geocode address to coordinates.

        Args:
            address: Address to geocode

        Returns:
            Geocoding result with coordinates
        """
        try:
            # Mock geocoding response
            mock_geocoding = {
                "status": "OK",
                "results": [
                    {
                        "address_components": [
                            {
                                "long_name": "강남구",
                                "short_name": "강남구",
                                "types": ["sublocality"],
                            },
                            {
                                "long_name": "서울",
                                "short_name": "서울",
                                "types": ["locality"],
                            },
                        ],
                        "formatted_address": "대한민국 서울특별시 강남구",
                        "geometry": {
                            "location": {"lat": 37.5665, "lng": 126.9780},
                            "location_type": "APPROXIMATE",
                            "viewport": {
                                "northeast": {"lat": 37.5678, "lng": 126.9793},
                                "southwest": {"lat": 37.5652, "lng": 126.9767},
                            },
                        },
                        "place_id": "mock_place_id",
                        "types": ["sublocality", "political"],
                    }
                ],
            }

            logger.info(f"Geocoded address: {address}")
            return mock_geocoding

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            raise

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to address.

        Args:
            latitude, longitude: Coordinates to reverse geocode

        Returns:
            Address information
        """
        try:
            # Mock reverse geocoding response
            mock_reverse = {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "대한민국 서울특별시 강남구 테헤란로 123",
                        "address_components": [
                            {
                                "long_name": "123",
                                "short_name": "123",
                                "types": ["street_number"],
                            },
                            {
                                "long_name": "테헤란로",
                                "short_name": "테헤란로",
                                "types": ["route"],
                            },
                            {
                                "long_name": "강남구",
                                "short_name": "강남구",
                                "types": ["sublocality"],
                            },
                        ],
                        "geometry": {
                            "location": {"lat": latitude, "lng": longitude},
                            "location_type": "ROOFTOP",
                        },
                        "place_id": "mock_reverse_place_id",
                        "types": ["street_address"],
                    }
                ],
            }

            logger.info(f"Reverse geocoded: ({latitude}, {longitude})")
            return mock_reverse

        except Exception as e:
            logger.error(f"Error reverse geocoding: {e}")
            raise
