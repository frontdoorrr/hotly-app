"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.api_v1.endpoints import content

api_router = APIRouter()
api_router.include_router(content.router, prefix="/content", tags=["content"])