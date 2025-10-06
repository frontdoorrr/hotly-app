import 'package:freezed_annotation/freezed_annotation.dart';

part 'map_entities.freezed.dart';

/// Geographic coordinate point
@freezed
class CoordinatePoint with _$CoordinatePoint {
  const factory CoordinatePoint({
    required double latitude,
    required double longitude,
  }) = _CoordinatePoint;
}

/// Address search result from geocoding
@freezed
class AddressSearchResult with _$AddressSearchResult {
  const factory AddressSearchResult({
    required String address,
    required double latitude,
    required double longitude,
    String? roadAddress,
    String? jibunAddress,
    String? buildingName,
  }) = _AddressSearchResult;
}

/// Reverse geocoding result
@freezed
class ReverseGeocodeResult with _$ReverseGeocodeResult {
  const factory ReverseGeocodeResult({
    required double latitude,
    required double longitude,
    String? roadAddress,
    String? jibunAddress,
    String? region1depth,
    String? region2depth,
    String? region3depth,
  }) = _ReverseGeocodeResult;
}

/// Place search result from Kakao Map
@freezed
class PlaceSearchResult with _$PlaceSearchResult {
  const factory PlaceSearchResult({
    required String placeId,
    required String placeName,
    required String address,
    required double latitude,
    required double longitude,
    String? categoryName,
    String? roadAddress,
    String? phone,
    String? placeUrl,
    double? distance,
  }) = _PlaceSearchResult;
}

/// Map marker cluster
@freezed
class MarkerCluster with _$MarkerCluster {
  const factory MarkerCluster({
    required String clusterId,
    required double centerLatitude,
    required double centerLongitude,
    required int placeCount,
    required List<String> placeIds,
    MapBounds? bounds,
  }) = _MarkerCluster;
}

/// Map viewport bounds
@freezed
class MapBounds with _$MapBounds {
  const factory MapBounds({
    required double north,
    required double south,
    required double east,
    required double west,
  }) = _MapBounds;
}

/// Route polyline for visualization
@freezed
class RoutePolyline with _$RoutePolyline {
  const factory RoutePolyline({
    required String routeId,
    required List<CoordinatePoint> coordinates,
    required double totalDistanceKm,
    required int totalDurationMinutes,
    required List<Map<String, dynamic>> waypoints,
  }) = _RoutePolyline;
}
