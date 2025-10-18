import 'package:dartz/dartz.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/place.dart';
import '../../../map/domain/entities/map_entities.dart';

/// Place Repository Interface
abstract class PlaceRepository {
  /// 장소 목록 조회
  Future<Either<ApiException, List<Place>>> getPlaces({
    int page = 1,
    int pageSize = 20,
  });

  /// 지도 영역 내 장소 조회 (동적 로딩용)
  Future<Either<ApiException, List<Place>>> getPlacesByBounds({
    required MapBounds bounds,
    int? zoomLevel,
  });

  /// 장소 상세 정보 조회
  Future<Either<ApiException, Place>> getPlaceById(String placeId);

  /// 장소 좋아요 토글
  Future<Either<ApiException, void>> toggleLike(String placeId);

  /// 장소 저장 토글
  Future<Either<ApiException, void>> toggleSave(String placeId);

  /// 비슷한 장소 조회
  Future<Either<ApiException, List<Place>>> getSimilarPlaces({
    required String placeId,
    int limit = 6,
  });
}
