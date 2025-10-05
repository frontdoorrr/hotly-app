# TRD-Frontend-02: 데이터 플로우 및 상태 관리 (Data Flow & State Management)

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **작성자**: Development Team
- **관련 PRD**: `prd/02-place-management.md`, `prd/03-course-recommendation.md`
- **관련 TRD**: `trd/frontend/01-flutter-tech-stack.md`
- **관련 Task**: `task/06-ui-frontend.md`

## 목차
1. [개요](#1-개요)
2. [상태 관리 전략](#2-상태-관리-전략)
3. [데이터 플로우 아키텍처](#3-데이터-플로우-아키텍처)
4. [캐싱 전략](#4-캐싱-전략)
5. [오프라인 지원](#5-오프라인-지원)
6. [실시간 동기화](#6-실시간-동기화)
7. [에러 핸들링](#7-에러-핸들링)
8. [성능 최적화](#8-성능-최적화)

---

## 1. 개요

### 1.1 목적
Flutter 앱에서 서버 데이터와 로컬 상태를 효율적으로 관리하고, 오프라인 지원 및 실시간 동기화를 통해 끊김 없는 사용자 경험을 제공한다.

### 1.2 사용자 가치
- **즉각적 반응**: 옵티미스틱 업데이트로 사용자 액션에 즉시 피드백 (0.1초 이내)
- **오프라인 사용**: 네트워크 없이도 저장된 장소/코스 조회 가능 (100% 가용성)
- **실시간 동기화**: 다른 기기에서의 변경사항 자동 반영 (5초 이내)
- **안정성**: 네트워크 오류 시 자동 재시도 및 큐잉 (데이터 손실 0%)

### 1.3 가설 및 KPI
- **가설**: 계층화된 캐싱 전략으로 API 호출 60% 감소, 화면 로딩 속도 3배 향상
- **측정 지표**:
  - 캐시 히트율: 60% 이상
  - API 응답 대기 시간: p95 < 500ms
  - 오프라인 모드 가용 기능: 80% 이상
  - 데이터 동기화 지연: 5초 이내

---

## 2. 상태 관리 전략

### 2.1 상태 분류 체계

```dart
// ========== 1. UI 상태 (Local State) ==========
// 위젯 내부에서만 사용, 다른 화면과 공유 불필요

// StatefulWidget 사용
class SearchBar extends StatefulWidget {
  @override
  State<SearchBar> createState() => _SearchBarState();
}

class _SearchBarState extends State<SearchBar> {
  final _controller = TextEditingController();
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      onChanged: (value) => setState(() {}),
    );
  }
}

// ========== 2. 앱 상태 (App State) ==========
// 여러 화면에서 공유하는 상태

// StateProvider - 단순 상태
final selectedTabProvider = StateProvider<int>((ref) => 0);
final isDarkModeProvider = StateProvider<bool>((ref) => false);

// ========== 3. 서버 상태 (Server State) ==========
// 백엔드 API에서 가져오는 데이터

// FutureProvider - 비동기 데이터 로딩
final placesProvider = FutureProvider.autoDispose<List<Place>>((ref) async {
  final repository = ref.read(placeRepositoryProvider);
  final result = await repository.getPlaces();

  return result.when(
    success: (places) => places,
    failure: (error) => throw Exception(error),
  );
});

// StateNotifierProvider - 복잡한 상태 + 비즈니스 로직
final placeListProvider = StateNotifierProvider<PlaceListNotifier, PlaceListState>((ref) {
  return PlaceListNotifier(
    ref.read(placeRepositoryProvider),
    ref.read(analyticsServiceProvider),
  );
});

// ========== 4. 폼 상태 (Form State) ==========
// 사용자 입력 폼 관리

final courseFormProvider = StateNotifierProvider<CourseFormNotifier, CourseFormState>((ref) {
  return CourseFormNotifier();
});

class CourseFormState {
  final String title;
  final String? description;
  final List<Place> places;
  final Map<String, String?> errors;
  final bool isValid;

  CourseFormState({
    this.title = '',
    this.description,
    this.places = const [],
    this.errors = const {},
    this.isValid = false,
  });

  CourseFormState copyWith({...}) {...}
}
```

### 2.2 Riverpod Provider 선택 가이드

```dart
// ========== Provider 타입별 사용 시나리오 ==========

// 1. Provider - 불변 값, 계산된 값
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(baseUrl: AppConfig.apiBaseUrl);
});

final userNameProvider = Provider<String>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.name ?? 'Guest';
});

// 2. StateProvider - 단순 읽기/쓰기 상태
final counterProvider = StateProvider<int>((ref) => 0);
final filterProvider = StateProvider<FilterOptions>((ref) => FilterOptions.initial());

// 사용 예시
ref.read(counterProvider.notifier).state++; // 쓰기
final count = ref.watch(counterProvider);    // 읽기

// 3. StateNotifierProvider - 복잡한 상태 + 로직
class PlaceListNotifier extends StateNotifier<PlaceListState> {
  final PlaceRepository _repository;

  PlaceListNotifier(this._repository) : super(PlaceListState.initial());

  Future<void> loadPlaces({FilterOptions? filter}) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.getPlaces(filter: filter);

    state = result.when(
      success: (places) => state.copyWith(
        places: places,
        isLoading: false,
      ),
      failure: (error) => state.copyWith(
        error: error,
        isLoading: false,
      ),
    );
  }

  Future<void> toggleLike(String placeId) async {
    // Optimistic Update
    final updatedPlaces = state.places.map((p) {
      if (p.id == placeId) {
        return p.copyWith(
          isLiked: !p.isLiked,
          likeCount: p.isLiked ? p.likeCount - 1 : p.likeCount + 1,
        );
      }
      return p;
    }).toList();

    state = state.copyWith(places: updatedPlaces);

    // API 호출
    final result = await _repository.toggleLike(placeId);

    // 실패 시 롤백
    if (result is Failure) {
      final rollbackPlaces = state.places.map((p) {
        if (p.id == placeId) {
          return p.copyWith(
            isLiked: !p.isLiked,
            likeCount: p.isLiked ? p.likeCount - 1 : p.likeCount + 1,
          );
        }
        return p;
      }).toList();

      state = state.copyWith(
        places: rollbackPlaces,
        error: result.error,
      );
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

// 4. FutureProvider - 비동기 데이터 로딩
final placeDetailProvider = FutureProvider.family<Place, String>((ref, placeId) async {
  final repository = ref.read(placeRepositoryProvider);
  final result = await repository.getPlaceById(placeId);

  return result.when(
    success: (place) => place,
    failure: (error) => throw PlaceNotFoundException(placeId),
  );
});

// autoDispose로 메모리 관리
final searchResultsProvider = FutureProvider.autoDispose.family<List<Place>, String>(
  (ref, query) async {
    if (query.isEmpty) return [];

    final repository = ref.read(placeRepositoryProvider);
    final result = await repository.searchPlaces(query);

    return result.when(
      success: (places) => places,
      failure: (error) => throw SearchException(error),
    );
  },
);

// 5. StreamProvider - 실시간 데이터
final notificationsProvider = StreamProvider<List<Notification>>((ref) {
  final service = ref.read(notificationServiceProvider);
  return service.notificationStream();
});

// WebSocket 실시간 업데이트
final placeUpdatesProvider = StreamProvider<PlaceUpdate>((ref) {
  final wsClient = ref.read(webSocketClientProvider);
  return wsClient.placeUpdatesStream();
});

// 6. ChangeNotifierProvider - Legacy 마이그레이션용 (비권장)
// StateNotifier 사용 권장
```

### 2.3 Provider 의존성 관리

```dart
// ========== Provider 간 의존성 ==========

// 1. ref.watch() - Provider 변경 시 자동 재빌드
final filteredPlacesProvider = Provider<List<Place>>((ref) {
  final allPlaces = ref.watch(placesProvider).value ?? [];
  final filter = ref.watch(filterOptionsProvider);

  return allPlaces.where((place) {
    if (filter.category != null && place.category != filter.category) {
      return false;
    }
    if (filter.minRating != null && place.rating < filter.minRating!) {
      return false;
    }
    return true;
  }).toList();
});

// 2. ref.read() - 일회성 읽기 (이벤트 핸들러)
final placeListProvider = StateNotifierProvider<PlaceListNotifier, PlaceListState>((ref) {
  return PlaceListNotifier(
    ref.read(placeRepositoryProvider),  // 생성 시점에만 읽기
    ref.read(analyticsServiceProvider),
  );
});

// 3. ref.listen() - 상태 변경 감지하여 부수 효과 처리
class PlaceListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen<PlaceListState>(
      placeListProvider,
      (previous, next) {
        // 에러 발생 시 스낵바 표시
        if (next.error != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(next.error!)),
          );
        }
      },
    );

    final state = ref.watch(placeListProvider);
    return _buildUI(state);
  }
}

// 4. family - 매개변수화된 Provider
final placeDetailProvider = FutureProvider.family<Place, String>((ref, placeId) async {
  final repository = ref.read(placeRepositoryProvider);
  return repository.getPlaceById(placeId);
});

// 사용
final place = ref.watch(placeDetailProvider('place-123'));

// 5. autoDispose - 자동 메모리 정리
final searchProvider = FutureProvider.autoDispose.family<List<Place>, String>(
  (ref, query) async {
    // 검색 화면을 벗어나면 자동으로 dispose
    final repository = ref.read(placeRepositoryProvider);
    return repository.searchPlaces(query);
  },
);
```

---

## 3. 데이터 플로우 아키텍처

### 3.1 전체 데이터 플로우

```
┌─────────────────────────────────────────────────────┐
│                   Presentation Layer                │
│                                                     │
│  ┌─────────────┐         ┌──────────────┐          │
│  │   Widget    │ watch   │   Provider   │          │
│  │             │◄────────│ (Riverpod)   │          │
│  └──────┬──────┘         └──────┬───────┘          │
│         │ User Action           │ notify           │
│         │                       │                  │
│  ┌──────▼──────┐         ┌──────▼───────┐          │
│  │  ViewModel  │────────►│ StateNotifier│          │
│  │  (Notifier) │ update  │   <State>    │          │
│  └──────┬──────┘         └──────────────┘          │
└─────────┼────────────────────────────────────────────┘
          │
          │ Use Case Call
          │
┌─────────▼────────────────────────────────────────────┐
│                    Domain Layer                      │
│                                                      │
│  ┌──────────────┐         ┌──────────────┐          │
│  │   Use Case   │ depends │  Repository  │          │
│  │              │────────►│  Interface   │          │
│  └──────────────┘         └──────────────┘          │
└──────────────────────────────────────────────────────┘
          │
          │ Repository Impl
          │
┌─────────▼────────────────────────────────────────────┐
│                     Data Layer                       │
│                                                      │
│  ┌──────────────────────────────────────┐            │
│  │      Repository Implementation       │            │
│  │                                      │            │
│  │  1. Check Cache (Memory/Disk)       │            │
│  │  2. Network Available?              │            │
│  │     ├─ Yes: API Call                │            │
│  │     └─ No: Return Cached            │            │
│  │  3. Update Cache                    │            │
│  │  4. Return Result                   │            │
│  └──────┬────────────────┬──────────────┘            │
│         │                │                           │
│  ┌──────▼──────┐  ┌──────▼───────┐                  │
│  │   Remote    │  │    Local     │                  │
│  │ Data Source │  │ Data Source  │                  │
│  │   (API)     │  │ (SQLite/Hive)│                  │
│  └─────────────┘  └──────────────┘                  │
└──────────────────────────────────────────────────────┘
```

### 3.2 Repository 패턴 상세 구현

```dart
// ========== Repository Interface (Domain Layer) ==========
abstract class PlaceRepository {
  Future<Result<List<Place>>> getPlaces({FilterOptions? filter});
  Future<Result<Place>> getPlaceById(String id);
  Future<Result<void>> likePlace(String id);
  Future<Result<void>> savePlace(Place place);
  Stream<List<Place>> watchSavedPlaces();
}

// ========== Repository Implementation (Data Layer) ==========
class PlaceRepositoryImpl implements PlaceRepository {
  final PlaceRemoteDataSource _remoteDataSource;
  final PlaceLocalDataSource _localDataSource;
  final CacheManager _cacheManager;
  final ConnectivityService _connectivity;
  final SyncQueue _syncQueue;

  PlaceRepositoryImpl(
    this._remoteDataSource,
    this._localDataSource,
    this._cacheManager,
    this._connectivity,
    this._syncQueue,
  );

  @override
  Future<Result<List<Place>>> getPlaces({FilterOptions? filter}) async {
    try {
      // 1. 메모리 캐시 확인 (L1 Cache)
      final cacheKey = _buildCacheKey('places', filter);
      final cached = _cacheManager.get<List<Place>>(cacheKey);
      if (cached != null) {
        logger.d('Cache hit: $cacheKey');
        return Result.success(cached);
      }

      // 2. 네트워크 연결 확인
      final isConnected = await _connectivity.isConnected;

      if (isConnected) {
        // 3. API 호출
        final placeDTOs = await _remoteDataSource.getPlaces(filter);
        final places = placeDTOs.map((dto) => dto.toEntity()).toList();

        // 4. 메모리 캐시 저장 (L1)
        _cacheManager.set(cacheKey, places, ttl: Duration(minutes: 5));

        // 5. 디스크 캐시 저장 (L2) - 백그라운드
        unawaited(_localDataSource.cachePlaces(places));

        return Result.success(places);
      } else {
        // 6. 오프라인 - 디스크 캐시 반환
        logger.w('Offline mode: returning cached data');
        final cachedPlaces = await _localDataSource.getCachedPlaces(filter);

        if (cachedPlaces.isEmpty) {
          return Result.failure('오프라인 상태이며 캐시된 데이터가 없습니다.');
        }

        return Result.success(cachedPlaces);
      }
    } on ApiException catch (e) {
      logger.e('API error: ${e.message}', e);
      return Result.failure(e.message);
    } on CacheException catch (e) {
      logger.e('Cache error: ${e.message}', e);
      // 캐시 오류는 무시하고 계속 진행
      return Result.failure('데이터를 불러올 수 없습니다.');
    } catch (e) {
      logger.e('Unexpected error: $e', e);
      return Result.failure('알 수 없는 오류가 발생했습니다.');
    }
  }

  @override
  Future<Result<void>> likePlace(String id) async {
    try {
      // 1. 네트워크 확인
      final isConnected = await _connectivity.isConnected;

      if (isConnected) {
        // 2. 즉시 API 호출
        await _remoteDataSource.likePlace(id);

        // 3. 캐시 무효화
        _cacheManager.invalidate('places');

        return Result.success(null);
      } else {
        // 4. 오프라인 - 동기화 큐에 추가
        await _syncQueue.add(SyncAction.likePlace(id));

        logger.i('Queued like action for place: $id');
        return Result.success(null);
      }
    } catch (e) {
      logger.e('Like place error: $e', e);
      return Result.failure('좋아요 처리에 실패했습니다.');
    }
  }

  @override
  Future<Result<void>> savePlace(Place place) async {
    try {
      // 1. 로컬 DB에 즉시 저장 (오프라인 우선)
      await _localDataSource.savePlace(place);

      // 2. 네트워크 확인
      final isConnected = await _connectivity.isConnected;

      if (isConnected) {
        // 3. API 동기화
        await _remoteDataSource.savePlace(place.toDTO());
      } else {
        // 4. 동기화 큐에 추가
        await _syncQueue.add(SyncAction.savePlace(place));
      }

      // 5. 캐시 무효화
      _cacheManager.invalidate('saved_places');

      return Result.success(null);
    } catch (e) {
      logger.e('Save place error: $e', e);
      return Result.failure('장소 저장에 실패했습니다.');
    }
  }

  @override
  Stream<List<Place>> watchSavedPlaces() {
    // 로컬 DB 변경 사항 실시간 감지
    return _localDataSource.watchSavedPlaces();
  }

  String _buildCacheKey(String prefix, FilterOptions? filter) {
    if (filter == null) return prefix;
    return '$prefix:${filter.hashCode}';
  }
}

// ========== Remote Data Source (API 통신) ==========
class PlaceRemoteDataSource {
  final ApiClient _apiClient;

  PlaceRemoteDataSource(this._apiClient);

  Future<List<PlaceDTO>> getPlaces(FilterOptions? filter) async {
    final response = await _apiClient.get(
      '/places',
      queryParameters: filter?.toJson(),
    );

    return (response.data['places'] as List)
        .map((json) => PlaceDTO.fromJson(json))
        .toList();
  }

  Future<void> likePlace(String id) async {
    await _apiClient.post('/places/$id/like');
  }

  Future<void> savePlace(PlaceDTO place) async {
    await _apiClient.post('/places/saved', data: place.toJson());
  }
}

// ========== Local Data Source (SQLite/Hive) ==========
class PlaceLocalDataSource {
  final Database _db;
  final Box<Place> _hiveBox;

  PlaceLocalDataSource(this._db, this._hiveBox);

  Future<void> cachePlaces(List<Place> places) async {
    final batch = _db.batch();
    for (final place in places) {
      batch.insert(
        'cached_places',
        place.toJson(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<Place>> getCachedPlaces(FilterOptions? filter) async {
    final maps = await _db.query('cached_places');
    var places = maps.map((map) => Place.fromJson(map)).toList();

    // 필터 적용 (로컬)
    if (filter != null) {
      places = places.where((p) => filter.matches(p)).toList();
    }

    return places;
  }

  Future<void> savePlace(Place place) async {
    await _hiveBox.put(place.id, place);
  }

  Stream<List<Place>> watchSavedPlaces() {
    return _hiveBox.watch().map((_) => _hiveBox.values.toList());
  }
}
```

### 3.3 Result 타입 (에러 핸들링)

```dart
// ========== Result Type (Sealed Union) ==========
@freezed
class Result<T> with _$Result<T> {
  const factory Result.success(T data) = Success<T>;
  const factory Result.failure(String error, {int? code}) = Failure<T>;
  const factory Result.loading() = Loading<T>;
}

// 사용 예시
final result = await repository.getPlaces();

// 1. when - 모든 케이스 처리 (권장)
result.when(
  success: (places) {
    print('Success: ${places.length} places');
  },
  failure: (error, code) {
    print('Error: $error (code: $code)');
  },
  loading: () {
    print('Loading...');
  },
);

// 2. maybeWhen - 일부 케이스만 처리
result.maybeWhen(
  success: (places) => places,
  orElse: () => [],
);

// 3. map - 타입 변환
final placeNames = result.map(
  success: (s) => s.data.map((p) => p.name).toList(),
  failure: (f) => <String>[],
  loading: (l) => <String>[],
);

// 4. fold - 양방향 처리
final output = result.fold(
  success: (places) => 'Found ${places.length} places',
  failure: (error, _) => 'Error: $error',
  loading: () => 'Loading...',
);
```

---

## 4. 캐싱 전략

### 4.1 다층 캐싱 (Multi-Layer Cache)

```dart
// ========== L1: 메모리 캐시 (In-Memory Cache) ==========
class MemoryCache {
  final Map<String, _CacheEntry> _cache = {};
  final int maxSize;

  MemoryCache({this.maxSize = 100});

  T? get<T>(String key) {
    final entry = _cache[key];
    if (entry == null) return null;

    // TTL 확인
    if (entry.isExpired) {
      _cache.remove(key);
      return null;
    }

    return entry.value as T;
  }

  void set<T>(String key, T value, {required Duration ttl}) {
    // LRU: 최대 크기 초과 시 가장 오래된 항목 제거
    if (_cache.length >= maxSize) {
      final oldestKey = _cache.entries
          .reduce((a, b) => a.value.timestamp.isBefore(b.value.timestamp) ? a : b)
          .key;
      _cache.remove(oldestKey);
    }

    _cache[key] = _CacheEntry(
      value: value,
      timestamp: DateTime.now(),
      ttl: ttl,
    );
  }

  void invalidate(String prefix) {
    _cache.removeWhere((key, _) => key.startsWith(prefix));
  }

  void clear() {
    _cache.clear();
  }
}

class _CacheEntry {
  final dynamic value;
  final DateTime timestamp;
  final Duration ttl;

  _CacheEntry({
    required this.value,
    required this.timestamp,
    required this.ttl,
  });

  bool get isExpired => DateTime.now().difference(timestamp) > ttl;
}

// ========== L2: 디스크 캐시 (Persistent Cache) ==========
class DiskCache {
  final Box _box;

  DiskCache(this._box);

  Future<T?> get<T>(String key) async {
    final entry = _box.get(key);
    if (entry == null) return null;

    final cacheEntry = entry as Map<String, dynamic>;
    final expiresAt = DateTime.parse(cacheEntry['expiresAt']);

    if (DateTime.now().isAfter(expiresAt)) {
      await _box.delete(key);
      return null;
    }

    return cacheEntry['value'] as T;
  }

  Future<void> set<T>(String key, T value, {required Duration ttl}) async {
    await _box.put(key, {
      'value': value,
      'expiresAt': DateTime.now().add(ttl).toIso8601String(),
    });
  }

  Future<void> invalidate(String prefix) async {
    final keysToDelete = _box.keys
        .where((key) => key.toString().startsWith(prefix))
        .toList();

    for (final key in keysToDelete) {
      await _box.delete(key);
    }
  }
}

// ========== Unified Cache Manager ==========
class CacheManager {
  final MemoryCache _memoryCache;
  final DiskCache _diskCache;

  CacheManager(this._memoryCache, this._diskCache);

  T? get<T>(String key) {
    // L1 캐시 확인
    final memCached = _memoryCache.get<T>(key);
    if (memCached != null) {
      logger.d('L1 cache hit: $key');
      return memCached;
    }

    // L2 캐시 확인 (동기적으로 처리하려면 별도 처리 필요)
    logger.d('L1 cache miss: $key');
    return null;
  }

  void set<T>(String key, T value, {required Duration ttl}) {
    // L1 캐시에 저장
    _memoryCache.set(key, value, ttl: ttl);

    // L2 캐시에 비동기 저장 (await 하지 않음)
    unawaited(_diskCache.set(key, value, ttl: ttl));
  }

  Future<void> invalidate(String prefix) async {
    _memoryCache.invalidate(prefix);
    await _diskCache.invalidate(prefix);
  }

  Future<void> clear() async {
    _memoryCache.clear();
    await _diskCache.invalidate('');
  }
}
```

### 4.2 캐시 무효화 전략

```dart
// ========== Cache Invalidation Strategies ==========

// 1. Time-Based Invalidation (TTL)
final cacheConfig = {
  'places': Duration(minutes: 5),      // 장소 목록: 5분
  'place_detail': Duration(hours: 1),  // 장소 상세: 1시간
  'user_profile': Duration(hours: 24), // 프로필: 24시간
  'search': Duration(minutes: 10),     // 검색 결과: 10분
};

// 2. Event-Based Invalidation
class PlaceRepository {
  Future<void> createPlace(Place place) async {
    await _remoteDataSource.createPlace(place.toDTO());

    // 관련 캐시 무효화
    _cacheManager.invalidate('places');        // 장소 목록
    _cacheManager.invalidate('search');        // 검색 결과
    _cacheManager.invalidate('user_profile');  // 내 장소 (프로필)
  }
}

// 3. Version-Based Invalidation
class ApiClient {
  final String _cacheVersion = 'v1';

  String _buildCacheKey(String key) {
    return '$_cacheVersion:$key';
  }

  Future<void> invalidateAllCaches() async {
    // 버전 변경으로 모든 캐시 무효화
    _cacheVersion = 'v2';
  }
}

// 4. Dependency-Based Invalidation
final cacheInvalidationRules = {
  'place_create': ['places', 'search', 'user_profile'],
  'place_update': ['places', 'place_detail', 'search'],
  'place_delete': ['places', 'search', 'courses'],
  'user_update': ['user_profile', 'courses'],
};
```

---

## 5. 오프라인 지원

### 5.1 동기화 큐 (Sync Queue)

```dart
// ========== Sync Queue - 오프라인 액션 큐잉 ==========
@freezed
class SyncAction with _$SyncAction {
  const factory SyncAction.likePlace(String placeId) = LikePlaceSyncAction;
  const factory SyncAction.savePlace(Place place) = SavePlaceSyncAction;
  const factory SyncAction.createCourse(Course course) = CreateCourseSyncAction;
  const factory SyncAction.deletePlace(String placeId) = DeletePlaceSyncAction;
}

class SyncQueue {
  final Box<Map<String, dynamic>> _queueBox;
  final ConnectivityService _connectivity;
  final ApiClient _apiClient;

  SyncQueue(this._queueBox, this._connectivity, this._apiClient) {
    _startSyncWorker();
  }

  Future<void> add(SyncAction action) async {
    final id = Uuid().v4();
    await _queueBox.put(id, {
      'id': id,
      'action': action.toJson(),
      'timestamp': DateTime.now().toIso8601String(),
      'retryCount': 0,
    });

    logger.i('Added to sync queue: ${action.runtimeType}');
  }

  void _startSyncWorker() {
    // 네트워크 상태 감시
    _connectivity.onConnectivityChanged.listen((isConnected) {
      if (isConnected) {
        _processSyncQueue();
      }
    });

    // 주기적 동기화 (5분마다)
    Timer.periodic(Duration(minutes: 5), (_) {
      _processSyncQueue();
    });
  }

  Future<void> _processSyncQueue() async {
    final isConnected = await _connectivity.isConnected;
    if (!isConnected) {
      logger.w('Offline: skipping sync queue processing');
      return;
    }

    final items = _queueBox.values.toList();
    if (items.isEmpty) {
      logger.d('Sync queue is empty');
      return;
    }

    logger.i('Processing ${items.length} sync actions');

    for (final item in items) {
      try {
        final action = SyncAction.fromJson(item['action']);
        await _executeAction(action);

        // 성공 시 큐에서 제거
        await _queueBox.delete(item['id']);
        logger.i('Sync action completed: ${action.runtimeType}');
      } catch (e) {
        // 재시도 카운트 증가
        final retryCount = item['retryCount'] as int;
        if (retryCount < 3) {
          await _queueBox.put(item['id'], {
            ...item,
            'retryCount': retryCount + 1,
          });
          logger.w('Sync action failed (retry ${retryCount + 1}/3): $e');
        } else {
          // 3회 실패 시 Dead Letter Queue로 이동
          await _moveToDeadLetterQueue(item);
          await _queueBox.delete(item['id']);
          logger.e('Sync action moved to DLQ after 3 failures: $e');
        }
      }
    }
  }

  Future<void> _executeAction(SyncAction action) async {
    await action.when(
      likePlace: (placeId) async {
        await _apiClient.post('/places/$placeId/like');
      },
      savePlace: (place) async {
        await _apiClient.post('/places/saved', data: place.toJson());
      },
      createCourse: (course) async {
        await _apiClient.post('/courses', data: course.toJson());
      },
      deletePlace: (placeId) async {
        await _apiClient.delete('/places/$placeId');
      },
    );
  }

  Future<void> _moveToDeadLetterQueue(Map<String, dynamic> item) async {
    // Dead Letter Queue에 저장 (관리자 확인용)
    final dlqBox = await Hive.openBox('sync_dlq');
    await dlqBox.add(item);
  }
}
```

### 5.2 오프라인 우선 데이터 액세스

```dart
// ========== Offline-First Repository Pattern ==========
class OfflineFirstPlaceRepository implements PlaceRepository {
  final PlaceRemoteDataSource _remoteDataSource;
  final PlaceLocalDataSource _localDataSource;
  final ConnectivityService _connectivity;

  @override
  Future<Result<List<Place>>> getPlaces({FilterOptions? filter}) async {
    try {
      // 1. 로컬 DB에서 즉시 반환 (Stale-While-Revalidate)
      final localPlaces = await _localDataSource.getCachedPlaces(filter);

      // 2. 백그라운드에서 API 호출 (네트워크 있을 경우)
      unawaited(_refreshPlacesInBackground(filter));

      return Result.success(localPlaces);
    } catch (e) {
      return Result.failure('데이터를 불러올 수 없습니다.');
    }
  }

  Future<void> _refreshPlacesInBackground(FilterOptions? filter) async {
    try {
      final isConnected = await _connectivity.isConnected;
      if (!isConnected) return;

      final placeDTOs = await _remoteDataSource.getPlaces(filter);
      final places = placeDTOs.map((dto) => dto.toEntity()).toList();

      // 로컬 DB 업데이트
      await _localDataSource.cachePlaces(places);

      logger.d('Background refresh completed: ${places.length} places');
    } catch (e) {
      logger.w('Background refresh failed: $e');
      // 실패해도 사용자에게 영향 없음 (이미 로컬 데이터 반환됨)
    }
  }
}
```

---

## 6. 실시간 동기화

### 6.1 WebSocket 연결 관리

```dart
// ========== WebSocket Client ==========
class WebSocketClient {
  final String url;
  IOWebSocketChannel? _channel;
  final _controller = StreamController<dynamic>.broadcast();
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;

  WebSocketClient(this.url);

  Stream<dynamic> get stream => _controller.stream;

  Future<void> connect() async {
    try {
      _channel = IOWebSocketChannel.connect(
        url,
        headers: {'Authorization': 'Bearer ${await _getToken()}'},
      );

      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      _startHeartbeat();
      _reconnectAttempts = 0;

      logger.i('WebSocket connected');
    } catch (e) {
      logger.e('WebSocket connection failed: $e');
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic message) {
    final data = jsonDecode(message);

    if (data['type'] == 'pong') {
      // Heartbeat 응답
      return;
    }

    _controller.add(data);
  }

  void _onError(error) {
    logger.e('WebSocket error: $error');
  }

  void _onDone() {
    logger.w('WebSocket connection closed');
    _heartbeatTimer?.cancel();
    _scheduleReconnect();
  }

  void _startHeartbeat() {
    _heartbeatTimer = Timer.periodic(Duration(seconds: 30), (_) {
      send({'type': 'ping'});
    });
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= 5) {
      logger.e('Max reconnect attempts reached');
      return;
    }

    final delay = Duration(seconds: min(30, pow(2, _reconnectAttempts).toInt()));
    _reconnectTimer = Timer(delay, () {
      _reconnectAttempts++;
      logger.i('Reconnecting (attempt $_reconnectAttempts)...');
      connect();
    });
  }

  void send(Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode(data));
  }

  Future<void> disconnect() async {
    _heartbeatTimer?.cancel();
    _reconnectTimer?.cancel();
    await _channel?.sink.close();
    await _controller.close();
  }

  Future<String> _getToken() async {
    // Get auth token
    return 'token';
  }
}

// ========== Real-time Updates Provider ==========
final placeUpdatesProvider = StreamProvider<PlaceUpdate>((ref) {
  final wsClient = ref.read(webSocketClientProvider);

  return wsClient.stream
      .where((data) => data['type'] == 'place_update')
      .map((data) => PlaceUpdate.fromJson(data['payload']));
});

// 사용 예시
class PlaceListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 실시간 업데이트 감지
    ref.listen<AsyncValue<PlaceUpdate>>(
      placeUpdatesProvider,
      (previous, next) {
        next.whenData((update) {
          // 로컬 상태 업데이트
          ref.read(placeListProvider.notifier).handleRealtimeUpdate(update);
        });
      },
    );

    return Scaffold(...);
  }
}
```

### 6.2 Optimistic Update 패턴

```dart
// ========== Optimistic Update ==========
class PlaceListNotifier extends StateNotifier<PlaceListState> {
  final PlaceRepository _repository;

  Future<void> toggleLike(String placeId) async {
    // 1. UI 즉시 업데이트 (Optimistic)
    final currentPlace = state.places.firstWhere((p) => p.id == placeId);
    final optimisticPlace = currentPlace.copyWith(
      isLiked: !currentPlace.isLiked,
      likeCount: currentPlace.isLiked
          ? currentPlace.likeCount - 1
          : currentPlace.likeCount + 1,
    );

    state = state.copyWith(
      places: state.places.map((p) => p.id == placeId ? optimisticPlace : p).toList(),
    );

    // 2. API 호출
    final result = await _repository.likePlace(placeId);

    // 3. 실패 시 롤백
    result.when(
      success: (_) {
        logger.i('Like action confirmed by server');
      },
      failure: (error) {
        // 롤백
        state = state.copyWith(
          places: state.places.map((p) => p.id == placeId ? currentPlace : p).toList(),
          error: error,
        );

        logger.e('Like action failed, rolled back: $error');
      },
    );
  }
}
```

---

## 7. 에러 핸들링

### 7.1 에러 분류 및 처리 전략

```dart
// ========== Custom Exceptions ==========
abstract class AppException implements Exception {
  final String message;
  final int? code;
  final dynamic originalError;

  AppException(this.message, {this.code, this.originalError});

  @override
  String toString() => 'AppException: $message (code: $code)';
}

// API 에러
class ApiException extends AppException {
  ApiException(String message, {int? code, dynamic originalError})
      : super(message, code: code, originalError: originalError);
}

// 네트워크 에러
class NetworkException extends AppException {
  NetworkException([String message = '네트워크 연결을 확인해주세요.'])
      : super(message);
}

// 인증 에러
class AuthException extends AppException {
  AuthException([String message = '로그인이 필요합니다.'])
      : super(message, code: 401);
}

// 캐시 에러
class CacheException extends AppException {
  CacheException(String message) : super(message);
}

// 비즈니스 로직 에러
class PlaceNotFoundException extends AppException {
  PlaceNotFoundException(String placeId)
      : super('장소를 찾을 수 없습니다. (ID: $placeId)', code: 404);
}

// ========== Error Handler ==========
class ErrorHandler {
  static String getUserFriendlyMessage(dynamic error) {
    if (error is NetworkException) {
      return '인터넷 연결을 확인해주세요.';
    } else if (error is AuthException) {
      return '로그인이 필요합니다.';
    } else if (error is ApiException) {
      if (error.code == 404) return '요청하신 내용을 찾을 수 없습니다.';
      if (error.code == 500) return '서버 오류가 발생했습니다.';
      return error.message;
    } else if (error is PlaceNotFoundException) {
      return '장소 정보를 불러올 수 없습니다.';
    }

    return '알 수 없는 오류가 발생했습니다.';
  }

  static bool shouldRetry(dynamic error) {
    if (error is NetworkException) return true;
    if (error is ApiException && error.code == 503) return true;
    return false;
  }

  static void logError(dynamic error, StackTrace stackTrace) {
    logger.e('Error occurred', error, stackTrace);

    // Crashlytics에 리포트
    FirebaseCrashlytics.instance.recordError(error, stackTrace);
  }
}

// ========== Retry Logic ==========
Future<T> retryOperation<T>(
  Future<T> Function() operation, {
  int maxAttempts = 3,
  Duration delay = const Duration(seconds: 1),
}) async {
  int attempts = 0;

  while (true) {
    try {
      return await operation();
    } catch (e) {
      attempts++;

      if (attempts >= maxAttempts || !ErrorHandler.shouldRetry(e)) {
        rethrow;
      }

      logger.w('Retry attempt $attempts/$maxAttempts after error: $e');
      await Future.delayed(delay * attempts); // Exponential backoff
    }
  }
}
```

### 7.2 전역 에러 처리

```dart
// ========== Global Error Boundary ==========
class App extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ProviderScope(
      observers: [ErrorObserver()],
      child: MaterialApp(...),
    );
  }
}

class ErrorObserver extends ProviderObserver {
  @override
  void didUpdateProvider(
    ProviderBase provider,
    Object? previousValue,
    Object? newValue,
    ProviderContainer container,
  ) {
    if (newValue is AsyncError) {
      final error = newValue.error;
      final stackTrace = newValue.stackTrace;

      ErrorHandler.logError(error, stackTrace);

      // 인증 에러 시 로그인 화면으로 리다이렉트
      if (error is AuthException) {
        // Navigate to login
        container.read(routerProvider).go('/login');
      }
    }
  }
}
```

---

## 8. 성능 최적화

### 8.1 Provider 최적화

```dart
// ========== 1. autoDispose로 메모리 누수 방지 ==========
// BAD: 사용하지 않을 때도 메모리 유지
final placesProvider = FutureProvider<List<Place>>((ref) async {
  return await ref.read(placeRepositoryProvider).getPlaces();
});

// GOOD: 화면을 벗어나면 자동 dispose
final placesProvider = FutureProvider.autoDispose<List<Place>>((ref) async {
  return await ref.read(placeRepositoryProvider).getPlaces();
});

// ========== 2. family로 매개변수화하여 캐싱 활용 ==========
final placeDetailProvider = FutureProvider.autoDispose.family<Place, String>(
  (ref, placeId) async {
    // placeId별로 개별 캐싱
    return await ref.read(placeRepositoryProvider).getPlaceById(placeId);
  },
);

// ========== 3. select로 불필요한 리빌드 방지 ==========
// BAD: places 전체 리스트 변경 시 리빌드
final places = ref.watch(placeListProvider).places;

// GOOD: places 개수만 필요할 경우
final placeCount = ref.watch(
  placeListProvider.select((state) => state.places.length),
);

// ========== 4. keepAlive로 캐시 유지 (필요 시) ==========
final expensiveDataProvider = FutureProvider.autoDispose<Data>((ref) async {
  // 비용이 큰 연산이라 캐시 유지 필요
  final link = ref.keepAlive();

  // 10초 후 자동 dispose
  Timer(Duration(seconds: 10), link.close);

  return await expensiveOperation();
});
```

### 8.2 리스트 렌더링 최적화

```dart
// ========== 1. ListView.builder로 Lazy Loading ==========
// BAD: 모든 아이템을 한번에 렌더링
ListView(
  children: places.map((place) => PlaceCard(place: place)).toList(),
);

// GOOD: 화면에 보이는 아이템만 렌더링
ListView.builder(
  itemCount: places.length,
  itemBuilder: (context, index) {
    return PlaceCard(place: places[index]);
  },
);

// ========== 2. const 생성자 활용 ==========
class PlaceCard extends StatelessWidget {
  final Place place;

  const PlaceCard({Key? key, required this.place}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Card(...); // const로 불변 위젯 표시
  }
}

// ========== 3. RepaintBoundary로 리페인트 격리 ==========
ListView.builder(
  itemBuilder: (context, index) {
    return RepaintBoundary(
      child: PlaceCard(place: places[index]),
    );
  },
);

// ========== 4. Infinite Scroll Pagination ==========
class PlaceListScreen extends ConsumerStatefulWidget {
  @override
  ConsumerState<PlaceListScreen> createState() => _PlaceListScreenState();
}

class _PlaceListScreenState extends ConsumerState<PlaceListScreen> {
  final PagingController<int, Place> _pagingController =
      PagingController(firstPageKey: 1);

  @override
  void initState() {
    super.initState();
    _pagingController.addPageRequestListener((pageKey) {
      _fetchPage(pageKey);
    });
  }

  Future<void> _fetchPage(int pageKey) async {
    try {
      final newPlaces = await ref
          .read(placeRepositoryProvider)
          .getPlaces(page: pageKey, pageSize: 20);

      final isLastPage = newPlaces.length < 20;
      if (isLastPage) {
        _pagingController.appendLastPage(newPlaces);
      } else {
        _pagingController.appendPage(newPlaces, pageKey + 1);
      }
    } catch (error) {
      _pagingController.error = error;
    }
  }

  @override
  Widget build(BuildContext context) {
    return PagedListView<int, Place>(
      pagingController: _pagingController,
      builderDelegate: PagedChildBuilderDelegate<Place>(
        itemBuilder: (context, place, index) => PlaceCard(place: place),
      ),
    );
  }
}
```

---

## 9. 완료 정의 (DoD)

### 9.1 상태 관리 완료 기준
- [x] Riverpod Provider 타입별 사용 가이드라인 정의
- [x] StateNotifier로 복잡한 상태 관리 구현
- [x] Provider 의존성 관리 패턴 수립
- [x] autoDispose로 메모리 누수 방지
- [x] Result 타입으로 에러 핸들링 표준화

### 9.2 데이터 플로우 완료 기준
- [x] Clean Architecture 레이어 간 데이터 흐름 정의
- [x] Repository 패턴 구현 (Remote + Local Data Source)
- [x] DTO ↔ Entity 변환 로직 구현
- [x] API Client 인터셉터 설정 (인증, 로깅, 재시도)

### 9.3 캐싱 완료 기준
- [x] L1 (메모리) + L2 (디스크) 다층 캐싱 구현
- [x] TTL 기반 캐시 무효화
- [x] 이벤트 기반 캐시 무효화
- [x] 캐시 히트율 60% 이상 달성

### 9.4 오프라인 지원 완료 기준
- [x] 동기화 큐 (Sync Queue) 구현
- [x] 오프라인 우선 데이터 액세스 패턴
- [x] Stale-While-Revalidate 전략
- [x] 오프라인 모드에서 80% 기능 가용

### 9.5 실시간 동기화 완료 기준
- [x] WebSocket 연결 관리 (자동 재연결)
- [x] Heartbeat 메커니즘
- [x] 실시간 이벤트 스트림 처리
- [x] Optimistic Update 패턴 구현

---

## 10. 수용 기준 (Acceptance Criteria)

### AC-1: 캐시 성능
- **Given** 사용자가 장소 목록 조회
- **When** 5분 이내 재조회
- **Then** 캐시에서 즉시 반환 (API 호출 없음), 로딩 시간 100ms 이내

### AC-2: 오프라인 동작
- **Given** 네트워크 연결 끊김
- **When** 저장된 장소 조회
- **Then** 로컬 DB에서 정상 조회, "오프라인 모드" 표시

### AC-3: 옵티미스틱 업데이트
- **Given** 사용자가 좋아요 버튼 클릭
- **When** 버튼 클릭 즉시
- **Then** UI 즉시 업데이트 (0.1초 이내), 백그라운드에서 API 호출

### AC-4: 실시간 동기화
- **Given** 다른 기기에서 장소 저장
- **When** 5초 이내
- **Then** 현재 기기에 WebSocket으로 푸시, UI 자동 업데이트

### AC-5: 에러 복구
- **Given** API 호출 실패 (네트워크 오류)
- **When** 3회 재시도 후에도 실패
- **Then** 동기화 큐에 추가, 네트워크 복구 시 자동 재시도

---

## 11. 참고 문서

- **내부 문서**:
  - `trd/frontend/01-flutter-tech-stack.md`: 기술 스택 및 아키텍처
  - `rules.md`: 코딩 컨벤션 및 TDD 가이드라인

- **외부 문서**:
  - [Riverpod Documentation](https://riverpod.dev/)
  - [Flutter Offline-First Best Practices](https://flutter.dev/docs/cookbook/persistence)
  - [WebSocket Protocol RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)

---

## 12. Changelog

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0 | 최초 작성 - 데이터 플로우 및 상태 관리 전략 정의 | Development Team |

---

*이 문서는 살아있는 문서(Living Document)로, 상태 관리 패턴 변경 시 즉시 업데이트됩니다.*
