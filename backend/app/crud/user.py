"""CRUD operations for User, UserPreference, and UserSettings."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_settings import UserSettings
from app.schemas.user import (
    UserCreate,
    UserPreferencesUpdate,
    UserProfileUpdate,
    UserSettingsUpdate,
    UserUpdate,
)


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    def get_by_firebase_uid(self, db: Session, *, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID."""
        return db.query(User).filter(User.firebase_uid == firebase_uid).first()

    def get_active_by_firebase_uid(
        self, db: Session, *, firebase_uid: str
    ) -> Optional[User]:
        """Get active (not deleted) user by Firebase UID."""
        return (
            db.query(User)
            .filter(User.firebase_uid == firebase_uid, User.deleted_at.is_(None))
            .first()
        )

    def update_profile(
        self, db: Session, *, db_obj: User, profile_data: UserProfileUpdate
    ) -> User:
        """Update user profile fields."""
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_profile_image(
        self, db: Session, *, db_obj: User, image_url: str
    ) -> User:
        """Update user profile image URL."""
        db_obj.profile_image_url = image_url
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, *, db_obj: User) -> User:
        """Soft delete user by setting deleted_at timestamp."""
        db_obj.deleted_at = datetime.utcnow()
        db_obj.is_active = False
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def restore(self, db: Session, *, db_obj: User) -> User:
        """Restore soft-deleted user."""
        db_obj.deleted_at = None
        db_obj.is_active = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_or_create_by_firebase_uid(
        self, db: Session, *, firebase_uid: str, email: str, **kwargs: Any
    ) -> User:
        """Get existing user or create new one by Firebase UID."""
        user = self.get_by_firebase_uid(db, firebase_uid=firebase_uid)
        if user:
            return user

        user = User(firebase_uid=firebase_uid, email=email, **kwargs)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class CRUDUserPreference:
    """CRUD operations for UserPreference model."""

    def get_by_user_id(
        self, db: Session, *, user_id: UUID
    ) -> Optional[UserPreference]:
        """Get user preferences by user ID."""
        return (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )

    def create(
        self, db: Session, *, user_id: UUID, obj_in: UserPreferencesUpdate
    ) -> UserPreference:
        """Create user preferences."""
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Convert nested models to dict
        if "food_preferences" in obj_data and obj_data["food_preferences"]:
            obj_data["food_preferences"] = (
                obj_data["food_preferences"].model_dump()
                if hasattr(obj_data["food_preferences"], "model_dump")
                else obj_data["food_preferences"]
            )
        if "atmosphere_preferences" in obj_data and obj_data["atmosphere_preferences"]:
            obj_data["atmosphere_preferences"] = (
                obj_data["atmosphere_preferences"].model_dump()
                if hasattr(obj_data["atmosphere_preferences"], "model_dump")
                else obj_data["atmosphere_preferences"]
            )

        db_obj = UserPreference(user_id=user_id, **obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: UserPreference,
        obj_in: UserPreferencesUpdate,
    ) -> UserPreference:
        """Update user preferences."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Convert nested models to dict
        if "food_preferences" in update_data and update_data["food_preferences"]:
            update_data["food_preferences"] = (
                update_data["food_preferences"].model_dump()
                if hasattr(update_data["food_preferences"], "model_dump")
                else update_data["food_preferences"]
            )
        if (
            "atmosphere_preferences" in update_data
            and update_data["atmosphere_preferences"]
        ):
            update_data["atmosphere_preferences"] = (
                update_data["atmosphere_preferences"].model_dump()
                if hasattr(update_data["atmosphere_preferences"], "model_dump")
                else update_data["atmosphere_preferences"]
            )

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_or_create(
        self, db: Session, *, user_id: UUID
    ) -> UserPreference:
        """Get existing preferences or create default ones."""
        prefs = self.get_by_user_id(db, user_id=user_id)
        if prefs:
            return prefs

        prefs = UserPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs


class CRUDUserSettings:
    """CRUD operations for UserSettings model."""

    def get_by_user_id(
        self, db: Session, *, user_id: UUID
    ) -> Optional[UserSettings]:
        """Get user settings by user ID."""
        return (
            db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        )

    def create(
        self, db: Session, *, user_id: UUID, obj_in: UserSettingsUpdate
    ) -> UserSettings:
        """Create user settings."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserSettings(user_id=user_id, **obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: UserSettings,
        obj_in: UserSettingsUpdate,
    ) -> UserSettings:
        """Update user settings."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_or_create(self, db: Session, *, user_id: UUID) -> UserSettings:
        """Get existing settings or create default ones."""
        settings = self.get_by_user_id(db, user_id=user_id)
        if settings:
            return settings

        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings


# Singleton instances
crud_user = CRUDUser(User)
crud_user_preference = CRUDUserPreference()
crud_user_settings = CRUDUserSettings()
