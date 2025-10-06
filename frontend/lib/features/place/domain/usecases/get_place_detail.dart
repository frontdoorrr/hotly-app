import 'package:dartz/dartz.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../shared/models/place.dart';
import '../repositories/place_repository.dart';

/// Get Place Detail Use Case
class GetPlaceDetail {
  final PlaceRepository _repository;

  GetPlaceDetail(this._repository);

  Future<Either<ApiException, Place>> call(String placeId) async {
    if (placeId.isEmpty) {
      return Left(
        ApiException(
          message: 'Place ID cannot be empty',
          statusCode: 400,
        ),
      );
    }

    return await _repository.getPlaceById(placeId);
  }
}
