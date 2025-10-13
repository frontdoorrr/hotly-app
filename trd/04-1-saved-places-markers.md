# TRD: 저장된 장소 지도 마커 표시

## 1. 기술 개요
**목적:** PRD 04-1-saved-places-markers 요구사항을 충족하기 위한 저장된 장소 지도 마커 시각화 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- UI Framework: Flutter 3.29.0+
- 상태 관리: Riverpod 2.x (SavedPlacesProvider, MapProvider)
- 지도 SDK: kakao_map_sdk ^1.2.0
- 위치 서비스: geolocator ^10.1.1

**상위 기술 문서:** TRD 04-map-visualization (지도 기반 시각화 및 경로 표시)

---

## 2. 시스템 아키텍처

### 2-1. 컴포넌트 다이어그램
```
┌─────────────────────────────────────────────────┐
│              SavedMapScreen                     │
│  ┌───────────────────────────────────────────┐  │
│  │         KakaoMap Widget                   │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │   Markers (from SavedPlacesProvider)│  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │      PlaceMarkerInfo                      │  │
│  │    (if selectedPlaceId != null)           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         ↑ watch                    ↑ watch
         │                          │
┌────────────────────┐     ┌───────────────────┐
│SavedPlacesProvider │     │   MapProvider      │
│ - places           │     │ - selectedPlaceId  │
│ - isLoading        │     │ - currentLocation  │
└────────────────────┘     └───────────────────┘
```

### 2-2. 데이터 흐름
```
1. SavedMapScreen 렌더링
   ↓
2. SavedPlacesProvider.watch()
   ↓ places: List<Place>
3. _buildMarkers(places)
   ↓ List<Marker>
4. KakaoMap(markers: markers)
   ↓
5. User taps marker
   ↓ onMarkerTap(markerId)
6. MapProvider.selectPlace(markerId)
   ↓ state.selectedPlaceId = markerId
7. PlaceMarkerInfo rebuilds with new placeId
```

---

## 3. 핵심 구현

### 3-1. SavedMapScreen 위젯
```dart
// lib/features/map/presentation/screens/saved_map_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';
import '../providers/map_provider.dart';
import '../widgets/place_marker_info.dart';

/// 저장된 장소들을 지도에 마커로 표시하는 화면
class SavedMapScreen extends ConsumerStatefulWidget {
  const SavedMapScreen({super.key});

  @override
  ConsumerState<SavedMapScreen> createState() => _SavedMapScreenState();
}

class _SavedMapScreenState extends ConsumerState<SavedMapScreen> {
  KakaoMapController? _mapController;
  bool _isMapReady = false;
  final _mapKey = UniqueKey(); // PlatformView 재생성 방지

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        // 현재 위치 가져오기
        ref.read(mapProvider.notifier).getCurrentLocation();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final savedState = ref.watch(savedPlacesProvider);
    final mapState = ref.watch(mapProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('저장된 장소'),
        actions: [
          // 현재 위치 버튼
          IconButton(
            icon: const Icon(Icons.my_location),
            onPressed: _moveToCurrentLocation,
            tooltip: '현재 위치',
          ),
        ],
      ),
      body: Stack(
        children: [
          // Kakao Map
          _buildMap(savedState.places, mapState.currentLocation),

          // 로딩 인디케이터
          if (savedState.isLoading || !_isMapReady)
            const Center(
              child: CircularProgressIndicator(),
            ),

          // 빈 상태
          if (!savedState.isLoading && savedState.places.isEmpty)
            _buildEmptyState(context),

          // 선택된 장소 정보 패널
          if (mapState.selectedPlaceId != null && _isMapReady)
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: PlaceMarkerInfo(
                placeId: mapState.selectedPlaceId!,
                onClose: () {
                  ref.read(mapProvider.notifier).selectPlace(null);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMap(List<Place> places, CoordinatePoint? currentLocation) {
    return KakaoMap(
      key: _mapKey,
      option: KakaoMapOption(
        position: currentLocation != null
            ? LatLng(currentLocation.latitude, currentLocation.longitude)
            : const LatLng(37.5665, 126.9780), // 서울시청 기본
        zoomLevel: 16,
        mapType: MapType.normal,
      ),
      markers: _buildMarkers(places),
      onMapReady: (controller) {
        _mapController = controller;
        setState(() {
          _isMapReady = true;
        });

        // 모든 마커가 보이도록 카메라 조정
        if (places.isNotEmpty) {
          _fitBoundsToMarkers(places);
        }

        debugPrint('🗺️ Saved places map is ready with ${places.length} markers');
      },
      onMarkerTap: (markerId, latLng, zoomLevel) {
        // 마커 선택
        ref.read(mapProvider.notifier).selectPlace(markerId);

        // 선택된 마커로 카메라 이동
        _moveToMarker(latLng);
      },
    );
  }

  /// Place 리스트를 Marker 리스트로 변환
  List<Marker> _buildMarkers(List<Place> places) {
    final markers = <Marker>[];

    for (final place in places) {
      // 좌표가 없는 장소는 스킵
      if (place.latitude == null || place.longitude == null) {
        debugPrint('⚠️ Skipping place without coordinates: ${place.name}');
        continue;
      }

      final marker = Marker(
        markerId: place.id,
        position: LatLng(place.latitude!, place.longitude!),
        // Phase 1: 기본 핀 사용 (icon 파라미터 생략)
      );

      markers.add(marker);
    }

    return markers;
  }

  /// 모든 마커가 화면에 들어오도록 카메라 조정
  Future<void> _fitBoundsToMarkers(List<Place> places) async {
    if (!_isMapReady || _mapController == null || places.isEmpty) return;

    try {
      // 좌표가 있는 장소들만 필터링
      final placesWithCoords = places.where(
        (p) => p.latitude != null && p.longitude != null,
      ).toList();

      if (placesWithCoords.isEmpty) return;

      // 경계 계산
      double minLat = placesWithCoords.first.latitude!;
      double maxLat = placesWithCoords.first.latitude!;
      double minLng = placesWithCoords.first.longitude!;
      double maxLng = placesWithCoords.first.longitude!;

      for (final place in placesWithCoords) {
        minLat = math.min(minLat, place.latitude!);
        maxLat = math.max(maxLat, place.latitude!);
        minLng = math.min(minLng, place.longitude!);
        maxLng = math.max(maxLng, place.longitude!);
      }

      // 경계 중심 계산
      final centerLat = (minLat + maxLat) / 2;
      final centerLng = (minLng + maxLng) / 2;

      // 적절한 줌 레벨 계산
      final latDiff = maxLat - minLat;
      final lngDiff = maxLng - minLng;
      final maxDiff = math.max(latDiff, lngDiff);

      int zoomLevel;
      if (maxDiff > 0.1) {
        zoomLevel = 12; // 먼 거리
      } else if (maxDiff > 0.05) {
        zoomLevel = 13;
      } else if (maxDiff > 0.02) {
        zoomLevel = 14;
      } else if (maxDiff > 0.01) {
        zoomLevel = 15;
      } else {
        zoomLevel = 16; // 가까운 거리
      }

      // 카메라 이동
      await _mapController!.moveCamera(
        CameraUpdate.newCenterPosition(
          LatLng(centerLat, centerLng),
          zoomLevel: zoomLevel,
        ),
        animation: const CameraAnimation(
          800,
          autoElevation: false,
        ),
      );
    } catch (e) {
      debugPrint('⛔ Camera fitBounds error: $e');
    }
  }

  /// 현재 위치로 카메라 이동
  Future<void> _moveToCurrentLocation() async {
    if (!_isMapReady || _mapController == null) return;

    await ref.read(mapProvider.notifier).getCurrentLocation();
    final currentLocation = ref.read(mapProvider).currentLocation;

    if (currentLocation != null) {
      await _mapController!.moveCamera(
        CameraUpdate.newCenterPosition(
          LatLng(currentLocation.latitude, currentLocation.longitude),
          zoomLevel: 16,
        ),
        animation: const CameraAnimation(500, autoElevation: false),
      );
    }
  }

  /// 선택된 마커로 카메라 이동
  Future<void> _moveToMarker(LatLng position) async {
    if (!_isMapReady || _mapController == null) return;

    try {
      await _mapController!.moveCamera(
        CameraUpdate.newCenterPosition(
          position,
          // 줌 레벨 유지
        ),
        animation: const CameraAnimation(300, autoElevation: false),
      );
    } catch (e) {
      debugPrint('⛔ Camera move error: $e');
    }
  }

  Widget _buildEmptyState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.place_outlined,
            size: 80,
            color: theme.colorScheme.outline,
          ),
          const SizedBox(height: AppTheme.space4),
          Text(
            '저장된 장소가 없습니다',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: AppTheme.space2),
          Text(
            '링크 분석으로 장소를 추가해보세요',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: AppTheme.space4),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context).pop(); // 홈으로 돌아가기
            },
            icon: const Icon(Icons.home),
            label: const Text('홈으로 가기'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _mapController?.finish();
    super.dispose();
  }
}
```

### 3-2. MapProvider 업데이트
```dart
// lib/features/map/presentation/providers/map_provider.dart

// 기존 MapState에 selectedPlaceId가 이미 있음
// 추가 변경사항 없음

/// 기존 코드:
@freezed
class MapState with _$MapState {
  const factory MapState({
    CoordinatePoint? currentLocation,
    @Default([]) List<PlaceSearchResult> searchResults,
    @Default([]) List<Map<String, dynamic>> placesOnMap,
    @Default(false) bool isLoading,
    @Default(false) bool isSearching,
    String? error,
    String? selectedPlaceId, // ← 이미 존재!
  }) = _MapState;
}

/// 기존 메서드:
/// Select a place on the map
void selectPlace(String? placeId) {
  state = state.copyWith(selectedPlaceId: placeId);
}
```

### 3-3. PlaceMarkerInfo 위젯 수정
```dart
// lib/features/map/presentation/widgets/place_marker_info.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';

/// 마커 클릭 시 하단에 표시되는 장소 정보 패널
class PlaceMarkerInfo extends ConsumerWidget {
  final String placeId;
  final VoidCallback onClose;

  const PlaceMarkerInfo({
    super.key,
    required this.placeId,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final savedState = ref.watch(savedPlacesProvider);

    // placeId로 Place 객체 찾기
    final place = savedState.places.firstWhere(
      (p) => p.id == placeId,
      orElse: () => null,
    );

    if (place == null) {
      return const SizedBox.shrink();
    }

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(AppTheme.radiusXl),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(AppTheme.space4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더: 장소명 + 닫기 버튼
          Row(
            children: [
              Expanded(
                child: Text(
                  place.name,
                  style: theme.textTheme.titleLarge,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: onClose,
                tooltip: '닫기',
              ),
            ],
          ),

          const SizedBox(height: AppTheme.space2),

          // 주소
          if (place.address != null)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.place_outlined,
                  size: 16,
                  color: theme.colorScheme.secondary,
                ),
                const SizedBox(width: AppTheme.space1),
                Expanded(
                  child: Text(
                    place.address!,
                    style: theme.textTheme.bodyMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),

          const SizedBox(height: AppTheme.space1),

          // 카테고리
          Row(
            children: [
              Icon(
                Icons.category_outlined,
                size: 16,
                color: theme.colorScheme.secondary,
              ),
              const SizedBox(width: AppTheme.space1),
              Text(
                place.category,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),

          // 평점 (있는 경우)
          if (place.rating > 0) ...[
            const SizedBox(height: AppTheme.space1),
            Row(
              children: [
                const Icon(
                  Icons.star,
                  size: 16,
                  color: Colors.amber,
                ),
                const SizedBox(width: AppTheme.space1),
                Text(
                  place.rating.toStringAsFixed(1),
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ],

          const SizedBox(height: AppTheme.space3),

          // 상세보기 버튼
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                // PlaceDetailScreen으로 이동
                context.push('/place/${place.id}');
              },
              child: const Text('상세보기'),
            ),
          ),
        ],
      ),
    );
  }
}
```

### 3-4. 네비게이션 라우팅
```dart
// lib/core/router/app_router.dart

final goRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      // ... 기존 라우트들

      // 저장 탭
      GoRoute(
        path: '/saved',
        builder: (context, state) => const SavedScreen(),
      ),

      // 저장된 장소 지도 화면 (추가)
      GoRoute(
        path: '/saved/map',
        builder: (context, state) => const SavedMapScreen(),
      ),

      // 장소 상세 화면
      GoRoute(
        path: '/place/:id',
        builder: (context, state) {
          final placeId = state.pathParameters['id']!;
          return PlaceDetailScreen(placeId: placeId);
        },
      ),

      // ... 기타 라우트들
    ],
  );
});
```

### 3-5. SavedScreen에 지도 진입 버튼 추가
```dart
// lib/features/saved/presentation/screens/saved_screen.dart

// AppBar에 지도 버튼 추가
@override
Widget build(BuildContext context, WidgetRef ref) {
  final theme = Theme.of(context);
  final state = ref.watch(savedPlacesProvider);

  return Scaffold(
    appBar: AppBar(
      title: const Text('저장한 장소'),
      automaticallyImplyLeading: false,
      actions: [
        // 지도 보기 버튼 추가
        IconButton(
          icon: const Icon(Icons.map),
          onPressed: () {
            context.push('/saved/map');
          },
          tooltip: '지도 보기',
        ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () {
            ref.read(savedPlacesProvider.notifier).refresh();
          },
        ),
      ],
    ),
    body: _buildBody(context, state, ref),
  );
}
```

---

## 4. 성능 최적화

### 4-1. 마커 렌더링 최적화
```dart
/// 좌표 null 체크를 빌드 시점에 수행
List<Marker> _buildMarkers(List<Place> places) {
  return places
      .where((p) => p.latitude != null && p.longitude != null)
      .map((place) => Marker(
            markerId: place.id,
            position: LatLng(place.latitude!, place.longitude!),
          ))
      .toList();
}
```

### 4-2. 불필요한 리빌드 방지
```dart
/// SavedMapScreen에서 watch 대신 select 사용 고려
// 기존:
final savedState = ref.watch(savedPlacesProvider);

// 최적화 (places만 필요한 경우):
final places = ref.watch(
  savedPlacesProvider.select((state) => state.places),
);
```

### 4-3. 카메라 이동 디바운싱
```dart
Timer? _cameraDebounceTimer;

void _debouncedCameraMove(LatLng position) {
  _cameraDebounceTimer?.cancel();
  _cameraDebounceTimer = Timer(const Duration(milliseconds: 300), () {
    _moveToMarker(position);
  });
}

@override
void dispose() {
  _cameraDebounceTimer?.cancel();
  _mapController?.finish();
  super.dispose();
}
```

---

## 5. 에러 처리

### 5-1. 좌표 없는 장소 처리
```dart
/// 로깅을 통해 문제 추적
if (place.latitude == null || place.longitude == null) {
  debugPrint(
    '⚠️ Place without coordinates: ${place.name} (${place.id})',
  );
  // Analytics 전송
  Analytics.track('map_marker_missing_coords', {
    'place_id': place.id,
    'place_name': place.name,
  });
  continue; // 마커 생성 스킵
}
```

### 5-2. 지도 초기화 실패 처리
```dart
@override
Widget build(BuildContext context) {
  return Scaffold(
    body: KakaoMap(
      // ...
      onMapError: (error) {
        debugPrint('🗺️ Map initialization error: $error');

        // 사용자에게 에러 표시
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('지도를 불러올 수 없습니다: $error'),
              action: SnackBarAction(
                label: '다시 시도',
                onPressed: () {
                  setState(() {
                    _mapKey = UniqueKey(); // 지도 재생성
                  });
                },
              ),
            ),
          );
        }
      },
    ),
  );
}
```

### 5-3. 위치 권한 거부 처리
```dart
/// MapProvider에서 처리 (이미 구현됨)
Future<void> getCurrentLocation() async {
  try {
    LocationPermission permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        state = state.copyWith(
          error: 'Location permission denied',
        );
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      state = state.copyWith(
        error: 'Location permission permanently denied',
      );
      return;
    }

    // 위치 가져오기
    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );

    state = state.copyWith(
      currentLocation: CoordinatePoint(
        latitude: position.latitude,
        longitude: position.longitude,
      ),
      error: null,
    );
  } catch (e) {
    state = state.copyWith(
      error: 'Failed to get location: $e',
    );
  }
}
```

---

## 6. 테스트 전략

### 6-1. 단위 테스트
```dart
// test/features/map/saved_map_screen_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

void main() {
  group('SavedMapScreen', () {
    testWidgets('should display markers for saved places', (tester) async {
      // Given
      final mockPlaces = [
        Place(
          id: '1',
          name: 'Test Cafe',
          latitude: 37.5665,
          longitude: 126.9780,
          category: '카페',
        ),
        Place(
          id: '2',
          name: 'Test Restaurant',
          latitude: 37.5675,
          longitude: 126.9785,
          category: '맛집',
        ),
      ];

      // Mock providers
      final container = ProviderContainer(
        overrides: [
          savedPlacesProvider.overrideWith((ref) {
            return MockSavedPlacesNotifier(
              const SavedPlacesState(places: mockPlaces),
            );
          }),
        ],
      );

      // When
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(
            home: SavedMapScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Then
      expect(find.byType(KakaoMap), findsOneWidget);

      final kakaoMap = tester.widget<KakaoMap>(find.byType(KakaoMap));
      expect(kakaoMap.markers.length, equals(2));
      expect(kakaoMap.markers[0].markerId, equals('1'));
      expect(kakaoMap.markers[1].markerId, equals('2'));
    });

    testWidgets('should show empty state when no places', (tester) async {
      // Given
      final container = ProviderContainer(
        overrides: [
          savedPlacesProvider.overrideWith((ref) {
            return MockSavedPlacesNotifier(
              const SavedPlacesState(places: []),
            );
          }),
        ],
      );

      // When
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(
            home: SavedMapScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Then
      expect(find.text('저장된 장소가 없습니다'), findsOneWidget);
      expect(find.text('링크 분석으로 장소를 추가해보세요'), findsOneWidget);
      expect(find.widgetWithText(ElevatedButton, '홈으로 가기'), findsOneWidget);
    });

    testWidgets('should skip places without coordinates', (tester) async {
      // Given
      final mockPlaces = [
        Place(
          id: '1',
          name: 'With Coords',
          latitude: 37.5665,
          longitude: 126.9780,
          category: '카페',
        ),
        Place(
          id: '2',
          name: 'Without Coords',
          latitude: null, // 좌표 없음
          longitude: null,
          category: '맛집',
        ),
      ];

      final container = ProviderContainer(
        overrides: [
          savedPlacesProvider.overrideWith((ref) {
            return MockSavedPlacesNotifier(
              SavedPlacesState(places: mockPlaces),
            );
          }),
        ],
      );

      // When
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(
            home: SavedMapScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Then
      final kakaoMap = tester.widget<KakaoMap>(find.byType(KakaoMap));
      expect(kakaoMap.markers.length, equals(1)); // 좌표 있는 장소만
      expect(kakaoMap.markers[0].markerId, equals('1'));
    });
  });

  group('_buildMarkers', () {
    test('should convert places to markers', () {
      // Given
      final places = [
        Place(
          id: '1',
          name: 'Place 1',
          latitude: 37.5665,
          longitude: 126.9780,
          category: '카페',
        ),
        Place(
          id: '2',
          name: 'Place 2',
          latitude: 37.5675,
          longitude: 126.9785,
          category: '맛집',
        ),
      ];

      final screenState = _SavedMapScreenState();

      // When
      final markers = screenState._buildMarkers(places);

      // Then
      expect(markers.length, equals(2));
      expect(markers[0].markerId, equals('1'));
      expect(markers[0].position.latitude, equals(37.5665));
      expect(markers[0].position.longitude, equals(126.9780));
    });

    test('should filter out places without coordinates', () {
      // Given
      final places = [
        Place(id: '1', name: 'Valid', latitude: 37.5, longitude: 126.9, category: '카페'),
        Place(id: '2', name: 'Invalid', latitude: null, longitude: null, category: '맛집'),
      ];

      final screenState = _SavedMapScreenState();

      // When
      final markers = screenState._buildMarkers(places);

      // Then
      expect(markers.length, equals(1));
      expect(markers[0].markerId, equals('1'));
    });
  });

  group('_fitBoundsToMarkers', () {
    test('should calculate correct zoom level', () async {
      // Given
      final places = [
        Place(id: '1', name: 'A', latitude: 37.5, longitude: 126.9, category: '카페'),
        Place(id: '2', name: 'B', latitude: 37.6, longitude: 127.0, category: '맛집'),
      ];

      final screenState = _SavedMapScreenState();

      // When
      await screenState._fitBoundsToMarkers(places);

      // Then
      // Mock 컨트롤러로 호출 확인
      verify(mockMapController.moveCamera(any, any)).called(1);
    });
  });
}
```

### 6-2. 위젯 테스트
```dart
// test/features/map/widgets/place_marker_info_test.dart

import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PlaceMarkerInfo', () {
    testWidgets('should display place information', (tester) async {
      // Given
      final place = Place(
        id: '1',
        name: 'Test Cafe',
        address: '서울시 강남구',
        latitude: 37.5665,
        longitude: 126.9780,
        category: '카페',
        rating: 4.5,
      );

      final container = ProviderContainer(
        overrides: [
          savedPlacesProvider.overrideWith((ref) {
            return MockSavedPlacesNotifier(
              SavedPlacesState(places: [place]),
            );
          }),
        ],
      );

      // When
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: Scaffold(
              body: PlaceMarkerInfo(
                placeId: '1',
                onClose: () {},
              ),
            ),
          ),
        ),
      );

      // Then
      expect(find.text('Test Cafe'), findsOneWidget);
      expect(find.text('서울시 강남구'), findsOneWidget);
      expect(find.text('카페'), findsOneWidget);
      expect(find.text('4.5'), findsOneWidget);
      expect(find.widgetWithText(ElevatedButton, '상세보기'), findsOneWidget);
    });

    testWidgets('should call onClose when close button tapped', (tester) async {
      // Given
      bool closeCalled = false;
      final place = Place(
        id: '1',
        name: 'Test',
        latitude: 37.5,
        longitude: 126.9,
        category: '카페',
      );

      final container = ProviderContainer(
        overrides: [
          savedPlacesProvider.overrideWith((ref) {
            return MockSavedPlacesNotifier(
              SavedPlacesState(places: [place]),
            );
          }),
        ],
      );

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: Scaffold(
              body: PlaceMarkerInfo(
                placeId: '1',
                onClose: () {
                  closeCalled = true;
                },
              ),
            ),
          ),
        ),
      );

      // When
      await tester.tap(find.byIcon(Icons.close));
      await tester.pumpAndSettle();

      // Then
      expect(closeCalled, isTrue);
    });
  });
}
```

### 6-3. 통합 테스트
```dart
// integration_test/saved_map_integration_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Saved Places Map Integration', () {
    testWidgets('complete user flow', (tester) async {
      // Given - 앱 시작
      await tester.pumpWidget(const HotlyApp());
      await tester.pumpAndSettle();

      // When - 저장 탭으로 이동
      await tester.tap(find.text('저장'));
      await tester.pumpAndSettle();

      // Then - 저장 화면 표시 확인
      expect(find.text('저장한 장소'), findsOneWidget);

      // When - 지도 보기 버튼 탭
      await tester.tap(find.byIcon(Icons.map));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Then - 지도 화면 로딩 확인
      expect(find.byType(KakaoMap), findsOneWidget);

      // When - 마커 탭 (실제 PlatformView이므로 모킹 필요)
      // await tester.tap(find.byType(Marker).first);
      // await tester.pumpAndSettle();

      // Then - PlaceMarkerInfo 표시 확인
      // expect(find.byType(PlaceMarkerInfo), findsOneWidget);

      // When - 상세보기 버튼 탭
      // await tester.tap(find.widgetWithText(ElevatedButton, '상세보기'));
      // await tester.pumpAndSettle();

      // Then - 상세 화면 이동 확인
      // expect(find.byType(PlaceDetailScreen), findsOneWidget);
    });
  });
}
```

---

## 7. 모니터링 및 로깅

### 7-1. 성능 메트릭 추적
```dart
class SavedMapAnalytics {
  static void trackMapLoad({
    required Duration loadTime,
    required int markerCount,
    required bool hasSavedPlaces,
  }) {
    Analytics.track('saved_map_load', {
      'load_time_ms': loadTime.inMilliseconds,
      'marker_count': markerCount,
      'has_saved_places': hasSavedPlaces,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  }

  static void trackMarkerTap({
    required String placeId,
    required String placeName,
  }) {
    Analytics.track('saved_map_marker_tap', {
      'place_id': placeId,
      'place_name': placeName,
    });
  }

  static void trackDetailNavigation({
    required String placeId,
    required String source, // 'marker_info' or 'direct'
  }) {
    Analytics.track('saved_map_detail_navigation', {
      'place_id': placeId,
      'source': source,
    });
  }

  static void trackMissingCoordinates({
    required String placeId,
    required String placeName,
  }) {
    Analytics.track('saved_map_missing_coords', {
      'place_id': placeId,
      'place_name': placeName,
    });
  }
}
```

### 7-2. 구현 시 로깅 추가
```dart
// SavedMapScreen의 onMapReady에서
onMapReady: (controller) {
  final stopwatch = Stopwatch()..stop();
  final loadTime = stopwatch.elapsed;

  _mapController = controller;
  setState(() {
    _isMapReady = true;
  });

  // 성능 메트릭 추적
  SavedMapAnalytics.trackMapLoad(
    loadTime: loadTime,
    markerCount: places.length,
    hasSavedPlaces: places.isNotEmpty,
  );

  if (places.isNotEmpty) {
    _fitBoundsToMarkers(places);
  }

  debugPrint(
    '🗺️ Map loaded in ${loadTime.inMilliseconds}ms with ${places.length} markers',
  );
},

// onMarkerTap에서
onMarkerTap: (markerId, latLng, zoomLevel) {
  final place = savedState.places.firstWhere(
    (p) => p.id == markerId,
    orElse: () => null,
  );

  if (place != null) {
    SavedMapAnalytics.trackMarkerTap(
      placeId: place.id,
      placeName: place.name,
    );
  }

  ref.read(mapProvider.notifier).selectPlace(markerId);
  _moveToMarker(latLng);
},
```

---

## 8. 배포 및 CI/CD

### 8-1. 빌드 설정
```yaml
# pubspec.yaml 의존성 확인
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.4.0
  freezed_annotation: ^2.4.1
  kakao_map_sdk: ^1.2.0  # 확인 필요
  geolocator: ^10.1.1
  permission_handler: ^11.4.0
  go_router: ^13.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  mockito: ^5.4.0
  build_runner: ^2.4.0
  freezed: ^2.4.1
```

### 8-2. 테스트 자동화
```yaml
# .github/workflows/flutter-test.yml

name: Flutter Tests

on:
  push:
    paths:
      - 'frontend/lib/features/map/**'
      - 'frontend/lib/features/saved/**'
      - 'frontend/test/features/map/**'
  pull_request:
    paths:
      - 'frontend/lib/features/map/**'

jobs:
  test:
    runs-on: macos-latest # Kakao Map SDK는 iOS/Android 필요

    steps:
      - uses: actions/checkout@v3

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.29.0'
          channel: 'stable'

      - name: Install dependencies
        working-directory: frontend
        run: flutter pub get

      - name: Run code generation
        working-directory: frontend
        run: flutter pub run build_runner build --delete-conflicting-outputs

      - name: Run unit tests
        working-directory: frontend
        run: flutter test test/features/map/
        env:
          KAKAO_NATIVE_APP_KEY: ${{ secrets.KAKAO_NATIVE_APP_KEY }}

      - name: Run integration tests
        working-directory: frontend
        run: flutter test integration_test/saved_map_integration_test.dart
        env:
          KAKAO_NATIVE_APP_KEY: ${{ secrets.KAKAO_NATIVE_APP_KEY }}
```

---

## 9. 보안 고려사항

### 9-1. API 키 보호
```dart
// .env.dev 파일에 저장 (git ignore)
KAKAO_NATIVE_APP_KEY=78ff40eb343af6b500a92c15fcd786db

// main.dart에서 로드
await dotenv.load(fileName: '.env.dev');
final kakaoMapKey = dotenv.env['KAKAO_NATIVE_APP_KEY'] ?? '';
```

### 9-2. 위치 데이터 보호
```dart
/// 사용자 위치는 메모리에만 저장, 서버에 전송 안 함
/// Analytics에도 정확한 좌표는 보내지 않고 지역(구 단위)만 전송
static void trackMapLoad({
  required int markerCount,
  String? userRegion, // "강남구" 수준의 정보만
}) {
  Analytics.track('saved_map_load', {
    'marker_count': markerCount,
    'user_region': userRegion, // 정확한 좌표 X
  });
}
```

---

## 10. 향후 개선사항 (Phase 2)

### 10-1. 커스텀 마커 아이콘
```dart
// 카테고리별 커스텀 아이콘
MarkerIcon _getCategoryIcon(String category) {
  switch (category) {
    case '카페':
      return const MarkerIcon(
        imagePath: 'assets/markers/cafe.png',
        size: Size(40, 40),
      );
    case '맛집':
      return const MarkerIcon(
        imagePath: 'assets/markers/restaurant.png',
        size: Size(40, 40),
      );
    // ...
    default:
      return const MarkerIcon(
        imagePath: 'assets/markers/default.png',
        size: Size(40, 40),
      );
  }
}
```

### 10-2. 마커 클러스터링
```dart
// 100개 이상 마커 시 클러스터링 적용
if (places.length > 100) {
  final clusterer = MarkerClusterer(
    clusterRadius: 100.0,
    maxMarkersPerCluster: 50,
  );
  markers = await clusterer.cluster(markers);
}
```

### 10-3. 필터링 기능
```dart
// 카테고리 필터 UI
Row(
  children: [
    FilterChip(
      label: const Text('카페'),
      selected: selectedCategories.contains('카페'),
      onSelected: (selected) {
        // 필터 토글
      },
    ),
    // ... 다른 카테고리들
  ],
)
```

---

## 11. 용어 사전 (Technical)

- **SavedPlacesProvider:** Riverpod StateNotifier, 저장된 장소 목록 관리
- **MapProvider:** 지도 상태(선택된 마커, 현재 위치) 관리
- **PlaceMarkerInfo:** 마커 클릭 시 하단에 표시되는 정보 위젯
- **KakaoMapController:** Kakao Map SDK 제어를 위한 컨트롤러
- **PlatformView:** Flutter에서 네이티브 뷰를 임베드하는 방식
- **UniqueKey:** 위젯 재생성을 강제하기 위한 키

---

## Changelog
- 2025-01-13: 초기 TRD 문서 작성 (작성자: Claude Code)
- 연관 문서:
  - PRD 04-1-saved-places-markers
  - TRD 04-map-visualization
- 버전: v1.0
