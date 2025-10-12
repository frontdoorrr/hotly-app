import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/place.dart';
import '../../domain/repositories/place_repository.dart';
import '../datasources/place_remote_datasource.dart';

/// Place Repository Implementation
class PlaceRepositoryImpl implements PlaceRepository {
  final PlaceRemoteDataSource remoteDataSource;

  PlaceRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<ApiException, List<Place>>> getPlaces({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final places = await remoteDataSource.getPlaces(
        page: page,
        pageSize: pageSize,
      );
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, Place>> getPlaceById(String placeId) async {
    try {
      final place = await remoteDataSource.getPlaceById(placeId);
      return Right(place);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, void>> toggleLike(String placeId) async {
    try {
      await remoteDataSource.toggleLike(placeId);
      return const Right(null);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, void>> toggleSave(String placeId) async {
    try {
      await remoteDataSource.toggleSave(placeId);
      return const Right(null);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, List<Place>>> getSimilarPlaces({
    required String placeId,
    int limit = 6,
  }) async {
    try {
      final places = await remoteDataSource.getSimilarPlaces(
        placeId: placeId,
        limit: limit,
      );
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }
}

/// Place Repository Provider
final placeRepositoryProvider = Provider<PlaceRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  final remoteDataSource = PlaceRemoteDataSource(dioClient);
  return PlaceRepositoryImpl(remoteDataSource);
});
