import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
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
  final Set<Marker> _markers = {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(mapProvider.notifier).getCurrentLocation();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mapProvider);

    return Scaffold(
      body: Stack(
        children: [
          // Kakao Map
          _buildKakaoMap(state),

          // Search bar overlay
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            left: 16,
            right: 16,
            child: const MapSearchBar(),
          ),

          // Current location button
          Positioned(
            bottom: 100,
            right: 16,
            child: FloatingActionButton(
              heroTag: 'current_location',
              onPressed: _moveToCurrentLocation,
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

  Widget _buildKakaoMap(MapState state) {
    // Default center: Seoul City Hall or current location
    final centerLat = state.currentLocation?.latitude ?? 37.5665;
    final centerLng = state.currentLocation?.longitude ?? 126.9780;

    // Create markers from places on map
    _updateMarkers(state.placesOnMap);

    return KakaoMap(
      onMapCreated: (controller) {
        setState(() {
          _mapController = controller;
        });
      },
      center: LatLng(centerLat, centerLng),
      markers: _markers.toList(),
      // TODO: kakao_map_plugin doesn't support onCameraMove callback
      // Consider using onMapTap or periodic updates to reload places
      onMapTap: (latLng) {
        // Deselect marker on map tap
        ref.read(mapProvider.notifier).selectPlace(null);
      },
    );
  }

  void _updateMarkers(List<Map<String, dynamic>> places) {
    _markers.clear();

    for (final place in places) {
      final lat = place['latitude'] as double?;
      final lng = place['longitude'] as double?;
      final placeId = place['id']?.toString() ?? '';
      final placeName = place['name'] as String? ?? 'Unknown';

      if (lat != null && lng != null) {
        _markers.add(
          Marker(
            markerId: placeId,
            latLng: LatLng(lat, lng),
            width: 30,
            height: 40,
            offsetX: 15,
            offsetY: 40,
            markerImageSrc:
                'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png',
          ),
        );
      }
    }

    if (mounted) {
      setState(() {});
    }
  }

  void _moveToCurrentLocation() async {
    await ref.read(mapProvider.notifier).getCurrentLocation();
    final location = ref.read(mapProvider).currentLocation;

    if (location != null && _mapController != null) {
      _mapController!.setCenter(
        LatLng(location.latitude, location.longitude),
      );
    }
  }

  // TODO: Implement dynamic place loading when kakao_map_plugin supports camera callbacks
  // For now, places are loaded based on user's location in _loadNearbyPlaces()

  @override
  void dispose() {
    _mapController?.dispose();
    super.dispose();
  }
}
