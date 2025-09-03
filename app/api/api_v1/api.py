"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import ai, content, link_analysis, places

api_router = APIRouter()
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(link_analysis.router, prefix="/links", tags=["link-analysis"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
