// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'user.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

User _$UserFromJson(Map<String, dynamic> json) {
  return _User.fromJson(json);
}

/// @nodoc
mixin _$User {
  String get id => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get email => throw _privateConstructorUsedError;
  String? get profileImageUrl => throw _privateConstructorUsedError;
  String? get phoneNumber =>
      throw _privateConstructorUsedError; // Supabase Auth fields
  bool get emailConfirmed => throw _privateConstructorUsedError;
  String? get provider =>
      throw _privateConstructorUsedError; // 'email', 'google', 'apple'
  @JsonKey(includeFromJson: false, includeToJson: false)
  Map<String, dynamic>? get metadata => throw _privateConstructorUsedError;
  DateTime? get lastSignInAt =>
      throw _privateConstructorUsedError; // App statistics
  int get savedPlacesCount => throw _privateConstructorUsedError;
  int get likedPlacesCount => throw _privateConstructorUsedError;
  int get coursesCount => throw _privateConstructorUsedError;
  DateTime? get createdAt => throw _privateConstructorUsedError;

  /// Serializes this User to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of User
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UserCopyWith<User> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UserCopyWith<$Res> {
  factory $UserCopyWith(User value, $Res Function(User) then) =
      _$UserCopyWithImpl<$Res, User>;
  @useResult
  $Res call(
      {String id,
      String name,
      String email,
      String? profileImageUrl,
      String? phoneNumber,
      bool emailConfirmed,
      String? provider,
      @JsonKey(includeFromJson: false, includeToJson: false)
      Map<String, dynamic>? metadata,
      DateTime? lastSignInAt,
      int savedPlacesCount,
      int likedPlacesCount,
      int coursesCount,
      DateTime? createdAt});
}

/// @nodoc
class _$UserCopyWithImpl<$Res, $Val extends User>
    implements $UserCopyWith<$Res> {
  _$UserCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of User
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? email = null,
    Object? profileImageUrl = freezed,
    Object? phoneNumber = freezed,
    Object? emailConfirmed = null,
    Object? provider = freezed,
    Object? metadata = freezed,
    Object? lastSignInAt = freezed,
    Object? savedPlacesCount = null,
    Object? likedPlacesCount = null,
    Object? coursesCount = null,
    Object? createdAt = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      profileImageUrl: freezed == profileImageUrl
          ? _value.profileImageUrl
          : profileImageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      phoneNumber: freezed == phoneNumber
          ? _value.phoneNumber
          : phoneNumber // ignore: cast_nullable_to_non_nullable
              as String?,
      emailConfirmed: null == emailConfirmed
          ? _value.emailConfirmed
          : emailConfirmed // ignore: cast_nullable_to_non_nullable
              as bool,
      provider: freezed == provider
          ? _value.provider
          : provider // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      lastSignInAt: freezed == lastSignInAt
          ? _value.lastSignInAt
          : lastSignInAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      savedPlacesCount: null == savedPlacesCount
          ? _value.savedPlacesCount
          : savedPlacesCount // ignore: cast_nullable_to_non_nullable
              as int,
      likedPlacesCount: null == likedPlacesCount
          ? _value.likedPlacesCount
          : likedPlacesCount // ignore: cast_nullable_to_non_nullable
              as int,
      coursesCount: null == coursesCount
          ? _value.coursesCount
          : coursesCount // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UserImplCopyWith<$Res> implements $UserCopyWith<$Res> {
  factory _$$UserImplCopyWith(
          _$UserImpl value, $Res Function(_$UserImpl) then) =
      __$$UserImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String name,
      String email,
      String? profileImageUrl,
      String? phoneNumber,
      bool emailConfirmed,
      String? provider,
      @JsonKey(includeFromJson: false, includeToJson: false)
      Map<String, dynamic>? metadata,
      DateTime? lastSignInAt,
      int savedPlacesCount,
      int likedPlacesCount,
      int coursesCount,
      DateTime? createdAt});
}

/// @nodoc
class __$$UserImplCopyWithImpl<$Res>
    extends _$UserCopyWithImpl<$Res, _$UserImpl>
    implements _$$UserImplCopyWith<$Res> {
  __$$UserImplCopyWithImpl(_$UserImpl _value, $Res Function(_$UserImpl) _then)
      : super(_value, _then);

  /// Create a copy of User
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? email = null,
    Object? profileImageUrl = freezed,
    Object? phoneNumber = freezed,
    Object? emailConfirmed = null,
    Object? provider = freezed,
    Object? metadata = freezed,
    Object? lastSignInAt = freezed,
    Object? savedPlacesCount = null,
    Object? likedPlacesCount = null,
    Object? coursesCount = null,
    Object? createdAt = freezed,
  }) {
    return _then(_$UserImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      profileImageUrl: freezed == profileImageUrl
          ? _value.profileImageUrl
          : profileImageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      phoneNumber: freezed == phoneNumber
          ? _value.phoneNumber
          : phoneNumber // ignore: cast_nullable_to_non_nullable
              as String?,
      emailConfirmed: null == emailConfirmed
          ? _value.emailConfirmed
          : emailConfirmed // ignore: cast_nullable_to_non_nullable
              as bool,
      provider: freezed == provider
          ? _value.provider
          : provider // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: freezed == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      lastSignInAt: freezed == lastSignInAt
          ? _value.lastSignInAt
          : lastSignInAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      savedPlacesCount: null == savedPlacesCount
          ? _value.savedPlacesCount
          : savedPlacesCount // ignore: cast_nullable_to_non_nullable
              as int,
      likedPlacesCount: null == likedPlacesCount
          ? _value.likedPlacesCount
          : likedPlacesCount // ignore: cast_nullable_to_non_nullable
              as int,
      coursesCount: null == coursesCount
          ? _value.coursesCount
          : coursesCount // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UserImpl extends _User {
  const _$UserImpl(
      {required this.id,
      required this.name,
      required this.email,
      this.profileImageUrl,
      this.phoneNumber,
      this.emailConfirmed = false,
      this.provider,
      @JsonKey(includeFromJson: false, includeToJson: false)
      final Map<String, dynamic>? metadata,
      this.lastSignInAt,
      this.savedPlacesCount = 0,
      this.likedPlacesCount = 0,
      this.coursesCount = 0,
      this.createdAt})
      : _metadata = metadata,
        super._();

  factory _$UserImpl.fromJson(Map<String, dynamic> json) =>
      _$$UserImplFromJson(json);

  @override
  final String id;
  @override
  final String name;
  @override
  final String email;
  @override
  final String? profileImageUrl;
  @override
  final String? phoneNumber;
// Supabase Auth fields
  @override
  @JsonKey()
  final bool emailConfirmed;
  @override
  final String? provider;
// 'email', 'google', 'apple'
  final Map<String, dynamic>? _metadata;
// 'email', 'google', 'apple'
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  Map<String, dynamic>? get metadata {
    final value = _metadata;
    if (value == null) return null;
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  final DateTime? lastSignInAt;
// App statistics
  @override
  @JsonKey()
  final int savedPlacesCount;
  @override
  @JsonKey()
  final int likedPlacesCount;
  @override
  @JsonKey()
  final int coursesCount;
  @override
  final DateTime? createdAt;

  @override
  String toString() {
    return 'User(id: $id, name: $name, email: $email, profileImageUrl: $profileImageUrl, phoneNumber: $phoneNumber, emailConfirmed: $emailConfirmed, provider: $provider, metadata: $metadata, lastSignInAt: $lastSignInAt, savedPlacesCount: $savedPlacesCount, likedPlacesCount: $likedPlacesCount, coursesCount: $coursesCount, createdAt: $createdAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UserImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.profileImageUrl, profileImageUrl) ||
                other.profileImageUrl == profileImageUrl) &&
            (identical(other.phoneNumber, phoneNumber) ||
                other.phoneNumber == phoneNumber) &&
            (identical(other.emailConfirmed, emailConfirmed) ||
                other.emailConfirmed == emailConfirmed) &&
            (identical(other.provider, provider) ||
                other.provider == provider) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata) &&
            (identical(other.lastSignInAt, lastSignInAt) ||
                other.lastSignInAt == lastSignInAt) &&
            (identical(other.savedPlacesCount, savedPlacesCount) ||
                other.savedPlacesCount == savedPlacesCount) &&
            (identical(other.likedPlacesCount, likedPlacesCount) ||
                other.likedPlacesCount == likedPlacesCount) &&
            (identical(other.coursesCount, coursesCount) ||
                other.coursesCount == coursesCount) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      name,
      email,
      profileImageUrl,
      phoneNumber,
      emailConfirmed,
      provider,
      const DeepCollectionEquality().hash(_metadata),
      lastSignInAt,
      savedPlacesCount,
      likedPlacesCount,
      coursesCount,
      createdAt);

  /// Create a copy of User
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UserImplCopyWith<_$UserImpl> get copyWith =>
      __$$UserImplCopyWithImpl<_$UserImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UserImplToJson(
      this,
    );
  }
}

abstract class _User extends User {
  const factory _User(
      {required final String id,
      required final String name,
      required final String email,
      final String? profileImageUrl,
      final String? phoneNumber,
      final bool emailConfirmed,
      final String? provider,
      @JsonKey(includeFromJson: false, includeToJson: false)
      final Map<String, dynamic>? metadata,
      final DateTime? lastSignInAt,
      final int savedPlacesCount,
      final int likedPlacesCount,
      final int coursesCount,
      final DateTime? createdAt}) = _$UserImpl;
  const _User._() : super._();

  factory _User.fromJson(Map<String, dynamic> json) = _$UserImpl.fromJson;

  @override
  String get id;
  @override
  String get name;
  @override
  String get email;
  @override
  String? get profileImageUrl;
  @override
  String? get phoneNumber; // Supabase Auth fields
  @override
  bool get emailConfirmed;
  @override
  String? get provider; // 'email', 'google', 'apple'
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  Map<String, dynamic>? get metadata;
  @override
  DateTime? get lastSignInAt; // App statistics
  @override
  int get savedPlacesCount;
  @override
  int get likedPlacesCount;
  @override
  int get coursesCount;
  @override
  DateTime? get createdAt;

  /// Create a copy of User
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UserImplCopyWith<_$UserImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UserStats _$UserStatsFromJson(Map<String, dynamic> json) {
  return _UserStats.fromJson(json);
}

/// @nodoc
mixin _$UserStats {
  int get savedPlaces => throw _privateConstructorUsedError;
  int get likedPlaces => throw _privateConstructorUsedError;
  int get courses => throw _privateConstructorUsedError;

  /// Serializes this UserStats to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UserStats
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UserStatsCopyWith<UserStats> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UserStatsCopyWith<$Res> {
  factory $UserStatsCopyWith(UserStats value, $Res Function(UserStats) then) =
      _$UserStatsCopyWithImpl<$Res, UserStats>;
  @useResult
  $Res call({int savedPlaces, int likedPlaces, int courses});
}

/// @nodoc
class _$UserStatsCopyWithImpl<$Res, $Val extends UserStats>
    implements $UserStatsCopyWith<$Res> {
  _$UserStatsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UserStats
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? savedPlaces = null,
    Object? likedPlaces = null,
    Object? courses = null,
  }) {
    return _then(_value.copyWith(
      savedPlaces: null == savedPlaces
          ? _value.savedPlaces
          : savedPlaces // ignore: cast_nullable_to_non_nullable
              as int,
      likedPlaces: null == likedPlaces
          ? _value.likedPlaces
          : likedPlaces // ignore: cast_nullable_to_non_nullable
              as int,
      courses: null == courses
          ? _value.courses
          : courses // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UserStatsImplCopyWith<$Res>
    implements $UserStatsCopyWith<$Res> {
  factory _$$UserStatsImplCopyWith(
          _$UserStatsImpl value, $Res Function(_$UserStatsImpl) then) =
      __$$UserStatsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int savedPlaces, int likedPlaces, int courses});
}

/// @nodoc
class __$$UserStatsImplCopyWithImpl<$Res>
    extends _$UserStatsCopyWithImpl<$Res, _$UserStatsImpl>
    implements _$$UserStatsImplCopyWith<$Res> {
  __$$UserStatsImplCopyWithImpl(
      _$UserStatsImpl _value, $Res Function(_$UserStatsImpl) _then)
      : super(_value, _then);

  /// Create a copy of UserStats
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? savedPlaces = null,
    Object? likedPlaces = null,
    Object? courses = null,
  }) {
    return _then(_$UserStatsImpl(
      savedPlaces: null == savedPlaces
          ? _value.savedPlaces
          : savedPlaces // ignore: cast_nullable_to_non_nullable
              as int,
      likedPlaces: null == likedPlaces
          ? _value.likedPlaces
          : likedPlaces // ignore: cast_nullable_to_non_nullable
              as int,
      courses: null == courses
          ? _value.courses
          : courses // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UserStatsImpl implements _UserStats {
  const _$UserStatsImpl(
      {this.savedPlaces = 0, this.likedPlaces = 0, this.courses = 0});

  factory _$UserStatsImpl.fromJson(Map<String, dynamic> json) =>
      _$$UserStatsImplFromJson(json);

  @override
  @JsonKey()
  final int savedPlaces;
  @override
  @JsonKey()
  final int likedPlaces;
  @override
  @JsonKey()
  final int courses;

  @override
  String toString() {
    return 'UserStats(savedPlaces: $savedPlaces, likedPlaces: $likedPlaces, courses: $courses)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UserStatsImpl &&
            (identical(other.savedPlaces, savedPlaces) ||
                other.savedPlaces == savedPlaces) &&
            (identical(other.likedPlaces, likedPlaces) ||
                other.likedPlaces == likedPlaces) &&
            (identical(other.courses, courses) || other.courses == courses));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, savedPlaces, likedPlaces, courses);

  /// Create a copy of UserStats
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UserStatsImplCopyWith<_$UserStatsImpl> get copyWith =>
      __$$UserStatsImplCopyWithImpl<_$UserStatsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UserStatsImplToJson(
      this,
    );
  }
}

abstract class _UserStats implements UserStats {
  const factory _UserStats(
      {final int savedPlaces,
      final int likedPlaces,
      final int courses}) = _$UserStatsImpl;

  factory _UserStats.fromJson(Map<String, dynamic> json) =
      _$UserStatsImpl.fromJson;

  @override
  int get savedPlaces;
  @override
  int get likedPlaces;
  @override
  int get courses;

  /// Create a copy of UserStats
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UserStatsImplCopyWith<_$UserStatsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
