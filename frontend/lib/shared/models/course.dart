import 'package:freezed_annotation/freezed_annotation.dart';
import 'place.dart';

part 'course.freezed.dart';
part 'course.g.dart';

enum CourseType {
  @JsonValue('date')
  date,
  @JsonValue('travel')
  travel,
  @JsonValue('food_tour')
  foodTour,
  @JsonValue('other')
  other,
}

@freezed
class Course with _$Course {
  const factory Course({
    required String id,
    required String title,
    required CourseType type,
    required List<CoursePlace> places,
    String? description,
    String? thumbnailUrl,
    @Default(Duration.zero) Duration totalDuration,
    @Default(0) int likeCount,
    @Default(0) int shareCount,
    @Default(false) bool isPublic,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) = _Course;

  factory Course.fromJson(Map<String, dynamic> json) => _$CourseFromJson(json);
}
