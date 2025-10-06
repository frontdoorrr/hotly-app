import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
    String? profileImageUrl,
    String? phoneNumber,
    @Default(0) int savedPlacesCount,
    @Default(0) int likedPlacesCount,
    @Default(0) int coursesCount,
    DateTime? createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);

  factory User.initial() => const User(
        id: '',
        name: 'Guest',
        email: 'guest@example.com',
      );
}

@freezed
class UserStats with _$UserStats {
  const factory UserStats({
    @Default(0) int savedPlaces,
    @Default(0) int likedPlaces,
    @Default(0) int courses,
  }) = _UserStats;

  factory UserStats.fromJson(Map<String, dynamic> json) =>
      _$UserStatsFromJson(json);
}
