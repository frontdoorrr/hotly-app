import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/map_provider.dart';
import '../widgets/map_search_bar.dart';
import '../widgets/place_marker_info.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  KakaoMapController? _mapController;
  bool _isMapReady = false;
  final _mapKey = UniqueKey(); // PlatformView 재생성 방지용 고유 키

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        ref.read(mapProvider.notifier).getCurrentLocation();
      }
    });
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
      debugPrint('⛔ Camera move error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mapProvider);

    return Scaffold(
      body: Stack(
        children: [
          // Kakao Map
          KakaoMap(
            key: _mapKey, // 고유 키로 PlatformView 재생성 문제 방지
            option: KakaoMapOption(
              position: const LatLng(37.5665, 126.9780), // 서울시청
              zoomLevel: 16,
              mapType: MapType.normal,
            ),
            onMapReady: (controller) {
              _mapController = controller;
              setState(() {
                _isMapReady = true;
              });
              debugPrint('🗺️ Kakao Map is now ready');
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
            child: const MapSearchBar(),
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

          // Selected place info
          if (state.selectedPlaceId != null)
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

  @override
  void dispose() {
    _mapController?.finish();
    super.dispose();
  }
}
