"""Geographic search and spatial analysis service."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.place import Place, PlaceStatus
from app.schemas.geo import GeoBoundingBox, GeoClusterResponse
from app.utils.distance_calculator import DistanceCalculator

logger = logging.getLogger(__name__)


class GeoService:
    """Service for geographic search and spatial operations."""

    def __init__(self, db: Session):
        self.db = db
        self.distance_calculator = DistanceCalculator()

    def search_places_in_radius(
        self,
        user_id: UUID,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Place]:
        """
        Search places within radius with enhanced filtering.

        Args:
            user_id: User identifier
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            category: Optional category filter
            limit: Maximum results

        Returns:
            List of places ordered by distance
        """
        try:
            pass

            # Convert radius to meters
            radius_m = radius_km * 1000

            query = self.db.query(Place).filter(
                Place.user_id == user_id,
                Place.status == PlaceStatus.ACTIVE,
                func.ST_DWithin(
                    Place.coordinates,
                    func.ST_GeogFromText(f"POINT({longitude} {latitude})"),
                    radius_m,
                ),
            )

            # Add category filter if specified
            if category:
                query = query.filter(Place.category == category)

            # Order by distance and limit results
            places = (
                query.order_by(
                    func.ST_Distance(
                        Place.coordinates,
                        func.ST_GeogFromText(f"POINT({longitude} {latitude})"),
                    )
                )
                .limit(limit)
                .all()
            )

            logger.info(
                f"Found {len(places)} places within {radius_km}km of ({latitude}, {longitude})"
            )
            return places

        except Exception as e:
            logger.error(f"Error in radius search: {e}")
            raise

    def get_places_in_bounding_box(
        self, user_id: UUID, bounding_box: GeoBoundingBox, limit: int = 100
    ) -> List[Place]:
        """
        Get places within a bounding box.

        Args:
            user_id: User identifier
            bounding_box: Geographic bounding box
            limit: Maximum results

        Returns:
            List of places within the bounding box
        """
        try:
            pass

            # Create bounding box polygon
            bbox_polygon = func.ST_MakeEnvelope(
                bounding_box.min_longitude,
                bounding_box.min_latitude,
                bounding_box.max_longitude,
                bounding_box.max_latitude,
                4326,  # WGS84 SRID
            )

            places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    func.ST_Within(Place.coordinates, bbox_polygon),
                )
                .limit(limit)
                .all()
            )

            logger.info(f"Found {len(places)} places in bounding box")
            return places

        except Exception as e:
            logger.error(f"Error in bounding box search: {e}")
            raise

    def cluster_places_by_region(
        self, user_id: UUID, cluster_distance_km: float = 2.0, min_cluster_size: int = 2
    ) -> List[GeoClusterResponse]:
        """
        Group places into geographic clusters.

        Args:
            user_id: User identifier
            cluster_distance_km: Maximum distance between places in same cluster
            min_cluster_size: Minimum places per cluster

        Returns:
            List of geographic clusters
        """
        try:
            pass

            # Get all active places for user
            places = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    Place.coordinates.isnot(None),
                )
                .all()
            )

            if not places:
                return []

            # Simple clustering algorithm
            clusters = []
            used_places = set()

            for place in places:
                if place.id in used_places:
                    continue

                # Start new cluster with current place
                cluster_places = [place]
                used_places.add(place.id)

                # Find nearby places for cluster
                for other_place in places:
                    if other_place.id in used_places:
                        continue

                    distance = self.distance_calculator.haversine_distance(
                        place.latitude,
                        place.longitude,
                        other_place.latitude,
                        other_place.longitude,
                    )

                    if distance <= cluster_distance_km:
                        cluster_places.append(other_place)
                        used_places.add(other_place.id)

                # Add cluster if it meets minimum size
                if len(cluster_places) >= min_cluster_size:
                    center_lat = sum(p.latitude for p in cluster_places) / len(
                        cluster_places
                    )
                    center_lng = sum(p.longitude for p in cluster_places) / len(
                        cluster_places
                    )

                    clusters.append(
                        GeoClusterResponse(
                            center_latitude=center_lat,
                            center_longitude=center_lng,
                            place_count=len(cluster_places),
                            place_ids=[str(p.id) for p in cluster_places],
                            radius_km=cluster_distance_km,
                        )
                    )

            logger.info(f"Created {len(clusters)} geographic clusters")
            return clusters

        except Exception as e:
            logger.error(f"Error in geographic clustering: {e}")
            raise

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate geographic coordinates.

        Args:
            latitude: Latitude value
            longitude: Longitude value

        Returns:
            True if coordinates are valid
        """
        return -90 <= latitude <= 90 and -180 <= longitude <= 180

    def get_optimal_zoom_level(self, places: List[Place]) -> int:
        """
        Calculate optimal zoom level for displaying places on map.

        Args:
            places: List of places

        Returns:
            Optimal zoom level (1-20)
        """
        if not places:
            return 10

        # Calculate bounding box
        lats = [p.latitude for p in places if p.latitude]
        lngs = [p.longitude for p in places if p.longitude]

        if not lats or not lngs:
            return 10

        lat_range = max(lats) - min(lats)
        lng_range = max(lngs) - min(lngs)

        # Simple zoom calculation based on coordinate range
        max_range = max(lat_range, lng_range)

        if max_range > 10:
            return 3
        elif max_range > 5:
            return 5
        elif max_range > 1:
            return 8
        elif max_range > 0.1:
            return 12
        else:
            return 15
