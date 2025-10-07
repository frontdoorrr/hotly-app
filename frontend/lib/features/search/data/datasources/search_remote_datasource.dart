import 'package:dio/dio.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../shared/models/place.dart';

/// Search Remote Data Source
class SearchRemoteDataSource {
  final Dio dio;

  SearchRemoteDataSource(this.dio);

  /// 장소 검색 API
  Future<List<Place>> searchPlaces({
    required String query,
    String? category,
    double? maxDistance,
    double? minRating,
    int limit = 20,
    int offset = 0,
  }) async {
    try {
      final queryParams = {
        'q': query,
        'limit': limit,
        'offset': offset,
        if (category != null) 'category': category,
        if (maxDistance != null) 'distance': maxDistance,
        if (minRating != null) 'min_rating': minRating,
      };

      final response = await dio.get(
        ApiEndpoints.search,
        queryParameters: queryParams,
      );

      final List<dynamic> data = response.data['places'] ?? response.data;
      return data.map((json) => Place.fromJson(json)).toList();
    } on DioException catch (e) {
      // Re-throw DioException - it will be handled by DioClient interceptors
      rethrow;
    }
  }

  /// 자동완성 API
  Future<List<String>> getAutocompleteSuggestions({
    required String query,
    int limit = 5,
  }) async {
    try {
      final response = await dio.get(
        ApiEndpoints.autocomplete,
        queryParameters: {
          'q': query,
          'limit': limit,
        },
      );

      final List<dynamic> data = response.data['suggestions'] ?? response.data;
      return data.map((item) => item.toString()).toList();
    } on DioException catch (e) {
      rethrow;
    }
  }
}
