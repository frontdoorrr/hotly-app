import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../repositories/home_repository.dart';

/// Use Case: 근처 장소 가져오기
class GetNearbyPlaces {
  final HomeRepository repository;

  GetNearbyPlaces(this.repository);

  Future<Either<ApiException, List<Place>>> call({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
    int limit = 20,
  }) async {
    return await repository.getNearbyPlaces(
      latitude: latitude,
      longitude: longitude,
      radiusKm: radiusKm,
      limit: limit,
    );
  }
}
