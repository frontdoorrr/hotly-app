# Task 2: 사용자 경험 개발 (User Experience Development)

## 2-1. 온보딩 및 초기 설정 백엔드

### 목표
새로운 사용자가 3분 이내 앱에서 첫 번째 코스를 생성할 수 있도록 안내하는 백엔드 시스템

### 완료 정의 (DoD)
- [ ] 온보딩 완료율 70% 이상
- [ ] 첫 장소 저장부터 앱 3분 이내
- [ ] 사용자 설정 정보로 개인화 추천 시작

### 수용 기준
- Given 앱 첫 실행, When 온보딩 진행, Then 핵심 저장소 3개의 샘플 표시
- Given 온보딩 완료, When 첫 코스 추천 시작, Then 설정 기반 개인화 추천 제공

### 세부 작업

#### 2-1-1. 온보딩 플로우 상태 스키마 및 로직
**상세**: 사용자별 온보딩 진행 상태 추적 및 단계별 가이드 제공

**구현 체크리스트**:
- [ ] 온보딩 상태 테이블 설계
- [ ] 단계별 진행률 추적
- [ ] 이탈 지점 분석 로직
- [ ] 건너뛰기 처리
- [ ] 재온보딩 시스템

**결과물**: 
- `app/models/onboarding.py` - 온보딩 상태 모델
- `app/services/onboarding_service.py` - 온보딩 로직
- `app/schemas/onboarding.py` - 온보딩 스키마

**API**: 
- `GET /api/v1/onboarding/status` - 온보딩 상태 조회
- `POST /api/v1/onboarding/step` - 단계 완료 처리
- `PUT /api/v1/onboarding/restart` - 재온보딩 시작

**테스트**: 단계별 완료 시나리오, 이탈 복구, 상태 추적

#### 2-1-2. 사용자 취향 설정 및 사용자 온보딩 시스템
**상세**: 초기 취향 수집, 추천 시드 데이터 생성, 맞춤화 기반 구축

**구현 체크리스트**:
- [ ] 취향 설문 시스템
- [ ] 관심사 카테고리 선택
- [ ] 선호 지역 설정
- [ ] 예산 범위 설정
- [ ] 동반자 유형 설정

**결과물**: 
- `app/services/preference_service.py` - 취향 설정 서비스
- `app/models/preference.py` - 취향 모델
- `app/schemas/preference.py` - 취향 스키마

**API**: 
- `POST /api/v1/preferences/setup` - 초기 취향 설정
- `GET /api/v1/preferences/categories` - 카테고리 목록
- `PUT /api/v1/preferences/update` - 취향 업데이트

**테스트**: 취향 설정 플로우, 추천 품질 개선, 설정 변경 추적

#### 2-1-3. 첫 경험을 위한 샘플 및 가이드 제공
**상세**: 지역별 인기 장소, 샘플 코스, 가이드 투어 제공

**구현 체크리스트**:
- [ ] 지역별 인기 장소 큐레이션
- [ ] 샘플 코스 데이터 준비
- [ ] 가이드 투어 시스템
- [ ] 튜토리얼 진행 추적
- [ ] 개인화 샘플 생성

**결과물**: 
- `app/services/sample_service.py` - 샘플 데이터 서비스
- `app/data/sample_data/` - 샘플 데이터 파일들
- `app/services/tutorial_service.py` - 튜토리얼 서비스

**API**: 
- `GET /api/v1/samples/places` - 샘플 장소 목록
- `GET /api/v1/samples/courses` - 샘플 코스 목록
- `POST /api/v1/tutorial/start` - 튜토리얼 시작

**테스트**: 샘플 데이터 품질, 개인화 정확도, 튜토리얼 완료율

#### 2-1-4. 온보딩 완료 5단계 및 진척 설정 추적
**상세**: 온보딩 5단계 체크포인트, 진행률 시각화, 완료 보상 시스템

**구현 체크리스트**:
- [ ] 5단계 체크포인트 정의
- [ ] 진행률 계산 로직
- [ ] 완료 보상 시스템
- [ ] 리마인더 알림
- [ ] 성취도 배지 시스템

**결과물**: 
- `app/services/milestone_service.py` - 마일스톤 추적
- `app/models/achievement.py` - 성취도 모델
- `app/services/reward_service.py` - 보상 시스템

**API**: 
- `GET /api/v1/onboarding/progress` - 진행률 조회
- `POST /api/v1/onboarding/milestone` - 마일스톤 달성
- `GET /api/v1/achievements` - 성취도 목록

**테스트**: 진행률 계산, 마일스톤 달성, 보상 지급

#### 2-1-5. 온보딩 개인화 생성 및 엔지니어링
**상세**: 사용자 행동 기반 온보딩 최적화, A/B 테스트 프레임워크

**구현 체크리스트**:
- [ ] 개인화 온보딩 플로우
- [ ] A/B 테스트 프레임워크
- [ ] 행동 분석 및 최적화
- [ ] 동적 콘텐츠 생성
- [ ] 성과 지표 추적

**결과물**: 
- `app/services/personalization_service.py` - 개인화 서비스
- `app/ab_testing/` - A/B 테스트 프레임워크
- `app/analytics/onboarding.py` - 온보딩 분석

**API**: 
- `GET /api/v1/onboarding/personalized` - 개인화 온보딩
- `POST /api/v1/ab-test/track` - A/B 테스트 추적
- `GET /api/v1/analytics/onboarding` - 온보딩 분석

**테스트**: 개인화 효과, A/B 테스트 신뢰도, 성과 지표 정확도

#### 2-1-6. 온보딩 플로우 테스트 코드 작성
**상세**: 전체 온보딩 플로우 E2E 테스트, 사용자 여정 검증

**구현 체크리스트**:
- [ ] E2E 온보딩 플로우 테스트
- [ ] 다양한 사용자 시나리오 테스트
- [ ] 이탈 복구 시나리오 테스트
- [ ] 성능 및 사용성 테스트
- [ ] 개인화 품질 테스트

**결과물**: 
- `tests/test_onboarding.py` - 온보딩 통합 테스트
- `tests/e2e/test_user_journey.py` - 사용자 여정 테스트
- `tests/performance/test_onboarding_performance.py` - 성능 테스트

**커버리지**: 온보딩 기능 85% 이상

**테스트**: 완료율 측정, 이탈 지점 분석, 개인화 효과

---

## 2-2. 알림 및 개인화 시스템 백엔드

### 목표
개인별 관심 사항과 맞춤형 타이밍에 따른 알림을 통해 개인별 사용 빈도 증진

### 완료 정의 (DoD)
- [ ] 푸시 알림 전달 95% 정확도
- [ ] 사용자별 알림 선호 설정 및 개인화 기능
- [ ] 알림을 통한 40% 이상 앱 재방문 달성

### 수용 기준
- Given 개인별 선호도, When 18시 추천, Then 맞춤형 알림 전송
- Given 개인화 설정, When 데이터 분석함, Then 4주 알림 효과 추적

### 세부 작업

#### 2-2-1. Firebase FCM 연동 및 푸시 알림 인프라
**상세**: Firebase Cloud Messaging 설정, 다중 디바이스 지원, 알림 전달 보장

**구현 체크리스트**:
- [ ] Firebase Admin SDK 설정
- [ ] FCM 토큰 관리 시스템
- [ ] 다중 디바이스 토큰 관리
- [ ] 알림 전달 상태 추적
- [ ] 실패 재시도 메커니즘

**결과물**: 
- `app/services/fcm_service.py` - FCM 서비스
- `app/models/device_token.py` - 디바이스 토큰 모델
- `app/schemas/notification.py` - 알림 스키마

**API**: 
- `POST /api/v1/notifications/register-token` - 토큰 등록
- `POST /api/v1/notifications/send` - 알림 전송
- `GET /api/v1/notifications/status` - 전송 상태 조회

**테스트**: 토큰 관리, 전송 실패 복구, 다중 디바이스 지원

#### 2-2-2. 알림 스케줄링 및 사용자별 타겟팅
**상세**: Celery 기반 알림 스케줄링, 사용자 행동 패턴 분석, 최적 시간대 추천

**구현 체크리스트**:
- [ ] Celery Beat 스케줄러 설정
- [ ] 사용자별 최적 시간대 분석
- [ ] 알림 빈도 조절 로직
- [ ] 타겟팅 규칙 엔진
- [ ] 스케줄 동적 조정

**결과물**: 
- `app/tasks/notification_tasks.py` - 알림 작업
- `app/services/scheduling_service.py` - 스케줄링 서비스
- `app/analytics/user_behavior.py` - 사용자 행동 분석

**API**: 
- `POST /api/v1/notifications/schedule` - 알림 예약
- `GET /api/v1/notifications/optimal-time` - 최적 시간 조회
- `PUT /api/v1/notifications/frequency` - 빈도 설정

**테스트**: 스케줄링 정확도, 최적 시간 예측, 빈도 조절 효과

#### 2-2-3. 시간대별 추천 시스템 (아침, 점심, 저녁시간대)
**상세**: 시간대별 맞춤 추천, 상황별 콘텐츠 제공, 실시간 개인화

**구현 체크리스트**:
- [ ] 시간대별 추천 로직
- [ ] 상황 인식 시스템
- [ ] 날씨 연동 추천
- [ ] 위치 기반 추천
- [ ] 실시간 업데이트

**결과물**: 
- `app/services/time_based_recommendation.py` - 시간별 추천
- `app/services/context_service.py` - 컨텍스트 인식
- `app/integrations/weather_api.py` - 날씨 API 연동

**API**: 
- `GET /api/v1/recommendations/time-based` - 시간별 추천
- `GET /api/v1/context/current` - 현재 컨텍스트 조회
- `POST /api/v1/recommendations/feedback` - 추천 피드백

**테스트**: 시간별 추천 품질, 컨텍스트 인식, 실시간 업데이트

#### 2-2-4. 알림 설정 UI 및 개인화 전송 기능
**상세**: 세분화된 알림 설정, 조용한 시간, 카테고리별 알림 제어

**구현 체크리스트**:
- [ ] 알림 설정 관리 시스템
- [ ] 조용한 시간 설정
- [ ] 카테고리별 알림 제어
- [ ] 알림 미리보기 기능
- [ ] 개인화 알림 생성

**결과물**: 
- `app/services/notification_settings.py` - 알림 설정 서비스
- `app/models/notification_preference.py` - 알림 선호도 모델
- `app/utils/quiet_hours.py` - 조용한 시간 처리

**API**: 
- `GET /api/v1/settings/notifications` - 알림 설정 조회
- `PUT /api/v1/settings/notifications` - 알림 설정 변경
- `POST /api/v1/notifications/preview` - 알림 미리보기

**테스트**: 설정 변경 효과, 조용한 시간 준수, 개인화 품질

#### 2-2-5. 알림 분석 및 효과 측정 시스템
**상세**: 알림 성과 분석, 클릭률/전환율 추적, 최적화 인사이트 제공

**구현 체크리스트**:
- [ ] 알림 성과 지표 수집
- [ ] 클릭률/전환율 분석
- [ ] 사용자 세그먼트별 분석
- [ ] A/B 테스트 프레임워크
- [ ] 최적화 추천 시스템

**결과물**: 
- `app/analytics/notification_analytics.py` - 알림 분석
- `app/services/optimization_service.py` - 최적화 서비스
- `app/reports/notification_reports.py` - 리포트 생성

**API**: 
- `GET /api/v1/analytics/notifications` - 알림 분석 조회
- `GET /api/v1/analytics/conversion` - 전환율 분석
- `POST /api/v1/optimization/suggest` - 최적화 제안

**테스트**: 지표 정확도, 분석 성능, 최적화 효과

#### 2-2-6. 알림 시스템 테스트 코드 작성
**상세**: 알림 전송, 스케줄링, 개인화 전 영역 테스트

**구현 체크리스트**:
- [ ] FCM 전송 테스트
- [ ] 스케줄링 정확도 테스트
- [ ] 개인화 품질 테스트
- [ ] 성능 및 부하 테스트
- [ ] 장애 복구 테스트

**결과물**: 
- `tests/test_notification_system.py` - 알림 시스템 테스트
- `tests/integration/test_fcm_integration.py` - FCM 통합 테스트
- `tests/performance/test_notification_performance.py` - 성능 테스트

**커버리지**: 알림 시스템 90% 이상

**테스트**: 전송 성공률, 스케줄링 정확도, 개인화 효과

---

## 2-3. 검색, 필터, 정렬 기능 백엔드

### 목표
광범위한 장소 데이터에서 사용자가 원하는 취향을 3초 이내 찾을 수 있는 고도화된 검색 기능

### 완료 정의 (DoD)
- [ ] 검색 응답시간 2초 이내
- [ ] 자동완성 제공 500ms 이내 표시
- [ ] 개인 필터 옵션으로 정확도 높은 결과 전송

### 수용 기준
- Given 키워드 2글자 이상 입력, When 500ms 대기, Then 자동완성 제공 표시
- Given 검색 필터 적용, When 검색 실행, Then 개인별로 정확도 높은 결과 제공

### 세부 작업

#### 2-3-1. PostgreSQL 기반 검색 인덱스 구축
**상세**: Full-text search, 한국어 형태소 분석, 검색 성능 최적화

**구현 체크리스트**:
- [ ] PostgreSQL tsvector 검색 설정
- [ ] 한국어 텍스트 분석 설정
- [ ] 검색 인덱스 최적화
- [ ] 검색 순위 알고리즘
- [ ] 인덱스 유지보수 자동화

**결과물**: 
- `app/services/search_engine.py` - 검색 엔진
- `app/db/search_indexes.sql` - 검색 인덱스
- `app/utils/korean_analyzer.py` - 한국어 분석기

**API**: 
- `GET /api/v1/search/places` - 장소 검색
- `GET /api/v1/search/courses` - 코스 검색
- `GET /api/v1/search/suggest` - 검색 제안

**성능**: 검색 응답 2초 이내, 인덱스 효율성 90% 이상

**테스트**: 검색 정확도, 한국어 처리, 성능 벤치마크

#### 2-3-2. 자동완성 및 검색 제안 시스템
**상세**: 실시간 자동완성, 인기 검색어, 개인화 제안

**구현 체크리스트**:
- [ ] 실시간 자동완성 구현
- [ ] 인기 검색어 수집 및 제안
- [ ] 개인화 검색 제안
- [ ] 검색어 순위 알고리즘
- [ ] 오타 교정 기능

**결과물**: 
- `app/services/autocomplete_service.py` - 자동완성 서비스
- `app/services/search_suggestion.py` - 검색 제안 서비스
- `app/utils/spell_checker.py` - 오타 교정

**API**: 
- `GET /api/v1/search/autocomplete` - 자동완성
- `GET /api/v1/search/popular` - 인기 검색어
- `GET /api/v1/search/suggestions` - 개인화 제안

**성능**: 자동완성 500ms 이내, 제안 품질 80% 이상

**테스트**: 자동완성 정확도, 개인화 품질, 응답 시간

#### 2-3-3. 고급 필터 및 정렬 시스템
**상세**: 다중 필터 조합, 동적 정렬, 사용자 설정 저장

**구현 체크리스트**:
- [ ] 다중 필터 조합 로직
- [ ] 동적 정렬 기능
- [ ] 필터 설정 저장
- [ ] 필터 성능 최적화
- [ ] 필터 추천 시스템

**결과물**: 
- `app/services/filter_service.py` - 필터 서비스
- `app/services/sort_service.py` - 정렬 서비스
- `app/models/search_preference.py` - 검색 선호도 모델

**API**: 
- `GET /api/v1/filters/available` - 사용 가능한 필터
- `POST /api/v1/filters/save` - 필터 설정 저장
- `GET /api/v1/filters/recommended` - 추천 필터

**성능**: 필터링 1초 이내, 복합 필터 지원

**테스트**: 필터 조합 테스트, 성능 테스트, 추천 품질

#### 2-3-4. 검색 결과 랭킹 및 개인화 시스템
**상세**: 개인화 랭킹 알고리즘, 학습 기반 결과 개선, 다양성 보장

**구현 체크리스트**:
- [ ] 개인화 랭킹 알고리즘
- [ ] 사용자 피드백 학습
- [ ] 결과 다양성 보장
- [ ] 실시간 랭킹 업데이트
- [ ] 랭킹 설명 기능

**결과물**: 
- `app/services/ranking_service.py` - 랭킹 서비스
- `app/ml/ranking/` - 랭킹 모델
- `app/services/diversity_service.py` - 다양성 보장

**API**: 
- `GET /api/v1/search/ranked` - 개인화 랭킹 검색
- `POST /api/v1/search/feedback` - 검색 피드백
- `GET /api/v1/search/explain` - 랭킹 설명

**성능**: 랭킹 계산 500ms 이내, 개인화 품질 75% 이상

**테스트**: 랭킹 정확도, 개인화 효과, 다양성 지표

#### 2-3-5. 검색 UI/UX 및 성능 최적화 구현
**상세**: 검색 UX 최적화, 캐싱 전략, 점진적 로딩

**구현 체크리스트**:
- [ ] 검색 결과 캐싱 최적화
- [ ] 점진적 로딩 구현
- [ ] 검색 히스토리 관리
- [ ] 즐겨찾는 검색 저장
- [ ] 검색 분석 대시보드

**결과물**: 
- `app/services/search_cache.py` - 검색 캐시
- `app/services/search_history.py` - 검색 히스토리
- `app/services/search_analytics.py` - 검색 분석

**API**: 
- `GET /api/v1/search/history` - 검색 히스토리
- `POST /api/v1/search/save` - 즐겨찾는 검색 저장
- `GET /api/v1/search/analytics` - 검색 분석

**성능**: 캐시 적중률 60% 이상, 로딩 시간 1초 이내

**테스트**: 캐싱 효과, 히스토리 관리, 분석 정확도

#### 2-3-6. 검색 필터 테스트 코드 작성
**상세**: 검색 정확도, 성능, 사용자 경험 종합 테스트

**구현 체크리스트**:
- [ ] 검색 정확도 테스트
- [ ] 필터 조합 테스트
- [ ] 성능 벤치마크 테스트
- [ ] 사용자 시나리오 테스트
- [ ] 개인화 품질 테스트

**결과물**: 
- `tests/test_search_system.py` - 검색 시스템 테스트
- `tests/performance/test_search_performance.py` - 성능 테스트
- `tests/e2e/test_search_ux.py` - UX 테스트

**커버리지**: 검색 기능 85% 이상

**테스트**: 검색 정확도, 응답 시간, 개인화 효과

---

## Backend Reference 활용 가이드

### 사용자 경험 기능 참고
`backend_reference/app/app/`에서 다음 패턴들 활용:

**사용자 관리**:
```python
# users.py 참고 - 사용자 CRUD 패턴
@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user
```

**알림 시스템**:
- `worker.py` Celery 비동기 작업 패턴
- `core/celery_app.py` Celery 설정 참고
- `email-templates/` 템플릿 관리 방식

**설정 및 보안**:
- `core/config.py` 환경변수 검증 패턴
- `core/security.py` JWT 및 비밀번호 처리

## 참고 문서

### 요구사항 문서
- `prd/06-onboarding-flow.md` - 온보딩 요구사항
- `prd/07-notification-system.md` - 알림 시스템 요구사항
- `prd/08-search-filter.md` - 검색 필터 요구사항

### 기술 설계 문서
- `trd/06-onboarding-flow.md` - 온보딩 기술 설계
- `trd/07-notification-system.md` - 알림 시스템 기술 설계
- `trd/08-search-filter.md` - 검색 필터 기술 설계

### 구현 참고 자료
- **`backend_reference/app/`** - FastAPI UX 기능 참고
  - 사용자 관리: `api/api_v1/endpoints/users.py`
  - 비동기 작업: `worker.py`, `core/celery_app.py`
  - 이메일 템플릿: `email-templates/`
  - 인증 미들웨어: `api/deps.py`
- `database-schema.md` - 데이터베이스 스키마
- `ui-design-system.md` - UI 컴포넌트 가이드
- `rules.md` - 개발 규칙

---

*작성일: 2025-01-XX*  
*작성자: Claude*  
*버전: 1.0*