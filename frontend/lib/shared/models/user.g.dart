// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$UserImpl _$$UserImplFromJson(Map<String, dynamic> json) => _$UserImpl(
      id: json['id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      profileImageUrl: json['profileImageUrl'] as String?,
      phoneNumber: json['phoneNumber'] as String?,
      emailConfirmed: json['emailConfirmed'] as bool? ?? false,
      provider: json['provider'] as String?,
      lastSignInAt: json['lastSignInAt'] == null
          ? null
          : DateTime.parse(json['lastSignInAt'] as String),
      savedPlacesCount: (json['savedPlacesCount'] as num?)?.toInt() ?? 0,
      likedPlacesCount: (json['likedPlacesCount'] as num?)?.toInt() ?? 0,
      coursesCount: (json['coursesCount'] as num?)?.toInt() ?? 0,
      createdAt: json['createdAt'] == null
          ? null
          : DateTime.parse(json['createdAt'] as String),
    );

Map<String, dynamic> _$$UserImplToJson(_$UserImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'email': instance.email,
      'profileImageUrl': instance.profileImageUrl,
      'phoneNumber': instance.phoneNumber,
      'emailConfirmed': instance.emailConfirmed,
      'provider': instance.provider,
      'lastSignInAt': instance.lastSignInAt?.toIso8601String(),
      'savedPlacesCount': instance.savedPlacesCount,
      'likedPlacesCount': instance.likedPlacesCount,
      'coursesCount': instance.coursesCount,
      'createdAt': instance.createdAt?.toIso8601String(),
    };

_$UserStatsImpl _$$UserStatsImplFromJson(Map<String, dynamic> json) =>
    _$UserStatsImpl(
      savedPlaces: (json['savedPlaces'] as num?)?.toInt() ?? 0,
      likedPlaces: (json['likedPlaces'] as num?)?.toInt() ?? 0,
      courses: (json['courses'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$UserStatsImplToJson(_$UserStatsImpl instance) =>
    <String, dynamic>{
      'savedPlaces': instance.savedPlaces,
      'likedPlaces': instance.likedPlaces,
      'courses': instance.courses,
    };
