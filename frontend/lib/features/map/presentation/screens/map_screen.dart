import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/place.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';
import '../../domain/entities/map_entities.dart';
import '../providers/map_provider.dart';
import '../widgets/map_search_bar.dart';
import '../widgets/place_marker_info.dart';
import '../widgets/search_result_info.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen>
    with WidgetsBindingObserver, AutomaticKeepAliveClientMixin {
  KakaoMapController? _mapController;
  bool _isMapReady = false;
  bool _markersAdded = false; // 마커 추가 완료 여부

  // Unique key for KakaoMap widget to prevent recreation issues
  final GlobalKey _mapKey = GlobalKey();

  @override
  bool get wantKeepAlive => true; // StatefulShellRoute에서 상태 유지

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    AppLogger.d('MapScreen initState', tag: 'Map');

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        ref.read(mapProvider.notifier).getCurrentLocation();
      }
    });

    // 저장된 장소 데이터가 변경될 때 마커 업데이트
    ref.listenManual(
      savedPlacesProvider.select((state) => state.places),
      (previous, next) {
        if (_isMapReady && !_markersAdded && next.isNotEmpty) {
          AppLogger.d('Places loaded, adding markers...', tag: 'Map');
          _addMarkersToMap(next);
          _markersAdded = true;
        }
      },
    );
  }

  @override
  void reassemble() {
    super.reassemble();
    // Hot Reload 시 호출됨
    AppLogger.d('MapScreen reassemble (Hot Reload detected)', tag: 'Map');
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    if (_mapController == null) return;

    switch (state) {
      case AppLifecycleState.resumed:
        AppLogger.d('MapScreen resumed', tag: 'Map');
        _mapController?.resume();
        break;
      case AppLifecycleState.paused:
      case AppLifecycleState.inactive:
        AppLogger.d('MapScreen paused/inactive', tag: 'Map');
        _mapController?.pause();
        break;
      case AppLifecycleState.detached:
      case AppLifecycleState.hidden:
        break;
    }
  }

  // 안전하게 카메라 이동
  Future<void> _moveToLocation(double latitude, double longitude) async {
    if (!_isMapReady || _mapController == null) return;

    try {
      await _mapController!.moveCamera(
        CameraUpdate.newCenterPosition(
          LatLng(latitude, longitude),
          zoomLevel: 16,
        ),
        animation: const CameraAnimation(
          500, // duration in milliseconds
          autoElevation: false,
        ),
      );
    } catch (e) {
      AppLogger.e('Camera move error', tag: 'Map', error: e);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context); // AutomaticKeepAliveClientMixin 필수
    final state = ref.watch(mapProvider);

    return Scaffold(
      body: Stack(
        children: [
          // Kakao Map
          KakaoMap(
            key: _mapKey,
            option: KakaoMapOption(
              position: const LatLng(37.5665, 126.9780), // 서울시청
              zoomLevel: 16,
              mapType: MapType.normal,
            ),
            onMapReady: (controller) async {
              _mapController = controller;
              setState(() {
                _isMapReady = true;
              });
              AppLogger.d('Kakao Map is now ready', tag: 'Map');

              // 저장된 장소 마커 추가 (이미 로드된 경우)
              final savedPlacesState = ref.read(savedPlacesProvider);
              if (!savedPlacesState.isLoading &&
                  savedPlacesState.places.isNotEmpty &&
                  !_markersAdded) {
                AppLogger.d('Places already loaded, adding markers...', tag: 'Map');
                await _addMarkersToMap(savedPlacesState.places);
                _markersAdded = true;
              }

              // 현재 위치 마커 추가
              final currentLocation = ref.read(mapProvider).currentLocation;
              if (currentLocation != null) {
                await _addCurrentLocationMarker(currentLocation);
              }
            },
          ),

          // Back button
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            left: 8,
            child: SafeArea(
              child: IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => Navigator.of(context).pop(),
                style: IconButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.textPrimary,
                ),
              ),
            ),
          ),

          // Search bar overlay
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            left: 64,
            right: 16,
            child: MapSearchBar(
              onPlaceSelected: (latitude, longitude) {
                _moveToLocation(latitude, longitude);
              },
            ),
          ),

          // Current location button
          Positioned(
            bottom: 100,
            right: 16,
            child: FloatingActionButton(
              heroTag: 'current_location',
              onPressed: () async {
                await ref.read(mapProvider.notifier).getCurrentLocation();
                final location = ref.read(mapProvider).currentLocation;
                if (location != null) {
                  _moveToLocation(location.latitude, location.longitude);
                }
              },
              backgroundColor: Colors.white,
              child: Icon(
                Icons.my_location,
                color: AppColors.primary,
              ),
            ),
          ),

          // Selected search result info
          if (state.selectedSearchResult != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: SearchResultInfo(
                place: state.selectedSearchResult!,
                onClose: () {
                  ref.read(mapProvider.notifier).selectSearchResult(null);
                },
              ),
            )
          // Selected saved place info
          else if (state.selectedPlaceId != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: PlaceMarkerInfo(
                placeId: state.selectedPlaceId!,
                onClose: () {
                  ref.read(mapProvider.notifier).selectPlace(null);
                },
              ),
            ),

          // Loading indicator
          if (state.isLoading)
            const Positioned(
              top: 100,
              left: 0,
              right: 0,
              child: Center(
                child: CircularProgressIndicator(),
              ),
            ),
        ],
      ),
    );
  }

  /// 지도에 마커 추가
  Future<void> _addMarkersToMap(List<Place> places) async {
    if (_mapController == null || !mounted) return;

    AppLogger.d('Starting to add ${places.length} markers', tag: 'Map');

    try {
      // 마커 아이콘 생성 (한 번만 생성해서 재사용)
      final markerIcon = await _createMarkerIcon();
      if (markerIcon == null) {
        AppLogger.e('Failed to create marker icon', tag: 'Map');
        return;
      }

      // 각 장소를 Poi로 추가
      for (final place in places) {
        // 좌표가 없는 장소는 스킵
        if (place.latitude == null || place.longitude == null) {
          AppLogger.w('Skipping place without coordinates: ${place.name}', tag: 'Map');
          continue;
        }

        try {
          // PoiStyle with icon
          final poiStyle = PoiStyle(
            icon: markerIcon,
            anchor: const KPoint(0.5, 1.0), // 하단 중앙 고정
            zoomLevel: 0,
          );

          await _mapController!.labelLayer.addPoi(
            LatLng(place.latitude!, place.longitude!),
            style: poiStyle,
            id: place.id,
            text: place.name,
            onClick: () {
              AppLogger.d('Marker tapped: ${place.name}', tag: 'Map');
              ref.read(mapProvider.notifier).selectPlace(place.id);
            },
          );

          AppLogger.d('Added marker for: ${place.name}', tag: 'Map');
        } catch (e) {
          AppLogger.e('Failed to add marker for ${place.name}', tag: 'Map', error: e);
        }
      }

      AppLogger.i('Finished adding markers', tag: 'Map');
    } catch (e) {
      AppLogger.e('Failed to add markers', tag: 'Map', error: e);
    }
  }

  /// 마커 아이콘 생성 (간단한 빨간색 핀 모양)
  Future<KImage?> _createMarkerIcon() async {
    try {
      final markerWidget = Container(
        width: 16,
        height: 20,
        decoration: BoxDecoration(
          color: Colors.red,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.place,
              color: Colors.white,
              size: 13,
            ),
            Container(
              width: 0,
              height: 0,
              decoration: const BoxDecoration(
                border: Border(
                  left: BorderSide(width: 3, color: Colors.transparent),
                  right: BorderSide(width: 3, color: Colors.transparent),
                  bottom: BorderSide(width: 4, color: Colors.red),
                ),
              ),
            ),
          ],
        ),
      );

      final icon = await KImage.fromWidget(
        markerWidget,
        const Size(16, 20),
        context: context,
      );

      return icon;
    } catch (e) {
      AppLogger.e('Failed to create marker icon', tag: 'Map', error: e);
      return null;
    }
  }

  /// 현재 위치 마커 추가
  Future<void> _addCurrentLocationMarker(CoordinatePoint location) async {
    if (_mapController == null || !mounted) return;

    try {
      // 현재 위치 아이콘 생성 (파란색 원)
      final currentLocationIcon = await _createCurrentLocationIcon();
      if (currentLocationIcon == null) {
        AppLogger.e('Failed to create current location icon', tag: 'Map');
        return;
      }

      final poiStyle = PoiStyle(
        icon: currentLocationIcon,
        anchor: const KPoint(0.5, 0.5),
        zoomLevel: 0,
      );

      // 현재 위치 Poi 추가
      await _mapController!.labelLayer.addPoi(
        LatLng(location.latitude, location.longitude),
        style: poiStyle,
        id: 'current_location',
        text: '현재 위치',
      );

      AppLogger.d('Added current location marker', tag: 'Map');
    } catch (e) {
      AppLogger.e('Failed to add current location marker', tag: 'Map', error: e);
    }
  }

  /// 현재 위치 아이콘 생성 (파란색 원)
  Future<KImage?> _createCurrentLocationIcon() async {
    try {
      final iconWidget = Container(
        width: 12,
        height: 12,
        decoration: BoxDecoration(
          color: Colors.blue,
          shape: BoxShape.circle,
          border: Border.all(
            color: Colors.white,
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.blue.withOpacity(0.3),
              blurRadius: 3,
              spreadRadius: 1,
            ),
          ],
        ),
      );

      final icon = await KImage.fromWidget(
        iconWidget,
        const Size(12, 12),
        context: context,
      );

      return icon;
    } catch (e) {
      AppLogger.e('Failed to create current location icon', tag: 'Map', error: e);
      return null;
    }
  }

  @override
  void dispose() {
    AppLogger.d('MapScreen dispose', tag: 'Map');
    WidgetsBinding.instance.removeObserver(this);
    _mapController?.finish();
    _mapController = null;
    super.dispose();
  }
}
