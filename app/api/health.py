"""Health check endpoints for Docker and Kubernetes readiness probes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.monitoring.cache_manager import CacheManager

router = APIRouter()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint for Docker HEALTHCHECK.

    Returns 200 OK if the application is running.
    """
    return {"status": "ok"}


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with service status.

    Checks database connectivity.
    """
    services = {"database": "ok"}

    try:
        # Test database connection
        db.execute("SELECT 1")
    except Exception:
        services["database"] = "error"

    return {
        "status": "ok" if all(s == "ok" for s in services.values()) else "error",
        "services": services,
    }


@router.get("/health/ready")
def readiness_check(
    db: Session = Depends(get_db), response: Response = None
) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes readiness probe.

    Checks all critical services (database, redis) and returns 503
    if any service is not ready. Kubernetes uses this to determine
    if the pod should receive traffic.

    Returns:
        - 200: All services ready, pod can receive traffic
        - 503: One or more services not ready, remove from load balancer
    """
    services = {}
    all_ready = True

    # Check database connection
    try:
        db.execute("SELECT 1")
        services["database"] = "ok"
    except Exception as e:
        services["database"] = f"error: {str(e)}"
        all_ready = False

    # Check Redis connection
    try:
        cache_manager = CacheManager()
        # Test Redis connection with a simple ping
        if cache_manager._redis:
            cache_manager._redis.ping()
            services["redis"] = "ok"
        else:
            services["redis"] = "error: Redis not initialized"
            all_ready = False
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
        all_ready = False

    # Set HTTP status code based on readiness
    if not all_ready and response:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"ready": all_ready, "services": services}
