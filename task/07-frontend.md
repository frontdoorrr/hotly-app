# Task 07: Frontend Development (Flutter)

## 문서 정보
- **작성일**: 2025-01-XX
- **상태**: In Progress
- **우선순위**: P0 (Critical)
- **관련 문서**:
  - PRD: `prd/01-core-features.md`
  - TRD: `trd/frontend/01-flutter-tech-stack.md`
  - Design: `ui-design-system.md`
  - **상세 참고**: `task/07-frontend-detailed.md` ⭐ (API 엔드포인트 및 Backend 파일 매핑)

---

## 목표
화면 스펙 문서를 기반으로 Flutter 앱의 모든 화면을 구현하고, 백엔드 API와 연동합니다.

---

## Phase 1: 프로젝트 기반 구축 ✅

### 1.1 프로젝트 초기화 ✅
- [x] Flutter 프로젝트 생성 및 의존성 설정
- [x] 디렉토리 구조 생성 (Clean Architecture)
- [x] 환경 변수 설정 (.env.dev, .env.prod)

### 1.2 디자인 시스템 구현 ✅
- [x] 색상 팔레트 정의 (`lib/core/theme/app_colors.dart`)
- [x] 타이포그래피 시스템 (`lib/core/theme/app_text_styles.dart`)
- [x] 테마 설정 (Light/Dark) (`lib/core/theme/app_theme.dart`)
- [x] 공통 상수 (`lib/core/constants/app_constants.dart`)

### 1.3 라우팅 및 네비게이션 ✅
- [x] go_router 설정 (`lib/core/router/app_router.dart`)
- [x] 라우트 정의 (홈, 검색, 장소, 코스, 프로필)
- [x] 딥링크 처리 구조

### 1.4 공통 모델 및 위젯 ✅
- [x] Place 모델 (`lib/shared/models/place.dart`)
- [x] Course 모델 (`lib/shared/models/course.dart`)
- [x] Atomic 위젯 (AppButton, AppInput)

**완료 기준**: ✅ 프로젝트 빌드 성공, 테마 적용 확인

---

## Phase 2: 코드 생성 및 네트워킹 설정 ✅

### 2.1 코드 생성 (build_runner) ✅
- [x] freezed 모델 생성
  ```bash
  flutter pub run build_runner build --delete-conflicting-outputs
  ```
- [x] Riverpod 코드 생성
- [x] JSON serialization 생성

### 2.2 네트워킹 레이어 구현 ✅
- [x] Dio 클라이언트 설정 (`lib/core/network/dio_client.dart`)
- [x] API 엔드포인트 상수 (`lib/core/network/api_endpoints.dart`)
- [x] 인터셉터 구현 (로깅, 인증, 에러 처리)
- [x] 네트워크 에러 핸들링

### 2.3 로컬 스토리지 설정 ✅
- [x] SharedPreferences 래퍼 클래스 (`lib/core/storage/local_storage.dart`)
- [x] Secure Storage (토큰 저장)
- [x] main.dart에서 초기화

**완료 기준**: ✅ 코드 생성 성공, 네트워킹 레이어 구축 완료

---

## Phase 3: 화면 구현 (우선순위 순)

### 3.1 홈 화면 구현 ✅
**참고**: `docs/screens/home-screen-spec.md` | 📋 [상세 API](task/07-frontend-detailed.md#31-홈-화면-구현-)

- [x] **도메인 레이어**
  - [x] Place Entity (`lib/features/home/domain/entities/place.dart`)
  - [x] Repository Interface
  - [x] Use Cases (GetRecommendedPlaces, GetNearbyPlaces)

- [x] **데이터 레이어**
  - [x] Place DTO/Model (`lib/features/home/data/models/place_model.dart`)
  - [x] Remote Data Source (API)
  - [x] Repository Implementation

- [x] **프레젠테이션 레이어**
  - [x] Home Provider (Riverpod)
  - [x] Home Screen (`lib/features/home/presentation/screens/home_screen.dart`)
  - [x] 위젯 구현:
    - [x] QuickFilterChips (Quick Action Buttons)
    - [x] RecommendedPlacesCarousel (Horizontal List)
    - [x] PopularPlacesGrid
    - [x] PlaceCard (재사용 가능)

**완료 기준**: ✅
- ✅ 추천 장소 카드 렌더링
- ✅ 인기 장소 그리드 표시
- ✅ 빠른 액션 버튼
- ✅ Pull-to-refresh 동작

---

### 3.2 검색 화면 구현 ✅
**참고**: `docs/screens/search-screen-spec.md` | 📋 [상세 API](task/07-frontend-detailed.md#32-검색-화면-구현-)

- [x] **도메인 레이어**
  - [x] Search Use Cases (SearchPlaces, GetSearchSuggestions, SaveSearchHistory)

- [x] **데이터 레이어**
  - [x] Search Repository
  - [x] 검색 히스토리 로컬 저장

- [x] **프레젠테이션 레이어**
  - [x] Search Provider (검색 상태 관리)
  - [x] Search Screen (`lib/features/search/presentation/screens/search_screen.dart`)
  - [x] 위젯 구현:
    - [x] SearchBar (자동완성)
    - [x] SearchHistory (최근 검색어)
    - [x] AutocompleteSuggestions (자동완성 오버레이)
    - [x] SearchResultsList (PlaceCard 재사용)
    - [x] PopularSearches (인기 검색어)

**완료 기준**: ✅
- ✅ 실시간 검색 제안 표시 (자동완성 오버레이)
- ✅ 검색 히스토리 저장/불러오기 (LocalStorage)
- ✅ 검색 결과 리스트 표시
- ✅ 인기 검색어 및 최근 검색어 UI

---

### 3.3 장소 상세 화면 구현 ✅
**참고**: `docs/screens/place-detail-screen-spec.md` | 📋 [상세 API](task/07-frontend-detailed.md#33-장소-상세-화면-구현-)

- [x] **도메인 레이어**
  - [x] Place Detail Use Cases (GetPlaceDetail, LikePlace, SavePlace)

- [x] **데이터 레이어**
  - [x] Place Detail Repository
  - [x] 좋아요/저장 상태 관리 (Optimistic UI)

- [x] **프레젠테이션 레이어**
  - [x] Place Detail Provider
  - [x] Place Detail Screen (`lib/features/place/presentation/screens/place_detail_screen.dart`)
  - [x] 위젯 구현:
    - [x] ImageGallery (PageView + Hero 애니메이션)
    - [x] PlaceInfo (이름, 평점, 태그, 주소)
    - [x] ActionButtons (좋아요, 저장, 공유, 코스 추가)
    - [x] 지도/경로 버튼 (Kakao Map/Google Maps)
    - [x] RelatedPlaces (비슷한 장소 리스트)

**완료 기준**: ✅
- ✅ 이미지 갤러리 스와이프 (PageView + 인디케이터)
- ✅ 좋아요/저장 토글 동작 (Optimistic UI)
- ✅ 코스에 추가 버튼 (바텀시트)
- ✅ 지도 보기/경로 찾기 (URL scheme)
- ✅ 비슷한 장소 추천
- ✅ 공유 기능

---

### 3.4 코스 빌더 화면 구현 ✅
**참고**: `docs/screens/course-builder-screen-spec.md` | 📋 [상세 API](task/07-frontend-detailed.md#34-코스-빌더-화면-구현-)

- [x] **도메인 레이어**
  - [x] Course Entity
  - [x] Create/Update Course Use Cases

- [x] **데이터 레이어**
  - [x] Course Repository (TODO: API 연동)

- [x] **프레젠테이션 레이어**
  - [x] Course Builder Provider ✅
  - [x] Course Builder Screen ✅
  - [x] 위젯 구현:
    - [x] CoursePlaceCard (드래그 가능) ✅
    - [x] RouteInfoCard (경로 정보) ✅
    - [x] DurationSlider (체류 시간 조정) ✅
    - [x] CourseTypeChips ✅

**완료 기준**: ✅
- [x] 드래그 앤 드롭 순서 변경
- [x] 체류 시간 조정
- [x] 총 소요 시간 자동 계산
- [ ] API 연동 (저장 기능)

---

### 3.5 프로필 화면 구현 ✅
**참고**: `docs/screens/profile-screen-spec.md` | 📋 [상세 API](task/07-frontend-detailed.md#35-프로필-화면-구현-)

- [x] **모델 레이어**
  - [x] User Entity (freezed + json_serializable)
  - [x] UserStats Entity

- [x] **프레젠테이션 레이어**
  - [x] Profile Provider (사용자 정보 + 통계)
  - [x] Settings Provider (앱 설정 관리)
  - [x] Profile Screen (`lib/features/profile/presentation/screens/profile_screen.dart`)
  - [x] 위젯 구현:
    - [x] UserInfoSection (프로필 이미지, 이름, 이메일)
    - [x] StatsSection (저장/좋아요/코스 통계)
    - [x] TabBar (저장된 장소 / 내 코스)
    - [x] SettingsSheet (바텀시트)
    - [x] ThemeSelector (다이얼로그)
    - [x] LanguageSelector (다이얼로그)

**완료 기준**: ✅
- ✅ 사용자 정보 표시 (Mock 데이터)
- ✅ 통계 카드 표시 및 네비게이션
- ✅ 탭 뷰 (저장된 장소 / 내 코스)
- ✅ 설정 바텀시트 (알림, 테마, 언어)
- ✅ 테마 변경 LocalStorage 저장
- ✅ 로그아웃 기능 (LocalStorage 초기화)
- ✅ 앱 정보 표시 (package_info_plus)

---

## Phase 4: 인증 및 온보딩 (Supabase Auth)

### 4.1 인증 플로우 🔐
**참고**: `docs/screens/auth-screen-spec.md` | Backend: Supabase Auth

- [ ] **Supabase Auth 설정**
  - [ ] supabase_flutter 패키지 설치
  - [ ] Supabase 클라이언트 초기화 (`lib/core/auth/supabase_client.dart`)
  - [ ] 환경 변수 설정 (SUPABASE_URL, SUPABASE_ANON_KEY)

- [ ] **도메인 레이어**
  - [ ] AuthRepository 인터페이스
  - [ ] User Entity (기존 확장)
  - [ ] Auth Use Cases (SignIn, SignUp, SignOut, GetCurrentUser)

- [ ] **데이터 레이어**
  - [ ] Supabase Auth Data Source
  - [ ] AuthRepository 구현

- [ ] **프레젠테이션 레이어**
  - [ ] Auth State Provider (로그인 상태 전역 관리)
  - [ ] Login Screen (`lib/features/auth/presentation/screens/login_screen.dart`)
    - [ ] 이메일/비밀번호 로그인
    - [ ] Google OAuth (Supabase)
    - [ ] Apple OAuth (Supabase)
    - [ ] "회원가입" 버튼
  - [ ] Sign Up Screen
    - [ ] 이메일/비밀번호 회원가입
    - [ ] 이메일 인증 안내
  - [ ] Auth Guard (라우팅 보호)

### 4.2 온보딩 플로우
- [ ] Onboarding Screen (`lib/features/onboarding/presentation/screens/onboarding_screen.dart`)
  - [ ] 관심사 선택 (Step 1)
  - [ ] 선호 카테고리 (Step 2)
  - [ ] 위치 권한 요청 (Step 3)
  - [ ] 알림 권한 요청 (Step 4)
  - [ ] 완료 화면 (Step 5)
- [ ] Progress Indicator
- [ ] Skip 기능

**완료 기준**:
- ✓ Supabase Auth 로그인/로그아웃 동작
- ✓ OAuth 소셜 로그인 (Google, Apple)
- ✓ 이메일 인증 플로우
- ✓ Auth State 전역 관리 (Riverpod)
- ✓ 온보딩 스텝 진행
- ✓ 첫 실행 시에만 온보딩 표시
- ✓ 인증 필요 화면 라우팅 보호

---

## Phase 5: 고급 기능 구현

### 5.1 지도 기능
- [ ] Google Maps 초기화
- [ ] 현재 위치 표시
- [ ] 장소 마커 표시
- [ ] 마커 클러스터링
- [ ] 경로 그리기 (Polyline)
- [ ] 지도 컨트롤 (줌, 현재 위치, 지도 타입)

### 5.2 링크 분석 기능
- [ ] Link Input Bottom Sheet
- [ ] URL 유���성 검사
- [ ] 분석 결과 표시
- [ ] 장소 추출 결과 → 장소 상세로 이동

### 5.3 푸시 알림
- [ ] FCM 초기화
- [ ] 토큰 저장
- [ ] Foreground 알림 처리
- [ ] Background 알림 처리
- [ ] 알림 클릭 시 화면 이동

### 5.4 공유 기능
- [ ] 장소 공유 (딥링크 생성)
- [ ] 코스 공유
- [ ] 다이나믹 링크 처리

---

## Phase 6: 최적화 및 테스트

### 6.1 성능 최적화
- [ ] 이미지 캐싱 (cached_network_image)
- [ ] 무한 스크롤 최적화 (pagination)
- [ ] 불필요한 리빌드 방지 (const, memo)
- [ ] 번들 사이즈 최적화

### 6.2 에러 처리
- [ ] Error Boundary (전역 에러 처리)
- [ ] Network Error UI
- [ ] Empty State UI
- [ ] Loading State UI

### 6.3 접근성
- [ ] Semantic Labels
- [ ] 스크린리더 테스트
- [ ] 색상 대비 검증 (WCAG AA)
- [ ] 최소 터치 타겟 (44dp) 검증

### 6.4 테스트 작성
- [ ] 위젯 테스트 (주요 화면)
- [ ] 통합 테스트 (주요 플로우)
- [ ] Golden 테스트 (UI 스냅샷)
- [ ] Provider 유닛 테스트

---

## Phase 7: 배포 준비

### 7.1 앱 설정
- [ ] 앱 아이콘 설정
- [ ] 스플래시 스크린
- [ ] 앱 이름 및 번들 ID
- [ ] 버전 관리

### 7.2 빌드 설정
- [ ] Android 빌드 설정 (build.gradle)
- [ ] iOS 빌드 설정 (Info.plist)
- [ ] 프로덕션 환경 변수
- [ ] 난독화 설정

### 7.3 스토어 제출
- [ ] 스크린샷 준비 (5.5", 6.5")
- [ ] 앱 설명 작성
- [ ] 개인정보 처리방침
- [ ] 테스트 플라이트 배포 (iOS)
- [ ] 내부 테스트 트랙 배포 (Android)

---

## 개발 가이드라인

### 코딩 규칙
1. **파일명**: `snake_case` (예: `home_screen.dart`)
2. **클래스명**: `PascalCase` (예: `HomeScreen`)
3. **변수/함수**: `camelCase` (예: `getUserProfile()`)
4. **상수**: `lowerCamelCase` with const (예: `const maxRetries = 3`)

### 상태 관리 패턴
```dart
// Provider 정의
final homeProvider = StateNotifierProvider.autoDispose<HomeNotifier, HomeState>((ref) {
  return HomeNotifier(ref.read(placeRepositoryProvider));
});

// State 클래스 (freezed)
@freezed
class HomeState with _$HomeState {
  const factory HomeState({
    @Default([]) List<Place> recommendedPlaces,
    @Default([]) List<Place> nearbyPlaces,
    @Default(false) bool isLoading,
    String? error,
  }) = _HomeState;
}
```

### 에러 처리 패턴
```dart
// Repository 레벨
Future<Either<Failure, List<Place>>> getPlaces() async {
  try {
    final result = await remoteDataSource.getPlaces();
    return Right(result);
  } on ServerException {
    return Left(ServerFailure());
  } on NetworkException {
    return Left(NetworkFailure());
  }
}

// Presentation 레벨
state.when(
  data: (places) => PlacesList(places: places),
  loading: () => LoadingIndicator(),
  error: (error) => ErrorWidget(error: error),
);
```

---

## 체크리스트

### 각 화면 구현 시
- [ ] 스펙 문서 리뷰
- [ ] 도메인 레이어 구현 (Entity, Use Case)
- [ ] 데이터 레이어 구현 (Repository, Data Source)
- [ ] 프레젠테이션 레이어 구현 (Provider, Screen, Widgets)
- [ ] 에러 처리 구현
- [ ] 로딩 상태 구현
- [ ] Empty 상태 구현
- [ ] 위젯 테스트 작성
- [ ] 접근성 검증

### 통합 전
- [ ] 빌드 성공 확인
- [ ] 주요 플로우 수동 테스트
- [ ] 메모리 누수 확인
- [ ] 네트워크 에러 시나리오 테스트
- [ ] 다크모드 동작 확인

---

## 진행 상황

| Phase | 완료율 | 상태 |
|-------|--------|------|
| Phase 1: 프로젝트 기반 | 100% | ✅ 완료 |
| Phase 2: 코드 생성 & 네트워킹 | 100% | ✅ 완료 |
| Phase 3: 화면 구현 | 20% | 🔄 진행중 |
| Phase 4: 인증 & 온보딩 | 0% | 🔜 대기 |
| Phase 5: 고급 기능 | 0% | 🔜 대기 |
| Phase 6: 최적화 & 테스트 | 0% | 🔜 대기 |
| Phase 7: 배포 준비 | 0% | 🔜 대기 |

**전체 진행률**: 30%

---

## 다음 액션 아이템

1. **즉시 진행**
   - [x] freezed 코드 생성 (`build_runner`) ✅
   - [x] Dio 클라이언트 설정 ✅
   - [x] 로컬 스토리지 설정 ✅
   - [ ] 홈 화면 구현 시작

2. **이번 주**
   - [ ] 홈 화면 구현 완료
   - [ ] 검색 화면 구현 시작
   - [ ] 라우터에 실제 화면 연결

3. **다음 주**
   - [ ] 장소 상세 화면 구현
   - [ ] 프로필 화면 구현
   - [ ] 인증 플로우 구현

---

*작성일: 2025-01-XX*
*업데이트: 2025-01-XX*
