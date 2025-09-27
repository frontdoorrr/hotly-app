"""
사용자 데이터 API 엔드포인트

인증된 사용자 로직 및 개인별 데이터 연동을 위한
API 엔드포인트들을 구현합니다.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.middleware.auth_middleware import get_current_user, require_permission
from app.models.user_data import AuthenticatedUser
from app.services.user_data_service import (
    AuthenticatedUserService,
    UserPersonalDataService,
    UserActivityLogService,
    UserSettingsService,
    UserDataPrivacyService
)
from app.schemas.user_data import (
    UserProfileResponse,
    UserProfileUpdate,
    UserPersonalDataResponse,
    UserPersonalDataCreate,
    UserActivityLogResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
    UserPrivacySettingsResponse,
    UserPrivacySettingsUpdate
)

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """현재 사용자 프로필 조회"""
    return UserProfileResponse(
        id=str(current_user.id),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        display_name=current_user.display_name,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        is_phone_verified=current_user.is_phone_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_service: AuthenticatedUserService = Depends()
):
    """사용자 프로필 업데이트"""
    update_data = profile_update.dict(exclude_unset=True)
    
    updated_user = user_service.update_profile(
        user_id=str(current_user.id),
        profile_updates=update_data
    )
    
    return UserProfileResponse(
        id=str(updated_user.id),
        firebase_uid=updated_user.firebase_uid,
        email=updated_user.email,
        display_name=updated_user.display_name,
        phone_number=updated_user.phone_number,
        is_active=updated_user.is_active,
        is_email_verified=updated_user.is_email_verified,
        is_phone_verified=updated_user.is_phone_verified,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        last_login_at=updated_user.last_login_at
    )


@router.post("/personal-data", response_model=UserPersonalDataResponse)
async def store_personal_data(
    data_create: UserPersonalDataCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    personal_data_service: UserPersonalDataService = Depends()
):
    """개인 데이터 저장"""
    stored_data = personal_data_service.store_data(
        user_id=str(current_user.id),
        data_type=data_create.data_type,
        data_content=data_create.data_content,
        encrypt=data_create.encrypt
    )
    
    return UserPersonalDataResponse(
        id=str(stored_data.id),
        user_id=stored_data.user_id,
        data_type=stored_data.data_type,
        data_content=stored_data.data_content,
        is_encrypted=stored_data.is_encrypted,
        sensitivity_level=stored_data.sensitivity_level,
        created_at=stored_data.created_at,
        updated_at=stored_data.updated_at
    )


@router.get("/personal-data/{data_type}", response_model=UserPersonalDataResponse)
async def get_personal_data(
    data_type: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    personal_data_service: UserPersonalDataService = Depends()
):
    """특정 타입의 개인 데이터 조회"""
    user_data = personal_data_service.get_by_type(
        user_id=str(current_user.id),
        data_type=data_type
    )
    
    if not user_data:
        raise HTTPException(
            status_code=404,
            detail=f"Personal data of type '{data_type}' not found"
        )
    
    return UserPersonalDataResponse(
        id=str(user_data.id),
        user_id=user_data.user_id,
        data_type=user_data.data_type,
        data_content=user_data.data_content,
        is_encrypted=user_data.is_encrypted,
        sensitivity_level=user_data.sensitivity_level,
        created_at=user_data.created_at,
        updated_at=user_data.updated_at
    )


@router.get("/activity-logs", response_model=List[UserActivityLogResponse])
async def get_activity_logs(
    limit: int = 50,
    current_user: AuthenticatedUser = Depends(get_current_user),
    activity_service: UserActivityLogService = Depends()
):
    """사용자 활동 로그 조회"""
    start_date = datetime.utcnow().replace(day=1)  # 이번 달 초부터
    end_date = datetime.utcnow()
    
    activity_logs = activity_service.get_user_activity_history(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return [
        UserActivityLogResponse(
            id=str(log.id),
            user_id=log.user_id,
            activity_type=log.activity_type,
            activity_data=log.activity_data,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at
        )
        for log in activity_logs
    ]


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: AuthenticatedUser = Depends(get_current_user),
    settings_service: UserSettingsService = Depends()
):
    """사용자 설정 조회"""
    # Mock 구현: 기본 설정 반환
    settings = settings_service.initialize_default_settings(str(current_user.id))
    
    return UserSettingsResponse(
        id=str(settings.id),
        user_id=settings.user_id,
        settings_type=settings.settings_type,
        settings_data=settings.settings_data,
        is_default=settings.is_default,
        version=settings.version,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )


@router.patch("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    settings_service: UserSettingsService = Depends()
):
    """사용자 설정 업데이트"""
    updated_settings = settings_service.update_settings(
        user_id=str(current_user.id),
        settings_type=settings_update.settings_type,
        settings_updates=settings_update.settings_data
    )
    
    return UserSettingsResponse(
        id=str(updated_settings.id),
        user_id=updated_settings.user_id,
        settings_type=updated_settings.settings_type,
        settings_data=updated_settings.settings_data,
        is_default=updated_settings.is_default,
        version=updated_settings.version,
        created_at=updated_settings.created_at,
        updated_at=updated_settings.updated_at
    )


@router.get("/privacy-settings", response_model=UserPrivacySettingsResponse)
async def get_privacy_settings(
    current_user: AuthenticatedUser = Depends(get_current_user),
    privacy_service: UserDataPrivacyService = Depends()
):
    """프라이버시 설정 조회"""
    # Mock 구현: 기본 프라이버시 설정 반환
    default_privacy = {
        "data_collection_consent": True,
        "marketing_consent": False,
        "location_tracking": True,
        "analytics_consent": True,
        "data_retention_days": 365
    }
    
    privacy_settings = privacy_service.setup_privacy_settings(
        user_id=str(current_user.id),
        privacy_preferences=default_privacy
    )
    
    return UserPrivacySettingsResponse(
        id=str(privacy_settings.id),
        user_id=privacy_settings.user_id,
        privacy_settings=privacy_settings.privacy_settings,
        gdpr_compliance=privacy_settings.gdpr_compliance,
        consent_date=privacy_settings.consent_date,
        consent_version=privacy_settings.consent_version,
        data_retention_days=privacy_settings.data_retention_days,
        created_at=privacy_settings.created_at,
        last_updated=privacy_settings.last_updated
    )


@router.patch("/privacy-settings", response_model=UserPrivacySettingsResponse)
async def update_privacy_settings(
    privacy_update: UserPrivacySettingsUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    privacy_service: UserDataPrivacyService = Depends()
):
    """프라이버시 설정 업데이트"""
    updated_privacy = privacy_service.setup_privacy_settings(
        user_id=str(current_user.id),
        privacy_preferences=privacy_update.privacy_settings
    )
    
    return UserPrivacySettingsResponse(
        id=str(updated_privacy.id),
        user_id=updated_privacy.user_id,
        privacy_settings=updated_privacy.privacy_settings,
        gdpr_compliance=updated_privacy.gdpr_compliance,
        consent_date=updated_privacy.consent_date,
        consent_version=updated_privacy.consent_version,
        data_retention_days=updated_privacy.data_retention_days,
        created_at=updated_privacy.created_at,
        last_updated=updated_privacy.last_updated
    )


@router.post("/request-data-deletion")
async def request_data_deletion(
    reason: str = "user_request",
    immediate: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_user),
    privacy_service: UserDataPrivacyService = Depends()
):
    """사용자 데이터 삭제 요청"""
    deletion_result = privacy_service.request_data_deletion(
        user_id=str(current_user.id),
        reason=reason,
        immediate=immediate
    )
    
    return {
        "message": "Data deletion request has been processed",
        "deletion_details": deletion_result
    }


@router.get("/export-data")
async def export_user_data(
    current_user: AuthenticatedUser = Depends(get_current_user),
    privacy_service: UserDataPrivacyService = Depends()
):
    """사용자 데이터 내보내기 (GDPR 권리)"""
    exported_data = privacy_service.export_user_data(str(current_user.id))
    
    return {
        "message": "User data export completed",
        "export_details": exported_data
    }


# 활동 로깅을 위한 내부 엔드포인트
@router.post("/log-activity", status_code=status.HTTP_201_CREATED)
async def log_user_activity(
    request: Request,
    activity_type: str,
    activity_data: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
    activity_service: UserActivityLogService = Depends()
):
    """사용자 활동 로깅 (내부 사용)"""
    request_info = {
        "ip_address": request.client.host if hasattr(request, 'client') else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    
    activity_log = activity_service.log_activity(
        user_id=str(current_user.id),
        activity_type=activity_type,
        activity_data=activity_data,
        request_info=request_info
    )
    
    return {
        "message": "Activity logged successfully",
        "activity_id": str(activity_log.id)
    }