import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/map_entities.dart';

part 'map_models.freezed.dart';
part 'map_models.g.dart';

/// Address search result model from API
@freezed
class AddressSearchResultModel with _$AddressSearchResultModel {
  const factory AddressSearchResultModel({
    required String address,
    required double latitude,
    required double longitude,
    @JsonKey(name: 'road_address') String? roadAddress,
    @JsonKey(name: 'jibun_address') String? jibunAddress,
    @JsonKey(name: 'building_name') String? buildingName,
  }) = _AddressSearchResultModel;

  factory AddressSearchResultModel.fromJson(Map<String, dynamic> json) =>
      _$AddressSearchResultModelFromJson(json);
}

/// Reverse geocode result model from API
@freezed
class ReverseGeocodeResultModel with _$ReverseGeocodeResultModel {
  const factory ReverseGeocodeResultModel({
    required double latitude,
    required double longitude,
    @JsonKey(name: 'road_address') String? roadAddress,
    @JsonKey(name: 'jibun_address') String? jibunAddress,
    @JsonKey(name: 'region_1depth') String? region1depth,
    @JsonKey(name: 'region_2depth') String? region2depth,
    @JsonKey(name: 'region_3depth') String? region3depth,
  }) = _ReverseGeocodeResultModel;

  factory ReverseGeocodeResultModel.fromJson(Map<String, dynamic> json) =>
      _$ReverseGeocodeResultModelFromJson(json);
}

/// Place search result model from API
@freezed
class PlaceSearchResultModel with _$PlaceSearchResultModel {
  const factory PlaceSearchResultModel({
    @JsonKey(name: 'place_id') required String placeId,
    @JsonKey(name: 'place_name') required String placeName,
    required String address,
    required double latitude,
    required double longitude,
    @JsonKey(name: 'category_name') String? categoryName,
    @JsonKey(name: 'road_address') String? roadAddress,
    String? phone,
    @JsonKey(name: 'place_url') String? placeUrl,
    double? distance,
  }) = _PlaceSearchResultModel;

  factory PlaceSearchResultModel.fromJson(Map<String, dynamic> json) =>
      _$PlaceSearchResultModelFromJson(json);
}

/// Extensions to convert models to entities
extension AddressSearchResultModelX on AddressSearchResultModel {
  AddressSearchResult toEntity() {
    return AddressSearchResult(
      address: address,
      latitude: latitude,
      longitude: longitude,
      roadAddress: roadAddress,
      jibunAddress: jibunAddress,
      buildingName: buildingName,
    );
  }
}

extension ReverseGeocodeResultModelX on ReverseGeocodeResultModel {
  ReverseGeocodeResult toEntity() {
    return ReverseGeocodeResult(
      latitude: latitude,
      longitude: longitude,
      roadAddress: roadAddress,
      jibunAddress: jibunAddress,
      region1depth: region1depth,
      region2depth: region2depth,
      region3depth: region3depth,
    );
  }
}

extension PlaceSearchResultModelX on PlaceSearchResultModel {
  PlaceSearchResult toEntity() {
    return PlaceSearchResult(
      placeId: placeId,
      placeName: placeName,
      address: address,
      latitude: latitude,
      longitude: longitude,
      categoryName: categoryName,
      roadAddress: roadAddress,
      phone: phone,
      placeUrl: placeUrl,
      distance: distance,
    );
  }
}
