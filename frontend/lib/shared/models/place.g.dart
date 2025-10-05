// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'place.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$PlaceImpl _$$PlaceImplFromJson(Map<String, dynamic> json) => _$PlaceImpl(
      id: json['id'] as String,
      name: json['name'] as String,
      address: json['address'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      description: json['description'] as String?,
      category: json['category'] as String?,
      imageUrl: json['imageUrl'] as String?,
      tags:
          (json['tags'] as List<dynamic>?)?.map((e) => e as String).toList() ??
              const [],
      rating: (json['rating'] as num?)?.toDouble() ?? 0.0,
      reviewCount: (json['reviewCount'] as num?)?.toInt() ?? 0,
      isLiked: json['isLiked'] as bool? ?? false,
      isSaved: json['isSaved'] as bool? ?? false,
    );

Map<String, dynamic> _$$PlaceImplToJson(_$PlaceImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'address': instance.address,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'description': instance.description,
      'category': instance.category,
      'imageUrl': instance.imageUrl,
      'tags': instance.tags,
      'rating': instance.rating,
      'reviewCount': instance.reviewCount,
      'isLiked': instance.isLiked,
      'isSaved': instance.isSaved,
    };

_$CoursePlaceImpl _$$CoursePlaceImplFromJson(Map<String, dynamic> json) =>
    _$CoursePlaceImpl(
      id: json['id'] as String,
      place: Place.fromJson(json['place'] as Map<String, dynamic>),
      order: (json['order'] as num).toInt(),
      startTime: DateTime.parse(json['startTime'] as String),
      duration: Duration(microseconds: (json['duration'] as num).toInt()),
    );

Map<String, dynamic> _$$CoursePlaceImplToJson(_$CoursePlaceImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'place': instance.place,
      'order': instance.order,
      'startTime': instance.startTime.toIso8601String(),
      'duration': instance.duration.inMicroseconds,
    };
