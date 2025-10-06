import '../../../../core/network/dio_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../shared/models/place.dart';

/// Place Remote Data Source
class PlaceRemoteDataSource {
  final DioClient _dioClient;

  PlaceRemoteDataSource(this._dioClient);

  /// 장소 상세 정보 조회
  Future<Place> getPlaceById(String placeId) async {
    final response = await _dioClient.get(
      '${ApiEndpoints.places}/$placeId',
    );

    return Place.fromJson(response.data);
  }

  /// 장소 좋아요 토글
  Future<void> toggleLike(String placeId) async {
    await _dioClient.post(
      '${ApiEndpoints.places}/$placeId/like',
    );
  }

  /// 장소 저장 토글
  Future<void> toggleSave(String placeId) async {
    await _dioClient.post(
      '${ApiEndpoints.places}/$placeId/save',
    );
  }

  /// 비슷한 장소 조회
  Future<List<Place>> getSimilarPlaces({
    required String placeId,
    int limit = 6,
  }) async {
    final response = await _dioClient.get(
      '${ApiEndpoints.places}/$placeId/similar',
      queryParameters: {
        'limit': limit,
      },
    );

    final List<dynamic> data = response.data['places'] ?? response.data;
    return data.map((json) => Place.fromJson(json)).toList();
  }
}
