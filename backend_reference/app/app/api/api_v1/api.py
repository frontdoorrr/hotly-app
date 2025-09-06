from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    courses,
    items,
    location,
    login,
    map,
    onboarding,
    places,
    preference_setup,
    preferences,
    tags,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(
    preferences.router, prefix="/preferences", tags=["preferences"]
)
api_router.include_router(location.router, prefix="/location", tags=["location"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(
    preference_setup.router, prefix="/preference-setup", tags=["preference_setup"]
)
