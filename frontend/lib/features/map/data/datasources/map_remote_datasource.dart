import 'package:dio/dio.dart';
import '../../../../core/network/api_endpoints.dart';
import '../models/map_models.dart';

/// Remote data source for Kakao Map API
class MapRemoteDataSource {
  final Dio _dio;

  MapRemoteDataSource(this._dio);

  /// Geocode address to coordinates
  ///
  /// POST /api/v1/map/geocode
  Future<AddressSearchResultModel> geocodeAddress(String address) async {
    try {
      final response = await _dio.post(
        '${ApiEndpoints.baseUrl}/map/geocode',
        queryParameters: {'address': address},
      );

      return AddressSearchResultModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Reverse geocode coordinates to address
  ///
  /// GET /api/v1/map/reverse-geocode
  Future<ReverseGeocodeResultModel> reverseGeocode({
    required double latitude,
    required double longitude,
  }) async {
    try {
      final response = await _dio.get(
        '${ApiEndpoints.baseUrl}/map/reverse-geocode',
        queryParameters: {
          'latitude': latitude,
          'longitude': longitude,
        },
      );

      return ReverseGeocodeResultModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Search places by keyword
  ///
  /// GET /api/v1/map/search
  Future<List<PlaceSearchResultModel>> searchPlaces({
    required String query,
    double? latitude,
    double? longitude,
    double? radiusKm,
    int limit = 15,
  }) async {
    try {
      final response = await _dio.get(
        '${ApiEndpoints.baseUrl}/map/search',
        queryParameters: {
          'query': query,
          if (latitude != null) 'latitude': latitude,
          if (longitude != null) 'longitude': longitude,
          if (radiusKm != null) 'radius_km': radiusKm,
          'limit': limit,
        },
      );

      final data = response.data as List;
      return data
          .map((json) =>
              PlaceSearchResultModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get places within map bounds
  ///
  /// GET /api/v1/map/places
  Future<List<Map<String, dynamic>>> getPlacesInBounds({
    required double swLat,
    required double swLng,
    required double neLat,
    required double neLng,
    String? category,
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '${ApiEndpoints.baseUrl}/map/places',
        queryParameters: {
          'sw_lat': swLat,
          'sw_lng': swLng,
          'ne_lat': neLat,
          'ne_lng': neLng,
          if (category != null) 'category': category,
          'limit': limit,
        },
      );

      return List<Map<String, dynamic>>.from(response.data as List);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    switch (e.response?.statusCode) {
      case 404:
        return Exception('Address or place not found');
      case 503:
        return Exception('Map service temporarily unavailable');
      default:
        return Exception(
          e.response?.data['detail'] ?? 'Failed to access map service',
        );
    }
  }
}
