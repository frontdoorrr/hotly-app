"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.api_v1.endpoints import content, ai

api_router = APIRouter()
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])