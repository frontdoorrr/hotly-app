"""User profile, preferences, and settings management endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user_data import AuthenticatedUser
from app.crud.user import crud_user, crud_user_preference, crud_user_settings
from app.schemas.user import (
    AccountDeleteRequest,
    AccountRestoreRequest,
    DataExportResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.services.image_upload_service import (
    ImageUploadError,
    image_upload_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_user_uuid(current_user: AuthenticatedUser) -> UUID:
    """Extract and convert user ID to UUID."""
    return current_user.id


# Profile endpoints
@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Get current user's profile."""
    firebase_uid = current_user.firebase_uid

    # Get or create user in database
    user = crud_user.get_or_create_by_firebase_uid(
        db,
        firebase_uid=firebase_uid,
        email=current_user.email or "",
        full_name=current_user.display_name,
        hashed_password="",  # Firebase handles auth
    )

    return UserProfileResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        full_name=user.full_name,
        nickname=user.nickname,
        profile_image_url=user.profile_image_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Update current user's profile."""
    firebase_uid = current_user.firebase_uid

    # Get user from database
    user = crud_user.get_by_firebase_uid(db, firebase_uid=firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if soft deleted
    if user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update profile
    user = crud_user.update_profile(db, db_obj=user, profile_data=profile_data)
    logger.info(f"Updated profile for user {firebase_uid}")

    return UserProfileResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        full_name=user.full_name,
        nickname=user.nickname,
        profile_image_url=user.profile_image_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/me/profile/image")
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, str]:
    """Upload profile image."""
    firebase_uid = current_user.firebase_uid

    # Get user from database
    user = crud_user.get_by_firebase_uid(db, firebase_uid=firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        # Delete old image if exists
        if user.profile_image_url:
            image_upload_service.delete_profile_image(user.profile_image_url)

        # Upload new image
        file_path = await image_upload_service.upload_profile_image(firebase_uid, file)

        # Update user's profile_image_url
        user = crud_user.update_profile_image(db, db_obj=user, image_url=file_path)
        logger.info(f"Uploaded profile image for user {firebase_uid}: {file_path}")

        return {"profile_image_url": file_path}
    except ImageUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Preferences endpoints
@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserPreferencesResponse:
    """Get current user's preferences."""
    user_id = _get_user_uuid(current_user)

    # Get or create preferences
    prefs = crud_user_preference.get_or_create(db, user_id=user_id)

    return UserPreferencesResponse(
        food_preferences=prefs.food_preferences or {"preset": [], "custom": []},
        atmosphere_preferences=prefs.atmosphere_preferences or {"preset": [], "custom": []},
        budget_level=prefs.budget_level,
        max_travel_distance_km=prefs.max_travel_distance_km,
        categories=prefs.categories or [],
    )


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserPreferencesResponse:
    """Update current user's preferences."""
    user_id = _get_user_uuid(current_user)

    # Get or create preferences
    prefs = crud_user_preference.get_by_user_id(db, user_id=user_id)

    if prefs:
        prefs = crud_user_preference.update(db, db_obj=prefs, obj_in=preferences_data)
    else:
        prefs = crud_user_preference.create(db, user_id=user_id, obj_in=preferences_data)

    logger.info(f"Updated preferences for user {user_id}")

    return UserPreferencesResponse(
        food_preferences=prefs.food_preferences or {"preset": [], "custom": []},
        atmosphere_preferences=prefs.atmosphere_preferences or {"preset": [], "custom": []},
        budget_level=prefs.budget_level,
        max_travel_distance_km=prefs.max_travel_distance_km,
        categories=prefs.categories or [],
    )


# Settings endpoints
@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_my_settings(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserSettingsResponse:
    """Get current user's settings."""
    user_id = _get_user_uuid(current_user)

    # Get or create settings
    settings = crud_user_settings.get_or_create(db, user_id=user_id)

    return UserSettingsResponse(
        push_enabled=settings.push_enabled,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        marketing_notifications=settings.marketing_notifications,
        recommendation_notifications=settings.recommendation_notifications,
        social_notifications=settings.social_notifications,
        profile_visibility=settings.profile_visibility,
        activity_visibility=settings.activity_visibility,
        show_saved_places=settings.show_saved_places,
        allow_friend_requests=settings.allow_friend_requests,
        language=settings.language,
        theme=settings.theme,
    )


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_my_settings(
    settings_data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserSettingsResponse:
    """Update current user's settings."""
    user_id = _get_user_uuid(current_user)

    # Get or create settings
    settings = crud_user_settings.get_by_user_id(db, user_id=user_id)

    if settings:
        settings = crud_user_settings.update(db, db_obj=settings, obj_in=settings_data)
    else:
        settings = crud_user_settings.create(db, user_id=user_id, obj_in=settings_data)

    logger.info(f"Updated settings for user {user_id}")

    return UserSettingsResponse(
        push_enabled=settings.push_enabled,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        marketing_notifications=settings.marketing_notifications,
        recommendation_notifications=settings.recommendation_notifications,
        social_notifications=settings.social_notifications,
        profile_visibility=settings.profile_visibility,
        activity_visibility=settings.activity_visibility,
        show_saved_places=settings.show_saved_places,
        allow_friend_requests=settings.allow_friend_requests,
        language=settings.language,
        theme=settings.theme,
    )


# Account management endpoints
@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    request: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Soft delete user account.

    Account can be restored within 30 days.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm account deletion",
        )

    firebase_uid = current_user.firebase_uid

    # Get user from database
    user = crud_user.get_by_firebase_uid(db, firebase_uid=firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Soft delete
    user = crud_user.soft_delete(db, db_obj=user)
    logger.info(f"Soft deleted account for user {firebase_uid}, reason: {request.reason}")

    return {
        "message": "Account scheduled for deletion",
        "deleted_at": user.deleted_at.isoformat(),
        "restore_deadline": (user.deleted_at + timedelta(days=30)).isoformat(),
    }


@router.post("/me/restore", status_code=status.HTTP_200_OK)
async def restore_my_account(
    request: AccountRestoreRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Restore soft-deleted account.

    Only works within 30 days of deletion.
    """
    firebase_uid = current_user.firebase_uid

    # Get user (including deleted)
    user = crud_user.get_by_firebase_uid(db, firebase_uid=firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not deleted",
        )

    # Check if within 30 days
    if datetime.utcnow() > user.deleted_at + timedelta(days=30):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restore period has expired (30 days)",
        )

    # Restore account
    user = crud_user.restore(db, db_obj=user)
    logger.info(f"Restored account for user {firebase_uid}")

    return {"message": "Account restored successfully"}


@router.get("/me/export", response_model=DataExportResponse)
async def export_my_data(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DataExportResponse:
    """
    Export all user data (GDPR compliance).

    Returns profile, preferences, and settings in a single response.
    """
    firebase_uid = current_user.firebase_uid
    user_id = _get_user_uuid(current_user)

    # Get user
    user = crud_user.get_by_firebase_uid(db, firebase_uid=firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get preferences
    prefs = crud_user_preference.get_by_user_id(db, user_id=user_id)

    # Get settings
    settings = crud_user_settings.get_by_user_id(db, user_id=user_id)

    logger.info(f"Exported data for user {firebase_uid}")

    return DataExportResponse(
        profile={
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "full_name": user.full_name,
            "nickname": user.nickname,
            "bio": user.bio,
            "profile_image_url": user.profile_image_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        preferences={
            "food_preferences": prefs.food_preferences if prefs else None,
            "atmosphere_preferences": prefs.atmosphere_preferences if prefs else None,
            "budget_level": prefs.budget_level if prefs else "medium",
            "categories": prefs.categories if prefs else [],
        },
        settings={
            "push_enabled": settings.push_enabled if settings else True,
            "email_enabled": settings.email_enabled if settings else True,
            "profile_visibility": settings.profile_visibility if settings else "public",
            "language": settings.language if settings else "ko",
            "theme": settings.theme if settings else "system",
        },
        exported_at=datetime.utcnow(),
    )
