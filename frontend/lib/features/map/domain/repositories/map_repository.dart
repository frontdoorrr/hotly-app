import 'package:dartz/dartz.dart';
import '../entities/map_entities.dart';

/// Repository interface for Map operations
abstract class MapRepository {
  /// Convert address to coordinates (geocoding)
  Future<Either<Exception, AddressSearchResult>> geocodeAddress(String address);

  /// Convert coordinates to address (reverse geocoding)
  Future<Either<Exception, ReverseGeocodeResult>> reverseGeocode({
    required double latitude,
    required double longitude,
  });

  /// Search places by keyword with optional location bias
  Future<Either<Exception, List<PlaceSearchResult>>> searchPlaces({
    required String query,
    double? latitude,
    double? longitude,
    double? radiusKm,
    int limit = 15,
  });

  /// Get user's saved places within map bounds
  Future<Either<Exception, List<Map<String, dynamic>>>> getPlacesInBounds({
    required double swLat,
    required double swLng,
    required double neLat,
    required double neLng,
    String? category,
    int limit = 100,
  });
}
