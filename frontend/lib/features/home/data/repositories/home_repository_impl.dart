import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../../domain/repositories/home_repository.dart';
import '../datasources/home_remote_datasource.dart';

/// Home Repository Implementation
/// Domain의 인터페이스를 구현하는 실제 구현체
class HomeRepositoryImpl implements HomeRepository {
  final HomeRemoteDataSource remoteDataSource;

  HomeRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<ApiException, List<Place>>> getRecommendedPlaces({
    int limit = 10,
  }) async {
    try {
      final places = await remoteDataSource.getRecommendedPlaces(
        limit: limit,
      );
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, List<Place>>> getNearbyPlaces({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
    int limit = 20,
  }) async {
    try {
      final places = await remoteDataSource.getNearbyPlaces(
        latitude: latitude,
        longitude: longitude,
        radiusKm: radiusKm,
        limit: limit,
      );
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, List<Place>>> getPopularPlaces({
    int limit = 12,
  }) async {
    try {
      final places = await remoteDataSource.getPopularPlaces(limit: limit);
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }
}
