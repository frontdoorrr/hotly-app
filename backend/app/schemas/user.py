from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Profile schemas
class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    nickname: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: int
    firebase_uid: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PreferenceTagsSchema(BaseModel):
    """Schema for preference tags."""
    preset: List[str] = []
    custom: List[str] = []


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    food_preferences: Optional[PreferenceTagsSchema] = None
    atmosphere_preferences: Optional[PreferenceTagsSchema] = None
    budget_level: Optional[str] = None
    max_travel_distance_km: Optional[int] = None

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response."""
    food_preferences: Optional[Dict[str, Any]] = None
    atmosphere_preferences: Optional[Dict[str, Any]] = None
    budget_level: str = "medium"
    max_travel_distance_km: int = 10
    categories: List[str] = []

    class Config:
        from_attributes = True


# Settings schemas
class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    # Notifications
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    marketing_notifications: Optional[bool] = None
    recommendation_notifications: Optional[bool] = None
    social_notifications: Optional[bool] = None
    # Privacy
    profile_visibility: Optional[str] = None
    activity_visibility: Optional[bool] = None
    show_saved_places: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    # App
    language: Optional[str] = None
    theme: Optional[str] = None

    class Config:
        from_attributes = True


class UserSettingsResponse(BaseModel):
    """Schema for user settings response."""
    # Notifications
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    marketing_notifications: bool = True
    recommendation_notifications: bool = True
    social_notifications: bool = True
    # Privacy
    profile_visibility: str = "public"
    activity_visibility: bool = True
    show_saved_places: bool = True
    allow_friend_requests: bool = True
    # App
    language: str = "ko"
    theme: str = "system"

    class Config:
        from_attributes = True


# Account management schemas
class AccountDeleteRequest(BaseModel):
    """Schema for account deletion request."""
    reason: Optional[str] = None
    confirm: bool = False


class AccountRestoreRequest(BaseModel):
    """Schema for account restoration request."""
    email: EmailStr


class DataExportResponse(BaseModel):
    """Schema for data export response."""
    profile: Dict[str, Any]
    preferences: Dict[str, Any]
    settings: Dict[str, Any]
    exported_at: datetime
