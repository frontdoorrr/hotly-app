import 'package:flutter/foundation.dart';
import '../monitoring/crashlytics_service.dart';

/// 앱 전역 로거
/// 프로덕션 환경에서는 자동으로 로그를 숨김
class AppLogger {
  static const String _tag = 'Hotly';

  /// Debug 레벨 로그 (개발 환경에서만 출력)
  static void d(String message, {String? tag}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] 🔍 $message');
    }
  }

  /// Info 레벨 로그
  static void i(String message, {String? tag}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] ℹ️ $message');
    }
  }

  /// Warning 레벨 로그
  static void w(String message, {String? tag}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] ⚠️ $message');
    }
  }

  /// Error 레벨 로그 (Crashlytics로 전송)
  static void e(String message, {String? tag, Object? error, StackTrace? stackTrace}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] ❌ $message');
      if (error != null) {
        debugPrint('Error: $error');
      }
      if (stackTrace != null) {
        debugPrint('StackTrace: $stackTrace');
      }
    }

    // Crashlytics로 에러 전송
    if (error != null) {
      CrashlyticsService.instance.recordError(
        error,
        stackTrace: stackTrace,
        reason: '[${tag ?? _tag}] $message',
      );
    } else {
      CrashlyticsService.instance.log('[${tag ?? _tag}] $message');
    }
  }

  /// 네트워크 관련 로그
  static void network(String message, {String? tag}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] 🌐 $message');
    }
  }

  /// 인증 관련 로그
  static void auth(String message, {String? tag}) {
    if (kDebugMode) {
      debugPrint('[${tag ?? _tag}] 🔐 $message');
    }
  }
}
