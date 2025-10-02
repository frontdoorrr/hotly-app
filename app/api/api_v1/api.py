"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    advanced_filters,
    ai,
    auth,
    autocomplete,
    cdn,
    content,
    courses,
    link_analysis,
    map,
    notifications,
    onboarding,
    performance,
    personalization,
    places,
    preference_setup,
    preferences,
    search,
    search_optimization,
    search_ranking,
    user_data,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
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
api_router.include_router(
    personalization.router, prefix="/personalization", tags=["personalization"]
)
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(
    autocomplete.router, prefix="/autocomplete", tags=["autocomplete"]
)
api_router.include_router(
    advanced_filters.router, prefix="/filters", tags=["advanced-filters"]
)
api_router.include_router(
    search_ranking.router, prefix="/ranking", tags=["search-ranking"]
)
api_router.include_router(
    search_optimization.router,
    prefix="/search-optimization",
    tags=["search-optimization"],
)
api_router.include_router(user_data.router, prefix="/user-data", tags=["user-data"])
api_router.include_router(
    performance.router, prefix="/performance", tags=["performance"]
)
api_router.include_router(cdn.router, prefix="/cdn", tags=["cdn"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
