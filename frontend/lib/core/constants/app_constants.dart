/// App-wide constants
class AppConstants {
  AppConstants._();

  // API Configuration
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  static const String apiVersion = 'v1';
  static const Duration apiTimeout = Duration(seconds: 30);

  // Cache Configuration
  static const Duration cacheExpiration = Duration(hours: 1);
  static const int maxCacheSize = 100; // MB

  // UI Configuration
  static const double minTouchTarget = 44.0; // WCAG 2.1 AA
  static const int debounceMilliseconds = 300;
  static const int throttleMilliseconds = 500;

  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 50;

  // Map Configuration
  static const double defaultMapZoom = 15.0;
  static const double minMapZoom = 10.0;
  static const double maxMapZoom = 18.0;

  // Image Configuration
  static const int maxImageSizeMB = 5;
  static const int imageCompressionQuality = 85;

  // Animation Durations
  static const Duration shortAnimation = Duration(milliseconds: 200);
  static const Duration mediumAnimation = Duration(milliseconds: 300);
  static const Duration longAnimation = Duration(milliseconds: 500);

  // Storage Keys
  static const String userPrefsKey = 'user_preferences';
  static const String authTokenKey = 'auth_token';
  static const String themeKey = 'theme_mode';
}
