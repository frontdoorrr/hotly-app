"""
Schemas for course recommendation API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CourseRequest(BaseModel):
    """Request for course recommendation."""

    place_ids: List[str] = Field(
        ...,
        min_length=3,
        max_length=6,
        description="List of 3-6 place IDs to include in course",
    )
    start_latitude: Optional[float] = Field(None, description="Starting latitude")
    start_longitude: Optional[float] = Field(None, description="Starting longitude")
    transport_mode: str = Field(
        "walking", description="Transport mode: walking, transit, driving"
    )
    start_time: Optional[str] = Field(None, description="Preferred start time (HH:MM)")


class PlaceInCourseResponse(BaseModel):
    """Place with travel information in course."""

    place_id: str
    place_name: str
    category: str
    address: str
    latitude: float
    longitude: float
    position: int = Field(..., description="Position in course (0-indexed)")
    travel_distance_km: Optional[float] = Field(
        None, description="Distance from previous place"
    )
    travel_duration_minutes: Optional[int] = Field(
        None, description="Travel time from previous place"
    )
    estimated_duration_minutes: int = Field(
        60, description="Estimated stay duration at this place"
    )
    arrival_time: Optional[str] = Field(None, description="Estimated arrival time")

    class Config:
        from_attributes = True


class CourseRecommendationResponse(BaseModel):
    """Course recommendation response."""

    course_id: str
    user_id: str
    places: List[PlaceInCourseResponse]
    total_distance_km: float
    total_duration_minutes: int
    optimization_score: float = Field(
        ..., ge=0.0, le=1.0, description="Optimization quality score (0-1)"
    )
    transport_mode: str
    created_at: datetime

    class Config:
        from_attributes = True


class CourseSaveRequest(BaseModel):
    """Request to save a course."""

    course_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CourseSavedResponse(BaseModel):
    """Saved course response."""

    course_id: str
    course_name: str
    is_saved: bool = True
    saved_at: datetime

    class Config:
        from_attributes = True
