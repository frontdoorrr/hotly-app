"""API v1 router."""
from fastapi import APIRouter

from app.api.v1.endpoints import analyze

api_router = APIRouter()
api_router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
