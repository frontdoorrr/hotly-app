"""Kakao Map SDK integration and visualization API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.map_service import (
    KakaoMapAPIService,
    MapService,
    MapVisualizationService,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.post("/initialize", response_model=dict)
async def initialize_map(
    *,
    db: Session = Depends(get_db),
    center: dict,
    zoom: int = Query(15, ge=1, le=20, description="Map zoom level"),
    map_type: str = Query("normal", description="Map display type"),
) -> dict:
    """
    Initialize Kakao Map with specified configuration.

    - **center**: Map center coordinates (latitude, longitude)
    - **zoom**: Initial zoom level (1-20)
    - **map_type**: Map display type (normal, satellite, hybrid)

    Returns Kakao Map initialization configuration.
    """
    try:
        # Validate center coordinates
        required_fields = ["latitude", "longitude"]
        for field in required_fields:
            if field not in center:
                raise HTTPException(
                    status_code=422, detail=f"Center coordinates missing {field}"
                )

        map_service = MapService(db)
        map_config = map_service.initialize_map(center, zoom, map_type)

        logger.info(f"Map initialized at zoom {zoom}")
        return map_config

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initialize map: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize map")


@router.post("/markers", response_model=dict)
async def create_map_markers(
    *,
    db: Session = Depends(get_db),
    places: List[dict],
    marker_style: str = Query("default", description="Marker visual style"),
) -> dict:
    """
    Create markers for places on map.

    - **places**: List of places with coordinates and metadata
    - **marker_style**: Visual style for markers

    Returns marker creation result with marker data.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        map_service = MapService(db)
        markers_data = map_service.create_markers(places, marker_style)

        logger.info(f"Created {len(places)} markers")
        return markers_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create markers: {e}")
        raise HTTPException(status_code=500, detail="Failed to create markers")


@router.post("/calculate-bounds", response_model=dict)
async def calculate_map_bounds(*, places: List[dict]) -> dict:
    """
    Calculate optimal map bounds for given places.

    - **places**: List of places with coordinates

    Returns optimal map center, zoom level, and bounds.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        # Validate place coordinates
        for i, place in enumerate(places):
            if "latitude" not in place or "longitude" not in place:
                raise HTTPException(
                    status_code=422, detail=f"Place {i+1} missing latitude or longitude"
                )

        map_service = MapService(db=None)  # No DB needed for bounds calculation
        bounds_data = map_service.calculate_map_bounds(places)

        logger.info(f"Calculated bounds for {len(places)} places")
        return bounds_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate bounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate map bounds")


@router.post("/render-places", response_model=dict)
async def render_places_on_map(
    *, db: Session = Depends(get_db), places: List[dict]
) -> dict:
    """
    Render places on map with performance optimization.

    - **places**: Places to render on map

    Returns rendering result with performance metrics.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        map_service = MapService(db)
        render_data = map_service.render_places_on_map(places)

        logger.info(f"Rendered {len(places)} places on map")
        return render_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render places: {e}")
        raise HTTPException(status_code=500, detail="Failed to render places")


@router.post("/cluster-markers", response_model=dict)
async def cluster_map_markers(
    *,
    db: Session = Depends(get_db),
    places: List[dict],
    cluster_threshold: int = Query(
        100, ge=10, le=1000, description="Clustering distance in meters"
    ),
) -> dict:
    """
    Apply marker clustering for dense place groups.

    - **places**: Places to cluster
    - **cluster_threshold**: Clustering distance threshold in meters

    Returns clustered marker data with individual markers.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        map_service = MapService(db)
        cluster_data = map_service.cluster_markers(places, cluster_threshold)

        logger.info(
            f"Clustered {len(places)} places with {cluster_threshold}m threshold"
        )
        return cluster_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cluster markers: {e}")
        raise HTTPException(status_code=500, detail="Failed to cluster markers")


@router.post("/viewport-places", response_model=dict)
async def load_viewport_places(
    *,
    db: Session = Depends(get_db),
    northeast: dict,
    southwest: dict,
    zoom_level: int = Query(15, ge=1, le=20),
) -> dict:
    """
    Load places within map viewport bounds.

    - **northeast**: Northeast corner coordinates
    - **southwest**: Southwest corner coordinates
    - **zoom_level**: Current map zoom level

    Returns places within viewport bounds.
    """
    try:
        # Validate bounds coordinates
        bounds_coords = [northeast, southwest]
        for i, coords in enumerate(bounds_coords):
            if "latitude" not in coords or "longitude" not in coords:
                corner_name = "northeast" if i == 0 else "southwest"
                raise HTTPException(
                    status_code=422,
                    detail=f"{corner_name} coordinates missing latitude or longitude",
                )

        viewport_bounds = {"northeast": northeast, "southwest": southwest}

        map_service = MapService(db)
        viewport_data = map_service.load_viewport_places(viewport_bounds, zoom_level)

        logger.info(f"Loaded viewport places at zoom {zoom_level}")
        return viewport_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load viewport places: {e}")
        raise HTTPException(status_code=500, detail="Failed to load viewport places")


@router.post("/cached-places", response_model=dict)
async def get_cached_map_places(*, db: Session = Depends(get_db), bounds: dict) -> dict:
    """
    Get map places with caching for performance.

    - **bounds**: Map bounds (northeast, southwest coordinates)

    Returns cached place data for map bounds.
    """
    try:
        # Validate bounds structure
        if "northeast" not in bounds or "southwest" not in bounds:
            raise HTTPException(
                status_code=422,
                detail="Bounds must contain northeast and southwest coordinates",
            )

        ne = bounds["northeast"]
        sw = bounds["southwest"]

        # Create cache key from bounds
        cache_key = f"map_places_{ne['latitude']}_{ne['longitude']}_{sw['latitude']}_{sw['longitude']}"

        map_service = MapService(db)

        # Check cache first
        if cache_key in map_service.map_cache:
            cached_result = map_service.map_cache[cache_key]
            cache_age = (
                datetime.utcnow() - datetime.fromisoformat(cached_result["cached_at"])
            ).seconds

            if cache_age < 3600:  # 1 hour cache
                cached_result["from_cache"] = True
                logger.info("Returning cached map places")
                return cached_result["data"]

        # Load from database
        viewport_data = map_service.load_viewport_places(bounds, 15)  # Default zoom

        # Cache the result
        map_service.map_cache[cache_key] = {
            "data": {**viewport_data, "from_cache": False},
            "cached_at": datetime.utcnow().isoformat(),
        }

        logger.info("Loaded and cached map places")
        return {**viewport_data, "from_cache": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached places: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cached places")


@router.post("/draw-route", response_model=dict)
async def draw_course_route(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    places: List[dict],
    route_style: Optional[dict] = None,
) -> dict:
    """
    Draw route path connecting course places.

    - **course_id**: Course identifier
    - **places**: Ordered list of places in course
    - **route_style**: Visual styling for route line

    Returns route visualization data with polyline.
    """
    try:
        if len(places) < 2:
            raise HTTPException(
                status_code=422, detail="Route requires at least 2 places"
            )

        visualization_service = MapVisualizationService(db)
        route_data = visualization_service.draw_route_path(
            course_id, places, route_style
        )

        logger.info(f"Drew route for course {course_id}")
        return route_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to draw route: {e}")
        raise HTTPException(status_code=500, detail="Failed to draw route")


@router.post("/calculate-route", response_model=dict)
async def calculate_map_route(
    *, db: Session = Depends(get_db), waypoints: List[dict]
) -> dict:
    """
    Calculate route between waypoints for map display.

    - **waypoints**: Route waypoints with coordinates

    Returns route calculation with timing information.
    """
    try:
        if len(waypoints) < 2:
            raise HTTPException(
                status_code=422,
                detail="Route calculation requires at least 2 waypoints",
            )

        # Validate waypoint structure
        for i, waypoint in enumerate(waypoints):
            if "latitude" not in waypoint or "longitude" not in waypoint:
                raise HTTPException(
                    status_code=422,
                    detail=f"Waypoint {i+1} missing latitude or longitude",
                )

        visualization_service = MapVisualizationService(db)

        # Create course data for route calculation
        course_data = {
            "course_id": f"temp_route_{datetime.utcnow().timestamp()}",
            "places": [
                {**waypoint, "visit_order": i + 1, "duration_minutes": 30}
                for i, waypoint in enumerate(waypoints)
            ],
        }

        route_data = visualization_service.draw_route_path(
            course_data["course_id"], course_data["places"]
        )

        logger.info(f"Calculated route for {len(waypoints)} waypoints")
        return route_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate route: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate route")


@router.post("/configure-interactions", response_model=dict)
async def configure_map_interactions(*, interaction_config: dict) -> dict:
    """
    Configure map interaction settings.

    - **interaction_config**: Map interaction configuration options

    Returns applied interaction configuration.
    """
    try:
        visualization_service = MapVisualizationService(db=None)
        config_result = visualization_service.configure_map_interactions(
            interaction_config
        )

        logger.info("Map interactions configured")
        return config_result

    except Exception as e:
        logger.error(f"Failed to configure interactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure interactions")


@router.post("/set-theme", response_model=dict)
async def set_map_theme(*, theme: str) -> dict:
    """
    Change map visual theme.

    - **theme**: Map theme (normal, satellite, hybrid, dark)

    Returns theme configuration result.
    """
    try:
        visualization_service = MapVisualizationService(db=None)
        theme_result = visualization_service.set_map_theme(theme)

        logger.info(f"Map theme set to: {theme}")
        return theme_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set map theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to set map theme")


@router.post("/style-markers", response_model=dict)
async def style_markers_by_category(*, places: List[dict]) -> dict:
    """
    Apply category-based styling to markers.

    - **places**: Places with category information

    Returns styled marker data with category-specific visuals.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        visualization_service = MapVisualizationService(db=None)
        styling_result = visualization_service.style_markers_by_category(places)

        logger.info(f"Applied category styling to {len(places)} markers")
        return styling_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to style markers: {e}")
        raise HTTPException(status_code=500, detail="Failed to style markers")


@router.post("/add-overlays", response_model=dict)
async def add_map_overlays(
    *,
    layers: List[str],
    opacity: float = Query(0.7, ge=0.0, le=1.0, description="Layer opacity"),
) -> dict:
    """
    Add overlay layers to map.

    - **layers**: List of overlay layer types (traffic, transit, bicycle, walking)
    - **opacity**: Layer opacity (0.0 to 1.0)

    Returns overlay configuration result.
    """
    try:
        if not layers:
            raise HTTPException(status_code=422, detail="Layers list cannot be empty")

        visualization_service = MapVisualizationService(db=None)
        overlay_result = visualization_service.add_overlay_layers(layers, opacity)

        logger.info(f"Added overlay layers: {layers}")
        return overlay_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add overlays: {e}")
        raise HTTPException(status_code=500, detail="Failed to add overlays")


@router.post("/validate-api", response_model=dict)
async def validate_kakao_api(*, validate_api_key: bool = True) -> dict:
    """
    Validate Kakao Map API key and configuration.

    - **validate_api_key**: Whether to validate API key

    Returns API validation status and quota information.
    """
    try:
        kakao_service = KakaoMapAPIService()
        validation_result = kakao_service.validate_api_key()

        logger.info("Kakao API validation completed")
        return validation_result

    except Exception as e:
        logger.error(f"Failed to validate API: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate API")


@router.get("/kakao-geocode", response_model=dict)
async def kakao_geocode_address(
    *, address: str = Query(..., min_length=5, description="Address to geocode")
) -> dict:
    """
    Geocode address using Kakao API.

    - **address**: Address to convert to coordinates

    Returns latitude/longitude coordinates for the address.
    """
    try:
        kakao_service = KakaoMapAPIService()
        geocode_result = await kakao_service.geocode_address(address)

        logger.info(f"Geocoded address: {address}")
        return geocode_result

    except Exception as e:
        logger.error(f"Failed to geocode address: {e}")
        raise HTTPException(status_code=500, detail="Failed to geocode address")


@router.post("/kakao-search", response_model=dict)
async def search_kakao_places(
    *,
    query: str,
    center: dict,
    radius: int = Query(1000, ge=100, le=20000, description="Search radius in meters"),
) -> dict:
    """
    Search places using Kakao Local API.

    - **query**: Search query
    - **center**: Search center coordinates
    - **radius**: Search radius in meters

    Returns place search results from Kakao Local.
    """
    try:
        # Validate center coordinates
        if "latitude" not in center or "longitude" not in center:
            raise HTTPException(
                status_code=422,
                detail="Center coordinates missing latitude or longitude",
            )

        kakao_service = KakaoMapAPIService()
        search_results = await kakao_service.search_places(query, center, radius)

        logger.info(f"Kakao place search: {query}")
        return search_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search places: {e}")
        raise HTTPException(status_code=500, detail="Failed to search places")


@router.post("/performance-render", response_model=dict)
async def performance_render_test(
    *, db: Session = Depends(get_db), places: List[dict]
) -> dict:
    """
    Performance test endpoint for rendering large number of places.

    - **places**: Large dataset of places to render

    Returns rendering performance metrics.
    """
    try:
        start_time = datetime.utcnow()

        map_service = MapService(db)
        render_result = map_service.render_places_on_map(places)

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        performance_data = {
            "places_count": len(places),
            "processing_time_seconds": round(processing_time, 3),
            "meets_60fps_requirement": processing_time < 0.017,  # 16.67ms for 60fps
            "meets_1second_requirement": processing_time < 1.0,
            "render_result": render_result,
            "performance_tested_at": end_time.isoformat(),
        }

        logger.info(f"Performance test: {len(places)} places in {processing_time:.3f}s")
        return performance_data

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        raise HTTPException(status_code=500, detail="Performance test failed")


@router.post("/zoom", response_model=dict)
async def handle_map_zoom(
    *,
    action: str,
    current_zoom: int = Query(..., ge=1, le=20),
    target_zoom: int = Query(..., ge=1, le=20),
) -> dict:
    """
    Handle map zoom operations.

    - **action**: Zoom action (zoom_in, zoom_out)
    - **current_zoom**: Current zoom level
    - **target_zoom**: Target zoom level

    Returns zoom operation result.
    """
    try:
        valid_actions = ["zoom_in", "zoom_out"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid action. Must be one of: {valid_actions}",
            )

        zoom_result = {
            "action": action,
            "previous_zoom": current_zoom,
            "new_zoom": target_zoom,
            "zoom_delta": target_zoom - current_zoom,
            "zoom_completed": True,
            "zoom_time": datetime.utcnow().isoformat(),
        }

        logger.info(f"Zoom {action}: {current_zoom} → {target_zoom}")
        return zoom_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle zoom: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle zoom")


@router.post("/large-area", response_model=dict)
async def load_large_area_places(
    *,
    db: Session = Depends(get_db),
    bounds: dict,
    max_places: int = Query(500, ge=100, le=1000),
) -> dict:
    """
    Load places for large geographic area with optimization.

    - **bounds**: Large area bounds
    - **max_places**: Maximum number of places to load

    Returns optimized place data for large area.
    """
    try:
        # Validate bounds
        if "northeast" not in bounds or "southwest" not in bounds:
            raise HTTPException(
                status_code=422,
                detail="Bounds must contain northeast and southwest coordinates",
            )

        ne = bounds["northeast"]
        sw = bounds["southwest"]

        # Query places within large bounds
        places_query = (
            self.db.query(Place)
            .filter(
                Place.latitude.between(sw["latitude"], ne["latitude"]),
                Place.longitude.between(sw["longitude"], ne["longitude"]),
            )
            .limit(max_places)
        )

        places = places_query.all()

        # Convert to map format with clustering if needed
        place_data = []
        for place in places:
            place_data.append(
                {
                    "place_id": str(place.id),
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "name": place.name,
                    "category": place.category,
                }
            )

        # Apply clustering for performance if many places
        if len(place_data) > 100:
            map_service = MapService(db)
            cluster_result = map_service.cluster_markers(
                place_data, 200
            )  # 200m clustering

            large_area_result = {
                "area_bounds": bounds,
                "places_found": len(place_data),
                "max_places_limit": max_places,
                "clustering_applied": True,
                "cluster_data": cluster_result,
                "loaded_at": datetime.utcnow().isoformat(),
            }
        else:
            large_area_result = {
                "area_bounds": bounds,
                "places_found": len(place_data),
                "max_places_limit": max_places,
                "clustering_applied": False,
                "places": place_data,
                "loaded_at": datetime.utcnow().isoformat(),
            }

        logger.info(f"Loaded {len(place_data)} places for large area")
        return large_area_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load large area: {e}")
        raise HTTPException(status_code=500, detail="Failed to load large area")


@router.post("/place-popup", response_model=dict)
async def get_place_popup_data(
    *,
    db: Session = Depends(get_db),
    place_id: str,
    user_id: str = TEMP_USER_ID,
    interaction_type: str = "marker_click",
) -> dict:
    """
    Get place popup data for map marker interaction.

    - **place_id**: Place identifier
    - **user_id**: User identifier for personalization
    - **interaction_type**: Type of interaction

    Returns place details for popup display.
    """
    try:
        # Get place from database
        place = self.db.query(Place).filter(Place.id == place_id).first()

        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        # Mock user location for distance calculation
        user_location = {
            "latitude": 37.5665,
            "longitude": 126.9780,
        }  # Default to Gangnam

        distance_calculator = DistanceCalculator()
        distance_km = distance_calculator.haversine_distance(
            user_location["latitude"],
            user_location["longitude"],
            place.latitude,
            place.longitude,
        )

        popup_data = {
            "place_name": place.name,
            "address": place.address or "주소 정보 없음",
            "category": place.category,
            "rating": 4.2,  # Mock rating
            "distance_from_user": round(distance_km, 2),
            "distance_text": f"{distance_km:.1f}km"
            if distance_km >= 1
            else f"{distance_km*1000:.0f}m",
            "is_saved": False,  # Mock save status
            "interaction_type": interaction_type,
            "popup_generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Generated popup data for place {place_id}")
        return popup_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get popup data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popup data")


@router.post("/search-places", response_model=dict)
async def search_places_on_map(
    *, db: Session = Depends(get_db), query: str, map_bounds: dict
) -> dict:
    """
    Search places within map bounds.

    - **query**: Search query
    - **map_bounds**: Current map bounds for search area

    Returns search results with highlighted map positions.
    """
    try:
        # Validate bounds
        if "northeast" not in map_bounds or "southwest" not in map_bounds:
            raise HTTPException(
                status_code=422,
                detail="Map bounds must contain northeast and southwest coordinates",
            )

        ne = map_bounds["northeast"]
        sw = map_bounds["southwest"]

        # Search places within bounds
        search_query = f"%{query}%"
        places = (
            self.db.query(Place)
            .filter(
                Place.name.ilike(search_query),
                Place.latitude.between(sw["latitude"], ne["latitude"]),
                Place.longitude.between(sw["longitude"], ne["longitude"]),
            )
            .limit(50)
            .all()
        )

        search_results = []
        highlighted_markers = []

        for place in places:
            result_item = {
                "place_id": str(place.id),
                "place_name": place.name,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "category": place.category,
                "address": place.address,
                "relevance_score": 0.8,  # Mock relevance
            }

            search_results.append(result_item)
            highlighted_markers.append(
                {
                    "marker_id": f"highlight_{place.id}",
                    "position": {
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                    },
                    "highlight_style": {"color": "#FF4444", "pulse": True},
                }
            )

        search_response = {
            "search_results": search_results,
            "highlighted_markers": highlighted_markers,
            "total_results": len(search_results),
            "query": query,
            "search_bounds": map_bounds,
            "searched_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Map search '{query}' returned {len(search_results)} results")
        return search_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search places on map: {e}")
        raise HTTPException(status_code=500, detail="Failed to search places")


@router.post("/visualize-course", response_model=dict)
async def visualize_course_on_map(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    places: List[dict],
    visualization_type: str = "route_with_timing",
) -> dict:
    """
    Visualize course on map with timing information.

    - **course_id**: Course identifier
    - **places**: Course places with visit order and duration
    - **visualization_type**: Type of visualization

    Returns course visualization data for map display.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Course places cannot be empty")

        visualization_service = MapVisualizationService(db)
        route_data = visualization_service.draw_route_path(course_id, places)

        # Add timing visualization
        timing_info = []
        cumulative_time = 0

        for place in sorted(
            places, key=lambda p: p.get("visit_order", p.get("order", 0))
        ):
            timing_info.append(
                {
                    "place_name": place.get("name", "Unknown Place"),
                    "arrival_time_minutes": cumulative_time,
                    "visit_duration_minutes": place.get("duration_minutes", 30),
                    "departure_time_minutes": cumulative_time
                    + place.get("duration_minutes", 30),
                }
            )

            cumulative_time += (
                place.get("duration_minutes", 30) + 15
            )  # 15min travel between places

        visualization_result = {
            "course_id": course_id,
            "route_polyline": route_data["polyline_points"],
            "place_markers": route_data.get("place_markers", []),
            "timing_info": timing_info,
            "total_course_duration": cumulative_time,
            "visualization_type": visualization_type,
            "visualized_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Visualized course {course_id} on map")
        return visualization_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to visualize course: {e}")
        raise HTTPException(status_code=500, detail="Failed to visualize course")
