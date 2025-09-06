"""Geographic and spatial data schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class GeoPoint(BaseModel):
    """Geographic coordinate point."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class GeoBoundingBox(BaseModel):
    """Geographic bounding box."""

    min_latitude: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    min_longitude: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_latitude: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    max_longitude: float = Field(..., ge=-180, le=180, description="Maximum longitude")

    @validator("max_latitude")
    def validate_latitude_order(cls, v, values):
        if "min_latitude" in values and v <= values["min_latitude"]:
            raise ValueError("max_latitude must be greater than min_latitude")
        return v

    @validator("max_longitude")
    def validate_longitude_order(cls, v, values):
        if "min_longitude" in values and v <= values["min_longitude"]:
            raise ValueError("max_longitude must be greater than min_longitude")
        return v


class GeoSearchRequest(BaseModel):
    """Request for geographic search operations."""

    center: GeoPoint = Field(..., description="Search center point")
    radius_km: float = Field(
        ..., ge=0.1, le=100, description="Search radius in kilometers"
    )
    category: Optional[str] = Field(None, description="Optional category filter")
    tags: List[str] = Field(default_factory=list, description="Optional tag filters")
    limit: int = Field(50, ge=1, le=200, description="Maximum results")


class GeoSearchResponse(BaseModel):
    """Response for geographic search with distance information."""

    place_id: str = Field(..., description="Place identifier")
    name: str = Field(..., description="Place name")
    category: str = Field(..., description="Place category")
    coordinates: GeoPoint = Field(..., description="Place coordinates")
    distance_km: float = Field(..., description="Distance from search center in km")
    bearing_degrees: Optional[float] = Field(
        None, description="Bearing from center in degrees"
    )


class GeoClusterResponse(BaseModel):
    """Geographic cluster of places."""

    center_latitude: float = Field(..., description="Cluster center latitude")
    center_longitude: float = Field(..., description="Cluster center longitude")
    place_count: int = Field(..., description="Number of places in cluster")
    place_ids: List[str] = Field(..., description="Place IDs in cluster")
    radius_km: float = Field(..., description="Cluster radius")


class RouteSearchRequest(BaseModel):
    """Request for finding places along a route."""

    waypoints: List[GeoPoint] = Field(
        ..., min_items=2, description="Route waypoints (minimum 2 points)"
    )
    buffer_km: float = Field(
        1.0, ge=0.1, le=10, description="Buffer distance from route in km"
    )
    category: Optional[str] = Field(None, description="Optional category filter")
    limit: int = Field(50, ge=1, le=100, description="Maximum results")


class RouteSearchResponse(BaseModel):
    """Response for route-based place search."""

    place_id: str = Field(..., description="Place identifier")
    name: str = Field(..., description="Place name")
    coordinates: GeoPoint = Field(..., description="Place coordinates")
    distance_to_route_km: float = Field(
        ..., description="Distance to nearest route point"
    )
    nearest_waypoint_index: int = Field(..., description="Index of nearest waypoint")


class GeoStatistics(BaseModel):
    """Geographic statistics for user's places."""

    total_places_with_coordinates: int = Field(
        ..., description="Places with valid coordinates"
    )
    geographic_coverage: GeoBoundingBox = Field(..., description="Coverage area")
    center_of_mass: GeoPoint = Field(..., description="Geographic center of all places")
    average_distance_between_places: float = Field(
        ..., description="Average distance in km"
    )
    clusters_found: int = Field(..., description="Number of geographic clusters")
    coverage_area_km2: float = Field(
        ..., description="Total coverage area in square km"
    )


class NearbySearchRequest(BaseModel):
    """Enhanced nearby search request."""

    center: GeoPoint = Field(..., description="Search center")
    radius_km: float = Field(5.0, ge=0.1, le=50, description="Search radius")
    category: Optional[str] = Field(None, description="Category filter")
    tags: List[str] = Field(default_factory=list, description="Tag filters")
    sort_by: str = Field(
        "distance", description="Sort criteria: distance, name, created_at"
    )
    include_distance: bool = Field(True, description="Include distance in response")
    include_bearing: bool = Field(False, description="Include bearing in response")
    limit: int = Field(50, ge=1, le=200, description="Maximum results")


class PlaceWithDistance(BaseModel):
    """Place response with distance information."""

    id: str = Field(..., description="Place ID")
    name: str = Field(..., description="Place name")
    description: Optional[str] = Field(None, description="Place description")
    address: Optional[str] = Field(None, description="Place address")
    category: str = Field(..., description="Place category")
    tags: List[str] = Field(default_factory=list, description="Place tags")
    coordinates: GeoPoint = Field(..., description="Place coordinates")
    distance_km: float = Field(..., description="Distance from search center")
    bearing_degrees: Optional[float] = Field(None, description="Bearing from center")

    class Config:
        orm_mode = True
