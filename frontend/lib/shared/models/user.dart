import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const User._(); // For custom methods

  const factory User({
    required String id,
    required String name,
    required String email,
    String? profileImageUrl,
    String? phoneNumber,

    // Supabase Auth fields
    @Default(false) bool emailConfirmed,
    String? provider, // 'email', 'google', 'apple'
    @JsonKey(includeFromJson: false, includeToJson: false)
    Map<String, dynamic>? metadata,
    DateTime? lastSignInAt,

    // App statistics
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

  /// Convert Supabase User to App User
  factory User.fromSupabase(supabase.User supabaseUser) {
    return User(
      id: supabaseUser.id,
      email: supabaseUser.email ?? '',
      name: supabaseUser.userMetadata?['name'] ??
            supabaseUser.email?.split('@').first ?? 'User',
      profileImageUrl: supabaseUser.userMetadata?['avatar_url'],
      phoneNumber: supabaseUser.phone,
      emailConfirmed: supabaseUser.emailConfirmedAt != null,
      provider: supabaseUser.appMetadata['provider'],
      metadata: supabaseUser.userMetadata,
      lastSignInAt: supabaseUser.lastSignInAt,
      createdAt: supabaseUser.createdAt,
    );
  }
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
