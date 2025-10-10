import 'package:dio/dio.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../shared/models/place.dart';

/// Home Remote Data Source
/// API 호출을 담당하는 레이어
class HomeRemoteDataSource {
  final Dio dio;

  HomeRemoteDataSource(this.dio);

  /// 추천 장소 API 호출
  /// TODO: 백엔드 API 구현 후 주석 해제
  Future<List<Place>> getRecommendedPlaces({int limit = 10}) async {
    // 임시: 빈 리스트 반환 (API 미구현)
    return [];

    /* API 구현 후 사용할 코드:
    try {
      final response = await dio.get(
        ApiEndpoints.recommendations,
        queryParameters: {'limit': limit},
      );

      final List<dynamic> data = response.data['places'] ?? response.data;
      return data.map((json) => Place.fromJson(json)).toList();
    } on DioException catch (e) {
      rethrow;
    }
    */
  }

  /// 근처 장소 API 호출
  /// TODO: 백엔드 API 구현 후 주석 해제
  Future<List<Place>> getNearbyPlaces({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
    int limit = 20,
  }) async {
    // 임시: 빈 리스트 반환 (API 미구현)
    return [];

    /* API 구현 후 사용할 코드:
    try {
      final response = await dio.get(
        ApiEndpoints.placeNearby,
        queryParameters: {
          'lat': latitude,
          'lng': longitude,
          'radius': radiusKm,
          'limit': limit,
        },
      );

      final List<dynamic> data = response.data['places'] ?? response.data;
      return data.map((json) => Place.fromJson(json)).toList();
    } on DioException catch (e) {
      rethrow;
    }
    */
  }

  /// 인기 장소 API 호출
  /// TODO: 백엔드 API 구현 후 주석 해제
  Future<List<Place>> getPopularPlaces({int limit = 12}) async {
    // 임시: 빈 리스트 반환 (API 미구현)
    return [];

    /* API 구현 후 사용할 코드:
    try {
      final response = await dio.get(
        ApiEndpoints.places,
        queryParameters: {
          'sort': 'popular',
          'limit': limit,
        },
      );

      final List<dynamic> data = response.data['places'] ?? response.data;
      return data.map((json) => Place.fromJson(json)).toList();
    } on DioException catch (e) {
      rethrow;
    }
    */
  }
}
