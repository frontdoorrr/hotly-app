import 'package:share_plus/share_plus.dart';
import 'package:logger/logger.dart';

/// Service for sharing content (places, courses)
class ShareService {
  static final Logger _logger = Logger();

  /// Share place details
  static Future<void> sharePlace({
    required String placeId,
    required String placeName,
    String? address,
    String? imageUrl,
  }) async {
    try {
      final deepLink = _generateDeepLink('place', placeId);
      final message = _buildPlaceMessage(placeName, address, deepLink);

      await Share.share(
        message,
        subject: '핫플레이스 추천: $placeName',
      );

      _logger.i('Shared place: $placeId');
    } catch (e) {
      _logger.e('Failed to share place: $e');
    }
  }

  /// Share course details
  static Future<void> shareCourse({
    required String courseId,
    required String courseName,
    int? placeCount,
    String? duration,
  }) async {
    try {
      final deepLink = _generateDeepLink('course', courseId);
      final message = _buildCourseMessage(courseName, placeCount, duration, deepLink);

      await Share.share(
        message,
        subject: '데이트 코스 추천: $courseName',
      );

      _logger.i('Shared course: $courseId');
    } catch (e) {
      _logger.e('Failed to share course: $e');
    }
  }

  /// Share with image file
  static Future<void> shareWithImage({
    required String text,
    required String imagePath,
  }) async {
    try {
      await Share.shareXFiles(
        [XFile(imagePath)],
        text: text,
      );

      _logger.i('Shared with image: $imagePath');
    } catch (e) {
      _logger.e('Failed to share with image: $e');
    }
  }

  /// Generate deep link URL
  static String _generateDeepLink(String type, String id) {
    // TODO: Replace with actual domain
    const domain = 'hotly.app';
    return 'https://$domain/$type/$id';
  }

  /// Build place share message
  static String _buildPlaceMessage(
    String placeName,
    String? address,
    String deepLink,
  ) {
    final buffer = StringBuffer();
    buffer.writeln('🔥 핫플레이스 추천');
    buffer.writeln();
    buffer.writeln('📍 $placeName');
    if (address != null) {
      buffer.writeln('🏠 $address');
    }
    buffer.writeln();
    buffer.writeln('앱에서 자세히 보기:');
    buffer.writeln(deepLink);
    buffer.writeln();
    buffer.writeln('#핫플레이스 #데이트코스 #Hotly');

    return buffer.toString();
  }

  /// Build course share message
  static String _buildCourseMessage(
    String courseName,
    int? placeCount,
    String? duration,
    String deepLink,
  ) {
    final buffer = StringBuffer();
    buffer.writeln('🗺️ 데이트 코스 추천');
    buffer.writeln();
    buffer.writeln('📝 $courseName');
    if (placeCount != null) {
      buffer.writeln('📍 총 $placeCount개 장소');
    }
    if (duration != null) {
      buffer.writeln('⏱️ 소요시간: $duration');
    }
    buffer.writeln();
    buffer.writeln('앱에서 자세히 보기:');
    buffer.writeln(deepLink);
    buffer.writeln();
    buffer.writeln('#데이트코스 #핫플레이스 #Hotly');

    return buffer.toString();
  }
}
