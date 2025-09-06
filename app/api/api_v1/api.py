"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    ai,
    content,
    courses,
    link_analysis,
    onboarding,
    places,
    preference_setup,
    preferences,
)

api_router = APIRouter()
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(link_analysis.router, prefix="/links", tags=["link-analysis"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(
    preference_setup.router, prefix="/preference-setup", tags=["preference-setup"]
)
api_router.include_router(
    preferences.router, prefix="/preferences", tags=["preferences"]
)
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
