import 'package:dartz/dartz.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../repositories/search_repository.dart';

/// Use Case: 장소 검색
class SearchPlaces {
  final SearchRepository repository;

  SearchPlaces(this.repository);

  Future<Either<ApiException, List<Place>>> call({
    required String query,
    String? category,
    double? maxDistance,
    double? minRating,
    int limit = 20,
    int offset = 0,
  }) async {
    // 빈 검색어는 에러
    if (query.trim().isEmpty) {
      return Left(
        ApiException(
          message: '검색어를 입력해주세요',
          type: ApiExceptionType.badRequest,
        ),
      );
    }

    return await repository.searchPlaces(
      query: query,
      category: category,
      maxDistance: maxDistance,
      minRating: minRating,
      limit: limit,
      offset: offset,
    );
  }
}
