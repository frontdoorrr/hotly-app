import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../repositories/home_repository.dart';

/// Use Case: 추천 장소 가져오기
/// 비즈니스 로직을 캡슐화하여 재사용 가능하게 만듦
class GetRecommendedPlaces {
  final HomeRepository repository;

  GetRecommendedPlaces(this.repository);

  Future<Either<ApiException, List<Place>>> call({
    int limit = 10,
  }) async {
    return await repository.getRecommendedPlaces(limit: limit);
  }
}
