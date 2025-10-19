# Task 3: 사용자 및 인증 관리 (Authentication & User Management)

## 3-1. Firebase 기반 사용자 시스템 백엔드

### 목표
신뢰성이 높은 다양한 로그인 및 인증 방식을 통해 안전한 사용자 시스템 구축

### 완료 정의 (DoD)
- [ ] 다양한 로그인 (구글, 애플, 카카오) 연동 완료
- [ ] 인증된 사용자 및 세션 관리 기능
- [ ] 생체 인증 및 보안 검증 시스템

### 수용 기준
- Given 다양한 로그인 선택, When 사용자 인증, Then 5초 이내 로그인 완료
- Given 인증된 사용자 세션, When 세션 관리, Then 인증된 개인별로 데이터 제공

### 세부 작업

#### 3-1-1. Firebase Auth 설정 및 다양한 로그인 구현
**상세**: Firebase Authentication 설정, OAuth 프로바이더 연동, Custom Token 관리

**구현 체크리스트**:
- [ ] Firebase Admin SDK 설정
- [ ] Firebase Authentication 활성화
- [ ] Google OAuth 로그인 구현
- [ ] Apple Sign-In 연동
- [ ] 카카오 Custom Token 연동
- [ ] 이메일/비밀번호 로그인
- [ ] 익명 인증 (Anonymous Auth)

**결과물**:
- `app/services/auth/firebase_auth_service.py` - Firebase 인증 서비스
- `app/middleware/jwt_middleware.py` - Firebase JWT 검증
- `app/schemas/auth.py` - 인증 스키마
- `app/api/api_v1/endpoints/auth.py` - 인증 API 엔드포인트
- Service Account Key JSON 파일

**API**:
- `POST /api/v1/auth/signup` - 회원가입 (클라이언트 SDK 권장)
- `POST /api/v1/auth/signin` - 이메일 로그인 (클라이언트 SDK 권장)
- `POST /api/v1/auth/social-login` - 소셜 로그인 (Google, Apple, Kakao)
- `POST /api/v1/auth/verify-token` - Firebase ID 토큰 검증
- `POST /api/v1/auth/anonymous` - 익명 사용자 생성

**테스트**: 각 프로바이더별 로그인, Firebase ID 토큰 검증, Custom Claims 검증, 에러 처리

#### 3-1-2. 인증된 사용자 로직 및 개인별 데이터 연동 시스템
**상세**: JWT 토큰 관리, 세션 상태 추적, 사용자 컨텍스트 관리

**구현 체크리스트**:
- [ ] JWT 토큰 생성/검증
- [ ] 세션 상태 관리
- [ ] 사용자 컨텍스트 추적
- [ ] 권한 기반 접근 제어
- [ ] 다중 디바이스 세션 관리

**결과물**:
- `app/core/security.py` - 보안 유틸리티
- `app/services/session_service.py` - 세션 관리
- `app/middleware/auth_middleware.py` - 인증 미들웨어
- `app/models/user_session.py` - 세션 모델

**API**:
- `POST /api/v1/auth/refresh` - 토큰 갱신
- `POST /api/v1/auth/logout` - 로그아웃
- `GET /api/v1/auth/sessions` - 세션 목록
- `DELETE /api/v1/auth/sessions/{session_id}` - 세션 종료

**테스트**: 토큰 생명주기, 세션 관리, 권한 검증

#### 3-1-3. 생체 인증 및 PIN 인증 시스템
**상세**: 생체 인증(지문, 얼굴), PIN 번호, 패턴 잠금 지원

**구현 체크리스트**:
- [ ] 생체 인증 백엔드 지원
- [ ] PIN 번호 설정/검증
- [ ] 패턴 잠금 구현
- [ ] 인증 실패 제한
- [ ] 복구 메커니즘

**결과물**:
- `app/services/biometric_service.py` - 생체 인증
- `app/services/pin_service.py` - PIN 인증
- `app/models/auth_method.py` - 인증 방법 모델

**API**:
- `POST /api/v1/auth/biometric/setup` - 생체 인증 설정
- `POST /api/v1/auth/pin/setup` - PIN 설정
- `POST /api/v1/auth/verify` - 인증 검증
- `POST /api/v1/auth/recovery` - 계정 복구

**테스트**: 인증 방법별 테스트, 실패 시나리오, 보안 검증

#### 3-1-4. 익명 사용자 및 게스트 개인화 백엔드
**상세**: 비로그인 사용자 경험, 임시 세션, 계정 연결 유도

**구현 체크리스트**:
- [ ] 익명 세션 관리
- [ ] 게스트 데이터 임시 저장
- [ ] 계정 연결 유도 시스템
- [ ] 게스트 권한 제한
- [ ] 데이터 마이그레이션

**결과물**:
- `app/services/guest_service.py` - 게스트 사용자 서비스
- `app/models/guest_session.py` - 게스트 세션 모델
- `app/services/account_linking.py` - 계정 연결 서비스

**API**:
- `POST /api/v1/guest/session` - 게스트 세션 생성
- `POST /api/v1/guest/link-account` - 계정 연결
- `GET /api/v1/guest/data` - 게스트 데이터 조회

**테스트**: 게스트 세션 관리, 계정 연결, 데이터 마이그레이션

#### 3-1-5. 보안 검증 및 데이터 보호 구현
**상세**: 보안 감사, 데이터 암호화, 접근 로그, 이상 행동 감지

**구현 체크리스트**:
- [ ] 보안 감사 로그
- [ ] 민감 데이터 암호화
- [ ] 접근 로그 및 분석
- [ ] 이상 행동 감지
- [ ] 보안 인시던트 대응

**결과물**:
- `app/services/security_service.py` - 보안 서비스
- `app/services/audit_service.py` - 감사 서비스
- `app/utils/encryption.py` - 암호화 유틸리티

**API**:
- `GET /api/v1/security/audit` - 보안 감사 로그
- `POST /api/v1/security/report` - 보안 인시던트 신고
- `GET /api/v1/security/status` - 보안 상태 조회

**테스트**: 보안 감사, 암호화/복호화, 이상 행동 감지

#### 3-1-6. 사용자 인증 테스트 코드 작성
**상세**: 인증 플로우, 보안, 성능 종합 테스트

**구현 체크리스트**:
- [ ] 인증 플로우 E2E 테스트
- [ ] 보안 취약점 테스트
- [ ] 성능 및 부하 테스트
- [ ] 다중 디바이스 테스트
- [ ] 장애 복구 테스트

**결과물**:
- `tests/test_authentication.py` - 인증 시스템 테스트
- `tests/security/test_auth_security.py` - 보안 테스트
- `tests/performance/test_auth_performance.py` - 성능 테스트

**커버리지**: 인증 시스템 90% 이상

**테스트**: 로그인 성공률, 보안 준수, 성능 지표

---

## 3-2. 사용자 프로필 및 설정 관리 백엔드

### 목표
사용자별 앱 사용 내역과 맞춤형 개인화 설정을 제공하는 프로필 관리 시스템

### 완료 정의 (DoD)
- [ ] 프로필 정보 3초 이내 저장 및 정보 제공
- [ ] 사용자별 설정 기반 추천 정확도 향상 지표
- [ ] GDPR 준수하는 사용자 정보 관리 기능

### 수용 기준
- Given 프로필 정보 업데이트, When 데이터 저장, Then 3초 이내 앱 정보 표시
- Given 사용자 정보 삭제 요청, When 24시간 대기, Then 데이터를 완전 삭제

### 세부 작업

#### 3-2-1. 사용자 프로필 관리 시스템 및 데이터 삭제
**상세**: 사용자 프로필 CRUD, 프로필 이미지 관리, 개인정보 보호

**구현 체크리스트**:
- [ ] 프로필 정보 CRUD API
- [ ] 프로필 이미지 업로드/관리
- [ ] 개인정보 마스킹 처리
- [ ] 데이터 삭제 요청 처리
- [ ] 삭제 예약 시스템

**결과물**:
- `app/api/v1/endpoints/profile.py` - 프로필 API
- `app/services/profile_service.py` - 프로필 서비스
- `app/services/image_service.py` - 이미지 관리
- `app/models/user_profile.py` - 프로필 모델

**API**:
- `GET /api/v1/profile` - 프로필 조회
- `PUT /api/v1/profile` - 프로필 수정
- `POST /api/v1/profile/image` - 프로필 이미지 업로드
- `DELETE /api/v1/profile` - 프로필 삭제 요청

**테스트**: CRUD 플로우, 이미지 처리, 삭제 프로세스

#### 3-2-2. 사용자별 설정 및 알림 관리 기능
**상세**: 개인화 설정, 알림 선호도, 프라이버시 설정 관리

**구현 체크리스트**:
- [ ] 개인화 설정 관리
- [ ] 알림 선호도 설정
- [ ] 프라이버시 설정
- [ ] 접근성 설정
- [ ] 설정 동기화

**결과물**:
- `app/services/user_settings.py` - 사용자 설정 서비스
- `app/models/user_setting.py` - 설정 모델
- `app/schemas/settings.py` - 설정 스키마

**API**:
- `GET /api/v1/settings` - 설정 조회
- `PUT /api/v1/settings/{category}` - 카테고리별 설정 변경
- `POST /api/v1/settings/sync` - 설정 동기화

**테스트**: 설정 변경 효과, 동기화 정확성, 개인화 품질

#### 3-2-3. 사용자 데이터 백업 및 분석 시스템
**상세**: 데이터 백업, 사용 패턴 분석, 개인화 인사이트 제공

**구현 체크리스트**:
- [ ] 자동 데이터 백업 시스템
- [ ] 사용 패턴 분석
- [ ] 개인화 인사이트 생성
- [ ] 데이터 내보내기 기능
- [ ] 백업 복구 시스템

**결과물**:
- `app/services/backup_service.py` - 백업 서비스
- `app/analytics/user_analytics.py` - 사용자 분석
- `app/services/export_service.py` - 데이터 내보내기

**API**:
- `POST /api/v1/backup/create` - 백업 생성
- `GET /api/v1/analytics/insights` - 개인 인사이트
- `POST /api/v1/export/request` - 데이터 내보내기 요청

**테스트**: 백업 무결성, 분석 정확도, 내보내기 완성도

#### 3-2-4. 사용자 정보 및 프라이버시 기능
**상세**: GDPR 준수, 개인정보 보호, 데이터 최소화, 동의 관리

**구현 체크리스트**:
- [ ] GDPR 준수 시스템
- [ ] 개인정보 처리 동의 관리
- [ ] 데이터 최소화 정책
- [ ] 정보 접근 권한 관리
- [ ] 개인정보 처리 이력

**결과물**:
- `app/services/privacy_service.py` - 프라이버시 서비스
- `app/services/consent_service.py` - 동의 관리 서비스
- `app/models/consent.py` - 동의 모델

**API**:
- `GET /api/v1/privacy/policy` - 개인정보 정책
- `POST /api/v1/privacy/consent` - 동의 처리
- `GET /api/v1/privacy/data` - 개인정보 조회
- `DELETE /api/v1/privacy/data` - 개인정보 삭제

**테스트**: GDPR 준수 검증, 동의 관리, 데이터 삭제

#### 3-2-5. 세션 관리 및 개인화 시스템
**상세**: 다중 디바이스 세션, 동기화, 개인화 데이터 관리

**구현 체크리스트**:
- [ ] 다중 디바이스 세션 관리
- [ ] 세션 동기화 시스템
- [ ] 개인화 데이터 관리
- [ ] 디바이스별 설정
- [ ] 세션 보안 강화

**결과물**:
- `app/services/multi_device_service.py` - 다중 디바이스 서비스
- `app/services/sync_service.py` - 동기화 서비스
- `app/models/device_session.py` - 디바이스 세션 모델

**API**:
- `GET /api/v1/devices` - 디바이스 목록
- `POST /api/v1/devices/register` - 디바이스 등록
- `POST /api/v1/sync/trigger` - 동기화 트리거
- `DELETE /api/v1/devices/{device_id}` - 디바이스 해제

**테스트**: 다중 디바이스 동기화, 세션 충돌, 보안 검증

#### 3-2-6. 사용자 프로필 테스트 코드 작성
**상세**: 프로필 관리, 설정, 프라이버시 전 영역 테스트

**구현 체크리스트**:
- [ ] 프로필 CRUD 테스트
- [ ] 설정 관리 테스트
- [ ] 프라이버시 보호 테스트
- [ ] 다중 디바이스 테스트
- [ ] GDPR 준수 테스트

**결과물**:
- `tests/test_user_profile.py` - 프로필 시스템 테스트
- `tests/integration/test_profile_integration.py` - 통합 테스트
- `tests/security/test_privacy_compliance.py` - 프라이버시 테스트

**커버리지**: 사용자 관리 시스템 85% 이상

**테스트**: 프로필 관리, 설정 효과, 프라이버시 준수

---

## Firebase 인증 구현 가이드

### Firebase Admin SDK 초기화
Service Account Key를 사용한 Firebase Admin SDK 초기화:

**Firebase Admin SDK 초기화**:
```python
# app/services/auth/firebase_auth_service.py
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
```

**인증 서비스 구현**:
```python
# app/services/auth/firebase_auth_service.py
class FirebaseAuthService:
    async def validate_access_token(self, token: str):
        """Firebase ID 토큰 검증"""
        try:
            decoded_token = auth.verify_id_token(token)
            return TokenValidationResult(
                is_valid=True,
                user_id=decoded_token['uid'],
                email=decoded_token.get('email')
            )
        except Exception as e:
            return TokenValidationResult(is_valid=False, error_message=str(e))

    async def create_custom_token(self, uid: str, claims: dict = None):
        """Custom Token 생성 (Kakao 연동용)"""
        return auth.create_custom_token(uid, claims)
```

**JWT 검증 미들웨어**:
```python
# app/middleware/jwt_middleware.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    token = credentials.credentials
    validation_result = await firebase_auth_service.validate_access_token(token)

    if not validation_result.is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "uid": validation_result.user_id,
        "email": validation_result.email,
        "permissions": validation_result.permissions
    }
```

**Custom Claims 설정**:
```python
# 사용자 권한 설정 (관리자, 일반 사용자 등)
auth.set_custom_user_claims(uid, {'admin': True, 'role': 'premium'})
```

## 참고 문서

### 요구사항 문서
- `prd/09-authentication.md` - 인증 시스템 요구사항
- `prd/10-user-profile.md` - 사용자 프로필 요구사항

### 기술 설계 문서
- `trd/09-authentication.md` - 인증 시스템 기술 설계
- `trd/10-user-profile.md` - 사용자 프로필 기술 설계

### 구현 참고 자료
- **Firebase 공식 문서**
  - [Firebase Authentication](https://firebase.google.com/docs/auth) - 인증 가이드
  - [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup) - Admin SDK 설정
  - [Custom Tokens](https://firebase.google.com/docs/auth/admin/create-custom-tokens) - Custom Token 생성
  - [Verify ID Tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens) - ID 토큰 검증
- **프로젝트 내부 참고**
  - `app/services/auth/firebase_auth_service.py` - Firebase 인증 서비스
  - `app/middleware/jwt_middleware.py` - JWT 검증 미들웨어
  - `app/schemas/auth.py` - 인증 스키마
  - `docs/firebase-setup-guide.md` - Firebase 설정 가이드
  - `prd/09-authentication.md` - PRD (Firebase 기반)
  - `trd/09-authentication.md` - TRD (Firebase 기반)
- `database-schema.md` - 데이터베이스 스키마
- `rules.md` - 개발 규칙

### Firebase 인증 구현 체크리스트
- [x] Firebase 프로젝트 생성 및 Service Account Key 발급
- [x] Firebase Admin SDK 초기화
- [x] OAuth 프로바이더 설정 (Google, Apple)
- [x] Kakao Custom Token 연동 구현
- [x] FastAPI 인증 미들웨어 구현
- [x] Frontend Flutter Firebase Auth 연동
- [ ] 테스트 및 검증

---

*작성일: 2025-01-XX*
*작성자: Claude*
*버전: 3.0 (Firebase 기반)*
