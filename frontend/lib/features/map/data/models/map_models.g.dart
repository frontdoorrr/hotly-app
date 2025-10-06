// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'map_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AddressSearchResultModelImpl _$$AddressSearchResultModelImplFromJson(
        Map<String, dynamic> json) =>
    _$AddressSearchResultModelImpl(
      address: json['address'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      roadAddress: json['road_address'] as String?,
      jibunAddress: json['jibun_address'] as String?,
      buildingName: json['building_name'] as String?,
    );

Map<String, dynamic> _$$AddressSearchResultModelImplToJson(
        _$AddressSearchResultModelImpl instance) =>
    <String, dynamic>{
      'address': instance.address,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'road_address': instance.roadAddress,
      'jibun_address': instance.jibunAddress,
      'building_name': instance.buildingName,
    };

_$ReverseGeocodeResultModelImpl _$$ReverseGeocodeResultModelImplFromJson(
        Map<String, dynamic> json) =>
    _$ReverseGeocodeResultModelImpl(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      roadAddress: json['road_address'] as String?,
      jibunAddress: json['jibun_address'] as String?,
      region1depth: json['region_1depth'] as String?,
      region2depth: json['region_2depth'] as String?,
      region3depth: json['region_3depth'] as String?,
    );

Map<String, dynamic> _$$ReverseGeocodeResultModelImplToJson(
        _$ReverseGeocodeResultModelImpl instance) =>
    <String, dynamic>{
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'road_address': instance.roadAddress,
      'jibun_address': instance.jibunAddress,
      'region_1depth': instance.region1depth,
      'region_2depth': instance.region2depth,
      'region_3depth': instance.region3depth,
    };

_$PlaceSearchResultModelImpl _$$PlaceSearchResultModelImplFromJson(
        Map<String, dynamic> json) =>
    _$PlaceSearchResultModelImpl(
      placeId: json['place_id'] as String,
      placeName: json['place_name'] as String,
      address: json['address'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      categoryName: json['category_name'] as String?,
      roadAddress: json['road_address'] as String?,
      phone: json['phone'] as String?,
      placeUrl: json['place_url'] as String?,
      distance: (json['distance'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$$PlaceSearchResultModelImplToJson(
        _$PlaceSearchResultModelImpl instance) =>
    <String, dynamic>{
      'place_id': instance.placeId,
      'place_name': instance.placeName,
      'address': instance.address,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'category_name': instance.categoryName,
      'road_address': instance.roadAddress,
      'phone': instance.phone,
      'place_url': instance.placeUrl,
      'distance': instance.distance,
    };
