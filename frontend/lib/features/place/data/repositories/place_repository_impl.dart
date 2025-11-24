import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/place.dart';
import '../../../map/domain/entities/map_entities.dart';
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
  Future<Either<ApiException, List<Place>>> getPlacesByBounds({
    required MapBounds bounds,
    int? zoomLevel,
  }) async {
    try {
      AppLogger.d('Fetching places in bounds: '
          'N:${bounds.north.toStringAsFixed(4)}, '
          'S:${bounds.south.toStringAsFixed(4)}, '
          'E:${bounds.east.toStringAsFixed(4)}, '
          'W:${bounds.west.toStringAsFixed(4)}', tag: 'PlaceRepo');

      // TODO: remoteDataSource.getPlacesByBounds() 구현 필요
      final places = await remoteDataSource.getPlaces(page: 1, pageSize: 100);

      // 클라이언트 사이드 필터링 (임시)
      final filteredPlaces = places.where((place) {
        if (place.latitude == null || place.longitude == null) return false;

        final lat = place.latitude!;
        final lng = place.longitude!;

        return lat <= bounds.north &&
            lat >= bounds.south &&
            lng <= bounds.east &&
            lng >= bounds.west;
      }).toList();

      AppLogger.d('Found ${filteredPlaces.length} places in bounds', tag: 'PlaceRepo');
      return Right(filteredPlaces);
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
  Future<Either<ApiException, List<Place>>> getSavedPlaces() async {
    try {
      final places = await remoteDataSource.getSavedPlaces();
      return Right(places);
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
