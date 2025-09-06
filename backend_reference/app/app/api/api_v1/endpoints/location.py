"""Real-time location and routing API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.location_service import GoogleMapsService, LocationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.post("/route-info", response_model=dict)
async def calculate_route_info(
    *,
    db: Session = Depends(get_db),
    waypoints: List[dict],
    travel_mode: str = Query(
        "driving", description="Travel mode: driving, walking, transit"
    ),
) -> dict:
    """
    Calculate route information for multiple waypoints.

    - **waypoints**: List of waypoint coordinates
    - **travel_mode**: Transportation mode

    Returns total distance, duration, and waypoint-by-waypoint breakdown.
    """
    try:
        if len(waypoints) < 2:
            raise HTTPException(
                status_code=422, detail="Route must have at least 2 waypoints"
            )

        # Validate waypoint structure
        for i, waypoint in enumerate(waypoints):
            if "latitude" not in waypoint or "longitude" not in waypoint:
                raise HTTPException(
                    status_code=422,
                    detail=f"Waypoint {i+1} missing latitude or longitude",
                )

        location_service = LocationService(db)
        route_info = await location_service.calculate_route_info(waypoints, travel_mode)

        logger.info(f"Route calculated with {len(waypoints)} waypoints")
        return route_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate route info: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate route")


@router.get("/directions", response_model=dict)
async def get_directions(
    *,
    origin_lat: float = Query(..., ge=-90, le=90, description="Origin latitude"),
    origin_lng: float = Query(..., ge=-180, le=180, description="Origin longitude"),
    dest_lat: float = Query(..., ge=-90, le=90, description="Destination latitude"),
    dest_lng: float = Query(..., ge=-180, le=180, description="Destination longitude"),
    mode: str = Query("driving", description="Travel mode"),
) -> dict:
    """
    Get directions between two points using Google Maps.

    - **origin_lat/lng**: Starting coordinates
    - **dest_lat/lng**: Destination coordinates
    - **mode**: Travel mode (driving, walking, transit)

    Returns Google Maps directions with route details.
    """
    try:
        google_service = GoogleMapsService()
        directions = await google_service.get_directions(
            origin_lat, origin_lng, dest_lat, dest_lng, mode
        )

        logger.info(f"Directions calculated for {mode} mode")
        return directions

    except Exception as e:
        logger.error(f"Failed to get directions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get directions")


@router.post("/update", response_model=dict)
async def update_user_location(
    *,
    db: Session = Depends(get_db),
    latitude: float,
    longitude: float,
    accuracy_meters: int = Query(
        10, ge=1, le=1000, description="GPS accuracy in meters"
    ),
    timestamp: Optional[datetime] = None,
) -> dict:
    """
    Update user's current location.

    - **latitude/longitude**: Current coordinates
    - **accuracy_meters**: GPS accuracy level
    - **timestamp**: Location timestamp

    Returns location update confirmation and nearby place distances.
    """
    try:
        location_service = LocationService(db)

        result = location_service.update_user_location(
            user_id=UUID(TEMP_USER_ID),
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            timestamp=timestamp,
        )

        logger.info(f"Location updated for user {TEMP_USER_ID}")
        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update location: {e}")
        raise HTTPException(status_code=500, detail="Failed to update location")


@router.post("/optimize-route", response_model=dict)
async def optimize_route_order(
    *,
    db: Session = Depends(get_db),
    places: List[dict],
    start_location: dict,
    optimization_goal: str = Query("shortest_time", description="Optimization goal"),
) -> dict:
    """
    Optimize visit order for multiple places.

    - **places**: List of places to visit with coordinates
    - **start_location**: Starting point coordinates
    - **optimization_goal**: Criteria for optimization

    Returns optimized route order using TSP algorithms.
    """
    try:
        if not places:
            raise HTTPException(status_code=422, detail="Places list cannot be empty")

        if "latitude" not in start_location or "longitude" not in start_location:
            raise HTTPException(
                status_code=422,
                detail="Start location must have latitude and longitude",
            )

        location_service = LocationService(db)
        optimized_route = location_service.optimize_route_order(
            places=places,
            start_location=start_location,
            optimization_goal=optimization_goal,
        )

        logger.info(f"Route optimized for {len(places)} places")
        return optimized_route

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize route: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize route")


@router.post("/eta", response_model=dict)
async def calculate_eta(
    *,
    db: Session = Depends(get_db),
    current_location: dict,
    destination: dict,
    travel_mode: str = Query("driving", description="Travel mode"),
) -> dict:
    """
    Calculate estimated time of arrival.

    - **current_location**: Current coordinates
    - **destination**: Destination coordinates
    - **travel_mode**: Transportation mode

    Returns ETA with real-time traffic considerations.
    """
    try:
        # Validate location data
        required_fields = ["latitude", "longitude"]
        for location, name in [
            (current_location, "current_location"),
            (destination, "destination"),
        ]:
            for field in required_fields:
                if field not in location:
                    raise HTTPException(
                        status_code=422, detail=f"{name} missing {field}"
                    )

        location_service = LocationService(db)
        eta_info = location_service.calculate_eta(
            current_location=current_location,
            destination=destination,
            travel_mode=travel_mode,
        )

        logger.info(f"ETA calculated: {eta_info['estimated_duration_minutes']}min")
        return eta_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate ETA: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate ETA")


@router.post("/distance-matrix", response_model=dict)
async def calculate_distance_matrix(
    *, db: Session = Depends(get_db), locations: List[dict]
) -> dict:
    """
    Calculate distance matrix for multiple locations.

    - **locations**: List of coordinate points

    Returns matrix of distances and durations between all locations.
    """
    try:
        if len(locations) < 2:
            raise HTTPException(
                status_code=422, detail="Need at least 2 locations for distance matrix"
            )

        location_service = LocationService(db)
        matrix = []

        # Calculate distances between all pairs
        for i, origin in enumerate(locations):
            row = []
            for j, destination in enumerate(locations):
                if i == j:
                    # Same location
                    row.append({"distance_km": 0.0, "duration_minutes": 0.0})
                else:
                    distance = location_service.distance_calculator.haversine_distance(
                        origin["latitude"],
                        origin["longitude"],
                        destination["latitude"],
                        destination["longitude"],
                    )
                    duration = location_service._estimate_travel_time(
                        distance, "driving"
                    )

                    row.append(
                        {
                            "distance_km": round(distance, 2),
                            "duration_minutes": round(duration, 1),
                        }
                    )
            matrix.append(row)

        result = {
            "distance_matrix": matrix,
            "location_count": len(locations),
            "calculated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Distance matrix calculated for {len(locations)} locations")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate distance matrix: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate distance matrix"
        )


@router.get("/geocode", response_model=dict)
async def geocode_address(
    *, address: str = Query(..., min_length=5, description="Address to geocode")
) -> dict:
    """
    Convert address to coordinates using Google Geocoding.

    - **address**: Address to convert

    Returns latitude/longitude coordinates for the address.
    """
    try:
        google_service = GoogleMapsService()
        geocoding_result = await google_service.geocode_address(address)

        if geocoding_result["status"] != "OK" or not geocoding_result["results"]:
            raise HTTPException(status_code=404, detail="Address not found")

        result = geocoding_result["results"][0]
        location = result["geometry"]["location"]

        response = {
            "latitude": location["lat"],
            "longitude": location["lng"],
            "formatted_address": result["formatted_address"],
            "accuracy": result["geometry"]["location_type"],
        }

        logger.info(f"Geocoded address: {address}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to geocode address: {e}")
        raise HTTPException(status_code=500, detail="Failed to geocode address")


@router.get("/reverse-geocode", response_model=dict)
async def reverse_geocode_coordinates(
    *,
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
) -> dict:
    """
    Convert coordinates to address using Google Reverse Geocoding.

    - **latitude/longitude**: Coordinates to convert

    Returns formatted address for the coordinates.
    """
    try:
        google_service = GoogleMapsService()
        reverse_result = await google_service.reverse_geocode(latitude, longitude)

        if reverse_result["status"] != "OK" or not reverse_result["results"]:
            raise HTTPException(status_code=404, detail="Location not found")

        result = reverse_result["results"][0]

        response = {
            "formatted_address": result["formatted_address"],
            "address_components": result["address_components"],
            "coordinates": {"latitude": latitude, "longitude": longitude},
        }

        logger.info(f"Reverse geocoded: ({latitude}, {longitude})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reverse geocode: {e}")
        raise HTTPException(status_code=500, detail="Failed to reverse geocode")


@router.get("/history", response_model=dict)
async def get_location_history(
    *, hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve")
) -> dict:
    """
    Get user's location history.

    - **hours**: Hours of history to retrieve

    Returns chronological location updates for the user.
    """
    try:
        # Mock location history for development
        # In production, would retrieve from location tracking database

        mock_history = {
            "user_id": TEMP_USER_ID,
            "history_period_hours": hours,
            "location_points": [
                {
                    "latitude": 37.5665,
                    "longitude": 126.9780,
                    "accuracy_meters": 5,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "address": "강남역 근처",
                },
                {
                    "latitude": 37.5660,
                    "longitude": 126.9785,
                    "accuracy_meters": 8,
                    "timestamp": "2024-01-01T12:30:00Z",
                    "address": "강남구 테헤란로",
                },
            ],
            "total_distance_km": 2.5,
            "active_time_minutes": 180,
        }

        logger.info(f"Location history retrieved for {hours} hours")
        return mock_history

    except Exception as e:
        logger.error(f"Failed to get location history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get location history")
