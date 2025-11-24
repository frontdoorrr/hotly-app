import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';

/// Firebase Crashlytics 서비스
/// 앱 전역 에러 모니터링 및 크래시 리포팅
class CrashlyticsService {
  static final CrashlyticsService _instance = CrashlyticsService._internal();
  static CrashlyticsService get instance => _instance;

  CrashlyticsService._internal();

  /// Crashlytics 초기화
  Future<void> initialize() async {
    // 개발 모드에서는 Crashlytics 비활성화
    if (kDebugMode) {
      await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(false);
      return;
    }

    // 프로덕션 모드에서 활성화
    await FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(true);

    // Flutter 에러 핸들러 설정
    FlutterError.onError = (errorDetails) {
      FirebaseCrashlytics.instance.recordFlutterFatalError(errorDetails);
    };

    // 비동기 에러 핸들러 설정
    PlatformDispatcher.instance.onError = (error, stack) {
      FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
      return true;
    };
  }

  /// 사용자 식별자 설정
  Future<void> setUserId(String userId) async {
    await FirebaseCrashlytics.instance.setUserIdentifier(userId);
  }

  /// 사용자 식별자 초기화
  Future<void> clearUserId() async {
    await FirebaseCrashlytics.instance.setUserIdentifier('');
  }

  /// 커스텀 키 설정
  Future<void> setCustomKey(String key, dynamic value) async {
    await FirebaseCrashlytics.instance.setCustomKey(key, value as Object);
  }

  /// 비치명적 에러 기록
  Future<void> recordError(
    dynamic exception, {
    StackTrace? stackTrace,
    String? reason,
    bool fatal = false,
  }) async {
    if (kDebugMode) return;

    await FirebaseCrashlytics.instance.recordError(
      exception,
      stackTrace ?? StackTrace.current,
      reason: reason,
      fatal: fatal,
    );
  }

  /// 로그 메시지 기록
  Future<void> log(String message) async {
    if (kDebugMode) return;

    await FirebaseCrashlytics.instance.log(message);
  }

  /// 강제 크래시 (테스트용)
  void crash() {
    FirebaseCrashlytics.instance.crash();
  }
}
