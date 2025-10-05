"""
Map visualization and Kakao Map API endpoints.

Provides geocoding, place search, and route visualization for map features.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.place import place as place_crud
from app.db.session import get_db
from app.schemas.map import (
    AddressSearchResult,
    CoordinateToAddressResult,
    PlaceSearchResult,
)
from app.schemas.place import PlaceResponse
from app.services.maps.kakao_map_service import KakaoMapService, KakaoMapServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user ID for MVP (will be replaced with auth)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/geocode", response_model=AddressSearchResult)
async def geocode_address(address: str):
    """
    Convert address to coordinates (geocoding).

    - **address**: Korean address string (e.g., "서울특별시 강남구 테헤란로 123")

    Returns latitude and longitude for the given address.
    """
    try:
        service = KakaoMapService()
        result = service.address_to_coordinate(address)

        return AddressSearchResult(
            address=address,
            latitude=result["latitude"],
            longitude=result["longitude"],
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KakaoMapServiceError as e:
        logger.error(f"Kakao Map API error: {e}")
        raise HTTPException(status_code=503, detail="Map service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reverse-geocode", response_model=CoordinateToAddressResult)
async def reverse_geocode(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Convert coordinates to address (reverse geocoding).

    - **latitude**: Latitude (-90 to 90)
    - **longitude**: Longitude (-180 to 180)

    Returns address information for the given coordinates.
    """
    try:
        service = KakaoMapService()
        result = service.coordinate_to_address(latitude, longitude)

        return CoordinateToAddressResult(
            latitude=latitude,
            longitude=longitude,
            road_address=result.get("road_address"),
            jibun_address=result.get("jibun_address"),
        )

    except KakaoMapServiceError as e:
        logger.error(f"Kakao Map API error: {e}")
        raise HTTPException(status_code=503, detail="Map service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in reverse geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=List[PlaceSearchResult])
async def search_places(
    query: str = Query(..., min_length=1, description="Search keyword"),
    latitude: float = Query(
        None, ge=-90, le=90, description="Center latitude for location bias"
    ),
    longitude: float = Query(
        None, ge=-180, le=180, description="Center longitude for location bias"
    ),
    radius_km: float = Query(
        None, gt=0, le=20, description="Search radius in kilometers (max 20km)"
    ),
    limit: int = Query(15, ge=1, le=45, description="Maximum number of results"),
):
    """
    Search places by keyword with optional location bias.

    - **query**: Search keyword (e.g., "강남역 카페")
    - **latitude**: Optional center point latitude
    - **longitude**: Optional center point longitude
    - **radius_km**: Optional search radius (max 20km)
    - **limit**: Maximum results (1-45, default 15)

    Returns list of places matching the search criteria.
    """
    try:
        service = KakaoMapService()
        results = service.search_places_by_keyword(
            keyword=query,
            center_latitude=latitude,
            center_longitude=longitude,
            radius_km=radius_km,
            limit=limit,
        )

        # Convert to schema format
        return [
            PlaceSearchResult(
                place_id=f"kakao_{i}",  # Temporary ID generation
                place_name=place["place_name"],
                address=place["address"],
                latitude=place["latitude"],
                longitude=place["longitude"],
                distance=place.get("distance"),
            )
            for i, place in enumerate(results)
        ]

    except KakaoMapServiceError as e:
        logger.error(f"Kakao Map API error: {e}")
        raise HTTPException(status_code=503, detail="Map service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in place search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/places", response_model=List[PlaceResponse])
async def get_places_in_bounds(
    *,
    db: Session = Depends(get_db),
    sw_lat: float = Query(..., ge=-90, le=90, description="Southwest corner latitude"),
    sw_lng: float = Query(
        ..., ge=-180, le=180, description="Southwest corner longitude"
    ),
    ne_lat: float = Query(..., ge=-90, le=90, description="Northeast corner latitude"),
    ne_lng: float = Query(
        ..., ge=-180, le=180, description="Northeast corner longitude"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
) -> List[PlaceResponse]:
    """
    Get user's saved places within map bounds for marker display.

    This endpoint is optimized for map visualization - returns places
    within the visible map area (bounding box).

    - **sw_lat, sw_lng**: Southwest corner of map bounds
    - **ne_lat, ne_lng**: Northeast corner of map bounds
    - **category**: Optional category filter
    - **limit**: Maximum results (default 100, max 500)

    Returns list of places with coordinates for map markers.
    """
    try:
        places = place_crud.get_places_in_bounds(
            db,
            user_id=UUID(TEMP_USER_ID),
            sw_lat=sw_lat,
            sw_lng=sw_lng,
            ne_lat=ne_lat,
            ne_lng=ne_lng,
            limit=limit,
            category=category,
        )

        return [PlaceResponse.from_orm(place) for place in places]

    except Exception as e:
        logger.error(f"Failed to get places in bounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve places for map")
