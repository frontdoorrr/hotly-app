"""Health check endpoints."""
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.exceptions import DatabaseError

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
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/health/detailed")  
def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check with service status."""
    services = {"database": "ok"}
    
    try:
        # Test database connection
        db.execute("SELECT 1")
    except Exception:
        services["database"] = "error"
    
    return {
        "status": "ok" if all(s == "ok" for s in services.values()) else "error",
        "services": services
    }