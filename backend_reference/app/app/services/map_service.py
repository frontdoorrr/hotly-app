"""Kakao Map SDK integration and map visualization service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.place import Place
from app.utils.distance_calculator import DistanceCalculator

logger = logging.getLogger(__name__)


class MapService:
    """Service for Kakao Map SDK integration and map visualization."""

    def __init__(self, db: Session, kakao_api_key: Optional[str] = None):
        self.db = db
        self.kakao_api_key = kakao_api_key or "mock_kakao_api_key"
        self.distance_calculator = DistanceCalculator()
        self.map_cache = {}  # In-memory cache for map data

    def initialize_map(
        self, center: Dict[str, float], zoom: int = 15, map_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        Initialize Kakao Map with specified configuration.

        Args:
            center: Map center coordinates
            zoom: Initial zoom level (1-20)
            map_type: Map display type

        Returns:
            Map initialization configuration
        """
        try:
            # Validate center coordinates
            if not (
                -90 <= center["latitude"] <= 90 and -180 <= center["longitude"] <= 180
            ):
                raise ValueError("Invalid center coordinates")

            # Validate zoom level
            if not (1 <= zoom <= 20):
                raise ValueError("Zoom level must be between 1 and 20")

            map_config = {
                "map_id": f"kakao_map_{datetime.utcnow().timestamp()}",
                "center": {
                    "latitude": center["latitude"],
                    "longitude": center["longitude"],
                },
                "zoom_level": zoom,
                "map_type": map_type,
                "api_key": self.kakao_api_key,
                "sdk_version": "2.0",
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Map initialized at ({center['latitude']}, {center['longitude']})"
            )
            return map_config

        except Exception as e:
            logger.error(f"Error initializing map: {e}")
            raise

    def create_markers(
        self, places: List[Dict[str, Any]], marker_style: str = "default"
    ) -> Dict[str, Any]:
        """
        Create markers for places on map.

        Args:
            places: List of places with coordinates
            marker_style: Visual style for markers

        Returns:
            Created marker information
        """
        try:
            markers = []

            for place in places:
                # Validate place data
                required_fields = ["latitude", "longitude"]
                for field in required_fields:
                    if field not in place:
                        raise ValueError(f"Place missing required field: {field}")

                marker = {
                    "marker_id": f"marker_{place.get('place_id', len(markers))}",
                    "position": {
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                    },
                    "title": place.get("name", "Unnamed Place"),
                    "style": marker_style,
                    "category": place.get("category", "general"),
                    "clickable": True,
                    "zIndex": 1,
                }

                markers.append(marker)

            marker_response = {
                "markers_created": len(markers),
                "markers": markers,
                "style_applied": marker_style,
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Created {len(markers)} markers with {marker_style} style")
            return marker_response

        except Exception as e:
            logger.error(f"Error creating markers: {e}")
            raise

    def calculate_map_bounds(self, places: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Calculate optimal map bounds for given places.

        Args:
            places: List of places with coordinates

        Returns:
            Optimal map bounds and zoom level
        """
        try:
            if not places:
                raise ValueError("Places list cannot be empty")

            # Find min/max coordinates
            latitudes = [place["latitude"] for place in places]
            longitudes = [place["longitude"] for place in places]

            min_lat, max_lat = min(latitudes), max(latitudes)
            min_lng, max_lng = min(longitudes), max(longitudes)

            # Calculate center
            center_lat = (min_lat + max_lat) / 2
            center_lng = (min_lng + max_lng) / 2

            # Calculate span and optimal zoom
            lat_span = max_lat - min_lat
            lng_span = max_lng - min_lng
            max_span = max(lat_span, lng_span)

            # Estimate zoom level based on span
            if max_span > 0.1:
                zoom_level = 10
            elif max_span > 0.05:
                zoom_level = 12
            elif max_span > 0.01:
                zoom_level = 14
            else:
                zoom_level = 16

            bounds_data = {
                "center": {"latitude": center_lat, "longitude": center_lng},
                "zoom_level": zoom_level,
                "bounds": {
                    "northeast": {"latitude": max_lat, "longitude": max_lng},
                    "southwest": {"latitude": min_lat, "longitude": min_lng},
                },
                "span": {"latitude": lat_span, "longitude": lng_span},
                "places_count": len(places),
            }

            logger.info(
                f"Map bounds calculated for {len(places)} places, zoom: {zoom_level}"
            )
            return bounds_data

        except Exception as e:
            logger.error(f"Error calculating map bounds: {e}")
            raise

    def render_places_on_map(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Render places on map with performance optimization.

        Args:
            places: Places to render

        Returns:
            Rendering result with performance metrics
        """
        try:
            start_time = datetime.utcnow()

            # Optimize rendering for performance
            if len(places) > 100:
                # Use clustering for large datasets
                clustered_data = self._cluster_places(places, cluster_radius=100)
                render_data = clustered_data
            else:
                # Render individual markers
                render_data = {
                    "markers": self._create_marker_data(places),
                    "clustering_applied": False,
                }

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            response_data = {
                "places_rendered": len(places),
                "rendering_method": "clustered" if len(places) > 100 else "individual",
                "processing_time_seconds": round(processing_time, 3),
                "performance_acceptable": processing_time < 1.0,  # 1 second requirement
                "render_data": render_data,
                "rendered_at": end_time.isoformat(),
            }

            logger.info(f"Rendered {len(places)} places in {processing_time:.3f}s")
            return response_data

        except Exception as e:
            logger.error(f"Error rendering places: {e}")
            raise

    def cluster_markers(
        self, places: List[Dict[str, Any]], cluster_threshold: int = 100
    ) -> Dict[str, Any]:
        """
        Apply marker clustering for dense place groups.

        Args:
            places: Places to cluster
            cluster_threshold: Clustering distance threshold in meters

        Returns:
            Clustered marker data
        """
        try:
            clusters = []
            individual_markers = []
            processed_places = set()

            for i, place in enumerate(places):
                if i in processed_places:
                    continue

                # Find nearby places for clustering
                cluster_places = [place]
                processed_places.add(i)

                for j, other_place in enumerate(places[i + 1 :], i + 1):
                    if j in processed_places:
                        continue

                    distance = (
                        self.distance_calculator.haversine_distance(
                            place["latitude"],
                            place["longitude"],
                            other_place["latitude"],
                            other_place["longitude"],
                        )
                        * 1000
                    )  # Convert to meters

                    if distance <= cluster_threshold:
                        cluster_places.append(other_place)
                        processed_places.add(j)

                # Create cluster or individual marker
                if len(cluster_places) >= 2:
                    cluster_center = self._calculate_cluster_center(cluster_places)
                    clusters.append(
                        {
                            "cluster_id": f"cluster_{len(clusters)}",
                            "center": cluster_center,
                            "place_count": len(cluster_places),
                            "places": cluster_places,
                            "radius_meters": cluster_threshold,
                        }
                    )
                else:
                    individual_markers.extend(self._create_marker_data(cluster_places))

            clustering_result = {
                "clusters": clusters,
                "individual_markers": individual_markers,
                "total_clusters": len(clusters),
                "total_individual": len(individual_markers),
                "clustering_threshold": cluster_threshold,
                "processed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Clustering: {len(clusters)} clusters, {len(individual_markers)} individual markers"
            )
            return clustering_result

        except Exception as e:
            logger.error(f"Error clustering markers: {e}")
            raise

    def load_viewport_places(
        self, viewport_bounds: Dict[str, Dict[str, float]], zoom_level: int
    ) -> Dict[str, Any]:
        """
        Load places within viewport bounds for performance.

        Args:
            viewport_bounds: Map viewport boundaries
            zoom_level: Current zoom level

        Returns:
            Places within viewport
        """
        try:
            ne = viewport_bounds["northeast"]
            sw = viewport_bounds["southwest"]

            # Query places within bounds
            places_query = self.db.query(Place).filter(
                Place.latitude.between(sw["latitude"], ne["latitude"]),
                Place.longitude.between(sw["longitude"], ne["longitude"]),
            )

            # Limit results based on zoom level for performance
            limit_by_zoom = {
                range(1, 10): 20,  # City level
                range(10, 14): 50,  # District level
                range(14, 17): 100,  # Street level
                range(17, 21): 200,  # Building level
            }

            limit = 100  # Default
            for zoom_range, zoom_limit in limit_by_zoom.items():
                if zoom_level in zoom_range:
                    limit = zoom_limit
                    break

            places = places_query.limit(limit).all()

            # Convert to map format
            viewport_places = []
            for place in places:
                viewport_places.append(
                    {
                        "place_id": str(place.id),
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                        "name": place.name,
                        "category": place.category,
                        "in_viewport": True,
                    }
                )

            viewport_data = {
                "places_count": len(viewport_places),
                "viewport_bounds": viewport_bounds,
                "zoom_level": zoom_level,
                "places": viewport_places,
                "performance_limit_applied": len(places) == limit,
                "loaded_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Loaded {len(viewport_places)} places for viewport at zoom {zoom_level}"
            )
            return viewport_data

        except Exception as e:
            logger.error(f"Error loading viewport places: {e}")
            raise

    def _cluster_places(
        self, places: List[Dict[str, Any]], cluster_radius: int = 100
    ) -> Dict[str, Any]:
        """Apply clustering algorithm for performance optimization."""
        try:
            # Simple grid-based clustering for performance
            grid_size = (
                cluster_radius / 111320
            )  # Convert meters to degrees (approximate)
            clusters = {}

            for place in places:
                # Calculate grid cell
                grid_lat = int(place["latitude"] / grid_size) * grid_size
                grid_lng = int(place["longitude"] / grid_size) * grid_size
                grid_key = f"{grid_lat:.6f}_{grid_lng:.6f}"

                if grid_key not in clusters:
                    clusters[grid_key] = []
                clusters[grid_key].append(place)

            # Create cluster representations
            cluster_markers = []
            for grid_key, grid_places in clusters.items():
                if len(grid_places) >= 2:
                    center = self._calculate_cluster_center(grid_places)
                    cluster_markers.append(
                        {
                            "type": "cluster",
                            "center": center,
                            "count": len(grid_places),
                            "places": grid_places,
                        }
                    )
                else:
                    cluster_markers.extend(
                        [{"type": "marker", "place": place} for place in grid_places]
                    )

            return {
                "clustered_markers": cluster_markers,
                "clustering_applied": True,
                "cluster_count": sum(
                    1 for m in cluster_markers if m["type"] == "cluster"
                ),
            }

        except Exception as e:
            logger.error(f"Error clustering places: {e}")
            raise

    def _create_marker_data(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create marker data structure for map rendering."""
        markers = []

        for place in places:
            marker = {
                "marker_id": f"marker_{place.get('place_id', len(markers))}",
                "position": {
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                },
                "title": place.get("name", "Unknown Place"),
                "category": place.get("category", "general"),
                "icon": self._get_marker_icon(place.get("category", "general")),
                "zIndex": 1,
                "clickable": True,
            }
            markers.append(marker)

        return markers

    def _calculate_cluster_center(
        self, places: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate center point for a cluster of places."""
        if not places:
            return {"latitude": 0.0, "longitude": 0.0}

        total_lat = sum(place["latitude"] for place in places)
        total_lng = sum(place["longitude"] for place in places)
        count = len(places)

        return {"latitude": total_lat / count, "longitude": total_lng / count}

    def _get_marker_icon(self, category: str) -> str:
        """Get appropriate marker icon based on place category."""
        category_icons = {
            "restaurant": "restaurant_marker.png",
            "cafe": "cafe_marker.png",
            "shopping": "shopping_marker.png",
            "entertainment": "entertainment_marker.png",
            "culture": "culture_marker.png",
            "general": "default_marker.png",
        }

        return category_icons.get(category, "default_marker.png")


class KakaoMapAPIService:
    """Service for Kakao Map API operations."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock_kakao_api_key"
        self.base_url = "https://dapi.kakao.com/v2/local"

    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate Kakao Map API key.

        Returns:
            API key validation status
        """
        try:
            # Mock validation for development
            # In production, would make actual API call to verify key

            validation_result = {
                "api_key_valid": True,
                "key_type": "REST",
                "quota_remaining": 9500,
                "daily_limit": 10000,
                "validated_at": datetime.utcnow().isoformat(),
            }

            logger.info("Kakao API key validation successful")
            return validation_result

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            raise

    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Geocode address using Kakao API.

        Args:
            address: Address to geocode

        Returns:
            Geocoding result with coordinates
        """
        try:
            # Mock Kakao geocoding response
            # In production, would call actual Kakao Geocoding API

            mock_geocoding = {
                "meta": {"total_count": 1, "pageable_count": 1},
                "documents": [
                    {
                        "address": {
                            "address_name": address,
                            "region_1depth_name": "서울",
                            "region_2depth_name": "강남구",
                            "region_3depth_name": "역삼동",
                        },
                        "road_address": {
                            "address_name": f"{address} (도로명)",
                            "region_1depth_name": "서울",
                            "region_2depth_name": "강남구",
                            "road_name": "테헤란로",
                        },
                        "x": "126.9780",  # longitude
                        "y": "37.5665",  # latitude
                    }
                ],
            }

            # Convert to standard format
            result = {
                "latitude": float(mock_geocoding["documents"][0]["y"]),
                "longitude": float(mock_geocoding["documents"][0]["x"]),
                "formatted_address": address,
                "address_components": mock_geocoding["documents"][0]["address"],
            }

            logger.info(f"Geocoded address: {address}")
            return result

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            raise

    async def search_places(
        self, query: str, center: Dict[str, float], radius: int = 1000
    ) -> Dict[str, Any]:
        """
        Search places using Kakao Local API.

        Args:
            query: Search query
            center: Search center coordinates
            radius: Search radius in meters

        Returns:
            Place search results
        """
        try:
            # Mock Kakao Local API response
            # In production, would call actual Kakao Local Search API

            mock_search_results = {
                "meta": {"total_count": 15, "pageable_count": 15},
                "documents": [
                    {
                        "place_name": f"{query} 검색결과 {i}",
                        "category_name": "음식점 > 카페 > 커피전문점",
                        "address_name": f"서울 강남구 테헤란로 {100 + i}",
                        "road_address_name": f"서울 강남구 테헤란로 {100 + i}",
                        "phone": f"02-{3400 + i}-{1000 + i}",
                        "place_url": f"http://place.map.kakao.com/{12345 + i}",
                        "x": str(126.9780 + i * 0.001),  # longitude
                        "y": str(37.5665 + i * 0.001),  # latitude
                        "distance": str(i * 50 + 100),  # distance in meters
                    }
                    for i in range(5)  # Return 5 mock results
                ],
            }

            # Convert to standard format
            search_results = []
            for doc in mock_search_results["documents"]:
                search_results.append(
                    {
                        "place_name": doc["place_name"],
                        "latitude": float(doc["y"]),
                        "longitude": float(doc["x"]),
                        "address": doc["address_name"],
                        "category": doc["category_name"],
                        "phone": doc.get("phone", ""),
                        "distance_meters": int(doc["distance"]),
                        "place_url": doc["place_url"],
                    }
                )

            response = {
                "places": search_results,
                "total_count": len(search_results),
                "query": query,
                "search_center": center,
                "search_radius": radius,
                "searched_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Kakao place search: {query}, found {len(search_results)} results"
            )
            return response

        except Exception as e:
            logger.error(f"Error searching places: {e}")
            raise


class MapVisualizationService:
    """Service for advanced map visualization features."""

    def __init__(self, db: Session):
        self.db = db
        self.distance_calculator = DistanceCalculator()

    def draw_route_path(
        self,
        course_id: str,
        places: List[Dict[str, Any]],
        route_style: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Draw route path connecting course places.

        Args:
            course_id: Course identifier
            places: Ordered list of places in course
            route_style: Visual styling for route line

        Returns:
            Route visualization data
        """
        try:
            if len(places) < 2:
                raise ValueError("Route requires at least 2 places")

            # Sort places by order
            sorted_places = sorted(
                places, key=lambda p: p.get("visit_order", p.get("order", 0))
            )

            # Default route styling
            default_style = {
                "color": "#FF6B6B",
                "weight": 3,
                "opacity": 0.8,
                "dash_pattern": None,
            }
            style = {**default_style, **(route_style or {})}

            # Generate polyline points
            polyline_points = []
            total_distance = 0.0
            total_time = 0.0

            for i in range(len(sorted_places)):
                place = sorted_places[i]
                polyline_points.append(
                    {
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "order": i + 1,
                    }
                )

                # Calculate segment distance and time
                if i > 0:
                    prev_place = sorted_places[i - 1]
                    segment_distance = self.distance_calculator.haversine_distance(
                        prev_place["latitude"],
                        prev_place["longitude"],
                        place["latitude"],
                        place["longitude"],
                    )
                    segment_time = self._estimate_travel_time(
                        segment_distance, "walking"
                    )

                    total_distance += segment_distance
                    total_time += segment_time + place.get("duration_minutes", 30)

            route_data = {
                "course_id": course_id,
                "polyline_points": polyline_points,
                "route_style": style,
                "total_distance_km": round(total_distance, 2),
                "estimated_time_minutes": round(total_time, 1),
                "place_count": len(sorted_places),
                "route_segments": len(polyline_points) - 1,
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Route drawn for course {course_id}: {total_distance:.2f}km")
            return route_data

        except Exception as e:
            logger.error(f"Error drawing route: {e}")
            raise

    def configure_map_interactions(
        self, interaction_config: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Configure map interaction settings.

        Args:
            interaction_config: Map interaction configuration

        Returns:
            Applied interaction configuration
        """
        try:
            default_interactions = {
                "enable_zoom": True,
                "enable_pan": True,
                "enable_marker_click": True,
                "enable_route_modification": False,
                "enable_place_creation": False,
                "enable_context_menu": True,
            }

            # Apply user configuration
            applied_config = {**default_interactions, **interaction_config}

            interaction_result = {
                "interactions_enabled": applied_config,
                "configuration_applied": True,
                "features_count": sum(applied_config.values()),
                "configured_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Map interactions configured: {sum(applied_config.values())} features enabled"
            )
            return interaction_result

        except Exception as e:
            logger.error(f"Error configuring map interactions: {e}")
            raise

    def set_map_theme(self, theme: str) -> Dict[str, Any]:
        """
        Change map visual theme.

        Args:
            theme: Map theme (normal, satellite, hybrid, dark)

        Returns:
            Theme configuration result
        """
        try:
            valid_themes = ["normal", "satellite", "hybrid", "dark"]

            if theme not in valid_themes:
                raise ValueError(f"Invalid theme. Must be one of: {valid_themes}")

            theme_config = {
                "current_theme": theme,
                "available_themes": valid_themes,
                "theme_applied": True,
                "applied_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Map theme changed to: {theme}")
            return theme_config

        except Exception as e:
            logger.error(f"Error setting map theme: {e}")
            raise

    def style_markers_by_category(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply category-based styling to markers.

        Args:
            places: Places with category information

        Returns:
            Styled marker data
        """
        try:
            category_styles = {
                "restaurant": {
                    "color": "#FF6B6B",
                    "icon": "restaurant",
                    "size": "medium",
                },
                "cafe": {"color": "#4ECDC4", "icon": "cafe", "size": "medium"},
                "shopping": {"color": "#45B7D1", "icon": "shopping", "size": "medium"},
                "entertainment": {
                    "color": "#96CEB4",
                    "icon": "entertainment",
                    "size": "large",
                },
                "culture": {"color": "#FECA57", "icon": "culture", "size": "medium"},
                "general": {"color": "#95A5A6", "icon": "default", "size": "small"},
            }

            styled_markers = []
            category_counts = {}

            for place in places:
                category = place.get("category", "general")
                style = category_styles.get(category, category_styles["general"])

                styled_marker = {
                    "place_id": place.get("place_id", ""),
                    "position": {
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                    },
                    "title": place.get("name", "Unknown Place"),
                    "category": category,
                    "style": style,
                    "marker_id": f"styled_marker_{len(styled_markers)}",
                }

                styled_markers.append(styled_marker)
                category_counts[category] = category_counts.get(category, 0) + 1

            styling_result = {
                "styled_markers": styled_markers,
                "category_distribution": category_counts,
                "total_markers": len(styled_markers),
                "styles_applied": len(
                    set(place.get("category", "general") for place in places)
                ),
                "styled_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Applied category styling to {len(styled_markers)} markers")
            return styling_result

        except Exception as e:
            logger.error(f"Error styling markers: {e}")
            raise

    def add_overlay_layers(
        self, layers: List[str], opacity: float = 0.7
    ) -> Dict[str, Any]:
        """
        Add overlay layers to map (traffic, transit, etc.).

        Args:
            layers: List of overlay layer types
            opacity: Layer opacity (0.0 to 1.0)

        Returns:
            Overlay configuration result
        """
        try:
            available_layers = ["traffic", "transit", "bicycle", "walking"]

            # Validate requested layers
            invalid_layers = [
                layer for layer in layers if layer not in available_layers
            ]
            if invalid_layers:
                raise ValueError(
                    f"Invalid layers: {invalid_layers}. Available: {available_layers}"
                )

            # Validate opacity
            if not (0.0 <= opacity <= 1.0):
                raise ValueError("Opacity must be between 0.0 and 1.0")

            overlay_config = {
                "active_layers": layers,
                "opacity": opacity,
                "layer_count": len(layers),
                "available_layers": available_layers,
                "configured_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Added overlay layers: {layers} with opacity {opacity}")
            return overlay_config

        except Exception as e:
            logger.error(f"Error adding overlay layers: {e}")
            raise

    def _estimate_travel_time(self, distance_km: float, mode: str = "walking") -> float:
        """Estimate travel time based on distance and mode."""
        mode_speeds = {"walking": 5.0, "driving": 30.0, "transit": 20.0}

        speed = mode_speeds.get(mode, 5.0)
        return (distance_km / speed) * 60  # Convert to minutes
