import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';

/// Home Repository Interface
/// Domain layer는 구현체가 아닌 인터페이스만 정의
abstract class HomeRepository {
  /// 추천 장소 조회
  Future<Either<ApiException, List<Place>>> getRecommendedPlaces({
    int limit = 10,
  });

  /// 근처 장소 조회
  Future<Either<ApiException, List<Place>>> getNearbyPlaces({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
    int limit = 20,
  });

  /// 인기 장소 조회
  Future<Either<ApiException, List<Place>>> getPopularPlaces({
    int limit = 12,
  });
}
