import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase;

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

    // Firebase Auth fields
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

  /// Convert Firebase User to App User
  factory User.fromFirebase(firebase.User firebaseUser) {
    // Firebase provider ID 파싱 (google.com, apple.com, password 등)
    String? provider;
    if (firebaseUser.providerData.isNotEmpty) {
      final providerId = firebaseUser.providerData.first.providerId;
      if (providerId == 'google.com') {
        provider = 'google';
      } else if (providerId == 'apple.com') {
        provider = 'apple';
      } else if (providerId == 'password') {
        provider = 'email';
      } else if (providerId.contains('kakao')) {
        provider = 'kakao';
      }
    }

    return User(
      id: firebaseUser.uid,
      email: firebaseUser.email ?? '',
      name: firebaseUser.displayName ??
            firebaseUser.email?.split('@').first ??
            'User',
      profileImageUrl: firebaseUser.photoURL,
      phoneNumber: firebaseUser.phoneNumber,
      emailConfirmed: firebaseUser.emailVerified,
      provider: provider,
      metadata: firebaseUser.metadata != null
          ? {
              'creationTime': firebaseUser.metadata!.creationTime?.toIso8601String(),
              'lastSignInTime': firebaseUser.metadata!.lastSignInTime?.toIso8601String(),
            }
          : null,
      lastSignInAt: firebaseUser.metadata?.lastSignInTime,
      createdAt: firebaseUser.metadata?.creationTime,
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
