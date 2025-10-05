# Task 07: Frontend Development - 상세 참고 자료

## Phase 3: 화면 구현 - API 및 문서 참고

### 3.1 홈 화면 구현 📱

**📚 참고 문서**:
- 화면 스펙: `docs/screens/home-screen-spec.md`
- PRD: `prd/02-place-management.md` (장소 관리)
- TRD: `trd/02-place-management.md` (기술 스펙)
- Design: `ui-design-system.md` (UI 컴포넌트)

**🔌 Backend API 엔드포인트**:
```
GET  /api/v1/places                          # 장소 목록 조회
GET  /api/v1/places/nearby?lat={}&lng={}     # 근처 장소 조회
GET  /api/v1/personalization/recommendations # 추천 장소
POST /api/v1/places/{id}/like                # 장소 좋아요
POST /api/v1/places/{id}/save                # 장소 저장
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/places.py` - 장소 CRUD
- `backend/app/api/api_v1/endpoints/personalization.py` - 추천 로직
- `backend/app/schemas/place.py` - Place 스키마 (DTO 참고용)

---

### 3.2 검색 화면 구현 🔍

**📚 참고 문서**:
- 화면 스펙: `docs/screens/search-screen-spec.md`
- PRD: `prd/08-search-filter.md` (검색 및 필터)
- TRD: `trd/08-search-filter.md` (기술 스펙)

**🔌 Backend API 엔드포인트**:
```
GET  /api/v1/search?q={query}                      # 장소 검색
GET  /api/v1/search?q={}&category={}&distance={}   # 필터 검색
GET  /api/v1/autocomplete?q={query}                # 자동완성 제안
GET  /api/v1/filters                               # 필터 옵션 조회
POST /api/v1/ranking/record                        # 검색 결과 클릭 기록
GET  /api/v1/map/search                            # 지도 검색
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/search.py` - 검색 엔드포인트
- `backend/app/api/api_v1/endpoints/autocomplete.py` - 자동완성
- `backend/app/api/api_v1/endpoints/advanced_filters.py` - 고급 필터
- `backend/app/api/api_v1/endpoints/search_ranking.py` - 검색 랭킹
- `backend/app/services/search/search_service.py` - 검색 비즈니스 로직

---

### 3.3 장소 상세 화면 구현 📍

**📚 참고 문서**:
- 화면 스펙: `docs/screens/place-detail-screen-spec.md`
- PRD: `prd/02-place-management.md` (장소 상세)
- PRD: `prd/05-sharing-system.md` (공유 기능)
- TRD: `trd/02-place-management.md`

**🔌 Backend API 엔드포인트**:
```
GET  /api/v1/places/{id}                # 장소 상세 조회
POST /api/v1/places/{id}/like           # 좋아요
POST /api/v1/places/{id}/save           # 저장
POST /api/v1/places/{id}/share          # 공유 링크 생성
GET  /api/v1/places/{id}/similar        # 비슷한 장소
GET  /api/v1/cdn/images/{place_id}      # 이미지 조회
GET  /api/v1/map/place/{id}             # 지도 데이터
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/places.py` - 장소 상세
- `backend/app/api/api_v1/endpoints/cdn.py` - 이미지 CDN
- `backend/app/api/api_v1/endpoints/map.py` - 지도 기능
- `backend/app/schemas/place.py` - Place 상세 스키마

---

### 3.4 코스 빌더 화면 구현 ✅

**📚 참고 문서**:
- 화면 스펙: `docs/screens/course-builder-screen-spec.md`
- PRD: `prd/03-course-recommendation.md` (코스 추천)
- TRD: `trd/03-course-recommendation.md`

**🔌 Backend API 엔드포인트**:
```
POST   /api/v1/courses              # 코스 생성
PUT    /api/v1/courses/{id}         # 코스 수정
GET    /api/v1/courses/{id}         # 코스 조회
DELETE /api/v1/courses/{id}         # 코스 삭제
POST   /api/v1/courses/{id}/share   # 코스 공유
GET    /api/v1/map/route            # 경로 계산 (이동 시간/거리)
POST   /api/v1/courses/optimize     # AI 코스 최적화
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/courses.py` - 코스 CRUD
- `backend/app/api/api_v1/endpoints/map.py` - 경로 계산
- `backend/app/services/courses/course_optimizer.py` - 코스 최적화 로직
- `backend/app/schemas/course.py` - Course 스키마

**TODO**:
- [ ] RouteInfoCard에 실제 경로 API 연동 (`map.py`)
- [ ] 코스 저장 기능 API 연동 (`courses.py`)

---

### 3.5 프로필 화면 구현 👤

**📚 참고 문서**:
- 화면 스펙: `docs/screens/profile-screen-spec.md`
- PRD: `prd/10-user-profile.md` (사용자 프로필)
- TRD: `trd/10-user-profile.md`

**🔌 Backend API 엔드포인트**:
```
GET  /api/v1/user-data/profile           # 프로필 조회
PUT  /api/v1/user-data/profile           # 프로필 수정
GET  /api/v1/user-data/stats             # 사용자 통계
GET  /api/v1/user-data/folders           # 폴더 목록
POST /api/v1/user-data/folders           # 폴더 생성
PUT  /api/v1/user-data/folders/{id}      # 폴더 수정
GET  /api/v1/user-data/saved-places      # 저장된 장소
GET  /api/v1/preferences                 # 설정 조회
PUT  /api/v1/preferences                 # 설정 변경
POST /api/v1/auth/logout                 # 로그아웃
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/user_data.py` - 사용자 데이터
- `backend/app/api/api_v1/endpoints/preferences.py` - 설정 관리
- `backend/app/api/api_v1/endpoints/auth.py` - 인증/로그아웃
- `backend/app/schemas/user_data.py` - User 스키마

---

## Phase 4: 인증 및 온보딩

### 4.1 인증 플로우

**📚 참고 문서**:
- PRD: `prd/09-authentication.md` (인증 시스템)
- TRD: `trd/09-authentication.md`

**🔌 Backend API 엔드포인트**:
```
POST /api/v1/auth/login                  # 이메일 로그인
POST /api/v1/auth/register               # 회원가입
POST /api/v1/auth/social/google          # Google 로그인
POST /api/v1/auth/social/apple           # Apple 로그인
POST /api/v1/auth/refresh                # 토큰 갱신
POST /api/v1/auth/logout                 # 로그아웃
GET  /api/v1/auth/me                     # 현재 사용자 정보
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/auth.py` - 인증 엔드포인트
- `backend/app/services/auth/firebase_auth_service.py` - Firebase 인증
- `backend/app/core/security.py` - JWT 토큰 관리

---

### 4.2 온보딩 플로우

**📚 참고 문서**:
- PRD: `prd/06-onboarding-flow.md` (온보딩)
- TRD: `trd/06-onboarding-flow.md`

**🔌 Backend API 엔드포인트**:
```
POST /api/v1/onboarding/interests        # 관심사 저장
POST /api/v1/onboarding/categories       # 선호 카테고리 저장
POST /api/v1/onboarding/location         # 위치 정보 저장
POST /api/v1/onboarding/complete         # 온보딩 완료
GET  /api/v1/onboarding/status           # 온보딩 상태 조회
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/onboarding.py` - 온보딩 엔드포인트
- `backend/app/services/auth/onboarding_service.py` - 온보딩 비즈니스 로직
- `backend/app/analytics/onboarding.py` - 온보딩 분석

---

## Phase 5: 고급 기능

### 5.1 지도 기능

**📚 참고 문서**:
- PRD: `prd/04-map-visualization.md` (지도 시각화)
- TRD: `trd/04-map-visualization.md`

**🔌 Backend API 엔드포인트**:
```
GET  /api/v1/map/places                  # 지도 영역 내 장소
GET  /api/v1/map/route                   # 경로 계산
GET  /api/v1/map/cluster                 # 마커 클러스터링
POST /api/v1/map/geocode                 # 주소 → 좌표
POST /api/v1/map/reverse-geocode         # 좌표 → 주소
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/map.py` - 지도 엔드포인트
- `backend/app/services/maps/kakao_map_service.py` - 카카오맵 연동
- `backend/app/services/maps/route_calculator.py` - 경로 계산

---

### 5.2 링크 분석 기능

**📚 참고 문서**:
- PRD: `prd/01-sns-link-analysis.md` (SNS 링크 분석)
- TRD: `trd/01-sns-link-analysis.md`

**🔌 Backend API 엔드포인트**:
```
POST /api/v1/links/analyze               # URL 분석
GET  /api/v1/links/{id}                  # 분석 결과 조회
GET  /api/v1/links/history               # 분석 히스토리
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/link_analysis.py` - 링크 분석
- `backend/app/services/places/content_extractor.py` - 콘텐츠 추출
- `backend/app/services/ai/gemini_analyzer_v2.py` - AI 분석

---

### 5.3 푸시 알림

**📚 참고 문서**:
- PRD: `prd/07-notification-system.md` (알림 시스템)
- TRD: `trd/07-notification-system.md`

**🔌 Backend API 엔드포인트**:
```
POST /api/v1/notifications/token         # FCM 토큰 등록
GET  /api/v1/notifications               # 알림 목록
PUT  /api/v1/notifications/{id}/read     # 알림 읽음 처리
POST /api/v1/notifications/settings      # 알림 설정
```

**Backend 파일 참고**:
- `backend/app/api/api_v1/endpoints/notifications.py` - 알림 엔드포인트
- `backend/app/services/notifications/fcm_service.py` - FCM 서비스
- `backend/app/services/notifications/notification_scheduler.py` - 알림 스케줄러

---

### 5.4 공유 기능

**📚 참고 문서**:
- PRD: `prd/05-sharing-system.md` (공유 시스템)
- TRD: `trd/05-sharing-system.md`

**🔌 Backend API 엔드포인트**:
```
POST /api/v1/places/{id}/share           # 장소 공유
POST /api/v1/courses/{id}/share          # 코스 공유
GET  /api/v1/share/{share_id}            # 공유 링크 접근
```

**Backend 파일 참고**:
- `backend/app/services/courses/course_sharing_service.py` - 공유 서비스

---

## 데이터 모델 참고

### Backend 스키마 → Flutter 모델 매핑

**Place 모델**:
- Backend: `backend/app/schemas/place.py`
- Flutter: `lib/shared/models/place.dart`

**Course 모델**:
- Backend: `backend/app/schemas/course.py`
- Flutter: `lib/shared/models/course.dart`

**User 모델**:
- Backend: `backend/app/schemas/user_data.py`
- Flutter: `lib/features/profile/data/models/user_model.dart`

**Search 관련**:
- Backend: `backend/app/schemas/search.py`
- Flutter: `lib/features/search/data/models/search_result.dart`

---

## API 호출 예시

### 장소 검색 (Search Screen)
```dart
// Flutter
final response = await dio.get('/api/v1/search', queryParameters: {
  'q': query,
  'category': selectedCategory,
  'distance': maxDistance,
  'lat': currentLat,
  'lng': currentLng,
});

// Backend 응답 참고: backend/app/schemas/search.py
```

### 코스 생성 (Course Builder)
```dart
// Flutter
final response = await dio.post('/api/v1/courses', data: {
  'title': courseTitle,
  'type': courseType,
  'places': places.map((p) => {
    'place_id': p.id,
    'order': p.order,
    'duration_minutes': p.duration.inMinutes,
  }).toList(),
});

// Backend 응답 참고: backend/app/schemas/course.py
```

---

## 환경 변수 설정

`.env.dev`:
```
API_BASE_URL=http://localhost:8000/api/v1
GOOGLE_MAPS_API_KEY=your_key_here
```

`.env.prod`:
```
API_BASE_URL=https://api.hotly.app/api/v1
GOOGLE_MAPS_API_KEY=your_prod_key
```

---

*작성일: 2025-01-XX*
*이 문서는 task/07-frontend.md의 상세 참고 자료입니다.*
