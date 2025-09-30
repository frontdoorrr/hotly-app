"""
Schemas for map visualization and Kakao Map API integration.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CoordinatePoint(BaseModel):
    """Geographic coordinate point."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude (-180 to 180)"
    )


class AddressSearchResult(BaseModel):
    """Result from address to coordinate conversion (geocoding)."""

    address: str = Field(..., description="Original address query")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    road_address: Optional[str] = Field(None, description="Road-based address (도로명주소)")
    jibun_address: Optional[str] = Field(None, description="Lot-based address (지번주소)")
    building_name: Optional[str] = Field(None, description="Building name")


class CoordinateToAddressResult(BaseModel):
    """Result from coordinate to address conversion (reverse geocoding)."""

    latitude: float
    longitude: float
    road_address: Optional[str] = Field(None, description="Road-based address")
    jibun_address: Optional[str] = Field(None, description="Lot-based address")
    region_1depth: Optional[str] = Field(None, description="시/도")
    region_2depth: Optional[str] = Field(None, description="구/군")
    region_3depth: Optional[str] = Field(None, description="동/읍/면")


class PlaceSearchResult(BaseModel):
    """Place search result from Kakao Map."""

    place_id: str = Field(..., description="Kakao place ID")
    place_name: str = Field(..., description="Place name")
    category_name: Optional[str] = Field(None, description="Category (e.g., 음식점 > 카페)")
    address: str = Field(..., description="Address")
    road_address: Optional[str] = Field(None, description="Road address")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    phone: Optional[str] = Field(None, description="Phone number")
    place_url: Optional[str] = Field(None, description="Kakao Map URL")
    distance: Optional[float] = Field(
        None, description="Distance from search center (meters)"
    )


class MarkerCluster(BaseModel):
    """Clustered map marker."""

    cluster_id: str = Field(..., description="Unique cluster identifier")
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)
    place_count: int = Field(..., ge=1, description="Number of places in cluster")
    place_ids: List[str] = Field(..., description="IDs of places in cluster")
    bounds: Optional[dict] = Field(
        None, description="Bounding box {north, south, east, west}"
    )


class RoutePolyline(BaseModel):
    """Route visualization data."""

    route_id: str = Field(..., description="Route identifier")
    coordinates: List[CoordinatePoint] = Field(
        ..., description="Ordered list of coordinates forming the route"
    )
    total_distance_km: float = Field(..., ge=0, description="Total route distance")
    total_duration_minutes: int = Field(..., ge=0, description="Estimated travel time")
    waypoints: List[dict] = Field(
        ..., description="Waypoint markers (place names and positions)"
    )


class MapBounds(BaseModel):
    """Map viewport bounds."""

    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)


class MarkerClusterRequest(BaseModel):
    """Request for marker clustering."""

    place_ids: List[str] = Field(..., min_items=1, max_items=1000)
    zoom_level: int = Field(
        ..., ge=1, le=21, description="Map zoom level (1=world, 21=building)"
    )
    bounds: MapBounds = Field(..., description="Current map viewport")


class RouteVisualizationRequest(BaseModel):
    """Request for route visualization data."""

    course_id: str = Field(..., description="Course ID from recommendation")
    include_waypoints: bool = Field(True, description="Include waypoint markers")
    simplify: bool = Field(
        False, description="Simplify polyline for performance (Douglas-Peucker)"
    )
