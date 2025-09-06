"""Distance calculation utilities for geographic operations."""

import math
from typing import List, Tuple


class DistanceCalculator:
    """Utility class for calculating distances between geographic coordinates."""

    EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers

    def haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points on Earth.

        Uses the Haversine formula for accurate distance calculation.

        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point

        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = self.EARTH_RADIUS_KM * c

        return distance

    def bearing_between_points(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate the bearing (direction) from point 1 to point 2.

        Args:
            lat1, lon1: Starting point coordinates
            lat2, lon2: Destination point coordinates

        Returns:
            Bearing in degrees (0-360), where 0 is North
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
            lat2_rad
        ) * math.cos(dlon_rad)

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        # Normalize to 0-360 degrees
        return (bearing_deg + 360) % 360

    def midpoint_between_points(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> Tuple[float, float]:
        """
        Calculate the midpoint between two geographic points.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Tuple of (latitude, longitude) for midpoint
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)

        bx = math.cos(lat2_rad) * math.cos(dlon_rad)
        by = math.cos(lat2_rad) * math.sin(dlon_rad)

        mid_lat = math.atan2(
            math.sin(lat1_rad) + math.sin(lat2_rad),
            math.sqrt((math.cos(lat1_rad) + bx) ** 2 + by**2),
        )

        mid_lon = math.radians(lon1) + math.atan2(by, math.cos(lat1_rad) + bx)

        return (math.degrees(mid_lat), math.degrees(mid_lon))

    def calculate_bounding_box(
        self, center_lat: float, center_lon: float, radius_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box for a center point and radius.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers

        Returns:
            Tuple of (min_lat, min_lon, max_lat, max_lon)
        """
        # Convert radius to degrees (approximate)
        lat_degree_km = 111.0  # 1 degree latitude ≈ 111 km
        lon_degree_km = 111.0 * math.cos(math.radians(center_lat))  # Varies by latitude

        lat_delta = radius_km / lat_degree_km
        lon_delta = radius_km / lon_degree_km

        min_lat = max(center_lat - lat_delta, -90.0)
        max_lat = min(center_lat + lat_delta, 90.0)
        min_lon = max(center_lon - lon_delta, -180.0)
        max_lon = min(center_lon + lon_delta, 180.0)

        return (min_lat, min_lon, max_lat, max_lon)

    def is_point_in_polygon(
        self,
        latitude: float,
        longitude: float,
        polygon_points: List[Tuple[float, float]],
    ) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            polygon_points: List of (lat, lon) tuples defining polygon

        Returns:
            True if point is inside polygon
        """
        x, y = longitude, latitude
        n = len(polygon_points)
        inside = False

        p1x, p1y = polygon_points[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon_points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_places_along_route(
        self,
        user_id: UUID,
        waypoints: List[Tuple[float, float]],
        buffer_km: float = 1.0,
        limit: int = 50,
    ) -> List[Tuple[Place, float]]:
        """
        Find places along a route with specified buffer distance.

        Args:
            user_id: User identifier
            waypoints: List of (lat, lon) route points
            buffer_km: Buffer distance from route
            limit: Maximum results

        Returns:
            List of (Place, distance_to_route) tuples
        """
        try:
            places_with_distance = []

            # Get all active places
            places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    Place.coordinates.isnot(None),
                )
                .all()
            )

            for place in places:
                min_distance = float("inf")

                # Find minimum distance to any route segment
                for i in range(len(waypoints) - 1):
                    start_lat, start_lon = waypoints[i]
                    end_lat, end_lon = waypoints[i + 1]

                    distance = self._distance_point_to_line(
                        place.latitude,
                        place.longitude,
                        start_lat,
                        start_lon,
                        end_lat,
                        end_lon,
                    )

                    min_distance = min(min_distance, distance)

                # Include place if within buffer distance
                if min_distance <= buffer_km:
                    places_with_distance.append((place, min_distance))

            # Sort by distance to route
            places_with_distance.sort(key=lambda x: x[1])

            logger.info(f"Found {len(places_with_distance)} places along route")
            return places_with_distance[:limit]

        except Exception as e:
            logger.error(f"Error finding places along route: {e}")
            raise

    def _distance_point_to_line(
        self,
        px: float,
        py: float,  # Point coordinates
        x1: float,
        y1: float,  # Line start
        x2: float,
        y2: float,  # Line end
    ) -> float:
        """
        Calculate minimum distance from point to line segment.

        Returns distance in kilometers using great circle calculations.
        """
        # Vector from line start to point
        A = px - x1
        B = py - y1

        # Vector from line start to end
        C = x2 - x1
        D = y2 - y1

        # Calculate dot product and line length squared
        dot = A * C + B * D
        len_sq = C * C + D * D

        if len_sq == 0:
            # Line is actually a point
            return self.haversine_distance(px, py, x1, y1)

        # Parameter t represents position along line (0 = start, 1 = end)
        t = dot / len_sq

        if t < 0:
            # Closest point is line start
            return self.haversine_distance(px, py, x1, y1)
        elif t > 1:
            # Closest point is line end
            return self.haversine_distance(px, py, x2, y2)
        else:
            # Closest point is on the line segment
            closest_x = x1 + t * C
            closest_y = y1 + t * D
            return self.haversine_distance(px, py, closest_x, closest_y)
