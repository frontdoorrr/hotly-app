import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/storage/local_storage.dart';
import '../../domain/repositories/search_repository.dart';
import '../datasources/search_remote_datasource.dart';

/// Search Repository Implementation
class SearchRepositoryImpl implements SearchRepository {
  final SearchRemoteDataSource remoteDataSource;
  final LocalStorage localStorage;

  SearchRepositoryImpl(this.remoteDataSource, this.localStorage);

  @override
  Future<Either<ApiException, List<Place>>> searchPlaces({
    required String query,
    String? category,
    double? maxDistance,
    double? minRating,
    int limit = 20,
    int offset = 0,
  }) async {
    try {
      final places = await remoteDataSource.searchPlaces(
        query: query,
        category: category,
        maxDistance: maxDistance,
        minRating: minRating,
        limit: limit,
        offset: offset,
      );
      return Right(places);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<Either<ApiException, List<String>>> getAutocompleteSuggestions({
    required String query,
    int limit = 5,
  }) async {
    try {
      final suggestions = await remoteDataSource.getAutocompleteSuggestions(
        query: query,
        limit: limit,
      );
      return Right(suggestions);
    } on ApiException catch (e) {
      return Left(e);
    }
  }

  @override
  Future<void> saveSearchHistory(String query) async {
    await localStorage.addSearchHistory(query);
  }

  @override
  Future<List<String>> getSearchHistory() async {
    return localStorage.searchHistory;
  }

  @override
  Future<void> clearSearchHistory() async {
    await localStorage.clearSearchHistory();
  }
}

/// Search Repository Provider
final searchRepositoryProvider = Provider<SearchRepository>((ref) {
  final dio = ref.watch(dioProvider);
  final localStorage = ref.watch(localStorageProvider);
  final remoteDataSource = SearchRemoteDataSource(dio);
  return SearchRepositoryImpl(remoteDataSource, localStorage);
});
