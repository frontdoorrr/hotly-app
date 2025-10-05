# API 연동 가이드 (API Integration Guide)

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **작성자**: Development Team
- **관련 TRD**: `trd/frontend/01-flutter-tech-stack.md`, `trd/frontend/02-data-flow-state-management.md`
- **관련 Backend**: `backend/app/api/api_v1/`

## 목차
1. [개요](#1-개요)
2. [API 기본 정보](#2-api-기본-정보)
3. [인증 및 토큰 관리](#3-인증-및-토큰-관리)
4. [API 클라이언트 구현](#4-api-클라이언트-구현)
5. [엔드포인트별 연동 가이드](#5-엔드포인트별-연동-가이드)
6. [에러 핸들링](#6-에러-핸들링)
7. [데이터 모델 (DTO)](#7-데이터-모델-dto)
8. [캐싱 및 오프라인 지원](#8-캐싱-및-오프라인-지원)
9. [테스트 전략](#9-테스트-전략)

---

## 1. 개요

### 1.1 목적
Flutter 앱에서 FastAPI 백엔드 API를 효율적으로 연동하기 위한 표준 가이드라인을 제공한다.

### 1.2 API 설계 원칙
- **RESTful**: 표준 HTTP 메서드 사용 (GET, POST, PUT, DELETE)
- **JSON**: 요청/응답 모두 JSON 형식
- **버저닝**: `/api/v1` prefix로 API 버전 관리
- **camelCase**: 외부 API JSON 필드는 camelCase (내부 Python은 snake_case)

---

## 2. API 기본 정보

### 2.1 Base URL

```dart
// lib/core/constants/api_constants.dart
class ApiConstants {
  // 환경별 Base URL
  static const String devBaseUrl = 'http://localhost:8000/api/v1';
  static const String stagingBaseUrl = 'https://staging-api.hotly.app/api/v1';
  static const String prodBaseUrl = 'https://api.hotly.app/api/v1';

  // 현재 환경 Base URL
  static String get baseUrl {
    const env = String.fromEnvironment('ENV', defaultValue: 'dev');
    switch (env) {
      case 'prod':
        return prodBaseUrl;
      case 'staging':
        return stagingBaseUrl;
      default:
        return devBaseUrl;
    }
  }

  // Timeout 설정
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
}
```

### 2.2 공통 헤더

```dart
class ApiHeaders {
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Version': AppConfig.version, // 앱 버전
    'X-Platform': Platform.isAndroid ? 'android' : 'ios',
  };

  static Map<String, String> authHeaders(String token) => {
    ...defaultHeaders,
    'Authorization': 'Bearer $token',
  };
}
```

---

## 3. 인증 및 토큰 관리

### 3.1 Firebase Authentication 연동

```dart
// lib/core/auth/auth_service.dart
class AuthService {
  final FirebaseAuth _firebaseAuth = FirebaseAuth.instance;
  final FlutterSecureStorage _secureStorage = FlutterSecureStorage();

  // Firebase ID Token 가져오기
  Future<String?> getIdToken() async {
    final user = _firebaseAuth.currentUser;
    if (user == null) return null;

    return await user.getIdToken();
  }

  // 토큰 갱신
  Future<String?> refreshToken() async {
    final user = _firebaseAuth.currentUser;
    if (user == null) return null;

    return await user.getIdToken(true); // 강제 갱신
  }

  // 로그아웃
  Future<void> signOut() async {
    await _firebaseAuth.signOut();
    await _secureStorage.deleteAll();
  }
}
```

### 3.2 토큰 자동 주입 (Interceptor)

```dart
// lib/core/network/interceptors/auth_interceptor.dart
class AuthInterceptor extends Interceptor {
  final AuthService _authService;

  AuthInterceptor(this._authService);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // 인증이 필요한 엔드포인트만 토큰 추가
    if (_requiresAuth(options.path)) {
      final token = await _authService.getIdToken();

      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      } else {
        // 토큰 없으면 요청 중단
        return handler.reject(
          DioException(
            requestOptions: options,
            type: DioExceptionType.cancel,
            error: 'Authentication required',
          ),
        );
      }
    }

    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // 401 Unauthorized - 토큰 만료
    if (err.response?.statusCode == 401) {
      try {
        // 토큰 갱신 시도
        final newToken = await _authService.refreshToken();

        if (newToken != null) {
          // 원래 요청 재시도
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';

          final response = await Dio().fetch(err.requestOptions);
          return handler.resolve(response);
        }
      } catch (e) {
        // 갱신 실패 - 로그아웃 처리
        await _authService.signOut();
        // 로그인 화면으로 리다이렉트
        GetIt.I<AppRouter>().go('/login');
      }
    }

    handler.next(err);
  }

  bool _requiresAuth(String path) {
    // 인증 불필요 엔드포인트
    const publicEndpoints = [
      '/auth/login',
      '/auth/signup',
      '/health',
    ];

    return !publicEndpoints.any((endpoint) => path.contains(endpoint));
  }
}
```

---

## 4. API 클라이언트 구현

### 4.1 Dio 기반 API Client

```dart
// lib/core/network/api_client.dart
class ApiClient {
  late final Dio _dio;

  ApiClient({
    required AuthService authService,
    required CacheManager cacheManager,
  }) {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      headers: ApiHeaders.defaultHeaders,
    ));

    // Interceptors 추가
    _dio.interceptors.addAll([
      AuthInterceptor(authService),
      LoggingInterceptor(),
      CacheInterceptor(cacheManager),
      RetryInterceptor(),
      ErrorInterceptor(),
    ]);
  }

  // GET 요청
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }

  // POST 요청
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  // PUT 요청
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Options? options,
  }) async {
    return await _dio.put<T>(
      path,
      data: data,
      options: options,
    );
  }

  // DELETE 요청
  Future<Response<T>> delete<T>(
    String path, {
    Options? options,
  }) async {
    return await _dio.delete<T>(
      path,
      options: options,
    );
  }

  // 파일 업로드
  Future<Response<T>> uploadFile<T>(
    String path,
    File file, {
    String fieldName = 'file',
    Map<String, dynamic>? data,
  }) async {
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(
        file.path,
        filename: file.path.split('/').last,
      ),
      ...?data,
    });

    return await _dio.post<T>(
      path,
      data: formData,
      options: Options(
        contentType: 'multipart/form-data',
      ),
    );
  }
}
```

### 4.2 Logging Interceptor

```dart
// lib/core/network/interceptors/logging_interceptor.dart
class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    logger.d('━━━━━━━━━━ REQUEST ━━━━━━━━━━');
    logger.d('${options.method} ${options.uri}');
    logger.d('Headers: ${options.headers}');
    if (options.data != null) {
      logger.d('Data: ${options.data}');
    }
    logger.d('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    logger.d('━━━━━━━━━━ RESPONSE ━━━━━━━━━━');
    logger.d('${response.statusCode} ${response.requestOptions.uri}');
    logger.d('Data: ${response.data}');
    logger.d('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    logger.e('━━━━━━━━━━ ERROR ━━━━━━━━━━');
    logger.e('${err.requestOptions.method} ${err.requestOptions.uri}');
    logger.e('${err.response?.statusCode} ${err.message}');
    logger.e('Data: ${err.response?.data}');
    logger.e('━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    handler.next(err);
  }
}
```

### 4.3 Retry Interceptor

```dart
// lib/core/network/interceptors/retry_interceptor.dart
class RetryInterceptor extends Interceptor {
  final int maxRetries = 3;
  final Duration retryDelay = Duration(seconds: 1);

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // 재시도 가능한 에러인지 확인
    if (!_shouldRetry(err)) {
      return handler.next(err);
    }

    final retryCount = err.requestOptions.extra['retryCount'] ?? 0;

    if (retryCount >= maxRetries) {
      logger.w('Max retries ($maxRetries) reached');
      return handler.next(err);
    }

    // 재시도 카운트 증가
    err.requestOptions.extra['retryCount'] = retryCount + 1;

    // 지수 백오프
    final delay = retryDelay * pow(2, retryCount);
    logger.i('Retrying request (${retryCount + 1}/$maxRetries) after ${delay.inSeconds}s...');

    await Future.delayed(delay);

    try {
      final response = await Dio().fetch(err.requestOptions);
      return handler.resolve(response);
    } catch (e) {
      return handler.next(err);
    }
  }

  bool _shouldRetry(DioException err) {
    // 네트워크 에러 또는 5xx 서버 에러만 재시도
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        (err.response?.statusCode ?? 0) >= 500;
  }
}
```

---

## 5. 엔드포인트별 연동 가이드

### 5.1 장소 (Places) API

#### 5.1.1 장소 목록 조회

**Endpoint**: `GET /places`

```dart
// lib/features/places/data/datasources/place_remote_datasource.dart
class PlaceRemoteDataSource {
  final ApiClient _apiClient;

  PlaceRemoteDataSource(this._apiClient);

  Future<List<PlaceDTO>> getPlaces({
    String? category,
    double? minRating,
    double? maxDistance,
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      '/places',
      queryParameters: {
        if (category != null) 'category': category,
        if (minRating != null) 'minRating': minRating,
        if (maxDistance != null) 'maxDistance': maxDistance,
        'page': page,
        'pageSize': pageSize,
      },
    );

    final placesJson = response.data!['places'] as List;
    return placesJson.map((json) => PlaceDTO.fromJson(json)).toList();
  }
}
```

**Request 예시**:
```http
GET /api/v1/places?category=cafe&minRating=4.0&page=1&pageSize=20
```

**Response 예시**:
```json
{
  "places": [
    {
      "id": "place-123",
      "name": "카페 A",
      "category": "cafe",
      "latitude": 37.4979,
      "longitude": 127.0276,
      "address": "서울시 강남구...",
      "rating": 4.5,
      "imageUrl": "https://cdn.hotly.app/places/123.jpg",
      "description": "분위기 좋은 카페",
      "tags": ["뷰맛집", "데이트"],
      "isLiked": false,
      "isSaved": false
    }
  ],
  "total": 132,
  "page": 1,
  "pageSize": 20
}
```

#### 5.1.2 장소 상세 조회

**Endpoint**: `GET /places/{placeId}`

```dart
Future<PlaceDTO> getPlaceById(String placeId) async {
  final response = await _apiClient.get<Map<String, dynamic>>(
    '/places/$placeId',
  );

  return PlaceDTO.fromJson(response.data!['place']);
}
```

#### 5.1.3 장소 검색

**Endpoint**: `GET /places/search`

```dart
Future<List<PlaceDTO>> searchPlaces({
  required String query,
  String? category,
  double? latitude,
  double? longitude,
}) async {
  final response = await _apiClient.get<Map<String, dynamic>>(
    '/places/search',
    queryParameters: {
      'q': query,
      if (category != null) 'category': category,
      if (latitude != null) 'lat': latitude,
      if (longitude != null) 'lng': longitude,
    },
  );

  final placesJson = response.data!['places'] as List;
  return placesJson.map((json) => PlaceDTO.fromJson(json)).toList();
}
```

#### 5.1.4 장소 저장

**Endpoint**: `POST /places/saved`

```dart
Future<void> savePlace(PlaceDTO place) async {
  await _apiClient.post(
    '/places/saved',
    data: place.toJson(),
  );
}
```

**Request Body**:
```json
{
  "placeId": "place-123",
  "folderId": "folder-456",
  "memo": "데이트 때 가기"
}
```

#### 5.1.5 장소 좋아요

**Endpoint**: `POST /places/{placeId}/like`

```dart
Future<void> likePlace(String placeId) async {
  await _apiClient.post('/places/$placeId/like');
}
```

### 5.2 링크 분석 (Link Analysis) API

#### 5.2.1 링크 분석 요청

**Endpoint**: `POST /link-analysis`

```dart
// lib/features/link_analysis/data/datasources/link_analysis_remote_datasource.dart
class LinkAnalysisRemoteDataSource {
  final ApiClient _apiClient;

  LinkAnalysisRemoteDataSource(this._apiClient);

  Future<LinkAnalysisResultDTO> analyzeLink(String url) async {
    final response = await _apiClient.post<Map<String, dynamic>>(
      '/link-analysis',
      data: {'url': url},
    );

    return LinkAnalysisResultDTO.fromJson(response.data!);
  }
}
```

**Request Body**:
```json
{
  "url": "https://www.instagram.com/p/ABC123/"
}
```

**Response 예시**:
```json
{
  "analysisId": "analysis-789",
  "extractedPlaces": [
    {
      "name": "카페 A",
      "category": "cafe",
      "address": "서울시 강남구...",
      "confidence": 0.85,
      "metadata": {
        "mentions": 3,
        "keywords": ["분위기", "데이트"]
      }
    }
  ],
  "platform": "instagram",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

### 5.3 코스 (Courses) API

#### 5.3.1 코스 생성

**Endpoint**: `POST /courses`

```dart
Future<CourseDTO> createCourse(CourseCreateDTO course) async {
  final response = await _apiClient.post<Map<String, dynamic>>(
    '/courses',
    data: course.toJson(),
  );

  return CourseDTO.fromJson(response.data!['course']);
}
```

**Request Body**:
```json
{
  "title": "강남 데이트 코스",
  "description": "분위기 좋은 카페와 맛집",
  "type": "date",
  "places": [
    {
      "placeId": "place-123",
      "order": 1,
      "duration": 90
    },
    {
      "placeId": "place-456",
      "order": 2,
      "duration": 120
    }
  ],
  "isPublic": false
}
```

#### 5.3.2 코스 목록 조회

**Endpoint**: `GET /courses`

```dart
Future<List<CourseDTO>> getCourses({
  String? type,
  bool? isPublic,
}) async {
  final response = await _apiClient.get<Map<String, dynamic>>(
    '/courses',
    queryParameters: {
      if (type != null) 'type': type,
      if (isPublic != null) 'isPublic': isPublic,
    },
  );

  final coursesJson = response.data!['courses'] as List;
  return coursesJson.map((json) => CourseDTO.fromJson(json)).toList();
}
```

### 5.4 사용자 (User) API

#### 5.4.1 프로필 조회

**Endpoint**: `GET /users/me`

```dart
Future<UserDTO> getCurrentUser() async {
  final response = await _apiClient.get<Map<String, dynamic>>('/users/me');
  return UserDTO.fromJson(response.data!['user']);
}
```

#### 5.4.2 프로필 업데이트

**Endpoint**: `PUT /users/me`

```dart
Future<UserDTO> updateProfile(UserUpdateDTO update) async {
  final response = await _apiClient.put<Map<String, dynamic>>(
    '/users/me',
    data: update.toJson(),
  );

  return UserDTO.fromJson(response.data!['user']);
}
```

---

## 6. 에러 핸들링

### 6.1 API 에러 응답 형식

```json
{
  "error": {
    "code": "PLACE_NOT_FOUND",
    "message": "장소를 찾을 수 없습니다",
    "details": {
      "placeId": "invalid-id"
    }
  }
}
```

### 6.2 에러 인터셉터

```dart
// lib/core/network/interceptors/error_interceptor.dart
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final apiException = _parseError(err);

    // Analytics에 에러 전송
    FirebaseCrashlytics.instance.recordError(
      apiException,
      err.stackTrace,
      reason: 'API Error',
    );

    handler.next(DioException(
      requestOptions: err.requestOptions,
      error: apiException,
      type: err.type,
    ));
  }

  ApiException _parseError(DioException err) {
    if (err.response != null) {
      final statusCode = err.response!.statusCode!;
      final data = err.response!.data;

      // 백엔드 에러 응답 파싱
      if (data is Map && data.containsKey('error')) {
        final error = data['error'];
        return ApiException(
          message: error['message'] ?? 'Unknown error',
          code: statusCode,
          errorCode: error['code'],
          details: error['details'],
        );
      }

      // HTTP 상태 코드별 처리
      switch (statusCode) {
        case 400:
          return BadRequestException('잘못된 요청입니다');
        case 401:
          return UnauthorizedException('로그인이 필요합니다');
        case 403:
          return ForbiddenException('권한이 없습니다');
        case 404:
          return NotFoundException('요청한 리소스를 찾을 수 없습니다');
        case 429:
          return RateLimitException('요청이 너무 많습니다. 잠시 후 다시 시도해주세요');
        case 500:
          return ServerException('서버 오류가 발생했습니다');
        default:
          return ApiException('알 수 없는 오류가 발생했습니다', code: statusCode);
      }
    }

    // 네트워크 에러
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout) {
      return NetworkException('네트워크 연결 시간이 초과되었습니다');
    }

    if (err.type == DioExceptionType.cancel) {
      return CancelledException('요청이 취소되었습니다');
    }

    return NetworkException('인터넷 연결을 확인해주세요');
  }
}
```

### 6.3 커스텀 Exception 클래스

```dart
// lib/core/error/exceptions.dart
abstract class AppException implements Exception {
  final String message;
  final int? code;

  AppException(this.message, {this.code});

  @override
  String toString() => message;
}

class ApiException extends AppException {
  final String? errorCode;
  final dynamic details;

  ApiException(
    String message, {
    int? code,
    this.errorCode,
    this.details,
  }) : super(message, code: code);
}

class NetworkException extends AppException {
  NetworkException(String message) : super(message);
}

class UnauthorizedException extends ApiException {
  UnauthorizedException(String message) : super(message, code: 401);
}

class NotFoundException extends ApiException {
  NotFoundException(String message) : super(message, code: 404);
}

// ... 기타 Exception 클래스
```

---

## 7. 데이터 모델 (DTO)

### 7.1 Place DTO

```dart
// lib/features/places/data/models/place_dto.dart
@freezed
class PlaceDTO with _$PlaceDTO {
  const factory PlaceDTO({
    required String id,
    required String name,
    required String category,
    required double latitude,
    required double longitude,
    String? address,
    double? rating,
    String? imageUrl,
    String? description,
    @Default([]) List<String> tags,
    @Default(false) bool isLiked,
    @Default(false) bool isSaved,
  }) = _PlaceDTO;

  factory PlaceDTO.fromJson(Map<String, dynamic> json) =>
      _$PlaceDTOFromJson(json);
}

// DTO → Entity 변환
extension PlaceDTOX on PlaceDTO {
  Place toEntity() {
    return Place(
      id: id,
      name: name,
      category: PlaceCategory.fromString(category),
      location: LatLng(latitude, longitude),
      address: address,
      rating: rating,
      imageUrl: imageUrl,
      description: description,
      tags: tags,
      isLiked: isLiked,
      isSaved: isSaved,
    );
  }
}
```

### 7.2 LinkAnalysisResult DTO

```dart
@freezed
class LinkAnalysisResultDTO with _$LinkAnalysisResultDTO {
  const factory LinkAnalysisResultDTO({
    required String analysisId,
    required List<ExtractedPlaceDTO> extractedPlaces,
    required String platform,
    required String createdAt,
  }) = _LinkAnalysisResultDTO;

  factory LinkAnalysisResultDTO.fromJson(Map<String, dynamic> json) =>
      _$LinkAnalysisResultDTOFromJson(json);
}

@freezed
class ExtractedPlaceDTO with _$ExtractedPlaceDTO {
  const factory ExtractedPlaceDTO({
    required String name,
    required String category,
    String? address,
    required double confidence,
    Map<String, dynamic>? metadata,
  }) = _ExtractedPlaceDTO;

  factory ExtractedPlaceDTO.fromJson(Map<String, dynamic> json) =>
      _$ExtractedPlaceDTOFromJson(json);
}
```

---

## 8. 캐싱 및 오프라인 지원

### 8.1 Cache Interceptor

```dart
// lib/core/network/interceptors/cache_interceptor.dart
class CacheInterceptor extends Interceptor {
  final CacheManager _cacheManager;

  CacheInterceptor(this._cacheManager);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // GET 요청만 캐싱
    if (options.method != 'GET') {
      return handler.next(options);
    }

    // 캐시 확인
    final cacheKey = _buildCacheKey(options);
    final cached = _cacheManager.get(cacheKey);

    if (cached != null) {
      logger.d('Cache hit: $cacheKey');

      // 캐시된 응답 반환
      return handler.resolve(
        Response(
          requestOptions: options,
          data: cached,
          statusCode: 200,
        ),
      );
    }

    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    // GET 요청 응답 캐싱
    if (response.requestOptions.method == 'GET') {
      final cacheKey = _buildCacheKey(response.requestOptions);
      final ttl = _getTTL(response.requestOptions.path);

      _cacheManager.set(cacheKey, response.data, ttl: ttl);
    }

    handler.next(response);
  }

  String _buildCacheKey(RequestOptions options) {
    final uri = options.uri.toString();
    return 'api_cache:$uri';
  }

  Duration _getTTL(String path) {
    // 엔드포인트별 TTL 설정
    if (path.contains('/places')) {
      return Duration(minutes: 5);
    } else if (path.contains('/courses')) {
      return Duration(minutes: 10);
    } else if (path.contains('/users/me')) {
      return Duration(hours: 1);
    }

    return Duration(minutes: 3); // 기본값
  }
}
```

### 8.2 오프라인 ���선 Repository 패턴

```dart
// lib/features/places/data/repositories/place_repository_impl.dart
class PlaceRepositoryImpl implements PlaceRepository {
  final PlaceRemoteDataSource _remoteDataSource;
  final PlaceLocalDataSource _localDataSource;
  final ConnectivityService _connectivity;

  @override
  Future<Result<List<Place>>> getPlaces() async {
    try {
      // 1. 로컬 DB에서 즉시 반환 (Stale-While-Revalidate)
      final localPlaces = await _localDataSource.getCachedPlaces();

      // 2. 백그라운드에서 API 호출 (네트워크 있을 경우)
      unawaited(_refreshPlacesInBackground());

      return Result.success(localPlaces.map((dto) => dto.toEntity()).toList());
    } catch (e) {
      return Result.failure('데이터를 불러올 수 없습니다');
    }
  }

  Future<void> _refreshPlacesInBackground() async {
    try {
      final isConnected = await _connectivity.isConnected;
      if (!isConnected) return;

      final placeDTOs = await _remoteDataSource.getPlaces();
      await _localDataSource.cachePlaces(placeDTOs);

      logger.d('Background refresh completed');
    } catch (e) {
      logger.w('Background refresh failed: $e');
    }
  }
}
```

---

## 9. 테스트 전략

### 9.1 API Client Mock 테스트

```dart
// test/core/network/api_client_test.dart
import 'package:mocktail/mocktail.dart';

class MockDio extends Mock implements Dio {}

void main() {
  late ApiClient apiClient;
  late MockDio mockDio;

  setUp(() {
    mockDio = MockDio();
    apiClient = ApiClient(dio: mockDio);
  });

  group('ApiClient', () {
    test('should_return_data_when_GET_request_succeeds', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: '/places'),
        data: {'places': []},
        statusCode: 200,
      );

      when(() => mockDio.get(
            any(),
            queryParameters: any(named: 'queryParameters'),
          )).thenAnswer((_) async => mockResponse);

      // Act
      final response = await apiClient.get('/places');

      // Assert
      expect(response.statusCode, 200);
      expect(response.data, isA<Map<String, dynamic>>());
      verify(() => mockDio.get('/places')).called(1);
    });

    test('should_throw_ApiException_when_request_fails', () async {
      // Arrange
      when(() => mockDio.get(any())).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: '/places'),
          response: Response(
            requestOptions: RequestOptions(path: '/places'),
            statusCode: 404,
          ),
        ),
      );

      // Act & Assert
      expect(
        () => apiClient.get('/places'),
        throwsA(isA<NotFoundException>()),
      );
    });
  });
}
```

### 9.2 Repository 테스트

```dart
// test/features/places/data/repositories/place_repository_impl_test.dart
void main() {
  late PlaceRepositoryImpl repository;
  late MockPlaceRemoteDataSource mockRemoteDataSource;
  late MockPlaceLocalDataSource mockLocalDataSource;

  setUp(() {
    mockRemoteDataSource = MockPlaceRemoteDataSource();
    mockLocalDataSource = MockPlaceLocalDataSource();
    repository = PlaceRepositoryImpl(
      mockRemoteDataSource,
      mockLocalDataSource,
    );
  });

  group('getPlaces', () {
    test('should_return_places_from_remote_when_online', () async {
      // Arrange
      final placeDTOs = [
        PlaceDTO(id: '1', name: 'Place 1', ...),
      ];

      when(() => mockRemoteDataSource.getPlaces())
          .thenAnswer((_) async => placeDTOs);

      // Act
      final result = await repository.getPlaces();

      // Assert
      expect(result, isA<Success<List<Place>>>());
      expect(result.data.length, 1);
      verify(() => mockRemoteDataSource.getPlaces()).called(1);
    });
  });
}
```

---

## 10. 완료 정의 (DoD)

### 10.1 API 연동 완료 기준
- [x] Dio 기반 API Client 구현
- [x] 인증 토큰 자동 주입 (Interceptor)
- [x] 재시도 로직 (최대 3회, 지수 백오프)
- [x] 에러 핸들링 및 커스텀 Exception
- [x] 로깅 (개발 환경)

### 10.2 데이터 모델 완료 기준
- [x] Freezed 기반 DTO 클래스 정의
- [x] JSON 직렬화/역직렬화
- [x] DTO → Entity 변환 Extension
- [x] 모든 필수 필드 포함

### 10.3 캐싱 완료 기준
- [x] GET 요청 응답 캐싱
- [x] 엔드포인트별 TTL 설정
- [x] 캐시 무효화 전략
- [x] 오프라인 우선 Repository 패턴

### 10.4 테스트 완료 기준
- [x] API Client 단위 테스트
- [x] Repository 통합 테스트
- [x] Mock 객체 활용
- [x] 테스트 커버리지 80% 이상

---

## 11. 참고 문서

- **내부 문서**:
  - `trd/frontend/02-data-flow-state-management.md`: 데이터 플로우
  - `backend/app/api/api_v1/`: 백엔드 API 구현

- **외부 문서**:
  - [Dio Documentation](https://pub.dev/packages/dio)
  - [Freezed Documentation](https://pub.dev/packages/freezed)
  - [RESTful API 설계 가이드](https://restfulapi.net/)

---

## 12. Changelog

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0 | 최초 작성 - API 연동 가이드 및 DTO 정의 | Development Team |

---

*이 문서는 살아있는 문서(Living Document)로, API 스펙 변경 시 즉시 업데이트됩니다.*
