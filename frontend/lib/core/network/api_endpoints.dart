/// API Endpoints
/// Base URL은 환경변수에서 가져옴
class ApiEndpoints {
  ApiEndpoints._();

  // Base
  static String get baseUrl => const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://localhost:8000/api/v1',
      );

  // Auth
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String socialGoogle = '/auth/social/google';
  static const String socialApple = '/auth/social/apple';
  static const String logout = '/auth/logout';
  static const String me = '/auth/me';

  // Places
  static const String places = '/places';
  static String placeDetail(String id) => '/places/$id';
  static String placeNearby = '/places/nearby';
  static String placeLike(String id) => '/places/$id/like';
  static String placeSave(String id) => '/places/$id/save';
  static String placeShare(String id) => '/places/$id/share';

  // Search
  static const String search = '/search';
  static const String autocomplete = '/autocomplete';
  static const String filters = '/filters';

  // Courses
  static const String courses = '/courses';
  static String courseDetail(String id) => '/courses/$id';
  static String courseShare(String id) => '/courses/$id/share';

  // User Data
  static const String userProfile = '/user-data/profile';
  static const String userStats = '/user-data/stats';
  static const String userFolders = '/user-data/folders';
  static const String userSavedPlaces = '/user-data/saved-places';

  // Personalization
  static const String recommendations = '/personalization/recommendations';

  // Map
  static const String mapRoute = '/map/route';
  static const String mapPlaces = '/map/places';

  // Onboarding
  static const String onboardingInterests = '/onboarding/interests';
  static const String onboardingComplete = '/onboarding/complete';

  // Notifications
  static const String notificationToken = '/notifications/token';
  static const String notifications = '/notifications';

  // Link Analysis
  static const String linkAnalyze = '/link-analysis/analyze';
  static String linkAnalysisStatus(String analysisId) =>
      '/link-analysis/analyses/$analysisId';
}
