"""
Hotly App FastAPI application.

Main application entry point following backend_reference patterns.
"""

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.api.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-based hot place/dating course/restaurant archiving app",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    def read_root() -> Dict[str, str]:
        """Root endpoint."""
        return {"message": "Hotly App API", "version": "0.1.0"}

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        try:
            # Initialize Elasticsearch connection
            from app.db.elasticsearch import init_elasticsearch

            await init_elasticsearch()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize Elasticsearch: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        try:
            # Close Elasticsearch connection
            from app.db.elasticsearch import close_elasticsearch

            await close_elasticsearch()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to close Elasticsearch connection: {e}")

    # Include health check routes
    app.include_router(health_router)

    # Include API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
