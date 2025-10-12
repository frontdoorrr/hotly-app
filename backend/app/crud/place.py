"""CRUD operations for Place model."""

from typing import List, Optional, Tuple
from uuid import UUID

from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_GeogFromText
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.place import Place, PlaceCategory, PlaceStatus
from app.schemas.place import PlaceCreate, PlaceListRequest, PlaceUpdate


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    """CRUD operations for Place model with geographical support."""

    def create_with_user(
        self, db: Session, *, obj_in: PlaceCreate, user_id: UUID
    ) -> Place:
        """Create place with user association and coordinates."""
        obj_in_data = obj_in.dict()

        # Extract coordinates
        latitude = obj_in_data.pop("latitude", None)
        longitude = obj_in_data.pop("longitude", None)

        # Create place instance
        db_obj = Place(**obj_in_data, user_id=user_id)

        # Set coordinates if provided
        if latitude is not None and longitude is not None:
            db_obj.set_coordinates(latitude, longitude)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_user(
        self, db: Session, *, user_id: UUID, place_id: UUID
    ) -> Optional[Place]:
        """Get place by ID and user ownership."""
        return (
            db.query(Place)
            .filter(Place.id == place_id, Place.user_id == user_id)
            .first()
        )

    def get_multi_by_user(
        self, db: Session, *, user_id: UUID, limit: int = 100, skip: int = 0
    ) -> List[Place]:
        """Get multiple places by user with pagination."""
        return (
            db.query(Place)
            .filter(Place.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_list_with_filters(
        self, db: Session, *, request: PlaceListRequest, user_id: UUID
    ) -> Tuple[List[Place], int]:
        """Get paginated place list with filters and geographical search."""
        query = db.query(Place).filter(Place.user_id == user_id)

        # Apply filters
        if request.status:
            query = query.filter(Place.status == request.status)

        if request.category:
            query = query.filter(Place.category == request.category)

        if request.tags:
            query = query.filter(Place.tags.overlap(request.tags))

        # Geographical search
        if (
            request.latitude is not None
            and request.longitude is not None
            and request.radius_km is not None
        ):
            # Convert km to meters for PostGIS
            radius_m = request.radius_km * 1000

            # Create point from coordinates
            center_point = ST_GeogFromText(
                f"POINT({request.longitude} {request.latitude})"
            )

            # Filter by distance
            query = query.filter(ST_DWithin(Place.coordinates, center_point, radius_m))

            # Order by distance if geographical search
            query = query.order_by(ST_Distance(Place.coordinates, center_point))

        # Full-text search
        if request.search_query:
            search_query = request.search_query.strip()
            if search_query:
                # PostgreSQL full-text search
                ts_query = func.plainto_tsquery("simple", search_query)
                ts_vector = func.to_tsvector(
                    "simple",
                    func.coalesce(Place.name, "")
                    + " "
                    + func.coalesce(Place.address, ""),
                )

                query = query.filter(ts_vector.op("@@")(ts_query))

                # Order by relevance
                query = query.order_by(func.ts_rank(ts_vector, ts_query).desc())

        # Default sorting (if no geographical or text search)
        if not request.search_query and not (
            request.latitude and request.longitude and request.radius_km
        ):
            if request.sort_by == "created_at":
                if request.sort_order == "desc":
                    query = query.order_by(Place.created_at.desc())
                else:
                    query = query.order_by(Place.created_at.asc())
            elif request.sort_by == "name":
                if request.sort_order == "desc":
                    query = query.order_by(Place.name.desc())
                else:
                    query = query.order_by(Place.name.asc())
            elif request.sort_by == "recommendation_score":
                query = query.order_by(
                    Place.recommendation_score.desc().nulls_last()
                    if request.sort_order == "desc"
                    else Place.recommendation_score.asc().nulls_last()
                )

        # Count total before pagination
        total = query.count()

        # Apply pagination
        offset = (request.page - 1) * request.page_size
        places = query.offset(offset).limit(request.page_size).all()

        return places, total

    def get_nearby_places(
        self,
        db: Session,
        *,
        user_id: UUID,
        latitude: float,
        longitude: float,
        radius_km: float,
        limit: int = 50,
    ) -> List[Place]:
        """Get places within specified radius, ordered by distance."""
        radius_m = radius_km * 1000

        center_point = ST_GeogFromText(f"POINT({longitude} {latitude})")

        return (
            db.query(Place)
            .filter(
                Place.user_id == user_id,
                Place.status == PlaceStatus.ACTIVE,
                ST_DWithin(Place.coordinates, center_point, radius_m),
            )
            .order_by(ST_Distance(Place.coordinates, center_point))
            .limit(limit)
            .all()
        )

    def get_places_in_bounds(
        self,
        db: Session,
        *,
        user_id: UUID,
        sw_lat: float,
        sw_lng: float,
        ne_lat: float,
        ne_lng: float,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> List[Place]:
        """Get places within map bounds (bounding box)."""
        from geoalchemy2.functions import ST_MakeEnvelope

        # Create bounding box polygon
        # ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid)
        bbox = ST_MakeEnvelope(sw_lng, sw_lat, ne_lng, ne_lat, 4326)

        query = db.query(Place).filter(
            Place.user_id == user_id,
            Place.status == PlaceStatus.ACTIVE,
            Place.coordinates.ST_Within(bbox),
        )

        if category:
            query = query.filter(Place.category == category)

        return query.limit(limit).all()

    def search_by_text(
        self,
        db: Session,
        *,
        user_id: UUID,
        query: str,
        category: Optional[PlaceCategory] = None,
        limit: int = 20,
    ) -> List[Place]:
        """Full-text search for places with optional category filter."""
        db_query = db.query(Place).filter(Place.user_id == user_id)

        if category:
            db_query = db_query.filter(Place.category == category)

        # Full-text search
        ts_query = func.plainto_tsquery("simple", query)
        ts_vector = func.to_tsvector(
            "simple",
            func.coalesce(Place.name, "") + " " + func.coalesce(Place.address, ""),
        )

        return (
            db_query.filter(ts_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(ts_vector, ts_query).desc())
            .limit(limit)
            .all()
        )

    def get_by_source_hash(
        self, db: Session, *, user_id: UUID, source_content_hash: str
    ) -> Optional[Place]:
        """Get place by source content hash for duplicate detection."""
        return (
            db.query(Place)
            .filter(
                Place.user_id == user_id,
                Place.source_content_hash == source_content_hash,
            )
            .first()
        )

    def get_user_statistics(self, db: Session, *, user_id: UUID) -> dict:
        """Get place statistics for a user."""
        # Total places
        total = db.query(Place).filter(Place.user_id == user_id).count()

        # Places by category
        category_stats = (
            db.query(Place.category, func.count(Place.id))
            .filter(Place.user_id == user_id)
            .group_by(Place.category)
            .all()
        )

        # Places by status
        status_stats = (
            db.query(Place.status, func.count(Place.id))
            .filter(Place.user_id == user_id)
            .group_by(Place.status)
            .all()
        )

        # Average AI confidence
        avg_confidence = (
            db.query(func.avg(Place.ai_confidence))
            .filter(Place.user_id == user_id, Place.ai_confidence.isnot(None))
            .scalar()
        )

        # Verified percentage
        verified_count = (
            db.query(Place)
            .filter(Place.user_id == user_id, Place.is_verified.is_(True))
            .count()
        )

        verified_percentage = (verified_count / total * 100) if total > 0 else 0.0

        return {
            "total_places": total,
            "places_by_category": dict(category_stats),
            "places_by_status": dict(status_stats),
            "average_confidence": float(avg_confidence) if avg_confidence else 0.0,
            "verified_percentage": verified_percentage,
        }

    def update_with_coordinates(
        self, db: Session, *, db_obj: Place, obj_in: PlaceUpdate
    ) -> Place:
        """Update place including coordinates if provided."""
        obj_data = obj_in.dict(exclude_unset=True)

        # Extract coordinates
        latitude = obj_data.pop("latitude", None)
        longitude = obj_data.pop("longitude", None)

        # Update regular fields
        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        # Update coordinates if both provided
        if latitude is not None and longitude is not None:
            db_obj.set_coordinates(latitude, longitude)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, *, place_id: UUID, user_id: UUID) -> bool:
        """Soft delete place by setting status to inactive."""
        db_obj = self.get_by_user(db, user_id=user_id, place_id=place_id)
        if db_obj:
            db_obj.status = PlaceStatus.INACTIVE
            db.commit()
            return True
        return False


# Create instance
place = CRUDPlace(Place)
