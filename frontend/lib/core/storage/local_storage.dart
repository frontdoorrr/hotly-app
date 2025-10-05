import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Local Storage Provider
final localStorageProvider = Provider<LocalStorage>((ref) {
  return LocalStorage.instance;
});

/// Local Storage Service
class LocalStorage {
  static final LocalStorage _instance = LocalStorage._internal();
  static LocalStorage get instance => _instance;

  late final SharedPreferences _prefs;
  late final FlutterSecureStorage _secureStorage;

  LocalStorage._internal() {
    _secureStorage = const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
      ),
    );
  }

  /// 초기화 (main.dart에서 호출)
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // ========== Secure Storage (토큰 등) ==========

  /// 토큰 저장
  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: _Keys.authToken, value: token);
  }

  /// 토큰 조회
  Future<String?> getToken() async {
    return await _secureStorage.read(key: _Keys.authToken);
  }

  /// 토큰 삭제
  Future<void> deleteToken() async {
    await _secureStorage.delete(key: _Keys.authToken);
  }

  /// Refresh 토큰 저장
  Future<void> saveRefreshToken(String token) async {
    await _secureStorage.write(key: _Keys.refreshToken, value: token);
  }

  /// Refresh 토큰 조회
  Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: _Keys.refreshToken);
  }

  // ========== SharedPreferences (일반 데이터) ==========

  /// 온보딩 완료 여부
  Future<void> setOnboardingCompleted(bool completed) async {
    await _prefs.setBool(_Keys.onboardingCompleted, completed);
  }

  bool get isOnboardingCompleted {
    return _prefs.getBool(_Keys.onboardingCompleted) ?? false;
  }

  /// 테마 모드
  Future<void> setThemeMode(String mode) async {
    await _prefs.setString(_Keys.themeMode, mode);
  }

  String? get themeMode {
    return _prefs.getString(_Keys.themeMode);
  }

  /// 언어 설정
  Future<void> setLanguage(String language) async {
    await _prefs.setString(_Keys.language, language);
  }

  String get language {
    return _prefs.getString(_Keys.language) ?? 'ko';
  }

  /// 알림 설정
  Future<void> setNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(_Keys.notificationsEnabled, enabled);
  }

  bool get notificationsEnabled {
    return _prefs.getBool(_Keys.notificationsEnabled) ?? true;
  }

  /// FCM 토큰
  Future<void> saveFcmToken(String token) async {
    await _prefs.setString(_Keys.fcmToken, token);
  }

  String? get fcmToken {
    return _prefs.getString(_Keys.fcmToken);
  }

  /// 검색 히스토리
  Future<void> saveSearchHistory(List<String> history) async {
    await _prefs.setStringList(_Keys.searchHistory, history);
  }

  List<String> get searchHistory {
    return _prefs.getStringList(_Keys.searchHistory) ?? [];
  }

  /// 검색 히스토리 추가
  Future<void> addSearchHistory(String query) async {
    final history = searchHistory;

    // 중복 제거
    history.remove(query);

    // 맨 앞에 추가
    history.insert(0, query);

    // 최대 20개까지만 저장
    if (history.length > 20) {
      history.removeRange(20, history.length);
    }

    await saveSearchHistory(history);
  }

  /// 검색 히스토리 삭제
  Future<void> clearSearchHistory() async {
    await _prefs.remove(_Keys.searchHistory);
  }

  /// 마지막 위치
  Future<void> saveLastLocation(double lat, double lng) async {
    await _prefs.setDouble(_Keys.lastLat, lat);
    await _prefs.setDouble(_Keys.lastLng, lng);
  }

  (double?, double?) get lastLocation {
    final lat = _prefs.getDouble(_Keys.lastLat);
    final lng = _prefs.getDouble(_Keys.lastLng);
    return (lat, lng);
  }

  /// 모든 데이터 삭제 (로그아웃 시)
  Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    await _prefs.clear();
  }
}

/// Storage Keys
class _Keys {
  static const String authToken = 'auth_token';
  static const String refreshToken = 'refresh_token';
  static const String onboardingCompleted = 'onboarding_completed';
  static const String themeMode = 'theme_mode';
  static const String language = 'language';
  static const String notificationsEnabled = 'notifications_enabled';
  static const String fcmToken = 'fcm_token';
  static const String searchHistory = 'search_history';
  static const String lastLat = 'last_lat';
  static const String lastLng = 'last_lng';
}
