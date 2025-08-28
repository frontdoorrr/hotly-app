# TRD: 지도 기반 시각화 및 경로 표시

## 1. 기술 개요
**목적:** PRD 04-map-visualization 요구사항을 충족하기 위한 지도 기반 시각화 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- 지도 SDK: Kakao Map JavaScript API v2 + Flutter plugin
- 위치 서비스: GPS + Network Location Provider
- 경로 계산: Kakao Directions API + Google Directions API
- 실시간 추적: WebRTC + WebSocket for position streaming
- 캐싱: Redis (지도 타일) + SQLite (오프라인 지도)

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Flutter App] → [Map Widget]
    ↓
[Native Bridge] → [Kakao Map SDK]
    ↓
[Location Service] ← [GPS/Network Provider]
    ↓
[Map Controller] → [Marker Manager] → [Route Renderer]
    ↓
[Cache Layer] → [Tile Cache] + [Route Cache]
    ↓
[Backend APIs] → [Place Service] + [Route Service]
```

### 2-2. 컴포넌트 구성
```
1. Map Rendering Engine
   - 지도 타일 로딩 및 캐싱
   - 마커 클러스터링 및 렌더링
   - 경로 시각화 및 애니메이션

2. Location Tracking Service
   - GPS 위치 추적
   - 배터리 최적화된 위치 업데이트
   - 위치 정확도 보정

3. Route Visualization Service
   - 경로 계산 및 표시
   - 실시간 내비게이션
   - 교통 정보 반영

4. Marker Management System
   - 동적 마커 생성/삭제
   - 마커 클러스터링
   - 상호작용 이벤트 처리
```

---

## 3. Flutter 지도 통합

### 3-1. Kakao Map Flutter Plugin
```dart
// kakao_map_plugin.dart
class KakaoMapPlugin {
  static const MethodChannel _channel = MethodChannel('kakao_map_plugin');
  
  static Future<void> initialize(String apiKey) async {
    await _channel.invokeMethod('initialize', {'apiKey': apiKey});
  }
  
  static Future<void> showMap(MapOptions options) async {
    await _channel.invokeMethod('showMap', options.toJson());
  }
}

class KakaoMapWidget extends StatefulWidget {
  final MapOptions options;
  final Function(KakaoMapController)? onMapCreated;
  final Function(LatLng)? onMapTap;
  final Function(Marker)? onMarkerTap;

  const KakaoMapWidget({
    Key? key,
    required this.options,
    this.onMapCreated,
    this.onMapTap,
    this.onMarkerTap,
  }) : super(key: key);

  @override
  _KakaoMapWidgetState createState() => _KakaoMapWidgetState();
}

class _KakaoMapWidgetState extends State<KakaoMapWidget> {
  KakaoMapController? _controller;

  @override
  Widget build(BuildContext context) {
    return AndroidView(
      viewType: 'kakao_map_view',
      onPlatformViewCreated: _onPlatformViewCreated,
      creationParams: widget.options.toJson(),
      creationParamsCodec: const StandardMessageCodec(),
    );
  }

  void _onPlatformViewCreated(int id) {
    _controller = KakaoMapController._(id);
    widget.onMapCreated?.call(_controller!);
  }
}

class KakaoMapController {
  final int _mapId;
  static const MethodChannel _channel = MethodChannel('kakao_map_plugin');

  KakaoMapController._(this._mapId);

  Future<void> addMarker(Marker marker) async {
    await _channel.invokeMethod('addMarker', {
      'mapId': _mapId,
      'marker': marker.toJson(),
    });
  }

  Future<void> removeMarker(String markerId) async {
    await _channel.invokeMethod('removeMarker', {
      'mapId': _mapId,
      'markerId': markerId,
    });
  }

  Future<void> drawRoute(List<LatLng> points, RouteStyle style) async {
    await _channel.invokeMethod('drawRoute', {
      'mapId': _mapId,
      'points': points.map((p) => p.toJson()).toList(),
      'style': style.toJson(),
    });
  }

  Future<void> animateCamera(CameraUpdate update) async {
    await _channel.invokeMethod('animateCamera', {
      'mapId': _mapId,
      'update': update.toJson(),
    });
  }

  Future<void> setMyLocationEnabled(bool enabled) async {
    await _channel.invokeMethod('setMyLocationEnabled', {
      'mapId': _mapId,
      'enabled': enabled,
    });
  }
}
```

### 3-2. 마커 관리 시스템
```dart
class MarkerManager {
  final KakaoMapController _controller;
  final Map<String, Marker> _markers = {};
  final MarkerClusterer _clusterer;

  MarkerManager(this._controller) : _clusterer = MarkerClusterer();

  Future<void> addPlaceMarkers(List<Place> places) async {
    _clearMarkers();
    
    final markers = places.map((place) => Marker(
      id: place.id,
      position: LatLng(place.latitude, place.longitude),
      icon: _getMarkerIcon(place.category),
      infoWindow: InfoWindow(
        title: place.name,
        snippet: place.address,
      ),
      onTap: () => _onMarkerTapped(place),
    )).toList();

    // 클러스터링 적용
    final clusteredMarkers = await _clusterer.cluster(markers);
    
    for (final marker in clusteredMarkers) {
      _markers[marker.id] = marker;
      await _controller.addMarker(marker);
    }
  }

  Future<void> addCourseMarkers(Course course) async {
    _clearMarkers();
    
    for (int i = 0; i < course.places.length; i++) {
      final place = course.places[i];
      final marker = Marker(
        id: 'course_${place.id}',
        position: LatLng(place.latitude, place.longitude),
        icon: _getCourseMarkerIcon(i + 1, place.category),
        infoWindow: InfoWindow(
          title: '${i + 1}. ${place.name}',
          snippet: '${place.arrivalTime} - ${place.departureTime}',
        ),
        zIndex: 100 + i,
      );
      
      _markers[marker.id] = marker;
      await _controller.addMarker(marker);
    }

    // 경로 표시
    await _drawCourseRoute(course);
  }

  MarkerIcon _getMarkerIcon(PlaceCategory category) {
    final color = _getCategoryColor(category);
    final iconPath = _getCategoryIcon(category);
    
    return MarkerIcon(
      imagePath: iconPath,
      size: const Size(40, 40),
      backgroundColor: color,
      borderColor: Colors.white,
      borderWidth: 2,
    );
  }

  MarkerIcon _getCourseMarkerIcon(int order, PlaceCategory category) {
    final color = _getCategoryColor(category);
    
    return MarkerIcon(
      text: order.toString(),
      textStyle: const TextStyle(
        color: Colors.white,
        fontSize: 14,
        fontWeight: FontWeight.bold,
      ),
      backgroundColor: color,
      borderColor: Colors.white,
      borderWidth: 2,
      size: const Size(32, 32),
    );
  }

  Color _getCategoryColor(PlaceCategory category) {
    switch (category) {
      case PlaceCategory.restaurant:
        return Colors.red;
      case PlaceCategory.cafe:
        return Colors.brown;
      case PlaceCategory.tourist:
        return Colors.blue;
      case PlaceCategory.shopping:
        return Colors.green;
      case PlaceCategory.culture:
        return Colors.purple;
      case PlaceCategory.activity:
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  Future<void> _clearMarkers() async {
    for (final markerId in _markers.keys) {
      await _controller.removeMarker(markerId);
    }
    _markers.clear();
  }

  void _onMarkerTapped(Place place) {
    // 마커 탭 이벤트 처리
    showModalBottomSheet(
      context: context,
      builder: (context) => PlaceDetailSheet(place: place),
    );
  }
}
```

### 3-3. 경로 렌더링 시스템
```dart
class RouteRenderer {
  final KakaoMapController _controller;
  final RouteCalculator _calculator;
  final List<Polyline> _activeRoutes = [];

  RouteRenderer(this._controller) : _calculator = RouteCalculator();

  Future<void> drawCourseRoute(Course course) async {
    _clearRoutes();

    for (int i = 0; i < course.places.length - 1; i++) {
      final from = course.places[i];
      final to = course.places[i + 1];
      
      final routePoints = await _calculator.calculateRoute(
        from: LatLng(from.latitude, from.longitude),
        to: LatLng(to.latitude, to.longitude),
        transportMode: course.transportMethod,
      );

      final routeStyle = _getRouteStyle(i, course.places.length);
      final polyline = Polyline(
        id: 'route_$i',
        points: routePoints,
        color: routeStyle.color,
        width: routeStyle.width,
        pattern: routeStyle.pattern,
        gradient: routeStyle.gradient,
      );

      _activeRoutes.add(polyline);
      await _controller.drawRoute(routePoints, routeStyle);
    }

    // 경로 애니메이션 효과
    await _animateRouteDrawing();
  }

  RouteStyle _getRouteStyle(int segmentIndex, int totalSegments) {
    // 진행도에 따른 그라데이션 색상
    final progress = segmentIndex / (totalSegments - 1);
    final color = Color.lerp(
      Colors.blue,
      Colors.red,
      progress,
    )!;

    return RouteStyle(
      color: color,
      width: 4.0,
      gradient: LinearGradient(
        colors: [
          color.withOpacity(0.7),
          color,
        ],
      ),
      pattern: _getPatternForTransport(),
    );
  }

  List<PatternItem> _getPatternForTransport() {
    // 교통수단별 선 패턴
    switch (transportMethod) {
      case TransportMethod.walking:
        return [Dash(4), Gap(4)]; // 점선
      case TransportMethod.transit:
        return []; // 실선
      case TransportMethod.driving:
        return [Dash(8), Gap(2)]; // 굵은 점선
      default:
        return [];
    }
  }

  Future<void> _animateRouteDrawing() async {
    // 경로를 단계별로 그리는 애니메이션
    for (int i = 0; i < _activeRoutes.length; i++) {
      await Future.delayed(const Duration(milliseconds: 300));
      await _drawRouteWithAnimation(_activeRoutes[i]);
    }
  }

  Future<void> _drawRouteWithAnimation(Polyline route) async {
    final points = route.points;
    final animatedPoints = <LatLng>[];

    for (int i = 0; i < points.length; i++) {
      animatedPoints.add(points[i]);
      await _controller.updateRoute(route.id, animatedPoints);
      await Future.delayed(const Duration(milliseconds: 50));
    }
  }

  Future<void> _clearRoutes() async {
    for (final route in _activeRoutes) {
      await _controller.removeRoute(route.id);
    }
    _activeRoutes.clear();
  }
}
```

---

## 4. 실시간 위치 추적

### 4-1. 위치 서비스
```dart
class LocationTrackingService {
  static const LocationSettings _settingsHigh = LocationSettings(
    accuracy: LocationAccuracy.high,
    distanceFilter: 1,
    timeLimit: Duration(minutes: 10),
  );
  
  static const LocationSettings _settingsBalanced = LocationSettings(
    accuracy: LocationAccuracy.balanced,
    distanceFilter: 5,
    timeLimit: Duration(minutes: 5),
  );

  StreamSubscription<Position>? _positionSubscription;
  final StreamController<UserLocation> _locationController = 
      StreamController<UserLocation>.broadcast();

  Stream<UserLocation> get locationStream => _locationController.stream;

  Future<bool> initialize() async {
    // 권한 요청
    LocationPermission permission = await Geolocator.checkPermission();
    
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return false;
    }

    return true;
  }

  Future<void> startTracking({required TrackingMode mode}) async {
    if (_positionSubscription != null) {
      await stopTracking();
    }

    final settings = mode == TrackingMode.navigation 
        ? _settingsHigh 
        : _settingsBalanced;

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: settings,
    ).listen(
      _onLocationUpdate,
      onError: _onLocationError,
    );
  }

  Future<void> stopTracking() async {
    await _positionSubscription?.cancel();
    _positionSubscription = null;
  }

  void _onLocationUpdate(Position position) {
    final userLocation = UserLocation(
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy,
      heading: position.heading,
      speed: position.speed,
      timestamp: position.timestamp,
    );

    _locationController.add(userLocation);
  }

  void _onLocationError(Object error) {
    logger.error('Location tracking error: $error');
    // 오류 처리 및 fallback
    _handleLocationError(error);
  }

  void _handleLocationError(Object error) {
    if (error is LocationServiceDisabledException) {
      // GPS 비활성화
      _showLocationServiceDialog();
    } else if (error is PermissionDeniedException) {
      // 권한 거부
      _showPermissionDeniedDialog();
    } else {
      // 기타 오류 - 네트워크 위치로 fallback
      _fallbackToNetworkLocation();
    }
  }

  Future<void> _fallbackToNetworkLocation() async {
    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 10),
      );
      _onLocationUpdate(position);
    } catch (e) {
      logger.warning('Network location fallback failed: $e');
    }
  }
}
```

### 4-2. 실시간 내비게이션
```dart
class NavigationService {
  final LocationTrackingService _locationService;
  final RouteCalculator _routeCalculator;
  final VoiceGuideService _voiceGuide;
  
  Course? _currentCourse;
  int _currentDestinationIndex = 0;
  NavigationState _state = NavigationState.idle;

  NavigationService(this._locationService, this._routeCalculator, this._voiceGuide);

  Future<void> startNavigation(Course course) async {
    _currentCourse = course;
    _currentDestinationIndex = 0;
    _state = NavigationState.navigating;

    // 실시간 위치 추적 시작
    await _locationService.startTracking(mode: TrackingMode.navigation);

    // 위치 업데이트 구독
    _locationService.locationStream.listen(_onLocationUpdate);

    // 첫 번째 목적지로 경로 계산
    await _calculateRouteToNextDestination();

    // 음성 안내 시작
    await _voiceGuide.announceNavigationStart(_getCurrentDestination());
  }

  Future<void> stopNavigation() async {
    _state = NavigationState.idle;
    await _locationService.stopTracking();
    await _voiceGuide.stop();
  }

  void _onLocationUpdate(UserLocation location) {
    if (_state != NavigationState.navigating || _currentCourse == null) {
      return;
    }

    final currentDestination = _getCurrentDestination();
    final distanceToDestination = Geolocator.distanceBetween(
      location.latitude,
      location.longitude,
      currentDestination.latitude,
      currentDestination.longitude,
    );

    // 도착 감지 (50m 이내)
    if (distanceToDestination <= 50) {
      _handleArrival();
      return;
    }

    // 경로 이탈 감지
    if (_isOffRoute(location)) {
      _handleRouteDeviation(location);
      return;
    }

    // 진행 상황 업데이트
    _updateNavigationProgress(location, distanceToDestination);
  }

  void _handleArrival() async {
    final destination = _getCurrentDestination();
    
    await _voiceGuide.announceArrival(destination);
    
    // 마지막 목적지인지 확인
    if (_currentDestinationIndex >= _currentCourse!.places.length - 1) {
      await _completeNavigation();
    } else {
      // 다음 목적지로 이동
      _currentDestinationIndex++;
      await _calculateRouteToNextDestination();
      await _voiceGuide.announceNextDestination(_getCurrentDestination());
    }
  }

  bool _isOffRoute(UserLocation location) {
    // 현재 경로에서 100m 이상 벗어났는지 확인
    final currentRoute = _getCurrentRoute();
    if (currentRoute == null) return false;

    double minDistance = double.infinity;
    for (final point in currentRoute) {
      final distance = Geolocator.distanceBetween(
        location.latitude,
        location.longitude,
        point.latitude,
        point.longitude,
      );
      minDistance = math.min(minDistance, distance);
    }

    return minDistance > 100; // 100m 이탈 시 true
  }

  Future<void> _handleRouteDeviation(UserLocation location) async {
    await _voiceGuide.announceRouteRecalculation();
    
    // 현재 위치에서 목적지까지 새로운 경로 계산
    await _calculateRouteToNextDestination(from: location);
  }

  void _updateNavigationProgress(UserLocation location, double distanceToDestination) {
    final progress = NavigationProgress(
      currentLocation: location,
      destination: _getCurrentDestination(),
      distanceRemaining: distanceToDestination,
      estimatedTimeArrival: _calculateETA(distanceToDestination),
    );

    _navigationProgressController.add(progress);
  }

  Future<void> _calculateRouteToNextDestination({UserLocation? from}) async {
    final destination = _getCurrentDestination();
    final origin = from ?? await _locationService.getCurrentLocation();
    
    final route = await _routeCalculator.calculateRoute(
      from: LatLng(origin.latitude, origin.longitude),
      to: LatLng(destination.latitude, destination.longitude),
      transportMode: _currentCourse!.transportMethod,
    );

    _currentRoute = route;
    _routeUpdateController.add(route);
  }

  Place _getCurrentDestination() {
    return _currentCourse!.places[_currentDestinationIndex];
  }
}
```

---

## 5. 지도 캐싱 시스템

### 5-1. 타일 캐시 매니저
```dart
class MapTileCache {
  static const String _cacheKey = 'map_tiles';
  static const int _maxCacheSize = 50 * 1024 * 1024; // 50MB
  static const Duration _tileExpiry = Duration(days: 7);

  final Directory _cacheDir;
  final Map<String, MapTile> _memoryCache = {};
  
  MapTileCache(this._cacheDir);

  Future<void> initialize() async {
    await _loadCacheIndex();
    await _cleanExpiredTiles();
  }

  Future<Uint8List?> getTile(int x, int y, int zoom) async {
    final tileKey = _generateTileKey(x, y, zoom);
    
    // 메모리 캐시 확인
    final memoryCachedTile = _memoryCache[tileKey];
    if (memoryCachedTile != null) {
      return memoryCachedTile.data;
    }

    // 디스크 캐시 확인
    final diskCachedTile = await _loadTileFromDisk(tileKey);
    if (diskCachedTile != null && !_isTileExpired(diskCachedTile)) {
      _memoryCache[tileKey] = diskCachedTile;
      return diskCachedTile.data;
    }

    return null;
  }

  Future<void> cacheTile(int x, int y, int zoom, Uint8List data) async {
    final tileKey = _generateTileKey(x, y, zoom);
    final tile = MapTile(
      key: tileKey,
      data: data,
      createdAt: DateTime.now(),
    );

    // 메모리 캐시 저장
    _memoryCache[tileKey] = tile;

    // 메모리 캐시 크기 제한
    if (_memoryCache.length > 100) {
      _evictOldestTiles();
    }

    // 디스크 캐시 저장
    await _saveTileToDisk(tile);

    // 캐시 크기 확인 및 정리
    await _checkCacheSize();
  }

  String _generateTileKey(int x, int y, int zoom) {
    return '${zoom}_${x}_$y';
  }

  Future<MapTile?> _loadTileFromDisk(String tileKey) async {
    try {
      final file = File('${_cacheDir.path}/$tileKey.tile');
      if (await file.exists()) {
        final data = await file.readAsBytes();
        final metadata = await _loadTileMetadata(tileKey);
        
        return MapTile(
          key: tileKey,
          data: data,
          createdAt: metadata?['createdAt'] ?? DateTime.now(),
        );
      }
    } catch (e) {
      logger.warning('Failed to load tile from disk: $e');
    }
    return null;
  }

  Future<void> _saveTileToDisk(MapTile tile) async {
    try {
      final file = File('${_cacheDir.path}/${tile.key}.tile');
      await file.writeAsBytes(tile.data);
      
      await _saveTileMetadata(tile.key, {
        'createdAt': tile.createdAt.millisecondsSinceEpoch,
        'size': tile.data.length,
      });
    } catch (e) {
      logger.error('Failed to save tile to disk: $e');
    }
  }

  void _evictOldestTiles() {
    final entries = _memoryCache.entries.toList();
    entries.sort((a, b) => a.value.createdAt.compareTo(b.value.createdAt));
    
    // 가장 오래된 20개 제거
    for (int i = 0; i < 20 && i < entries.length; i++) {
      _memoryCache.remove(entries[i].key);
    }
  }

  Future<void> _checkCacheSize() async {
    final cacheSize = await _calculateCacheSize();
    
    if (cacheSize > _maxCacheSize) {
      await _cleanupCache();
    }
  }

  Future<int> _calculateCacheSize() async {
    int totalSize = 0;
    final files = _cacheDir.listSync();
    
    for (final file in files) {
      if (file is File && file.path.endsWith('.tile')) {
        final stat = await file.stat();
        totalSize += stat.size;
      }
    }
    
    return totalSize;
  }

  Future<void> _cleanupCache() async {
    // LRU 기반 캐시 정리
    final files = <File>[];
    
    await for (final entity in _cacheDir.list()) {
      if (entity is File && entity.path.endsWith('.tile')) {
        files.add(entity);
      }
    }

    // 접근 시간 기준 정렬
    files.sort((a, b) {
      final aStat = a.statSync();
      final bStat = b.statSync();
      return aStat.accessed.compareTo(bStat.accessed);
    });

    // 오래된 파일부터 삭제 (캐시 크기의 30% 정리)
    final targetSize = (_maxCacheSize * 0.7).round();
    int currentSize = await _calculateCacheSize();
    
    for (final file in files) {
      if (currentSize <= targetSize) break;
      
      final stat = await file.stat();
      currentSize -= stat.size;
      await file.delete();
      
      // 메타데이터도 삭제
      final metadataFile = File(file.path.replaceAll('.tile', '.meta'));
      if (await metadataFile.exists()) {
        await metadataFile.delete();
      }
    }
  }
}
```

### 5-2. 경로 캐시 시스템
```dart
class RouteCacheManager {
  static const String _cachePrefix = 'route_cache';
  static const Duration _cacheExpiry = Duration(hours: 6);
  
  final CacheManager _cacheManager;
  
  RouteCacheManager() : _cacheManager = DefaultCacheManager();

  Future<List<LatLng>?> getCachedRoute(RouteRequest request) async {
    final cacheKey = _generateRouteCacheKey(request);
    
    try {
      final cacheInfo = await _cacheManager.getFileFromCache(cacheKey);
      
      if (cacheInfo?.file != null) {
        final jsonString = await cacheInfo!.file.readAsString();
        final jsonData = json.decode(jsonString);
        
        // 만료 확인
        final cachedTime = DateTime.parse(jsonData['cachedAt']);
        if (DateTime.now().difference(cachedTime) < _cacheExpiry) {
          final pointsData = jsonData['points'] as List;
          return pointsData.map((point) => LatLng(
            point['latitude'],
            point['longitude'],
          )).toList();
        }
      }
    } catch (e) {
      logger.warning('Failed to load cached route: $e');
    }
    
    return null;
  }

  Future<void> cacheRoute(RouteRequest request, List<LatLng> route) async {
    final cacheKey = _generateRouteCacheKey(request);
    
    final cacheData = {
      'points': route.map((point) => {
        'latitude': point.latitude,
        'longitude': point.longitude,
      }).toList(),
      'cachedAt': DateTime.now().toIso8601String(),
    };
    
    final jsonString = json.encode(cacheData);
    final bytes = utf8.encode(jsonString);
    
    await _cacheManager.putFile(
      cacheKey,
      bytes,
      maxAge: _cacheExpiry,
    );
  }

  String _generateRouteCacheKey(RouteRequest request) {
    final components = [
      request.origin.latitude.toStringAsFixed(4),
      request.origin.longitude.toStringAsFixed(4),
      request.destination.latitude.toStringAsFixed(4),
      request.destination.longitude.toStringAsFixed(4),
      request.transportMode.toString(),
    ];
    
    final baseString = components.join('_');
    final hash = baseString.hashCode;
    
    return '${_cachePrefix}_$hash';
  }
}
```

---

## 6. 성능 최적화

### 6-1. 마커 클러스터링
```dart
class MarkerClusterer {
  static const double _clusterRadius = 100.0; // pixels
  static const int _maxMarkersPerCluster = 100;
  
  Future<List<Marker>> cluster(List<Marker> markers) async {
    if (markers.length <= 10) {
      return markers; // 적은 수는 클러스터링 안함
    }

    final clusters = <MarkerCluster>[];
    final unclustered = markers.toList();

    // 클러스터 생성
    while (unclustered.isNotEmpty) {
      final seed = unclustered.removeAt(0);
      final cluster = MarkerCluster(center: seed.position);
      cluster.addMarker(seed);

      // 반경 내 마커들을 클러스터에 추가
      final nearby = <Marker>[];
      for (final marker in unclustered) {
        final distance = _calculatePixelDistance(seed.position, marker.position);
        if (distance <= _clusterRadius) {
          nearby.add(marker);
        }
      }

      for (final marker in nearby) {
        cluster.addMarker(marker);
        unclustered.remove(marker);
      }

      clusters.add(cluster);
    }

    // 클러스터를 마커로 변환
    return clusters.map(_clusterToMarker).toList();
  }

  Marker _clusterToMarker(MarkerCluster cluster) {
    if (cluster.markers.length == 1) {
      return cluster.markers.first;
    }

    return Marker(
      id: 'cluster_${cluster.hashCode}',
      position: cluster.center,
      icon: _createClusterIcon(cluster.markers.length),
      onTap: () => _onClusterTap(cluster),
    );
  }

  MarkerIcon _createClusterIcon(int count) {
    Color backgroundColor;
    if (count < 10) {
      backgroundColor = Colors.green;
    } else if (count < 50) {
      backgroundColor = Colors.orange;
    } else {
      backgroundColor = Colors.red;
    }

    return MarkerIcon(
      text: count.toString(),
      textStyle: const TextStyle(
        color: Colors.white,
        fontSize: 12,
        fontWeight: FontWeight.bold,
      ),
      backgroundColor: backgroundColor,
      borderColor: Colors.white,
      borderWidth: 2,
      size: Size(
        math.max(24, math.min(48, 24 + count * 0.3)),
        math.max(24, math.min(48, 24 + count * 0.3)),
      ),
    );
  }

  double _calculatePixelDistance(LatLng pos1, LatLng pos2) {
    // 지구상 거리를 픽셀 거리로 근사 변환
    final earthRadius = 6371000; // meters
    final latDiff = (pos2.latitude - pos1.latitude) * math.pi / 180;
    final lngDiff = (pos2.longitude - pos1.longitude) * math.pi / 180;
    
    final a = math.sin(latDiff / 2) * math.sin(latDiff / 2) +
        math.cos(pos1.latitude * math.pi / 180) *
        math.cos(pos2.latitude * math.pi / 180) *
        math.sin(lngDiff / 2) * math.sin(lngDiff / 2);
    
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    final distance = earthRadius * c;
    
    // 대략적인 픽셀 변환 (줌 레벨 고려 필요)
    return distance * 0.01; // 임시 스케일링
  }

  void _onClusterTap(MarkerCluster cluster) {
    // 클러스터 확대 또는 마커 목록 표시
    if (cluster.markers.length <= 10) {
      _showClusterMarkers(cluster);
    } else {
      _zoomToCluster(cluster);
    }
  }
}
```

### 6-2. 배터리 최적화
```dart
class BatteryOptimizedLocationService {
  Timer? _locationUpdateTimer;
  UserLocation? _lastLocation;
  double _lastSpeed = 0.0;
  DateTime? _lastUpdateTime;

  Future<void> startAdaptiveTracking() async {
    _locationUpdateTimer = Timer.periodic(
      const Duration(seconds: 1),
      (_) => _adaptiveLocationUpdate(),
    );
  }

  Future<void> _adaptiveLocationUpdate() async {
    final currentTime = DateTime.now();
    
    // 마지막 업데이트로부터 시간 계산
    final timeSinceLastUpdate = _lastUpdateTime != null 
        ? currentTime.difference(_lastUpdateTime!)
        : Duration.zero;

    // 속도와 이동 상태에 따른 업데이트 주기 조정
    Duration updateInterval;
    if (_lastSpeed < 1.0) {
      // 정지 상태: 10초마다
      updateInterval = const Duration(seconds: 10);
    } else if (_lastSpeed < 5.0) {
      // 도보: 3초마다
      updateInterval = const Duration(seconds: 3);
    } else if (_lastSpeed < 20.0) {
      // 자전거/대중교통: 2초마다
      updateInterval = const Duration(seconds: 2);
    } else {
      // 자동차: 1초마다
      updateInterval = const Duration(seconds: 1);
    }

    if (timeSinceLastUpdate >= updateInterval) {
      await _updateLocation();
    }
  }

  Future<void> _updateLocation() async {
    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: _getAccuracyBySpeed(_lastSpeed),
      );

      final newLocation = UserLocation(
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
        speed: position.speed,
        timestamp: position.timestamp,
      );

      // 의미있는 이동이 있을 때만 업데이트
      if (_isSignificantLocationChange(_lastLocation, newLocation)) {
        _lastLocation = newLocation;
        _lastSpeed = position.speed;
        _lastUpdateTime = DateTime.now();
        
        _locationController.add(newLocation);
      }
    } catch (e) {
      logger.warning('Adaptive location update failed: $e');
    }
  }

  LocationAccuracy _getAccuracyBySpeed(double speed) {
    if (speed < 1.0) {
      return LocationAccuracy.medium; // 정지 시 정확도 낮춤
    } else if (speed < 10.0) {
      return LocationAccuracy.high;
    } else {
      return LocationAccuracy.best; // 고속 이동 시 최고 정확도
    }
  }

  bool _isSignificantLocationChange(UserLocation? old, UserLocation newLoc) {
    if (old == null) return true;
    
    final distance = Geolocator.distanceBetween(
      old.latitude,
      old.longitude,
      newLoc.latitude,
      newLoc.longitude,
    );

    // 이동 거리가 의미있을 때만 업데이트
    return distance > 5.0; // 5m 이상 이동
  }
}
```

---

## 7. 네이티브 플랫폼 통합

### 7-1. Android 구현
```kotlin
// android/src/main/kotlin/com/hotly/kakao_map_plugin/KakaoMapPlugin.kt
class KakaoMapPlugin : FlutterPlugin, MethodCallHandler {
    private lateinit var context: Context
    private lateinit var channel: MethodChannel
    
    override fun onAttachedToEngine(flutterPluginBinding: FlutterPlugin.FlutterPluginBinding) {
        context = flutterPluginBinding.applicationContext
        channel = MethodChannel(flutterPluginBinding.binaryMessenger, "kakao_map_plugin")
        channel.setMethodCallHandler(this)
        
        // Kakao Map SDK 초기화
        KakaoSdk.init(context, BuildConfig.KAKAO_API_KEY)
    }

    override fun onMethodCall(call: MethodCall, result: Result) {
        when (call.method) {
            "initialize" -> {
                val apiKey = call.argument<String>("apiKey")
                initializeKakaoMap(apiKey, result)
            }
            "showMap" -> {
                val options = call.arguments as Map<String, Any>
                showMap(options, result)
            }
            else -> result.notImplemented()
        }
    }

    private fun initializeKakaoMap(apiKey: String?, result: Result) {
        try {
            KakaoSdk.init(context, apiKey ?: BuildConfig.KAKAO_API_KEY)
            result.success(null)
        } catch (e: Exception) {
            result.error("INIT_ERROR", e.message, null)
        }
    }
}

// KakaoMapView.kt
class KakaoMapView(
    context: Context,
    id: Int,
    creationParams: Map<String, Any>?
) : PlatformView, MapView.MapViewEventListener {
    
    private val mapView: MapView = MapView(context)
    private val kakaoMap: KakaoMap by lazy { mapView.kakaoMap }
    private val markerManager = MarkerManager()
    
    init {
        mapView.start(object : MapLifeCycleCallback() {
            override fun onMapDestroy() {
                // 정리 작업
            }

            override fun onMapError(error: Exception) {
                Log.e("KakaoMapView", "Map error: ${error.message}")
            }
        }, this)
        
        setupInitialOptions(creationParams)
    }

    override fun getView(): View = mapView

    override fun dispose() {
        mapView.finish()
    }

    fun addMarker(markerData: Map<String, Any>) {
        val latLng = LatLng.from(
            markerData["latitude"] as Double,
            markerData["longitude"] as Double
        )
        
        val marker = Marker.from(latLng).apply {
            setTag(markerData["id"])
            
            // 커스텀 마커 이미지 설정
            val iconData = markerData["icon"] as? Map<String, Any>
            if (iconData != null) {
                setImage(createMarkerImage(iconData))
            }
        }
        
        kakaoMap.addMarker(marker)
        markerManager.addMarker(marker)
    }

    private fun createMarkerImage(iconData: Map<String, Any>): Bitmap {
        val size = iconData["size"] as? Map<String, Double>
        val width = size?.get("width")?.toInt() ?: 40
        val height = size?.get("height")?.toInt() ?: 40
        
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        
        // 배경 그리기
        val backgroundColor = Color.parseColor(iconData["backgroundColor"] as String)
        val paint = Paint().apply {
            color = backgroundColor
            isAntiAlias = true
        }
        
        val radius = width / 2f
        canvas.drawCircle(radius, radius, radius, paint)
        
        // 텍스트 그리기 (숫자 마커의 경우)
        val text = iconData["text"] as? String
        if (text != null) {
            val textPaint = Paint().apply {
                color = Color.WHITE
                textSize = 14.sp.toPx()
                textAlign = Paint.Align.CENTER
                isAntiAlias = true
            }
            
            canvas.drawText(
                text,
                radius,
                radius + textPaint.textSize / 3,
                textPaint
            )
        }
        
        return bitmap
    }

    fun drawRoute(points: List<Map<String, Double>>, style: Map<String, Any>) {
        val latLngs = points.map { 
            LatLng.from(it["latitude"]!!, it["longitude"]!!)
        }
        
        val polyline = Polyline.from(latLngs).apply {
            setStrokeWidth((style["width"] as Double).toFloat())
            setStrokeColor(Color.parseColor(style["color"] as String))
            
            // 패턴 설정
            val pattern = style["pattern"] as? List<Double>
            if (pattern != null) {
                setPattern(pattern.map { it.toFloat() }.toFloatArray())
            }
        }
        
        kakaoMap.addPolyline(polyline)
    }
}
```

### 7-2. iOS 구현
```swift
// ios/Classes/KakaoMapPlugin.swift
import Flutter
import KakaoMapsSDK

public class KakaoMapPlugin: NSObject, FlutterPlugin {
    public static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(name: "kakao_map_plugin", binaryMessenger: registrar.messenger())
        let instance = KakaoMapPlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
        
        registrar.register(
            KakaoMapViewFactory(messenger: registrar.messenger()),
            withId: "kakao_map_view"
        )
    }
    
    public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "initialize":
            let args = call.arguments as? [String: Any]
            let apiKey = args?["apiKey"] as? String
            initializeKakaoMap(apiKey: apiKey, result: result)
        case "showMap":
            let options = call.arguments as? [String: Any]
            showMap(options: options, result: result)
        default:
            result(FlutterMethodNotImplemented)
        }
    }
    
    private func initializeKakaoMap(apiKey: String?, result: @escaping FlutterResult) {
        guard let key = apiKey ?? Bundle.main.object(forInfoDictionaryKey: "KakaoApiKey") as? String else {
            result(FlutterError(code: "INIT_ERROR", message: "API Key not found", details: nil))
            return
        }
        
        KMController.shared().prepareEngine { error in
            if let error = error {
                result(FlutterError(code: "INIT_ERROR", message: error.localizedDescription, details: nil))
            } else {
                result(nil)
            }
        }
    }
}

// KakaoMapView.swift
class KakaoMapView: NSObject, FlutterPlatformView {
    private let mapView: KMViewContainer
    private var mapController: KMController?
    private let markerManager = MarkerManager()
    
    init(frame: CGRect, viewId: Int64, args: Any?, messenger: FlutterBinaryMessenger) {
        mapView = KMViewContainer()
        super.init()
        
        setupMap(args: args)
    }
    
    func view() -> UIView {
        return mapView
    }
    
    private func setupMap(args: Any?) {
        mapView.resizeWithParent(view: mapView)
        
        mapController = KMController(viewContainer: mapView)!
        mapController?.delegate = self
        mapController?.prepareEngine()
        
        if let params = args as? [String: Any] {
            configureInitialOptions(params)
        }
    }
    
    func addMarker(markerData: [String: Any]) {
        guard let mapController = mapController else { return }
        
        let latitude = markerData["latitude"] as! Double
        let longitude = markerData["longitude"] as! Double
        let position = MapPoint(longitude: longitude, latitude: latitude)
        
        let marker = Marker(position: position)
        
        // 커스텀 마커 이미지 설정
        if let iconData = markerData["icon"] as? [String: Any] {
            marker.image = createMarkerImage(iconData: iconData)
        }
        
        marker.tag = markerData["id"] as? String
        
        mapController.addMarker(marker)
        markerManager.addMarker(marker)
    }
    
    private func createMarkerImage(iconData: [String: Any]) -> UIImage {
        let sizeData = iconData["size"] as? [String: Double]
        let width = CGFloat(sizeData?["width"] ?? 40)
        let height = CGFloat(sizeData?["height"] ?? 40)
        
        let size = CGSize(width: width, height: height)
        
        UIGraphicsBeginImageContextWithOptions(size, false, 0)
        guard let context = UIGraphicsGetCurrentContext() else {
            return UIImage()
        }
        
        // 배경 원 그리기
        if let colorString = iconData["backgroundColor"] as? String {
            let color = UIColor(hexString: colorString)
            context.setFillColor(color.cgColor)
            context.fillEllipse(in: CGRect(origin: .zero, size: size))
        }
        
        // 텍스트 그리기
        if let text = iconData["text"] as? String {
            let attributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.boldSystemFont(ofSize: 14),
                .foregroundColor: UIColor.white
            ]
            
            let textSize = text.size(withAttributes: attributes)
            let textRect = CGRect(
                x: (width - textSize.width) / 2,
                y: (height - textSize.height) / 2,
                width: textSize.width,
                height: textSize.height
            )
            
            text.draw(in: textRect, withAttributes: attributes)
        }
        
        let image = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        return image ?? UIImage()
    }
    
    func drawRoute(points: [[String: Double]], style: [String: Any]) {
        guard let mapController = mapController else { return }
        
        let routePoints = points.map { point in
            MapPoint(
                longitude: point["longitude"]!,
                latitude: point["latitude"]!
            )
        }
        
        let polyline = Polyline(points: routePoints)
        
        if let width = style["width"] as? Double {
            polyline.strokeWidth = Float(width)
        }
        
        if let colorString = style["color"] as? String {
            polyline.strokeColor = UIColor(hexString: colorString)
        }
        
        mapController.addPolyline(polyline)
    }
}

extension KakaoMapView: KMControllerDelegate {
    func controllerDidCompleteEngine(_ controller: KMController) {
        // 지도 엔진 초기화 완료
        controller.startRendering()
    }
    
    func controller(_ controller: KMController, didFailToStartRenderingWithError error: Error) {
        print("Map rendering failed: \(error.localizedDescription)")
    }
}
```

---

## 8. 테스트 전략

### 8-1. 단위 테스트 (TDD)
```dart
class TestMapVisualizationService {
  @testWidgets('Map should load and display markers correctly')
  Future<void> testMapMarkerDisplay(WidgetTester tester) async {
    // Given
    final places = [
      Place(id: '1', name: 'Test Cafe', latitude: 37.5665, longitude: 126.9780, category: PlaceCategory.cafe),
      Place(id: '2', name: 'Test Restaurant', latitude: 37.5675, longitude: 126.9790, category: PlaceCategory.restaurant),
    ];
    
    final mapController = MockKakaoMapController();
    final markerManager = MarkerManager(mapController);

    // When
    await markerManager.addPlaceMarkers(places);

    // Then
    verify(mapController.addMarker(any)).called(2);
    
    final capturedMarkers = verify(mapController.addMarker(captureAny))
        .captured.cast<Marker>();
    
    expect(capturedMarkers.length, equals(2));
    expect(capturedMarkers[0].id, equals('1'));
    expect(capturedMarkers[1].id, equals('2'));
    
    // 마커 위치 검증
    expect(capturedMarkers[0].position.latitude, closeTo(37.5665, 0.0001));
    expect(capturedMarkers[0].position.longitude, closeTo(126.9780, 0.0001));
  }

  @test
  void testRouteVisualization() async {
    // Given
    final course = Course(
      id: 'test_course',
      places: [
        CoursePlaceDetail(placeId: '1', order: 1, arrivalTime: TimeOfDay(hour: 10, minute: 0)),
        CoursePlaceDetail(placeId: '2', order: 2, arrivalTime: TimeOfDay(hour: 12, minute: 0)),
        CoursePlaceDetail(placeId: '3', order: 3, arrivalTime: TimeOfDay(hour: 14, minute: 0)),
      ],
      transportMethod: TransportMethod.walking,
    );

    final routeRenderer = RouteRenderer(mockMapController);
    final mockRouteCalculator = MockRouteCalculator();
    
    when(mockRouteCalculator.calculateRoute(any, any, any)).thenAnswer((_) async => [
      LatLng(37.5665, 126.9780),
      LatLng(37.5670, 126.9785),
      LatLng(37.5675, 126.9790),
    ]);

    // When
    await routeRenderer.drawCourseRoute(course);

    // Then
    verify(mockMapController.drawRoute(any, any)).called(2); // 3개 장소 = 2개 경로
    
    final drawnRoutes = verify(mockMapController.drawRoute(captureAny, captureAny)).captured;
    expect(drawnRoutes.length, equals(4)); // points + style for each route
  }

  @test
  void testLocationTrackingAccuracy() async {
    // Given
    final locationService = LocationTrackingService();
    final mockPositionStream = Stream<Position>.fromIterable([
      Position(
        latitude: 37.5665,
        longitude: 126.9780,
        accuracy: 5.0,
        timestamp: DateTime.now(),
        speed: 0.0,
        heading: 0.0,
      ),
      Position(
        latitude: 37.5670,
        longitude: 126.9785,
        accuracy: 3.0,
        timestamp: DateTime.now().add(Duration(seconds: 5)),
        speed: 1.2,
        heading: 45.0,
      ),
    ]);

    when(mockGeolocator.getPositionStream(any)).thenAnswer((_) => mockPositionStream);

    final locations = <UserLocation>[];
    locationService.locationStream.listen((location) => locations.add(location));

    // When
    await locationService.startTracking(mode: TrackingMode.navigation);
    await Future.delayed(Duration(seconds: 6));

    // Then
    expect(locations.length, equals(2));
    expect(locations[0].accuracy, equals(5.0));
    expect(locations[1].accuracy, equals(3.0));
    expect(locations[1].speed, equals(1.2));
  }

  @test
  void testMarkerClustering() async {
    // Given
    final clusterer = MarkerClusterer();
    final markers = List.generate(20, (index) => Marker(
      id: 'marker_$index',
      position: LatLng(
        37.5665 + (index * 0.001), // 가까운 위치들
        126.9780 + (index * 0.001),
      ),
    ));

    // When
    final clusteredMarkers = await clusterer.cluster(markers);

    // Then
    expect(clusteredMarkers.length, lessThan(markers.length));
    
    // 클러스터 마커가 생성되었는지 확인
    final clusterMarkers = clusteredMarkers.where((m) => m.id.startsWith('cluster_'));
    expect(clusterMarkers.isNotEmpty, isTrue);
  }
}
```

### 8-2. 통합 테스트
```dart
class TestMapIntegration {
  @testWidgets('Map integration with course visualization')
  Future<void> testCourseMapIntegration(WidgetTester tester) async {
    // Given
    final course = await createTestCourse();
    
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: CourseMapView(course: course),
      ),
    ));

    // 지도 로딩 대기
    await tester.pump();
    await tester.pump(Duration(seconds: 3));

    // Then
    // 지도 위젯이 표시되는지 확인
    expect(find.byType(KakaoMapWidget), findsOneWidget);
    
    // 마커들이 올바르게 표시되는지 확인 (네이티브 호출 모킹)
    final mapWidget = tester.widget<KakaoMapWidget>(find.byType(KakaoMapWidget));
    expect(mapWidget.options.initialMarkers?.length, equals(course.places.length));
    
    // 경로가 그려지는지 확인
    await tester.pump(Duration(seconds: 1));
    // 경로 렌더링 검증 로직
  }

  @testWidgets('Real-time navigation UI updates')
  Future<void> testNavigationUIUpdates(WidgetTester tester) async {
    // Given
    final navigationService = NavigationService(
      mockLocationService,
      mockRouteCalculator,
      mockVoiceGuide,
    );
    
    await tester.pumpWidget(MaterialApp(
      home: NavigationScreen(navigationService: navigationService),
    ));

    // When - 내비게이션 시작
    await tester.tap(find.text('길찾기 시작'));
    await tester.pump();

    // 모의 위치 업데이트
    mockLocationService.simulateLocationUpdate(UserLocation(
      latitude: 37.5665,
      longitude: 126.9780,
      accuracy: 5.0,
      timestamp: DateTime.now(),
    ));

    await tester.pump();

    // Then
    expect(find.text('다음 목적지:'), findsOneWidget);
    expect(find.byType(NavigationInfoPanel), findsOneWidget);
  }
}
```

### 8-3. 성능 테스트
```dart
class TestMapPerformance {
  @test
  void testMapLoadingPerformance() async {
    // Given
    final places = List.generate(100, (index) => Place(
      id: 'place_$index',
      name: 'Place $index',
      latitude: 37.5665 + (index * 0.01),
      longitude: 126.9780 + (index * 0.01),
      category: PlaceCategory.cafe,
    ));

    final mapController = TestKakaoMapController();
    final markerManager = MarkerManager(mapController);

    // When
    final stopwatch = Stopwatch()..start();
    await markerManager.addPlaceMarkers(places);
    stopwatch.stop();

    // Then
    expect(stopwatch.elapsedMilliseconds, lessThan(3000)); // 3초 이내
    expect(mapController.addMarkerCallCount, lessThanOrEqualTo(50)); // 클러스터링 효과
  }

  @test
  void testMemoryUsageDuringMapInteraction() async {
    // Given
    final tileCache = MapTileCache(Directory.systemTemp);
    await tileCache.initialize();

    final initialMemory = await _getCurrentMemoryUsage();

    // When - 많은 타일 캐싱
    for (int zoom = 10; zoom <= 15; zoom++) {
      for (int x = 0; x < 10; x++) {
        for (int y = 0; y < 10; y++) {
          final tileData = Uint8List.fromList(List.filled(1024, 0)); // 1KB 타일
          await tileCache.cacheTile(x, y, zoom, tileData);
        }
      }
    }

    final afterCachingMemory = await _getCurrentMemoryUsage();

    // Then
    final memoryIncrease = afterCachingMemory - initialMemory;
    expect(memoryIncrease, lessThan(100 * 1024 * 1024)); // 100MB 이하
  }

  @test
  void testBatteryOptimizedTracking() async {
    // Given
    final batteryService = BatteryOptimizedLocationService();
    final batteryMonitor = MockBatteryMonitor();
    
    final initialBattery = 100.0;
    batteryMonitor.setBatteryLevel(initialBattery);

    // When - 1시간 추적 시뮬레이션
    await batteryService.startAdaptiveTracking();
    
    // 정지 상태 시뮬레이션 (30분)
    batteryService.simulateSpeed(0.0);
    await Future.delayed(Duration(minutes: 30));
    
    // 이동 상태 시뮬레이션 (30분)
    batteryService.simulateSpeed(5.0); // 도보
    await Future.delayed(Duration(minutes: 30));

    await batteryService.stopTracking();

    // Then
    final finalBattery = batteryMonitor.getCurrentBatteryLevel();
    final batteryUsage = initialBattery - finalBattery;
    
    expect(batteryUsage, lessThan(15.0)); // 15% 이하 소모
  }

  Future<int> _getCurrentMemoryUsage() async {
    // 플랫폼별 메모리 사용량 측정
    return await MemoryInfo.getCurrentUsage();
  }
}
```

---

## 9. 배포 및 운영

### 9-1. 환경 설정
```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  kakao_map_plugin:
    path: ./plugins/kakao_map_plugin
  geolocator: ^9.0.2
  permission_handler: ^10.2.0
  cached_network_image: ^3.2.3
  flutter_cache_manager: ^3.3.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  mockito: ^5.4.0
  integration_test:
    sdk: flutter
```

```dart
// lib/config/map_config.dart
class MapConfig {
  static const String kakaoApiKey = String.fromEnvironment(
    'KAKAO_API_KEY',
    defaultValue: '',
  );
  
  static const bool enableOfflineMap = bool.fromEnvironment(
    'ENABLE_OFFLINE_MAP',
    defaultValue: true,
  );
  
  static const int maxCacheSize = int.fromEnvironment(
    'MAP_CACHE_SIZE_MB',
    defaultValue: 50,
  ) * 1024 * 1024; // Convert to bytes
  
  static const Duration locationUpdateInterval = Duration(
    seconds: int.fromEnvironment('LOCATION_UPDATE_INTERVAL_SEC', defaultValue: 3),
  );
}
```

### 9-2. CI/CD 파이프라인
```yaml
# .github/workflows/map-test.yml
name: Map Visualization Tests

on:
  push:
    paths:
      - 'lib/features/map/**'
      - 'plugins/kakao_map_plugin/**'
      - 'test/map/**'
  pull_request:
    paths:
      - 'lib/features/map/**'
      - 'plugins/kakao_map_plugin/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.16.0'
    
    - name: Install dependencies
      run: flutter pub get
    
    - name: Run unit tests
      run: flutter test test/map/
      env:
        KAKAO_API_KEY: ${{ secrets.KAKAO_API_KEY }}
    
    - name: Build Android
      run: flutter build apk --debug
      env:
        KAKAO_API_KEY: ${{ secrets.KAKAO_API_KEY }}
    
    - name: Run integration tests on Android
      uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: 29
        script: flutter test integration_test/map_integration_test.dart
      env:
        KAKAO_API_KEY: ${{ secrets.KAKAO_API_KEY }}

  performance-test:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.16.0'
    
    - name: Run performance tests
      run: flutter test test/map/performance/ --reporter=json > performance_results.json
    
    - name: Analyze performance results
      run: |
        python scripts/analyze_performance.py performance_results.json
        if [ $? -ne 0 ]; then
          echo "Performance regression detected"
          exit 1
        fi
```

---

## 10. 모니터링 및 로깅

### 10-1. 지도 사용 메트릭
```dart
class MapAnalytics {
  static const String _eventPrefix = 'map';
  
  static void trackMapLoad({
    required Duration loadTime,
    required int markerCount,
    required bool useCache,
  }) {
    Analytics.track('${_eventPrefix}_load', {
      'load_time_ms': loadTime.inMilliseconds,
      'marker_count': markerCount,
      'cache_hit': useCache,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  }
  
  static void trackMarkerInteraction({
    required String markerId,
    required String action, // tap, info_window, cluster_expand
    required LatLng position,
  }) {
    Analytics.track('${_eventPrefix}_marker_interaction', {
      'marker_id': markerId,
      'action': action,
      'latitude': position.latitude,
      'longitude': position.longitude,
    });
  }
  
  static void trackNavigationUsage({
    required Duration sessionDuration,
    required double totalDistance,
    required int waypoints,
    required TransportMethod transportMethod,
  }) {
    Analytics.track('${_eventPrefix}_navigation_session', {
      'duration_minutes': sessionDuration.inMinutes,
      'distance_meters': totalDistance.round(),
      'waypoints': waypoints,
      'transport_method': transportMethod.toString(),
      'completed': true,
    });
  }
  
  static void trackPerformanceMetric({
    required String metric,
    required double value,
    Map<String, dynamic>? additionalData,
  }) {
    final data = <String, dynamic>{
      'metric': metric,
      'value': value,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    };
    
    if (additionalData != null) {
      data.addAll(additionalData);
    }
    
    Analytics.track('${_eventPrefix}_performance', data);
  }
}
```

---

## 11. 용어 사전 (Technical)
- **Polyline:** 지도에서 여러 점을 연결한 선
- **Clustering:** 가까운 마커들을 그룹화하여 하나의 마커로 표시
- **Tile:** 지도를 구성하는 256x256 픽셀 이미지 조각
- **Geocoding:** 주소를 GPS 좌표로 변환하는 과정
- **Reverse Geocoding:** GPS 좌표를 주소로 변환하는 과정
- **Viewport:** 현재 화면에 보이는 지도 영역
- **Zoom Level:** 지도의 확대/축소 정도 (1-20)

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 04-map-visualization 버전과 연동