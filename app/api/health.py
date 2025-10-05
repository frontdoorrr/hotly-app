"""Health check endpoints for Docker and Kubernetes readiness probes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

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


# TODO(human): Implement /health/ready endpoint for Kubernetes readiness probe
# This should check all critical services (database, redis, etc.)
# and return 503 if any service is not ready
