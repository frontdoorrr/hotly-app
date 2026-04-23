import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/place.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';
import '../../../saved/presentation/widgets/tag_filter_chips.dart';
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
  bool _markersAdded = false;
  bool _showList = false;
  KImage? _cachedMarkerIcon;
  KImage? _cachedCurrentLocationIcon;
  ProviderSubscription<List<Place>>? _placesSubscription;

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
        // 위치 요청과 마커 아이콘 렌더링을 WebView 로딩과 병렬로 시작
        ref.read(mapProvider.notifier).getCurrentLocation();
        _createMarkerIcon();
        _createCurrentLocationIcon();
      }
    });

    // 저장된 장소 데이터가 변경될 때 마커 업데이트
    _placesSubscription = ref.listenManual(
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
    final selectedSearchResult = ref.watch(mapProvider.select((s) => s.selectedSearchResult));
    final selectedPlaceId = ref.watch(mapProvider.select((s) => s.selectedPlaceId));
    final isLoading = ref.watch(mapProvider.select((s) => s.isLoading));

    return Scaffold(
      body: Stack(
        children: [
          // Kakao Map (항상 렌더링 — 상태 유지)
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

              final savedPlacesState = ref.read(savedPlacesProvider);
              final currentLocation = ref.read(mapProvider).currentLocation;

              // 저장된 장소 마커와 현재 위치 마커를 병렬로 추가
              await Future.wait([
                if (!savedPlacesState.isLoading &&
                    savedPlacesState.places.isNotEmpty &&
                    !_markersAdded)
                  _addMarkersToMap(savedPlacesState.places).then((_) {
                    _markersAdded = true;
                  }),
                if (currentLocation != null)
                  _addCurrentLocationMarker(currentLocation),
              ]);
            },
          ),

          // Search bar overlay
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            left: 16,
            right: 16,
            child: MapSearchBar(
              onPlaceSelected: (latitude, longitude) {
                _moveToLocation(latitude, longitude);
              },
            ),
          ),

          // Current location button (지도 모드일 때만)
          if (!_showList)
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

          // 목록 오버레이
          if (_showList)
            Positioned.fill(
              top: MediaQuery.of(context).padding.top + 56,
              child: _buildPlacesList(context, ref),
            ),

          // 목록/지도 토글 버튼
          Positioned(
            bottom: 36,
            right: 16,
            child: FloatingActionButton.extended(
              heroTag: 'toggle_list',
              onPressed: () => setState(() => _showList = !_showList),
              backgroundColor: AppColors.primary,
              icon: Icon(
                _showList ? Icons.map : Icons.list,
                color: Colors.white,
              ),
              label: Text(
                _showList ? '지도' : '목록',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
              ),
            ),
          ),

          // Selected search result info (지도 모드일 때만)
          if (!_showList && selectedSearchResult != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: SearchResultInfo(
                place: selectedSearchResult,
                onClose: () {
                  ref.read(mapProvider.notifier).selectSearchResult(null);
                },
              ),
            )
          // Selected saved place info
          else if (selectedPlaceId != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: PlaceMarkerInfo(
                placeId: selectedPlaceId,
                onClose: () {
                  ref.read(mapProvider.notifier).selectPlace(null);
                },
              ),
            ),

          // Loading indicator
          if (isLoading)
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

      // PoiStyle은 모든 마커가 동일하므로 한 번만 생성
      final poiStyle = PoiStyle(
        icon: markerIcon,
        anchor: const KPoint(0.5, 1.0),
        zoomLevel: 0,
      );

      final validPlaces = places
          .where((p) => p.latitude != null && p.longitude != null)
          .toList();

      // 모든 마커를 병렬로 추가
      await Future.wait(
        validPlaces.map((place) async {
          try {
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
          } catch (e) {
            AppLogger.e('Failed to add marker for ${place.name}', tag: 'Map', error: e);
          }
        }),
      );

      AppLogger.i('Finished adding ${validPlaces.length} markers', tag: 'Map');
    } catch (e) {
      AppLogger.e('Failed to add markers', tag: 'Map', error: e);
    }
  }

  /// 마커 아이콘 생성 (간단한 빨간색 핀 모양)
  Future<KImage?> _createMarkerIcon() async {
    if (_cachedMarkerIcon != null) return _cachedMarkerIcon;
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

      _cachedMarkerIcon = icon;
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
    if (_cachedCurrentLocationIcon != null) return _cachedCurrentLocationIcon;
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

      _cachedCurrentLocationIcon = icon;
      return icon;
    } catch (e) {
      AppLogger.e('Failed to create current location icon', tag: 'Map', error: e);
      return null;
    }
  }

  Widget _buildPlacesList(BuildContext context, WidgetRef ref) {
    final state = ref.watch(savedPlacesProvider);
    final notifier = ref.read(savedPlacesProvider.notifier);

    return Container(
      color: Theme.of(context).scaffoldBackgroundColor,
      child: _buildListBody(context, state, notifier, ref),
    );
  }

  Widget _buildListBody(
    BuildContext context,
    SavedPlacesState state,
    SavedPlacesNotifier notifier,
    WidgetRef ref,
  ) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: AppColors.error),
            const SizedBox(height: 16),
            Text(
              state.errorMessage ?? '장소를 불러올 수 없습니다.',
              style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(savedPlacesProvider.notifier).refresh(),
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (state.places.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.bookmark_border, size: 64, color: AppColors.textSecondary),
            const SizedBox(height: 16),
            Text(
              '저장된 장소가 없습니다.',
              style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }

    final tagStats = notifier.tagStatistics;
    final filteredPlaces = notifier.filteredPlaces;

    return Column(
      children: [
        if (tagStats.isNotEmpty)
          TagFilterChips(
            availableTags: tagStats.keys.toList(),
            tagCounts: tagStats.values.toList(),
            selectedTags: state.selectedTags,
            totalPlacesCount: state.places.length,
            onTagSelected: (tag) {
              if (tag.isEmpty) {
                notifier.clearTagFilters();
              } else {
                notifier.toggleTag(tag);
              }
            },
          ),
        Expanded(
          child: filteredPlaces.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.search_off, size: 64, color: AppColors.textSecondary),
                      const SizedBox(height: 16),
                      Text(
                        '해당 태그의 장소가 없습니다.',
                        style: AppTextStyles.body2.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      OutlinedButton(
                        onPressed: () => notifier.clearTagFilters(),
                        child: const Text('필터 초기화'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    await ref.read(savedPlacesProvider.notifier).refresh();
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.all(AppTheme.space4),
                    itemCount: filteredPlaces.length,
                    itemBuilder: (context, index) {
                      final place = filteredPlaces[index];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: AppTheme.space3),
                        child: PlaceCard(
                          place: place,
                          onTap: () {
                            setState(() => _showList = false);
                            if (place.latitude != null && place.longitude != null) {
                              _moveToLocation(place.latitude!, place.longitude!);
                            }
                          },
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    AppLogger.d('MapScreen dispose', tag: 'Map');
    _placesSubscription?.close();
    WidgetsBinding.instance.removeObserver(this);
    _mapController?.finish();
    _mapController = null;
    super.dispose();
  }
}
