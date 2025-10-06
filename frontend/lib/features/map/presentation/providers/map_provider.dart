import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:geolocator/geolocator.dart';
import '../../../../core/network/dio_client.dart';
import '../../data/datasources/map_remote_datasource.dart';
import '../../data/repositories/map_repository_impl.dart';
import '../../domain/entities/map_entities.dart';
import '../../domain/repositories/map_repository.dart';

part 'map_provider.freezed.dart';

/// Map State
@freezed
class MapState with _$MapState {
  const factory MapState({
    CoordinatePoint? currentLocation,
    @Default([]) List<PlaceSearchResult> searchResults,
    @Default([]) List<Map<String, dynamic>> placesOnMap,
    @Default(false) bool isLoading,
    @Default(false) bool isSearching,
    String? error,
    String? selectedPlaceId,
  }) = _MapState;
}

/// Map State Notifier
class MapNotifier extends StateNotifier<MapState> {
  final MapRepository _repository;

  MapNotifier(this._repository) : super(const MapState());

  /// Get current location
  Future<void> getCurrentLocation() async {
    try {
      // Check permission
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

      // Get position
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

  /// Search places by keyword
  Future<void> searchPlaces({
    required String query,
    double? radiusKm,
  }) async {
    state = state.copyWith(isSearching: true, error: null);

    final result = await _repository.searchPlaces(
      query: query,
      latitude: state.currentLocation?.latitude,
      longitude: state.currentLocation?.longitude,
      radiusKm: radiusKm,
      limit: 20,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isSearching: false,
          error: error.toString(),
        );
      },
      (results) {
        state = state.copyWith(
          isSearching: false,
          searchResults: results,
        );
      },
    );
  }

  /// Load places within map bounds
  Future<void> loadPlacesInBounds({
    required double swLat,
    required double swLng,
    required double neLat,
    required double neLng,
    String? category,
  }) async {
    state = state.copyWith(isLoading: true);

    final result = await _repository.getPlacesInBounds(
      swLat: swLat,
      swLng: swLng,
      neLat: neLat,
      neLng: neLng,
      category: category,
      limit: 100,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error.toString(),
        );
      },
      (places) {
        state = state.copyWith(
          isLoading: false,
          placesOnMap: places,
        );
      },
    );
  }

  /// Geocode address to coordinates
  Future<CoordinatePoint?> geocodeAddress(String address) async {
    final result = await _repository.geocodeAddress(address);

    return result.fold(
      (error) {
        state = state.copyWith(error: error.toString());
        return null;
      },
      (addressResult) {
        return CoordinatePoint(
          latitude: addressResult.latitude,
          longitude: addressResult.longitude,
        );
      },
    );
  }

  /// Reverse geocode coordinates to address
  Future<String?> reverseGeocode({
    required double latitude,
    required double longitude,
  }) async {
    final result = await _repository.reverseGeocode(
      latitude: latitude,
      longitude: longitude,
    );

    return result.fold(
      (error) {
        state = state.copyWith(error: error.toString());
        return null;
      },
      (reverseResult) {
        return reverseResult.roadAddress ?? reverseResult.jibunAddress;
      },
    );
  }

  /// Select a place on the map
  void selectPlace(String? placeId) {
    state = state.copyWith(selectedPlaceId: placeId);
  }

  /// Clear search results
  void clearSearch() {
    state = state.copyWith(searchResults: []);
  }
}

/// Provider for MapRepository
final mapRepositoryProvider = Provider<MapRepository>((ref) {
  final dio = ref.watch(dioClientProvider);
  final remoteDataSource = MapRemoteDataSource(dio);
  return MapRepositoryImpl(remoteDataSource);
});

/// Provider for MapNotifier
final mapProvider = StateNotifierProvider<MapNotifier, MapState>((ref) {
  final repository = ref.watch(mapRepositoryProvider);
  return MapNotifier(repository);
});
