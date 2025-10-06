import 'package:dartz/dartz.dart';
import '../../domain/entities/map_entities.dart';
import '../../domain/repositories/map_repository.dart';
import '../datasources/map_remote_datasource.dart';
import '../models/map_models.dart';

/// Implementation of MapRepository
class MapRepositoryImpl implements MapRepository {
  final MapRemoteDataSource _remoteDataSource;

  MapRepositoryImpl(this._remoteDataSource);

  @override
  Future<Either<Exception, AddressSearchResult>> geocodeAddress(
    String address,
  ) async {
    try {
      final result = await _remoteDataSource.geocodeAddress(address);
      return Right(result.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, ReverseGeocodeResult>> reverseGeocode({
    required double latitude,
    required double longitude,
  }) async {
    try {
      final result = await _remoteDataSource.reverseGeocode(
        latitude: latitude,
        longitude: longitude,
      );
      return Right(result.toEntity());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, List<PlaceSearchResult>>> searchPlaces({
    required String query,
    double? latitude,
    double? longitude,
    double? radiusKm,
    int limit = 15,
  }) async {
    try {
      final results = await _remoteDataSource.searchPlaces(
        query: query,
        latitude: latitude,
        longitude: longitude,
        radiusKm: radiusKm,
        limit: limit,
      );
      return Right(results.map((model) => model.toEntity()).toList());
    } on Exception catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<Exception, List<Map<String, dynamic>>>> getPlacesInBounds({
    required double swLat,
    required double swLng,
    required double neLat,
    required double neLng,
    String? category,
    int limit = 100,
  }) async {
    try {
      final results = await _remoteDataSource.getPlacesInBounds(
        swLat: swLat,
        swLng: swLng,
        neLat: neLat,
        neLng: neLng,
        category: category,
        limit: limit,
      );
      return Right(results);
    } on Exception catch (e) {
      return Left(e);
    }
  }
}
