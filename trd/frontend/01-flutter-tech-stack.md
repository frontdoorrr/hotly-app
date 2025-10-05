# TRD-Frontend-01: Flutter 기술 스택 및 아키텍처 (Flutter Tech Stack & Architecture)

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **작성자**: Development Team
- **관련 PRD**: `prd/main.md`, `prd/06-onboarding-flow.md`
- **관련 Task**: `task/06-ui-frontend.md`

## 목차
1. [개요](#1-개요)
2. [기술 스택 선정](#2-기술-스택-선정)
3. [아키텍처 패턴](#3-아키텍처-패턴)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [의존성 관리](#5-의존성-관리)
6. [개발 환경 설정](#6-개발-환경-설정)
7. [빌드 및 배포 전략](#7-빌드-및-배포-전략)
8. [품질 보증](#8-품질-보증)

---

## 1. 개요

### 1.1 목적
hotly-app의 모바일 애플리케이션을 위한 기술 스택, 아키텍처 패턴, 개발 환경을 정의하여 일관되고 확장 가능한 개발 기반을 구축한다.

### 1.2 사용자 가치
- **크로스 플랫폼**: iOS/Android 동시 지원으로 더 많은 사용자에게 도달
- **네이티브 성능**: 60fps 버터 스무스 UI로 우수한 사용자 경험
- **빠른 개발**: Hot Reload로 개발 생산성 3배 향상
- **안정성**: TDD 기반 개발로 버그 발생률 80% 감소

### 1.3 가설 및 KPI
- **가설**: Flutter 기반 크로스 플랫폼 개발로 개발 시간 50% 단축, 코드 재사용률 90% 달성
- **측정 지표**:
  - 개발 속도: iOS/Android 동시 릴리즈 (단일 코드베이스)
  - 성능: 앱 시작 시간 3초 이내, 화면 전환 60fps 유지
  - 안정성: 크래시율 0.1% 이하, 테스트 커버리지 80% 이상
  - 번들 크기: APK 50MB 이하, IPA 100MB 이하

---

## 2. 기술 스택 선정

### 2.1 핵심 프레임워크

#### Flutter SDK
```yaml
선정 이유:
  - 크로스 플랫폼 단일 코드베이스로 개발 효율성 극대화
  - 60fps 네이티브급 성능 보장
  - 풍부한 Material Design/Cupertino 위젯 제공
  - Hot Reload로 개발 생산성 향상
  - Google 공식 지원 및 활발한 커뮤니티

버전: ^3.19.0 (2024 Q4 기준)
채널: stable
최소 Dart SDK: ^3.3.0
```

#### 플랫폼 지원
```yaml
Android:
  minSdkVersion: 21 (Android 5.0 Lollipop, 2014년)
  targetSdkVersion: 34 (Android 14)
  compileSdkVersion: 34

iOS:
  minimumOSVersion: 13.0 (iOS 13, 2019년)
  targetOS: 17.0

웹 (Optional - Phase 2):
  지원: Flutter Web
  렌더러: CanvasKit (성능 우선)
```

**선정 근거**:
- Android 21 이상: 글로벌 사용자 기기의 99.5% 커버
- iOS 13 이상: 활성 iOS 기기의 95% 커버
- Material You (Android 12+), iOS 디자인 가이드라인 네이티브 지원

### 2.2 상태 관리

#### Riverpod 2.x (메인 상태 관리)
```dart
// 선정 이유
선택: flutter_riverpod ^2.4.0

장점:
  - 컴파일 타임 안전성 (Provider 타입 체크)
  - 전역 상태 없이 의존성 주입 (DI)
  - 테스트 용이성 (Mock/Override 간편)
  - 불필요한 리빌드 최소화 (세밀한 선택적 구독)
  - 자동 dispose로 메모리 누수 방지

대안 검토:
  - Provider: 기능이 제한적, Riverpod의 전신
  - BLoC: 보일러플레이트 코드 과다
  - GetX: 비표준적 패턴, 의존성 주입 불투명
```

**상태 관리 전략**:
```dart
// 1. StateProvider: 단순 상태 (카운터, 토글 등)
final filterStateProvider = StateProvider<FilterState>((ref) {
  return FilterState.initial();
});

// 2. StateNotifierProvider: 복잡한 상태 + 비즈니스 로직
final placesProvider = StateNotifierProvider<PlacesNotifier, PlacesState>((ref) {
  return PlacesNotifier(ref.read(placeRepositoryProvider));
});

// 3. FutureProvider: 비동기 데이터 로딩
final placeDetailProvider = FutureProvider.family<Place, String>((ref, id) {
  return ref.read(placeRepositoryProvider).getPlace(id);
});

// 4. StreamProvider: 실시간 업데이트 (WebSocket, FCM)
final notificationsProvider = StreamProvider<List<Notification>>((ref) {
  return ref.read(notificationServiceProvider).notificationStream();
});
```

#### GetIt (의존성 주입 - 서비스 레이어)
```dart
// 선정 이유
선택: get_it ^7.6.0

용도:
  - Repository, Service, API Client 등 싱글톤 관리
  - Riverpod과 상호 보완 (Riverpod은 UI 상태, GetIt은 서비스)
  - 테스트 시 Mock 객체 교체 용이

예시:
final getIt = GetIt.instance;

void setupDependencies() {
  // Singleton
  getIt.registerSingleton<ApiClient>(ApiClient());
  getIt.registerSingleton<SecureStorage>(SecureStorage());

  // Lazy Singleton (최초 사용 시 생성)
  getIt.registerLazySingleton<PlaceRepository>(
    () => PlaceRepositoryImpl(getIt<ApiClient>())
  );

  // Factory (매번 새 인스턴스)
  getIt.registerFactory<PlaceService>(
    () => PlaceService(getIt<PlaceRepository>())
  );
}
```

### 2.3 네트워킹 및 데이터

#### HTTP 통신
```dart
// Dio - Advanced HTTP Client
선택: dio ^5.4.0

장점:
  - Interceptor로 인증 토큰 자동 주입
  - 요청/응답 로깅, 타임아웃 관리
  - FormData, 파일 업로드 지원
  - 재시도 로직 (dio_smart_retry)
  - 네이티브 Adapter 지원 (성능 최적화)

설정 예시:
class ApiClient {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'https://api.hotly.app',
    connectTimeout: Duration(seconds: 10),
    receiveTimeout: Duration(seconds: 30),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ));

  ApiClient() {
    _dio.interceptors.addAll([
      AuthInterceptor(),      // 토큰 자동 주입
      LoggingInterceptor(),   // 디버그 로깅
      RetryInterceptor(),     // 재시도 로직
      ErrorInterceptor(),     // 에러 핸들링
    ]);
  }
}
```

#### JSON 직렬화
```dart
// Freezed + json_serializable
선택:
  - freezed: ^2.4.0 (불변 모델 생성)
  - freezed_annotation: ^2.4.0
  - json_serializable: ^6.7.0
  - json_annotation: ^4.8.0

장점:
  - 불변성 보장 (Data Class)
  - copyWith, ==, hashCode 자동 생성
  - Union Types (sealed class) 지원
  - JSON 직렬화/역직렬화 코드 생성
  - null safety 완벽 지원

모델 예시:
@freezed
class Place with _$Place {
  const factory Place({
    required String id,
    required String name,
    required LatLng location,
    required PlaceCategory category,
    String? description,
    List<String>? images,
    @Default(0) int likeCount,
    @Default(false) bool isLiked,
  }) = _Place;

  factory Place.fromJson(Map<String, dynamic> json) => _$PlaceFromJson(json);
}

// Union Type for API Response
@freezed
class ApiResult<T> with _$ApiResult<T> {
  const factory ApiResult.success(T data) = Success<T>;
  const factory ApiResult.failure(String error, {int? code}) = Failure<T>;
  const factory ApiResult.loading() = Loading<T>;
}
```

#### 로컬 데이터베이스
```dart
// SQLite - 오프라인 지원, 복잡한 쿼리
선택: sqflite ^2.3.0

용도:
  - 저장된 장소/코스 캐싱
  - 오프라인 모드 데이터
  - 검색 히스토리
  - 필터 상태 영속화

// Hive - 빠른 Key-Value 저장소
선택: hive ^2.2.3, hive_flutter ^1.1.0

용도:
  - 사용자 설정 (테마, 언어 등)
  - 인증 토큰 (암호화)
  - 간단한 캐시 데이터
```

### 2.4 UI 및 위젯

#### 디자인 시스템
```dart
// Material Design 3 (Material You)
선택: Built-in Material 3 지원

장점:
  - Dynamic Color (시스템 색상 자동 적용)
  - Adaptive Components (플랫폼별 최적화)
  - 풍부한 Material Widgets

// Cupertino (iOS 스타일)
선택: Built-in Cupertino Widgets

전략: Adaptive Widgets (플랫폼 자동 감지)
```

#### 애니메이션
```dart
// 기본 Animation
선택: Built-in Animation Framework

// 고급 애니메이션
선택: flutter_animate ^4.3.0

장점:
  - 선언적 애니메이션 API
  - 60fps 보장
  - 복잡한 시퀀스 애니메이션 간편 구현

예시:
Text('Hello')
  .animate()
  .fadeIn(duration: 300.ms)
  .slideY(begin: -20, end: 0)
  .shimmer(delay: 300.ms, duration: 1500.ms);
```

#### 리스트 최적화
```dart
// Infinite Scroll + Lazy Loading
선택: infinite_scroll_pagination ^4.0.0

장점:
  - 자동 페이지네이션
  - 로딩/에러 상태 관리
  - Pull-to-Refresh 통합

// Sticky Header
선택: sticky_headers ^0.3.0

용도: 검색 결과, 코스 타임라인 등
```

### 2.5 지도 및 위치

#### 지도 SDK
```dart
// Kakao Map Flutter Plugin
선택: kakao_map_plugin ^0.5.0 (커뮤니티)

대안:
  - Google Maps: flutter_google_maps ^2.2.0
  - 선택 기준: 한국 지도 정확도, 주소 검색 품질

// 위치 서비스
선택:
  - geolocator ^10.1.0 (GPS, 네트워크 위치)
  - geocoding ^2.1.0 (주소 ↔ 좌표 변환)
```

### 2.6 인증 및 알림

#### Firebase 통합
```dart
// Firebase Core
선택:
  - firebase_core: ^2.24.0
  - firebase_auth: ^4.16.0 (소셜 로그인)
  - firebase_messaging: ^14.7.0 (FCM Push)
  - firebase_analytics: ^10.8.0 (사용자 분석)
  - firebase_crashlytics: ^3.4.0 (크래시 리포팅)

// 소셜 로그인
선택:
  - google_sign_in: ^6.2.0
  - sign_in_with_apple: ^5.0.0 (iOS 필수)
```

### 2.7 이미지 처리

```dart
// 이미지 로딩 및 캐싱
선택: cached_network_image ^3.3.0

장점:
  - 자동 캐싱 (메모리 + 디스크)
  - Placeholder, Error Widget
  - Progressive Loading

// 이미지 최적화
선택: flutter_image_compress ^2.1.0

용도: 사용자 업로드 이미지 압축 (3MB → 500KB)
```

### 2.8 유틸리티

```dart
// 날짜/시간
선택: intl ^0.19.0

// 권한 관리
선택: permission_handler ^11.1.0

// 공유 기능
선택: share_plus ^7.2.0

// URL 런처
선택: url_launcher ^6.2.0

// 로컬 스토리지 (간단한 Key-Value)
선택: shared_preferences ^2.2.0

// 보안 저장소 (토큰, 민감정보)
선택: flutter_secure_storage ^9.0.0
```

---

## 3. 아키텍처 패턴

### 3.1 Clean Architecture + MVVM

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (Views + ViewModels + Widgets)         │
│                                         │
│  - UI 렌더링 및 사용자 인터랙션          │
│  - StateNotifier로 상태 관리            │
│  - Riverpod Provider로 ViewModel 주입   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│          Domain Layer                   │
│  (Entities + Use Cases + Repository     │
│   Interfaces)                           │
│                                         │
│  - 비즈니스 로직 (플랫폼 독립적)         │
│  - Entity: 핵심 데이터 모델             │
│  - Use Case: 단일 책임 비즈니스 로직    │
│  - Repository Interface: 데이터 계약    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│           Data Layer                    │
│  (Repository Impl + Data Sources)       │
│                                         │
│  - API 통신 (Remote Data Source)        │
│  - 로컬 DB (Local Data Source)          │
│  - 캐싱 전략 구현                       │
│  - DTO ↔ Entity 변환                    │
└─────────────────────────────────────────┘
```

### 3.2 레이어별 책임

#### Presentation Layer
```dart
// ViewModel (StateNotifier)
class PlaceListViewModel extends StateNotifier<PlaceListState> {
  final GetPlacesUseCase _getPlaces;
  final LikePlaceUseCase _likePlace;

  PlaceListViewModel(this._getPlaces, this._likePlace)
    : super(PlaceListState.initial());

  Future<void> loadPlaces({FilterOptions? filter}) async {
    state = state.copyWith(isLoading: true);

    final result = await _getPlaces(filter: filter);

    result.when(
      success: (places) => state = state.copyWith(
        places: places,
        isLoading: false,
      ),
      failure: (error) => state = state.copyWith(
        error: error,
        isLoading: false,
      ),
    );
  }

  Future<void> toggleLike(String placeId) async {
    await _likePlace(placeId: placeId);
    // Optimistic Update
    state = state.copyWith(
      places: state.places.map((p) =>
        p.id == placeId ? p.copyWith(isLiked: !p.isLiked) : p
      ).toList(),
    );
  }
}

// View
class PlaceListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(placeListViewModelProvider);

    return Scaffold(
      body: state.when(
        loading: () => LoadingIndicator(),
        error: (error) => ErrorView(error),
        success: (places) => PlaceListView(places),
      ),
    );
  }
}
```

#### Domain Layer
```dart
// Entity (순수 Dart 클래스, Flutter 의존성 없음)
class Place {
  final String id;
  final String name;
  final LatLng location;
  final PlaceCategory category;

  Place({required this.id, required this.name, ...});
}

// Repository Interface (추상화)
abstract class PlaceRepository {
  Future<Result<List<Place>>> getPlaces({FilterOptions? filter});
  Future<Result<Place>> getPlaceById(String id);
  Future<Result<void>> likePlace(String id);
}

// Use Case (단일 책임)
class GetPlacesUseCase {
  final PlaceRepository repository;

  GetPlacesUseCase(this.repository);

  Future<Result<List<Place>>> call({FilterOptions? filter}) async {
    return await repository.getPlaces(filter: filter);
  }
}
```

#### Data Layer
```dart
// Repository Implementation
class PlaceRepositoryImpl implements PlaceRepository {
  final PlaceRemoteDataSource remoteDataSource;
  final PlaceLocalDataSource localDataSource;
  final ConnectivityService connectivity;

  PlaceRepositoryImpl(this.remoteDataSource, this.localDataSource, this.connectivity);

  @override
  Future<Result<List<Place>>> getPlaces({FilterOptions? filter}) async {
    try {
      // 1. 네트워크 확인
      if (await connectivity.isConnected) {
        // 2. API 호출
        final placeDTOs = await remoteDataSource.getPlaces(filter);
        final places = placeDTOs.map((dto) => dto.toEntity()).toList();

        // 3. 로컬 캐시 저장
        await localDataSource.cachePlaces(places);

        return Result.success(places);
      } else {
        // 4. 오프라인 - 캐시 반환
        final cachedPlaces = await localDataSource.getCachedPlaces(filter);
        return Result.success(cachedPlaces);
      }
    } catch (e) {
      return Result.failure(e.toString());
    }
  }
}

// Data Source (API 통신)
class PlaceRemoteDataSource {
  final ApiClient apiClient;

  Future<List<PlaceDTO>> getPlaces(FilterOptions? filter) async {
    final response = await apiClient.get('/api/v1/places', queryParameters: {
      'category': filter?.category?.name,
      'minRating': filter?.minRating,
    });

    return (response.data['places'] as List)
        .map((json) => PlaceDTO.fromJson(json))
        .toList();
  }
}
```

### 3.3 의존성 방향

```
┌───────────────┐
│  Presentation │ ───depends on───┐
└──────��────────┘                 │
                                  ▼
                          ┌───────────────┐
                          │    Domain     │
                          └───────────────┘
                                  ▲
┌───────────────┐                 │
│      Data     │ ───implements───┘
└───────────────┘

규칙:
- Presentation → Domain (ViewModel은 Use Case 사용)
- Data → Domain (Repository Impl은 Interface 구현)
- Domain → 외부 의존 없음 (순수 Dart)
```

---

## 4. 프로젝트 구조

### 4.1 디렉토리 구조 (Feature-First)

```
frontend/
├── lib/
│   ├── main.dart                    # 앱 진입점
│   ├── app.dart                     # MaterialApp 설정
│   │
│   ├── core/                        # 공통 인프라
│   │   ├── config/
│   │   │   ├── app_config.dart      # 환경별 설정 (dev/prod)
│   │   │   └── theme_config.dart    # 테마 설정
│   │   ├── constants/
│   │   │   ├── api_constants.dart   # API 엔드포인트
│   │   │   ├── app_constants.dart   # 앱 상수
│   │   │   └── asset_constants.dart # 이미지/아이콘 경로
│   │   ├── di/
│   │   │   └── injection.dart       # GetIt 의존성 주입
│   │   ├── error/
│   │   │   ├── failures.dart        # 에러 타입 정의
│   │   │   └── exceptions.dart      # 커스텀 예외
│   │   ├── network/
│   │   │   ├── api_client.dart      # Dio 설정
│   │   │   └── interceptors/        # HTTP 인터셉터
│   │   ├── router/
│   │   │   └── app_router.dart      # go_router 설정
│   │   └── utils/
│   │       ├── logger.dart          # 로깅 유틸
│   │       ├── validators.dart      # 입력 검증
│   │       └── extensions.dart      # Dart 확장
│   │
│   ├── features/                    # 기능별 모듈
│   │   ├── auth/                    # 인증 기능
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── auth_remote_datasource.dart
│   │   │   │   │   └── auth_local_datasource.dart
│   │   │   │   ├── models/
│   │   │   │   │   └── user_dto.dart
│   │   │   │   └── repositories/
│   │   │   │       └── auth_repository_impl.dart
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   └── user.dart
│   │   │   │   ├── repositories/
│   │   │   │   │   └── auth_repository.dart
│   │   │   │   └── usecases/
│   │   │   │       ├── login_usecase.dart
│   │   │   │       └── logout_usecase.dart
│   │   │   └── presentation/
│   │   │       ├── providers/
│   │   │       │   └── auth_provider.dart
│   │   │       ├── screens/
│   │   │       │   ├── login_screen.dart
│   │   │       │   └── signup_screen.dart
│   │   │       └── widgets/
│   │   │           └── auth_button.dart
│   │   │
│   │   ├── home/                    # 홈 화면
│   │   │   ├── data/
│   │   │   ├── domain/
│   │   │   └── presentation/
│   │   │
│   │   ├── places/                  # 장소 관리
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   ├── models/
│   │   │   │   │   └── place_dto.dart
│   │   │   │   └── repositories/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   └── place.dart
│   │   │   │   ├── repositories/
│   │   │   │   └── usecases/
│   │   │   │       ├── get_places_usecase.dart
│   │   │   │       ├── like_place_usecase.dart
│   │   │   │       └── save_place_usecase.dart
│   │   │   └── presentation/
│   │   │       ├── providers/
│   │   │       │   ├── place_list_provider.dart
│   │   │       │   └── place_detail_provider.dart
│   │   │       ├── screens/
│   │   │       │   ├── place_list_screen.dart
│   │   │       │   └── place_detail_screen.dart
│   │   │       └── widgets/
│   │   │           ├── place_card.dart
│   │   │           └── place_filter_panel.dart
│   │   │
│   │   ├── courses/                 # 코스 관리
│   │   ├── search/                  # 검색 기능
│   │   ├── link_analysis/           # 링크 분석
│   │   ├── map/                     # 지도 기능
│   │   └── profile/                 # 프로필 및 설정
│   │
│   └── shared/                      # 공유 위젯 및 유틸
│       ├── widgets/
│       │   ├── buttons/
│       │   │   ├── primary_button.dart
│       │   │   └── icon_button.dart
│       │   ├── inputs/
│       │   │   ├── text_field.dart
│       │   │   └── search_bar.dart
│       │   ├── cards/
│       │   │   └── base_card.dart
│       │   ├── dialogs/
│       │   │   └── confirmation_dialog.dart
│       │   └── common/
│       │       ├── loading_indicator.dart
│       │       ├── error_view.dart
│       │       └── empty_state.dart
│       └── providers/
│           └── theme_provider.dart
│
├── test/                            # 테스트 코드
│   ├── unit/                        # 단위 테스트
│   │   ├── features/
│   │   │   └── places/
│   │   │       ├── domain/
│   │   │       │   └── usecases/
│   │   │       │       └── get_places_usecase_test.dart
│   │   │       └── data/
│   │   │           └── repositories/
│   │   │               └── place_repository_impl_test.dart
│   │   └── core/
│   │       └── utils/
│   │           └── validators_test.dart
│   ├── widget/                      # 위젯 테스트
│   │   └── features/
│   │       └── places/
│   │           └── presentation/
│   │               └── widgets/
│   │                   └── place_card_test.dart
│   ├── integration/                 # 통합 테스트
│   │   └── features/
│   │       └── places/
│   │           └── place_flow_test.dart
│   └── fixtures/                    # 테스트 데이터
│       ├── place_fixture.dart
│       └── user_fixture.dart
│
├── assets/                          # 앱 리소스
│   ├── images/
│   │   ├── logo/
│   │   ├── onboarding/
│   │   └── placeholder/
│   ├── icons/
│   ├── fonts/
│   │   └── Pretendard/
│   └── animations/
│       └── lottie/
│
├── android/                         # Android 네이티브 코드
├── ios/                             # iOS 네이티브 코드
├── web/                             # Web 설정 (Optional)
│
├── pubspec.yaml                     # 패키지 의존성
├── analysis_options.yaml            # Lint 규칙
├── .env.dev                         # 개�� 환경 변수
├── .env.prod                        # 프로덕션 환경 변수
└── README.md                        # 프로젝트 문서
```

### 4.2 파일 네이밍 규칙 (rules.md 준수)

```yaml
디렉토리/파일: snake_case
  - place_repository_impl.dart ✓
  - PlaceRepositoryImpl.dart ✗

클래스/Enum: PascalCase
  - class PlaceRepository
  - enum PlaceCategory

메서드/변수: lowerCamelCase
  - Future<void> getPlaces()
  - final String userName

상수: lowerCamelCase (const)
  - const primaryColor = Color(0xFFE53E3E);
  - const apiTimeout = Duration(seconds: 10);

Private: _prefix
  - class _PlaceCardState
  - final _dio = Dio();
```

---

## 5. 의존성 관리

### 5.1 pubspec.yaml 구조

```yaml
name: hotly_app
description: AI 기반 핫플레이스 아카이빙 앱
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: ^3.3.0
  flutter: ^3.19.0

# ========== Core Dependencies ==========
dependencies:
  flutter:
    sdk: flutter

  # 상태 관리
  flutter_riverpod: ^2.4.0
  get_it: ^7.6.0

  # 네트워킹
  dio: ^5.4.0
  dio_smart_retry: ^6.0.0
  connectivity_plus: ^5.0.0

  # 데이터 모델
  freezed_annotation: ^2.4.0
  json_annotation: ^4.8.0

  # 로컬 스토리지
  sqflite: ^2.3.0
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  shared_preferences: ^2.2.0
  flutter_secure_storage: ^9.0.0

  # UI/UX
  flutter_animate: ^4.3.0
  cached_network_image: ^3.3.0
  infinite_scroll_pagination: ^4.0.0
  sticky_headers: ^0.3.0
  shimmer: ^3.0.0

  # 라우팅
  go_router: ^13.0.0

  # Firebase
  firebase_core: ^2.24.0
  firebase_auth: ^4.16.0
  firebase_messaging: ^14.7.0
  firebase_analytics: ^10.8.0
  firebase_crashlytics: ^3.4.0

  # 소셜 로그인
  google_sign_in: ^6.2.0
  sign_in_with_apple: ^5.0.0

  # 지도/위치
  kakao_map_plugin: ^0.5.0
  geolocator: ^10.1.0
  geocoding: ^2.1.0

  # 유틸리티
  intl: ^0.19.0
  permission_handler: ^11.1.0
  share_plus: ^7.2.0
  url_launcher: ^6.2.0
  image_picker: ^1.0.0
  flutter_image_compress: ^2.1.0

  # 로깅
  logger: ^2.0.0

# ========== Dev Dependencies ==========
dev_dependencies:
  flutter_test:
    sdk: flutter

  # 코드 생성
  build_runner: ^2.4.0
  freezed: ^2.4.0
  json_serializable: ^6.7.0
  hive_generator: ^2.0.0

  # 테스팅
  mocktail: ^1.0.0
  integration_test:
    sdk: flutter

  # Lint/Format
  flutter_lints: ^3.0.0
  very_good_analysis: ^5.1.0

  # 유틸리티
  flutter_launcher_icons: ^0.13.0
  flutter_native_splash: ^2.3.0

# ========== Assets ==========
flutter:
  uses-material-design: true

  assets:
    - assets/images/
    - assets/images/logo/
    - assets/images/onboarding/
    - assets/icons/
    - assets/animations/
    - .env.dev
    - .env.prod

  fonts:
    - family: Pretendard
      fonts:
        - asset: assets/fonts/Pretendard/Pretendard-Regular.otf
          weight: 400
        - asset: assets/fonts/Pretendard/Pretendard-Medium.otf
          weight: 500
        - asset: assets/fonts/Pretendard/Pretendard-SemiBold.otf
          weight: 600
        - asset: assets/fonts/Pretendard/Pretendard-Bold.otf
          weight: 700
```

### 5.2 의존성 업데이트 정책

```yaml
업데이트 주기:
  - Major 버전: 분기별 검토 (Breaking Changes 주의)
  - Minor/Patch: 월별 업데이트
  - Security Patch: 즉시 적용

테스트 절차:
  1. flutter pub outdated로 업데이트 가능 패키지 확인
  2. dev/staging 환경에서 업데이트 테스트
  3. 전체 테스트 스위트 실행 (flutter test)
  4. 회귀 테스트 통과 후 프로덕션 적용
```

---

## 6. 개발 환경 설정

### 6.1 Flutter 버전 관리 (FVM)

```bash
# FVM 설치
dart pub global activate fvm

# 프로젝트에 Flutter 버전 고정
fvm use 3.19.0 --force

# .gitignore에 FVM 캐시 추가
.fvm/flutter_sdk

# .fvmrc 생성
{
  "flutter": "3.19.0"
}

# IDE 설정 (VSCode)
{
  "dart.flutterSdkPath": ".fvm/flutter_sdk",
  "search.exclude": {
    "**/.fvm": true
  }
}
```

### 6.2 환경 변수 관리

```dart
// .env.dev
APP_ENV=development
API_BASE_URL=http://localhost:8000/api/v1
KAKAO_MAP_API_KEY=dev_kakao_key
GOOGLE_CLIENT_ID=dev_google_client_id
ENABLE_LOGGING=true

// .env.prod
APP_ENV=production
API_BASE_URL=https://api.hotly.app/api/v1
KAKAO_MAP_API_KEY=prod_kakao_key
GOOGLE_CLIENT_ID=prod_google_client_id
ENABLE_LOGGING=false

// lib/core/config/app_config.dart
import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static String get apiBaseUrl => dotenv.env['API_BASE_URL']!;
  static String get kakaoMapApiKey => dotenv.env['KAKAO_MAP_API_KEY']!;
  static bool get enableLogging => dotenv.env['ENABLE_LOGGING'] == 'true';

  static Future<void> load(String env) async {
    await dotenv.load(fileName: '.env.$env');
  }
}

// main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 환경별 설정 로드
  const env = String.fromEnvironment('ENV', defaultValue: 'dev');
  await AppConfig.load(env);

  runApp(const App());
}

// 빌드 명령어
flutter run --dart-define=ENV=dev
flutter build apk --dart-define=ENV=prod
```

### 6.3 Lint 및 Code Style

```yaml
# analysis_options.yaml
include: package:very_good_analysis/analysis_options.yaml

analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
    - "build/**"
    - "lib/generated/**"

  errors:
    invalid_annotation_target: ignore
    missing_required_param: error
    missing_return: error

  language:
    strict-casts: true
    strict-inference: true
    strict-raw-types: true

linter:
  rules:
    # 필수 규칙
    - always_declare_return_types
    - always_use_package_imports
    - avoid_print
    - avoid_unnecessary_containers
    - prefer_const_constructors
    - prefer_const_declarations
    - prefer_const_literals_to_create_immutables
    - prefer_final_fields
    - prefer_final_locals
    - require_trailing_commas
    - sort_child_properties_last
    - use_key_in_widget_constructors

    # TDD 지원 규칙
    - test_types_in_equals
    - avoid_relative_lib_imports
```

---

## 7. 빌드 및 배포 전략

### 7.1 빌드 모드

```yaml
Debug:
  - Hot Reload/Restart 지원
  - 모든 assertions 활성화
  - 디버그 로깅 출력
  - 성능 오버헤드 존재
  - 명령어: flutter run

Profile:
  - 성능 측정 전용
  - DevTools 프로파일링 가능
  - Release와 유사한 성능
  - 명령어: flutter run --profile

Release:
  - 최적화된 바이너리
  - Obfuscation 적용
  - Tree Shaking으로 코드 크기 최소화
  - 명령어: flutter build apk/ipa --release
```

### 7.2 Android 빌드 설정

```gradle
// android/app/build.gradle
android {
    namespace "com.hotly.app"
    compileSdkVersion 34

    defaultConfig {
        applicationId "com.hotly.app"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName

        multiDexEnabled true
    }

    signingConfigs {
        release {
            storeFile file(System.getenv("KEYSTORE_PATH") ?: "upload-keystore.jks")
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true

            // ProGuard 규칙
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    flavorDimensions "environment"
    productFlavors {
        dev {
            dimension "environment"
            applicationIdSuffix ".dev"
            versionNameSuffix "-dev"
        }
        staging {
            dimension "environment"
            applicationIdSuffix ".staging"
            versionNameSuffix "-staging"
        }
        prod {
            dimension "environment"
        }
    }
}
```

### 7.3 iOS 빌드 설정

```ruby
# ios/Podfile
platform :ios, '13.0'

use_frameworks!
use_modular_headers!

target 'Runner' do
  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))

  # Firebase 설정
  pod 'FirebaseFirestore', :git => 'https://github.com/invertase/firestore-ios-sdk-frameworks.git', :tag => '10.0.0'
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)

    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '13.0'
      config.build_settings['EXCLUDED_ARCHS[sdk=iphonesimulator*]'] = 'arm64'
    end
  end
end
```

### 7.4 배포 자동화 (CI/CD)

```yaml
# .github/workflows/flutter_ci.yml
name: Flutter CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.0'
          channel: 'stable'

      - name: Install dependencies
        run: flutter pub get

      - name: Run code generation
        run: flutter pub run build_runner build --delete-conflicting-outputs

      - name: Analyze code
        run: flutter analyze

      - name: Format check
        run: dart format --set-exit-if-changed .

      - name: Run unit tests
        run: flutter test --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage/lcov.info

  build_android:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
      - uses: actions/setup-java@v3
        with:
          distribution: 'zulu'
          java-version: '17'

      - name: Build APK
        run: flutter build apk --release --dart-define=ENV=prod

      - name: Upload to Play Store
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_JSON }}
          packageName: com.hotly.app
          releaseFiles: build/app/outputs/flutter-apk/app-release.apk
          track: internal

  build_ios:
    needs: test
    runs-on: macos-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2

      - name: Install CocoaPods
        run: cd ios && pod install

      - name: Build IPA
        run: flutter build ipa --release --dart-define=ENV=prod

      - name: Upload to TestFlight
        uses: apple-actions/upload-testflight-build@v1
        with:
          app-path: build/ios/ipa/hotly_app.ipa
          issuer-id: ${{ secrets.APPSTORE_ISSUER_ID }}
          api-key-id: ${{ secrets.APPSTORE_API_KEY_ID }}
          api-private-key: ${{ secrets.APPSTORE_API_PRIVATE_KEY }}
```

---

## 8. 품질 보증

### 8.1 TDD 테스트 전략 (rules.md 준수)

```dart
// ========== Red-Green-Refactor 사이클 ==========

// 1. RED: 실패하는 테스트 작성
// test/unit/features/places/domain/usecases/get_places_usecase_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockPlaceRepository extends Mock implements PlaceRepository {}

void main() {
  late GetPlacesUseCase useCase;
  late MockPlaceRepository mockRepository;

  setUp(() {
    mockRepository = MockPlaceRepository();
    useCase = GetPlacesUseCase(mockRepository);
  });

  group('GetPlacesUseCase', () {
    test('should_return_places_when_repository_succeeds', () async {
      // Arrange
      final expectedPlaces = [
        Place(id: '1', name: 'Test Place', ...),
      ];
      when(() => mockRepository.getPlaces())
          .thenAnswer((_) async => Result.success(expectedPlaces));

      // Act
      final result = await useCase();

      // Assert
      expect(result, isA<Success<List<Place>>>());
      expect(result.data, expectedPlaces);
      verify(() => mockRepository.getPlaces()).called(1);
    });

    test('should_return_failure_when_repository_fails', () async {
      // Arrange
      when(() => mockRepository.getPlaces())
          .thenAnswer((_) async => Result.failure('Network Error'));

      // Act
      final result = await useCase();

      // Assert
      expect(result, isA<Failure<List<Place>>>());
      expect(result.error, 'Network Error');
    });
  });
}

// 2. GREEN: 최소 구현
class GetPlacesUseCase {
  final PlaceRepository repository;

  GetPlacesUseCase(this.repository);

  Future<Result<List<Place>>> call() async {
    return await repository.getPlaces();
  }
}

// 3. REFACTOR: 필터 기능 추가 등 확장
class GetPlacesUseCase {
  final PlaceRepository repository;
  final CacheManager cacheManager;

  GetPlacesUseCase(this.repository, this.cacheManager);

  Future<Result<List<Place>>> call({FilterOptions? filter}) async {
    // 캐시 확인
    final cacheKey = _buildCacheKey(filter);
    final cached = await cacheManager.get<List<Place>>(cacheKey);
    if (cached != null) {
      return Result.success(cached);
    }

    // API 호출
    final result = await repository.getPlaces(filter: filter);

    // 성공 시 캐싱
    if (result is Success) {
      await cacheManager.set(cacheKey, result.data, ttl: Duration(minutes: 5));
    }

    return result;
  }

  String _buildCacheKey(FilterOptions? filter) {
    return 'places_${filter?.hashCode ?? 'all'}';
  }
}
```

### 8.2 테스트 커버리지 목표

```yaml
전체 커버리지: 80% 이상

레이어별 커버리지:
  Domain Layer (Use Cases): 100% (비즈니스 로직 핵심)
  Data Layer (Repositories): 90% (에러 처리 중요)
  Presentation Layer (ViewModels): 80% (UI 로직)
  Widgets: 60% (중요 위젯만 테스트)

측정 방법:
  flutter test --coverage
  genhtml coverage/lcov.info -o coverage/html
  open coverage/html/index.html

CI 통합:
  - PR 생성 시 자동 테스트 실행
  - 커버리지 80% 미만 시 머지 불가
  - 커버리지 리포트 자동 코멘트
```

### 8.3 성능 테스트

```dart
// test/performance/place_list_performance_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('PlaceList should render 100 items in less than 16ms', (tester) async {
    // Given
    final places = List.generate(100, (i) => Place(id: '$i', name: 'Place $i', ...));

    // When
    final stopwatch = Stopwatch()..start();
    await tester.pumpWidget(
      MaterialApp(
        home: PlaceListScreen(places: places),
      ),
    );
    await tester.pumpAndSettle();
    stopwatch.stop();

    // Then
    expect(stopwatch.elapsedMilliseconds, lessThan(16)); // 60fps = 16ms per frame
  });
}
```

### 8.4 접근성 테스트

```dart
// test/accessibility/place_card_accessibility_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('PlaceCard should meet accessibility guidelines', (tester) async {
    // Given
    final place = Place(id: '1', name: 'Test Place', ...);

    // When
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PlaceCard(place: place),
        ),
      ),
    );

    // Then - Semantic Labels
    expect(
      find.bySemanticsLabel('장소 카드: Test Place'),
      findsOneWidget,
    );

    // Then - Touch Target Size (최소 44dp)
    final likeButton = tester.getSize(find.byType(LikeButton));
    expect(likeButton.width, greaterThanOrEqualTo(44));
    expect(likeButton.height, greaterThanOrEqualTo(44));
  });
}
```

---

## 9. 완료 정의 (DoD)

### 9.1 기술 스택 선정 완료 기준
- [x] Flutter 3.19+ stable 설치 및 검증
- [x] 모든 핵심 패키지 (Riverpod, Dio, Freezed 등) pubspec.yaml에 정의
- [x] 개발/스테이징/프로덕션 환경 설정 분리
- [x] Android/iOS 최소 버전 및 빌드 설정 완료

### 9.2 아키텍처 구축 완료 기준
- [x] Clean Architecture 레이어 구조 정의
- [x] Feature-First 디렉토리 구조 생성
- [x] 의존성 주입 (GetIt) 설정 완료
- [x] 라우팅 시스템 (go_router) 구축
- [x] 에러 핸들링 및 로깅 시스템 구현

### 9.3 개발 환경 완료 기준
- [x] FVM으로 Flutter 버전 고정
- [x] Lint 규칙 (very_good_analysis) 적용
- [x] 환경 변수 관리 (.env) 설정
- [x] Pre-commit 훅 설정 (format, analyze)
- [x] CI/CD 파이프라인 구축 (GitHub Actions)

### 9.4 품질 보증 완료 기준
- [x] TDD 테스트 템플릿 작성
- [x] 단위/위젯/통합 테스트 프레임워크 구축
- [x] 테스트 커버리지 80% 이상 설정
- [x] 성능 테스트 기준 정의 (60fps, 3초 이내 시작)
- [x] 접근성 테스트 자동화

---

## 10. 수용 기준 (Acceptance Criteria)

### AC-1: 크로스 플랫폼 개발
- **Given** Flutter 앱 개발
- **When** 단일 코드베이스로 구현
- **Then** iOS/Android 동시 빌드 가능, 코드 재사용률 90% 이상

### AC-2: 네이티브 성능
- **Given** 앱 실행
- **When** 홈 화면 렌더링
- **Then** 3초 이내 화면 표시, 모든 애니메이션 60fps 유지

### AC-3: TDD 기반 개발
- **Given** 새로운 기능 개발
- **When** 코드 작성
- **Then** 테스트 먼저 작성 (Red-Green-Refactor), 테스트 커버리지 80% 이상

### AC-4: 안정성 보장
- **Given** 프로덕션 배포
- **When** 사용자 사용
- **Then** 크래시율 0.1% 이하, 에러 트래킹 100% (Crashlytics)

---

## 11. 참고 문서

- **내부 문서**:
  - `rules.md`: 코드 컨벤션 및 개발 규칙
  - `ui-design-system.md`: 디자인 시스템 가이드라인
  - `task/06-ui-frontend.md`: 프론트엔드 구현 작업 목록

- **외부 문서**:
  - [Flutter Official Docs](https://docs.flutter.dev/)
  - [Riverpod Documentation](https://riverpod.dev/)
  - [Effective Dart](https://dart.dev/guides/language/effective-dart)
  - [Material Design 3](https://m3.material.io/)

---

## 12. Changelog

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0 | 최초 작성 - Flutter 기술 스택 및 아키텍처 정의 | Development Team |

---

*이 문서는 살아있는 문서(Living Document)로, 기술 스택 변경 시 즉시 업데이트됩니다.*
