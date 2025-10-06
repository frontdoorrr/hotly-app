import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';

/// Search Repository Interface
abstract class SearchRepository {
  /// 장소 검색
  Future<Either<ApiException, List<Place>>> searchPlaces({
    required String query,
    String? category,
    double? maxDistance,
    double? minRating,
    int limit = 20,
    int offset = 0,
  });

  /// 자동완성 제안
  Future<Either<ApiException, List<String>>> getAutocompleteSuggestions({
    required String query,
    int limit = 5,
  });

  /// 검색 히스토리 저장
  Future<void> saveSearchHistory(String query);

  /// 검색 히스토리 조회
  Future<List<String>> getSearchHistory();

  /// 검색 히스토리 삭제
  Future<void> clearSearchHistory();
}
