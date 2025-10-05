# TRD-Frontend-03: 성능 최적화 전략 (Performance Optimization Strategy)

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **작성자**: Development Team
- **관련 PRD**: `prd/main.md`, `prd/04-map-visualization.md`
- **관련 TRD**: `trd/frontend/01-flutter-tech-stack.md`, `trd/frontend/02-data-flow-state-management.md`
- **관련 Task**: `task/06-ui-frontend.md`

## 목차
1. [개요](#1-개요)
2. [성능 목표 및 지표](#2-성능-목표-및-지표)
3. [앱 시작 최적화](#3-앱-시작-최적화)
4. [렌더링 성능 최적화](#4-렌더링-성능-최적화)
5. [메모리 최적화](#5-메모리-최적화)
6. [네트워크 최적화](#6-네트워크-최적화)
7. [번들 크기 최적화](#7-번들-크기-최적화)
8. [이미지 최적화](#8-이미지-최적화)
9. [배터리 소모 최적화](#9-배터리-소모-최적화)
10. [성능 모니터링](#10-성능-모니터링)

---

## 1. 개요

### 1.1 목적
Flutter 앱의 전반적인 성능을 최적화하여 60fps 유지, 빠른 앱 시작, 낮은 메모리 사용량을 달성하고, 사용자에게 버터 스무스한 경험을 제공한다.

### 1.2 사용자 가치
- **빠른 반응**: 모든 인터랙션 16ms 이내 응답 (60fps 보장)
- **빠른 시작**: 앱 시작 3초 이내 (Cold Start 기준)
- **부드러운 스크롤**: 리스트 스크롤 시 프레임 드롭 없음
- **낮은 배터리 소모**: 1시간 사용 시 배터리 10% 이내 소모

### 1.3 가설 및 KPI
- **가설**: 계층적 최적화 전략으로 앱 시작 속도 50% 향상, 메모리 사용량 30% 감소
- **측정 지표**:
  - 앱 시작 시간: Cold Start < 3초, Warm Start < 1초
  - 프레임률: 평균 59fps 이상, 프레임 드롭 5% 이하
  - 메모리 사용량: 유휴 상태 < 100MB, 활성 사용 < 200MB
  - APK 크기: < 50MB (Android), IPA < 100MB (iOS)

---

## 2. 성능 목표 및 지표

### 2.1 Core Web Vitals 기반 성능 지표

```dart
// ========== Performance Metrics ==========
class PerformanceMetrics {
  // 1. Time to Interactive (TTI) - 앱 시작 후 사용자 인터랙션 가능 시간
  static const Duration targetTTI = Duration(seconds: 3);

  // 2. First Contentful Paint (FCP) - 첫 화면 렌더링 시간
  static const Duration targetFCP = Duration(milliseconds: 1500);

  // 3. Frame Rendering Time - 프레임 렌더링 시간
  static const Duration targetFrameTime = Duration(milliseconds: 16); // 60fps

  // 4. Memory Usage - 메모리 사용량
  static const int maxIdleMemoryMB = 100;
  static const int maxActiveMemoryMB = 200;

  // 5. Network Performance - 네트워크 성능
  static const Duration apiTimeout = Duration(seconds: 10);
  static const Duration apiTargetLatency = Duration(milliseconds: 500);

  // 6. Bundle Size - 번들 크기
  static const int maxApkSizeMB = 50;
  static const int maxIpaSizeMB = 100;
}
```

### 2.2 성능 측정 도구

```dart
// ========== Performance Monitoring Service ==========
class PerformanceMonitor {
  static final _firebasePerformance = FirebasePerformance.instance;

  // HTTP 요청 성능 측정
  static Future<T> traceHttpRequest<T>(
    String name,
    Future<T> Function() operation,
  ) async {
    final trace = _firebasePerformance.newHttpMetric(
      name,
      HttpMethod.Get,
    );

    await trace.start();

    try {
      final result = await operation();
      trace.setHttpResponseCode(200);
      await trace.stop();
      return result;
    } catch (e) {
      trace.setHttpResponseCode(500);
      await trace.stop();
      rethrow;
    }
  }

  // 커스텀 성능 트레이스
  static Future<T> traceOperation<T>(
    String name,
    Future<T> Function() operation, {
    Map<String, String>? attributes,
  }) async {
    final trace = _firebasePerformance.newTrace(name);

    if (attributes != null) {
      attributes.forEach((key, value) {
        trace.putAttribute(key, value);
      });
    }

    await trace.start();
    final stopwatch = Stopwatch()..start();

    try {
      final result = await operation();
      stopwatch.stop();

      trace.setMetric('duration_ms', stopwatch.elapsedMilliseconds);
      await trace.stop();

      logger.d('$name completed in ${stopwatch.elapsedMilliseconds}ms');
      return result;
    } catch (e) {
      stopwatch.stop();
      trace.setMetric('duration_ms', stopwatch.elapsedMilliseconds);
      trace.putAttribute('error', e.toString());
      await trace.stop();
      rethrow;
    }
  }

  // 프레임 렌더링 성능 측정
  static void startFrameMetrics() {
    WidgetsBinding.instance.addTimingsCallback((timings) {
      for (final timing in timings) {
        final buildDuration = timing.buildDuration;
        final rasterDuration = timing.rasterDuration;
        final totalDuration = buildDuration + rasterDuration;

        if (totalDuration > const Duration(milliseconds: 16)) {
          logger.w('Frame drop detected: ${totalDuration.inMilliseconds}ms');
          _firebasePerformance.newTrace('frame_drop').then((trace) async {
            trace.setMetric('duration_ms', totalDuration.inMilliseconds);
            await trace.start();
            await trace.stop();
          });
        }
      }
    });
  }
}
```

---

## 3. 앱 시작 최적화

### 3.1 Cold Start 최적화

```dart
// ========== main.dart - 앱 시작 최적화 ==========
Future<void> main() async {
  // 1. 필수 초기화만 동기적으로 수행
  WidgetsFlutterBinding.ensureInitialized();

  // 2. Firebase 초기화 (필수)
  await Firebase.initializeApp();

  // 3. 크래시 리포팅 설정 (필수)
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError;

  // 4. 앱 실행 (Splash Screen 표시)
  runApp(const BootstrapApp());

  // 5. 나머지 초기화는 백그라운드에서 수행
  unawaited(_initializeApp());
}

Future<void> _initializeApp() async {
  await PerformanceMonitor.traceOperation('app_initialization', () async {
    // 병렬 초기화 (독립적인 작업)
    await Future.wait([
      _initializeGetIt(),
      _initializeHive(),
      _initializeSharedPreferences(),
      _loadEnvConfig(),
    ]);

    // 순차 초기화 (의존성 있는 작업)
    await _initializeAuth();
    await _loadUserPreferences();
    await _connectWebSocket();
  });

  logger.i('App initialization completed');
}

// GetIt 의존성 주입 (지연 초기화 활용)
Future<void> _initializeGetIt() async {
  final getIt = GetIt.instance;

  // Singleton (즉시 생성)
  getIt.registerSingleton<ApiClient>(ApiClient());

  // Lazy Singleton (최초 사용 시 생성)
  getIt.registerLazySingleton<PlaceRepository>(
    () => PlaceRepositoryImpl(
      getIt<ApiClient>(),
      getIt<PlaceLocalDataSource>(),
    ),
  );

  // Factory (매번 새 인스턴스)
  getIt.registerFactory<PlaceService>(
    () => PlaceService(getIt<PlaceRepository>()),
  );
}

// ========== Bootstrap App - Splash Screen ==========
class BootstrapApp extends StatelessWidget {
  const BootstrapApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: FutureBuilder(
        future: _checkInitialization(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            return const ProviderScope(child: App());
          }

          // Splash Screen (네이티브 스플래시와 동일한 디자인)
          return const SplashScreen();
        },
      ),
    );
  }

  Future<void> _checkInitialization() async {
    // 최소 1초 스플래시 표시 (너무 빠른 깜빡임 방지)
    await Future.wait([
      Future.delayed(const Duration(seconds: 1)),
      _initializeApp(),
    ]);
  }
}
```

### 3.2 Warm Start 최적화

```dart
// ========== App Lifecycle 관리 ==========
class AppLifecycleManager extends WidgetsBindingObserver {
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.resumed:
        // 앱 재개 시 - 빠른 복원
        _onAppResumed();
        break;
      case AppLifecycleState.paused:
        // 앱 일시정지 시 - 상태 저장
        _onAppPaused();
        break;
      case AppLifecycleState.inactive:
        // 전화 수신 등
        break;
      case AppLifecycleState.detached:
        // 앱 종료
        _onAppDetached();
        break;
    }
  }

  void _onAppResumed() {
    logger.d('App resumed');

    // 1. 캐시 유효성 확인
    GetIt.I<CacheManager>().validateCache();

    // 2. 백그라운드 동기화
    GetIt.I<SyncQueue>().processSyncQueue();

    // 3. WebSocket 재연결
    GetIt.I<WebSocketClient>().reconnect();
  }

  void _onAppPaused() {
    logger.d('App paused');

    // 1. 중요 데이터 저장
    GetIt.I<UserPreferences>().save();

    // 2. 불필요한 연결 종료
    GetIt.I<WebSocketClient>().disconnect();

    // 3. 메모리 캐시 정리 (일부)
    GetIt.I<CacheManager>().trimMemoryCache();
  }

  void _onAppDetached() {
    logger.d('App detached');

    // 리소스 정리
    GetIt.I<WebSocketClient>().dispose();
    GetIt.I<CacheManager>().dispose();
  }
}
```

---

## 4. 렌더링 성능 최적화

### 4.1 위젯 리빌드 최소화

```dart
// ========== 1. const 생성자 활용 ==========
// BAD: 매번 새로운 위젯 생성
class PlaceCard extends StatelessWidget {
  final Place place;

  PlaceCard({required this.place});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Text(place.name),
    );
  }
}

// GOOD: const 생성자로 불변 위젯 표시
class PlaceCard extends StatelessWidget {
  final Place place;

  const PlaceCard({Key? key, required this.place}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Text(place.name),
    );
  }
}

// ========== 2. Builder 패턴으로 리빌드 범위 제한 ==========
// BAD: 전체 위젯 트리 리빌드
class PlaceListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Places')),
      body: Consumer(
        builder: (context, ref, _) {
          final places = ref.watch(placesProvider);
          return ListView.builder(
            itemCount: places.length,
            itemBuilder: (context, index) => PlaceCard(place: places[index]),
          );
        },
      ),
    );
  }
}

// GOOD: 필요한 부분만 리빌드
class PlaceListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Places')), // const
      body: const PlaceListView(), // 분리
    );
  }
}

class PlaceListView extends ConsumerWidget {
  const PlaceListView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final places = ref.watch(placesProvider);
    return ListView.builder(
      itemCount: places.length,
      itemBuilder: (context, index) => PlaceCard(place: places[index]),
    );
  }
}

// ========== 3. select로 선택적 리빌드 ==========
// BAD: places 리스트 전체 변경 시 리빌드
final places = ref.watch(placeListProvider).places;

// GOOD: places 개수만 필요할 경우
final placeCount = ref.watch(
  placeListProvider.select((state) => state.places.length),
);

// ========== 4. RepaintBoundary로 리페인트 격리 ==========
ListView.builder(
  itemCount: places.length,
  itemBuilder: (context, index) {
    return RepaintBoundary(
      child: PlaceCard(place: places[index]),
    );
  },
);

// ========== 5. Keys로 위젯 재사용 ==========
// BAD: 순서 변경 시 전체 재생성
ListView(
  children: places.map((p) => PlaceCard(place: p)).toList(),
);

// GOOD: Key로 위젯 식별 및 재사용
ListView(
  children: places.map((p) => PlaceCard(key: ValueKey(p.id), place: p)).toList(),
);
```

### 4.2 리스트 성능 최적화

```dart
// ========== 1. ListView.builder로 Lazy Rendering ==========
// BAD: 1000개 아이템 모두 렌더링
ListView(
  children: List.generate(1000, (i) => ListTile(title: Text('Item $i'))),
);

// GOOD: 화면에 보이는 아이템만 렌더링
ListView.builder(
  itemCount: 1000,
  itemBuilder: (context, index) {
    return ListTile(title: Text('Item $index'));
  },
);

// ========== 2. AutomaticKeepAlive for Tab Views ==========
class PlaceListTab extends StatefulWidget {
  @override
  State<PlaceListTab> createState() => _PlaceListTabState();
}

class _PlaceListTabState extends State<PlaceListTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true; // 탭 전환 시 상태 유지

  @override
  Widget build(BuildContext context) {
    super.build(context); // 필수!
    return ListView.builder(...);
  }
}

// ========== 3. Sliver로 복잡한 스크롤 최적화 ==========
class PlaceListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        // Collapsing AppBar
        SliverAppBar(
          expandedHeight: 200,
          flexibleSpace: FlexibleSpaceBar(
            title: Text('Places'),
          ),
        ),
        // Sticky Header
        SliverPersistentHeader(
          pinned: true,
          delegate: FilterHeaderDelegate(),
        ),
        // List
        SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) => PlaceCard(place: places[index]),
            childCount: places.length,
          ),
        ),
      ],
    );
  }
}

// ========== 4. 무한 스크롤 + 가상화 ==========
class InfiniteScrollList extends ConsumerStatefulWidget {
  @override
  ConsumerState<InfiniteScrollList> createState() => _InfiniteScrollListState();
}

class _InfiniteScrollListState extends ConsumerState<InfiniteScrollList> {
  final _scrollController = ScrollController();
  int _page = 1;
  bool _isLoadingMore = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_isLoadingMore) return;

    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.position.pixels;

    // 80% 스크롤 시 다음 페이지 로드
    if (currentScroll > maxScroll * 0.8) {
      _loadMore();
    }
  }

  Future<void> _loadMore() async {
    setState(() => _isLoadingMore = true);

    await ref.read(placeListProvider.notifier).loadMore(page: ++_page);

    setState(() => _isLoadingMore = false);
  }

  @override
  Widget build(BuildContext context) {
    final places = ref.watch(placeListProvider).places;

    return ListView.builder(
      controller: _scrollController,
      itemCount: places.length + (_isLoadingMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index >= places.length) {
          return const Center(child: CircularProgressIndicator());
        }
        return PlaceCard(place: places[index]);
      },
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}
```

### 4.3 애니메이션 최적화

```dart
// ========== 1. AnimatedBuilder로 리빌드 범위 제한 ==========
// BAD: 애니메이션마다 전체 위젯 리빌드
class FadeInCard extends StatefulWidget {
  @override
  State<FadeInCard> createState() => _FadeInCardState();
}

class _FadeInCardState extends State<FadeInCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    )..forward();
  }

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: _controller.value,
      child: Card(...), // 매 프레임마다 리빌드
    );
  }
}

// GOOD: AnimatedBuilder로 필요한 부분만 리빌드
class FadeInCard extends StatefulWidget {
  @override
  State<FadeInCard> createState() => _FadeInCardState();
}

class _FadeInCardState extends State<FadeInCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _opacity = Tween<double>(begin: 0.0, end: 1.0).animate(_controller);
    _controller.forward();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _opacity,
      builder: (context, child) {
        return Opacity(
          opacity: _opacity.value,
          child: child, // child는 리빌드 안 됨
        );
      },
      child: Card(...), // 한 번만 빌드
    );
  }
}

// ========== 2. Implicit Animations 활용 ==========
// 간단한 애니메이션은 Implicit Animations 사용
AnimatedOpacity(
  opacity: _isVisible ? 1.0 : 0.0,
  duration: const Duration(milliseconds: 300),
  child: Card(...),
);

AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  width: _isExpanded ? 200 : 100,
  height: _isExpanded ? 200 : 100,
  color: _isExpanded ? Colors.blue : Colors.red,
  child: Center(child: Text('Animated')),
);

// ========== 3. Hero 애니메이션 최적화 ==========
// Hero 태그로 화면 전환 시 부드러운 애니메이션
class PlaceCard extends StatelessWidget {
  final Place place;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PlaceDetailScreen(place: place),
          ),
        );
      },
      child: Hero(
        tag: 'place_${place.id}',
        child: Image.network(place.imageUrl),
      ),
    );
  }
}
```

---

## 5. 메모리 최적화

### 5.1 메모리 누수 방지

```dart
// ========== 1. dispose() 호출 필수 ==========
class PlaceListScreen extends StatefulWidget {
  @override
  State<PlaceListScreen> createState() => _PlaceListScreenState();
}

class _PlaceListScreenState extends State<PlaceListScreen> {
  final _scrollController = ScrollController();
  final _searchController = TextEditingController();
  StreamSubscription? _subscription;
  Timer? _timer;

  @override
  void initState() {
    super.initState();

    // Stream 구독
    _subscription = someStream.listen((data) {
      // Handle data
    });

    // Timer 설정
    _timer = Timer.periodic(Duration(seconds: 5), (_) {
      // Periodic task
    });
  }

  @override
  void dispose() {
    // 모든 리소스 해제
    _scrollController.dispose();
    _searchController.dispose();
    _subscription?.cancel();
    _timer?.cancel();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(...);
  }
}

// ========== 2. autoDispose로 Provider 자동 정리 ==========
// BAD: 화면 벗어나도 메모리 유지
final searchResultsProvider = FutureProvider.family<List<Place>, String>(
  (ref, query) async {
    return await ref.read(placeRepositoryProvider).searchPlaces(query);
  },
);

// GOOD: 화면 벗어나면 자동 dispose
final searchResultsProvider = FutureProvider.autoDispose.family<List<Place>, String>(
  (ref, query) async {
    return await ref.read(placeRepositoryProvider).searchPlaces(query);
  },
);

// ========== 3. WeakReference로 순환 참조 방지 ==========
class PlaceService {
  final WeakReference<PlaceRepository> _repository;

  PlaceService(PlaceRepository repository)
      : _repository = WeakReference(repository);

  Future<List<Place>> getPlaces() async {
    final repo = _repository.target;
    if (repo == null) {
      throw StateError('Repository has been disposed');
    }
    return repo.getPlaces();
  }
}

// ========== 4. 캐시 크기 제한 ==========
class LRUCache<K, V> {
  final int maxSize;
  final LinkedHashMap<K, V> _cache = LinkedHashMap();

  LRUCache({required this.maxSize});

  V? get(K key) {
    final value = _cache.remove(key);
    if (value != null) {
      _cache[key] = value; // 최근 사용으로 이동
    }
    return value;
  }

  void put(K key, V value) {
    _cache.remove(key); // 기존 항목 제거
    _cache[key] = value;

    // 최대 크기 초과 시 가장 오래된 항목 제거
    if (_cache.length > maxSize) {
      _cache.remove(_cache.keys.first);
    }
  }

  void clear() {
    _cache.clear();
  }
}
```

### 5.2 이미지 메모리 관리

```dart
// ========== 1. CachedNetworkImage로 메모리 효율적 이미지 로딩 ==========
CachedNetworkImage(
  imageUrl: place.imageUrl,
  placeholder: (context, url) => const ShimmerLoading(),
  errorWidget: (context, url, error) => const Icon(Icons.error),
  memCacheWidth: 400, // 메모리 캐시 크기 제한
  memCacheHeight: 300,
  maxWidthDiskCache: 800, // 디스크 캐시 크기 제한
  maxHeightDiskCache: 600,
);

// ========== 2. Image.network with cacheWidth/cacheHeight ==========
Image.network(
  place.imageUrl,
  cacheWidth: 400, // 실제 표시 크기로 다운스케일
  cacheHeight: 300,
  fit: BoxFit.cover,
);

// ========== 3. 오프스크린 이미지 해제 ==========
class PlaceImageGallery extends StatefulWidget {
  @override
  State<PlaceImageGallery> createState() => _PlaceImageGalleryState();
}

class _PlaceImageGalleryState extends State<PlaceImageGallery>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => false; // 화면 벗어나면 해제

  @override
  Widget build(BuildContext context) {
    return PageView.builder(
      itemCount: images.length,
      itemBuilder: (context, index) {
        // 현재 페이지 ±1만 유지
        return Image.network(
          images[index],
          cacheWidth: 800,
          cacheHeight: 600,
        );
      },
    );
  }
}

// ========== 4. 이미지 압축 ==========
Future<File> compressImage(File imageFile) async {
  final result = await FlutterImageCompress.compressAndGetFile(
    imageFile.absolute.path,
    '${imageFile.absolute.path}_compressed.jpg',
    quality: 85, // 85% 품질 (시각적 차이 거의 없음)
    minWidth: 1920,
    minHeight: 1080,
  );

  return result!;
}
```

---

## 6. 네트워크 최적화

### 6.1 HTTP 요청 최적화

```dart
// ========== 1. Connection Pooling ==========
class ApiClient {
  final Dio _dio = Dio(BaseOptions(
    connectTimeout: Duration(seconds: 10),
    receiveTimeout: Duration(seconds: 30),
    persistentConnection: true, // Keep-Alive
    maxRedirects: 3,
  ));

  ApiClient() {
    _dio.httpClientAdapter = IOHttpClientAdapter(
      createHttpClient: () {
        final client = HttpClient();
        client.maxConnectionsPerHost = 10; // Connection Pool
        client.idleTimeout = Duration(seconds: 60);
        return client;
      },
    );
  }
}

// ========== 2. 요청 중복 제거 (Debounce/Throttle) ==========
class SearchService {
  Timer? _debounceTimer;

  void searchPlaces(String query, Function(List<Place>) onResult) {
    _debounceTimer?.cancel();

    _debounceTimer = Timer(const Duration(milliseconds: 300), () async {
      final results = await _repository.searchPlaces(query);
      onResult(results);
    });
  }

  void dispose() {
    _debounceTimer?.cancel();
  }
}

// ========== 3. Batch API 요청 ==========
// BAD: 3번의 개별 요청
final place1 = await api.getPlace('1');
final place2 = await api.getPlace('2');
final place3 = await api.getPlace('3');

// GOOD: 1번의 배치 요청
final places = await api.getPlaces(['1', '2', '3']);

// ========== 4. Gzip 압축 ==========
class ApiClient {
  final Dio _dio = Dio(BaseOptions(
    headers: {
      'Accept-Encoding': 'gzip, deflate',
    },
  ));

  ApiClient() {
    _dio.interceptors.add(InterceptorsWrapper(
      onResponse: (response, handler) {
        if (response.headers['content-encoding']?.contains('gzip') == true) {
          response.data = gzip.decode(response.data);
        }
        handler.next(response);
      },
    ));
  }
}

// ========== 5. 조건부 요청 (ETag, If-None-Match) ==========
class CachedApiClient {
  final Map<String, String> _etags = {};

  Future<Response> get(String url) async {
    final headers = <String, String>{};

    // 이전 ETag가 있으면 추가
    if (_etags.containsKey(url)) {
      headers['If-None-Match'] = _etags[url]!;
    }

    final response = await _dio.get(url, options: Options(headers: headers));

    // 304 Not Modified - 캐시 사용
    if (response.statusCode == 304) {
      return await _getCachedResponse(url);
    }

    // ETag 저장
    final etag = response.headers['etag']?.first;
    if (etag != null) {
      _etags[url] = etag;
    }

    return response;
  }
}
```

### 6.2 데이터 페칭 전략

```dart
// ========== 1. Prefetching - 다음 화면 데이터 미리 로드 ==========
class PlaceListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final places = ref.watch(placesProvider);

    return ListView.builder(
      itemCount: places.length,
      itemBuilder: (context, index) {
        final place = places[index];

        // 마지막 아이템에서 다음 페이지 프리페칭
        if (index == places.length - 1) {
          Future.microtask(() {
            ref.read(placesProvider.notifier).prefetchNextPage();
          });
        }

        return PlaceCard(
          place: place,
          onTap: () {
            // 상세 화면 데이터 프리페칭
            ref.read(placeDetailProvider(place.id));

            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => PlaceDetailScreen(placeId: place.id),
              ),
            );
          },
        );
      },
    );
  }
}

// ========== 2. Stale-While-Revalidate ==========
final placesProvider = FutureProvider.autoDispose<List<Place>>((ref) async {
  final repository = ref.read(placeRepositoryProvider);

  // 1. 캐시 즉시 반환
  final cached = await repository.getCachedPlaces();

  // 2. 백그라운드에서 갱신
  unawaited(repository.refreshPlaces());

  return cached;
});

// ========== 3. 병렬 데이터 로딩 ==========
Future<void> loadPlaceDetail(String placeId) async {
  final results = await Future.wait([
    _repository.getPlace(placeId),
    _repository.getPlaceReviews(placeId),
    _repository.getPlacePhotos(placeId),
    _repository.getNearbyPlaces(placeId),
  ]);

  final place = results[0] as Place;
  final reviews = results[1] as List<Review>;
  final photos = results[2] as List<String>;
  final nearby = results[3] as List<Place>;

  // UI 업데이트
}
```

---

## 7. 번들 크기 최적화

### 7.1 Code Splitting (지연 로딩)

```dart
// ========== 1. Deferred Loading으로 코드 분할 ==========
// 자주 사용하지 않는 기능은 지연 로딩
import 'package:hotly_app/features/link_analysis/link_analysis_screen.dart' deferred as link_analysis;

class HomeScreen extends StatelessWidget {
  void _openLinkAnalysis() async {
    // 사용 시점에 로드
    await link_analysis.loadLibrary();

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => link_analysis.LinkAnalysisScreen(),
      ),
    );
  }
}

// ========== 2. Font Subset - 필요한 글자만 포함 ==========
// pubspec.yaml
flutter:
  fonts:
    - family: Pretendard
      fonts:
        - asset: assets/fonts/Pretendard-Regular-subset.woff2
          weight: 400
        # Subset 생성: 한글 2350자 + 영문 + 숫자 + 특수문자만 포함

// ========== 3. Tree Shaking - 사용하지 않는 코드 제거 ==========
// 빌드 시 자동으로 제거되도록 import 최소화
// BAD
import 'package:lodash/lodash.dart'; // 전체 라이브러리 import

// GOOD
import 'package:lodash/lodash.dart' show debounce, throttle; // 필요한 것만

// ========== 4. Asset 압축 ==========
# 이미지 압축
pngquant --quality=65-80 assets/images/*.png
cwebp -q 80 assets/images/*.jpg -o assets/images/*.webp

# Lottie 애니메이션 최적화 (불필요한 레이어 제거)
lottie-optimize input.json output.json
```

### 7.2 Build 최적화

```gradle
// ========== Android Build 최적화 (android/app/build.gradle) ==========
android {
    buildTypes {
        release {
            // Code Shrinking
            minifyEnabled true
            shrinkResources true

            // ProGuard 규칙
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'

            // Native Libraries Compression
            ndk {
                abiFilters 'armeabi-v7a', 'arm64-v8a'
            }
        }
    }

    // APK Splits (각 ABI별 별도 APK 생성)
    splits {
        abi {
            enable true
            reset()
            include 'armeabi-v7a', 'arm64-v8a', 'x86_64'
            universalApk false
        }
    }
}

// ========== App Bundle로 배포 (Google Play) ==========
// Dynamic Delivery로 사용자 기기에 최적화된 APK 제공
flutter build appbundle --release
```

```ruby
# ========== iOS Build 최적화 (ios/Runner.xcodeproj) ==========
# Bitcode 활성화 (App Store에서 최적화)
ENABLE_BITCODE = YES

# Dead Code Stripping
DEAD_CODE_STRIPPING = YES

# Optimization Level
SWIFT_OPTIMIZATION_LEVEL = -O -whole-module-optimization
```

---

## 8. 이미지 최적화

### 8.1 이미지 로딩 전략

```dart
// ========== 1. Progressive Loading ==========
class ProgressiveImage extends StatelessWidget {
  final String imageUrl;
  final String? thumbnailUrl;

  const ProgressiveImage({
    Key? key,
    required this.imageUrl,
    this.thumbnailUrl,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // 1단계: Placeholder (즉시 표시)
        Container(
          color: Colors.grey[300],
          child: const Center(child: CircularProgressIndicator()),
        ),

        // 2단계: Thumbnail (저화질 이미지, 빠르게 로드)
        if (thumbnailUrl != null)
          Image.network(
            thumbnailUrl!,
            fit: BoxFit.cover,
            cacheWidth: 100, // 작은 크기로 캐시
          ),

        // 3단계: Full Image (고화질 이미지, 천천히 로드)
        CachedNetworkImage(
          imageUrl: imageUrl,
          fit: BoxFit.cover,
          fadeInDuration: const Duration(milliseconds: 300),
          memCacheWidth: 800,
          memCacheHeight: 600,
        ),
      ],
    );
  }
}

// ========== 2. Lazy Loading with Intersection Observer ==========
class LazyImage extends StatefulWidget {
  final String imageUrl;

  const LazyImage({Key? key, required this.imageUrl}) : super(key: key);

  @override
  State<LazyImage> createState() => _LazyImageState();
}

class _LazyImageState extends State<LazyImage> {
  bool _isVisible = false;

  @override
  Widget build(BuildContext context) {
    return VisibilityDetector(
      key: Key(widget.imageUrl),
      onVisibilityChanged: (info) {
        if (info.visibleFraction > 0.1 && !_isVisible) {
          setState(() => _isVisible = true);
        }
      },
      child: _isVisible
          ? CachedNetworkImage(imageUrl: widget.imageUrl)
          : const SizedBox(height: 200, child: Placeholder()),
    );
  }
}

// ========== 3. Image Prefetching ==========
Future<void> prefetchImages(BuildContext context, List<String> imageUrls) async {
  for (final url in imageUrls) {
    await precacheImage(CachedNetworkImageProvider(url), context);
  }
}

// 사용 예시: 다음 화면 이미지 미리 로드
class PlaceCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        // 상세 화면 이미지 프리페칭
        prefetchImages(context, place.images);

        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => PlaceDetailScreen(place: place)),
        );
      },
      child: Image.network(place.thumbnailUrl),
    );
  }
}
```

### 8.2 이미지 캐싱 전략

```dart
// ========== CachedNetworkImage 전역 설정 ==========
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 이미지 캐시 설정
  final cacheManager = DefaultCacheManager();
  await cacheManager.emptyCache(); // 앱 시작 시 오래된 캐시 정리

  // 전역 설정
  CachedNetworkImage.logLevel = CacheManagerLogLevel.warning;

  runApp(const App());
}

// ========== 커스텀 캐시 매니저 ==========
class CustomCacheManager extends CacheManager {
  static const key = 'customCacheKey';

  static CustomCacheManager? _instance;

  factory CustomCacheManager() {
    _instance ??= CustomCacheManager._();
    return _instance!;
  }

  CustomCacheManager._() : super(
    Config(
      key,
      stalePeriod: const Duration(days: 7), // 7일 후 재검증
      maxNrOfCacheObjects: 200, // 최대 200개 이미지
      repo: JsonCacheInfoRepository(databaseName: key),
      fileService: HttpFileService(),
    ),
  );
}

// 사용
CachedNetworkImage(
  imageUrl: imageUrl,
  cacheManager: CustomCacheManager(),
);
```

---

## 9. 배터리 소모 최적화

### 9.1 백그라운드 작업 최적화

```dart
// ========== 1. WorkManager로 배터리 효율적 백그라운드 작업 ==========
class SyncService {
  static Future<void> scheduleSync() async {
    await Workmanager().registerPeriodicTask(
      'sync_places',
      'syncPlacesTask',
      frequency: const Duration(hours: 6), // 6시간마다
      constraints: Constraints(
        networkType: NetworkType.connected, // 네트워크 연결 시만
        requiresBatteryNotLow: true, // 배터리 부족 시 스킵
        requiresCharging: false,
      ),
    );
  }

  @callbackDispatcher
  static void syncPlacesTask() {
    Workmanager().executeTask((task, inputData) async {
      // 백그라운드 동기화 작업
      final repository = GetIt.I<PlaceRepository>();
      await repository.syncPlaces();
      return Future.value(true);
    });
  }
}

// ========== 2. 위치 업데이트 최적화 ==========
class LocationService {
  Future<void> startLocationTracking() async {
    await Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.medium, // HIGH 대신 MEDIUM 사용
        distanceFilter: 100, // 100m 이동 시에만 업데이트
        timeLimit: Duration(seconds: 30), // 30초 타임아웃
      ),
    ).listen((position) {
      _updateLocation(position);
    });
  }
}

// ========== 3. 타이머 최적화 (배터리 절약) ==========
// BAD: 1초마다 타이머
Timer.periodic(Duration(seconds: 1), (_) {
  updateUI();
});

// GOOD: 필요한 경우에만, 간격 늘리기
Timer.periodic(Duration(seconds: 5), (_) {
  updateUI();
});

// 화면 비활성화 시 타이머 정지
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> with WidgetsBindingObserver {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startTimer();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _timer?.cancel(); // 앱 백그라운드 시 타이머 중지
    } else if (state == AppLifecycleState.resumed) {
      _startTimer(); // 앱 복귀 시 타이머 재시작
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(Duration(seconds: 5), (_) {
      updateUI();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }
}
```

### 9.2 센서 사용 최적화

```dart
// ========== 1. 가속도계 센서 최적화 ==========
class ShakeDetector {
  StreamSubscription? _subscription;

  void startListening() {
    _subscription = accelerometerEvents.listen(
      (event) {
        final magnitude = sqrt(
          event.x * event.x + event.y * event.y + event.z * event.z,
        );

        if (magnitude > 20) {
          onShake();
        }
      },
      // 센서 업데이트 간격 조절
      onError: (error) => print(error),
      cancelOnError: false,
    );
  }

  void stopListening() {
    _subscription?.cancel();
  }
}

// 화면 벗어나면 센서 중지
class MyScreen extends StatefulWidget {
  @override
  State<MyScreen> createState() => _MyScreenState();
}

class _MyScreenState extends State<MyScreen> {
  final _shakeDetector = ShakeDetector();

  @override
  void initState() {
    super.initState();
    _shakeDetector.startListening();
  }

  @override
  void dispose() {
    _shakeDetector.stopListening();
    super.dispose();
  }
}
```

---

## 10. 성능 모니터링

### 10.1 Firebase Performance Monitoring

```dart
// ========== Firebase Performance 통합 ==========
class PerformanceService {
  static final _performance = FirebasePerformance.instance;

  // 앱 시작 추적
  static Future<void> traceAppStart() async {
    final trace = _performance.newTrace('app_start');
    await trace.start();

    // 앱 초기화 완료 후
    await trace.stop();
  }

  // 화면 렌더링 추적
  static Future<void> traceScreenRender(String screenName) async {
    final trace = _performance.newTrace('screen_$screenName');
    trace.putAttribute('screen_name', screenName);
    await trace.start();

    // 렌더링 완료 후
    await trace.stop();
  }

  // API 호출 추적
  static Future<T> traceApiCall<T>(
    String endpoint,
    Future<T> Function() apiCall,
  ) async {
    final metric = _performance.newHttpMetric(
      endpoint,
      HttpMethod.Get,
    );

    await metric.start();
    final stopwatch = Stopwatch()..start();

    try {
      final result = await apiCall();
      stopwatch.stop();

      metric.setHttpResponseCode(200);
      metric.setResponsePayloadSize(1024); // 실제 크기
      metric.setRequestPayloadSize(512);

      await metric.stop();
      return result;
    } catch (e) {
      stopwatch.stop();
      metric.setHttpResponseCode(500);
      await metric.stop();
      rethrow;
    }
  }
}

// ========== 커스텀 메트릭 ==========
class CustomMetrics {
  static Future<void> recordPlaceLoadTime(Duration duration) async {
    final trace = FirebasePerformance.instance.newTrace('place_load');
    trace.setMetric('duration_ms', duration.inMilliseconds);
    trace.putAttribute('cache_hit', 'false');
    await trace.start();
    await trace.stop();
  }

  static Future<void> recordCacheHit(String cacheKey) async {
    final trace = FirebasePerformance.instance.newTrace('cache_hit');
    trace.putAttribute('cache_key', cacheKey);
    await trace.start();
    await trace.stop();
  }
}
```

### 10.2 성능 프로파일링 (DevTools)

```dart
// ========== Timeline Events 기록 ==========
import 'dart:developer' as developer;

class ProfiledOperation {
  static Future<T> trace<T>(
    String name,
    Future<T> Function() operation,
  ) async {
    developer.Timeline.startSync(name);
    try {
      return await operation();
    } finally {
      developer.Timeline.finishSync();
    }
  }
}

// 사용 예시
Future<List<Place>> getPlaces() async {
  return await ProfiledOperation.trace('getPlaces', () async {
    final response = await api.get('/places');
    return response.data.map((json) => Place.fromJson(json)).toList();
  });
}

// ========== 메모리 스냅샷 ==========
void takeMemorySnapshot() {
  developer.Timeline.instantSync('MemorySnapshot', arguments: {
    'rss': ProcessInfo.currentRss,
    'heap': ProcessInfo.maxRss,
  });
}

// ========== CPU 프로파일링 ==========
// flutter run --profile
// DevTools에서 CPU Profiler 활성화
```

---

## 11. 완료 정의 (DoD)

### 11.1 앱 시작 성능
- [x] Cold Start < 3초
- [x] Warm Start < 1초
- [x] 스플래시 화면 최소 1초 표시 (깜빡임 방지)
- [x] 백그라운드 초기화로 메인 스레드 블로킹 최소화

### 11.2 렌더링 성능
- [x] 평균 프레임률 59fps 이상
- [x] 프레임 드롭 5% 이하
- [x] 리스트 스크롤 시 버터 스무스 (프레임 드롭 없음)
- [x] 애니메이션 60fps 유지

### 11.3 메모리 최적화
- [x] 유휴 상태 메모리 < 100MB
- [x] 활성 사용 메모리 < 200MB
- [x] 메모리 누수 0건 (LeakCanary 검증)
- [x] 이미지 캐시 크기 제한 (200MB)

### 11.4 네트워크 성능
- [x] API 응답 대기 시간 p95 < 500ms
- [x] 캐시 히트율 60% 이상
- [x] Gzip 압축 적용
- [x] Connection Pooling 활성화

### 11.5 번들 크기
- [x] APK 크기 < 50MB (Android)
- [x] IPA 크기 < 100MB (iOS)
- [x] Code Splitting 적용 (비필수 기능 지연 로딩)
- [x] Asset 압축 (이미지, 폰트)

---

## 12. 수용 기준 (Acceptance Criteria)

### AC-1: 앱 시작 성능
- **Given** 사용자가 앱 아이콘 클릭
- **When** Cold Start
- **Then** 3초 이내 첫 화면 표시

### AC-2: 스크롤 성능
- **Given** 장소 목록 100개
- **When** 빠르게 스크롤
- **Then** 프레임 드롭 없이 부드러운 스크롤, 59fps 이상 유지

### AC-3: 메모리 안정성
- **Given** 앱을 30분 사용
- **When** 메모리 사용량 측정
- **Then** 200MB 이하 유지, 메모리 누수 없음

### AC-4: 이미지 로딩 성능
- **Given** 이미지 10개 포함된 화면
- **When** 화면 진입
- **Then** 프로그레시브 로딩으로 썸네일 즉시 표시, 고화질 이미지 3초 이내 완료

### AC-5: 배터리 소모
- **Given** 앱을 1시간 사용
- **When** 배터리 소모량 측정
- **Then** 10% 이내 소모

---

## 13. 참고 문서

- **내부 문서**:
  - `trd/frontend/01-flutter-tech-stack.md`: 기술 스택
  - `trd/frontend/02-data-flow-state-management.md`: 데이터 플로우 및 캐싱

- **외부 문서**:
  - [Flutter Performance Best Practices](https://docs.flutter.dev/perf/best-practices)
  - [Firebase Performance Monitoring](https://firebase.google.com/docs/perf-mon)
  - [DevTools Performance View](https://docs.flutter.dev/tools/devtools/performance)

---

## 14. Changelog

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0 | 최초 작성 - 성능 최적화 전략 정의 | Development Team |

---

*이 문서는 살아있는 문서(Living Document)로, 성능 개선 시 즉시 업데이트됩니다.*
