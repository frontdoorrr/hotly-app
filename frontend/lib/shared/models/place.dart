import 'package:freezed_annotation/freezed_annotation.dart';

part 'place.freezed.dart';
part 'place.g.dart';

@freezed
class Place with _$Place {
  const factory Place({
    required String id,
    required String name,
    String? address,
    double? latitude,
    double? longitude,
    String? description,
    required String category,
    String? imageUrl,
    @Default([]) List<String> tags,
    @Default(0.0) double rating,
    @Default(0) int reviewCount,
    @Default(false) bool isLiked,
    @Default(false) bool isSaved,
  }) = _Place;

  factory Place.fromJson(Map<String, dynamic> json) => _$PlaceFromJson(json);
}

@freezed
class CoursePlace with _$CoursePlace {
  const factory CoursePlace({
    required String id,
    required Place place,
    required int order,
    required DateTime startTime,
    required Duration duration,
  }) = _CoursePlace;

  factory CoursePlace.fromJson(Map<String, dynamic> json) =>
      _$CoursePlaceFromJson(json);

  factory CoursePlace.fromPlace({
    required Place place,
    required int order,
    required DateTime startTime,
    required Duration duration,
  }) {
    return CoursePlace(
      id: place.id,
      place: place,
      order: order,
      startTime: startTime,
      duration: duration,
    );
  }
}
