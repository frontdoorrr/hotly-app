import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../../core/storage/local_storage.dart';
import '../../../../core/notifications/fcm_service.dart';

part 'settings_provider.freezed.dart';

enum NotificationToggleResult { granted, denied, permanentlyDenied }

@freezed
class AppSettings with _$AppSettings {
  const factory AppSettings({
    @Default(ThemeMode.system) ThemeMode themeMode,
    @Default(true) bool notificationsEnabled,
    @Default('ko') String language,
  }) = _AppSettings;
}

class SettingsNotifier extends StateNotifier<AppSettings> {
  final LocalStorage _localStorage;

  // 알림 토픽 — FCM 서버 구독 상태의 단일 진실 원천(state.notificationsEnabled)을 따른다.
  static const List<String> _notificationTopics = [
    'all_users',
    'recommendations',
  ];

  SettingsNotifier(this._localStorage) : super(const AppSettings()) {
    _init();
  }

  Future<void> _init() async {
    final themeString = _localStorage.themeMode;
    final language = _localStorage.language;
    state = state.copyWith(
      themeMode: _parseThemeMode(themeString),
      language: language,
    );
    await _reconcile();
  }

  /// OS 권한이 알림 설정의 단일 진실 원천(source of truth).
  /// `state.notificationsEnabled`는 (사용자 opt-in) AND (OS 권한 허용)의 결과.
  /// 드리프트 케이스(시스템 설정에서 권한 회수 등)는 로컬 opt-in과 토픽 구독을 정리.
  Future<void> _reconcile() async {
    final permGranted = (await Permission.notification.status).isGranted;
    final userOptedIn = _localStorage.notificationsEnabled;
    final effective = permGranted && userOptedIn;

    // 드리프트: 사용자는 켜놨지만 OS 권한이 없는 경우 → 정리
    if (userOptedIn && !permGranted) {
      await _localStorage.setNotificationsEnabled(false);
      await _syncTopics(subscribe: false);
    }

    if (state.notificationsEnabled != effective) {
      state = state.copyWith(notificationsEnabled: effective);
    }
  }

  /// 화면 진입/포그라운드 복귀 시 OS 권한과 재동기화.
  Future<void> syncWithOsPermission() => _reconcile();

  Future<void> setThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    await _localStorage.setThemeMode(mode.toString());
  }

  Future<NotificationToggleResult> setNotifications(bool enabled) async {
    if (!enabled) {
      await _localStorage.setNotificationsEnabled(false);
      await _syncTopics(subscribe: false);
      state = state.copyWith(notificationsEnabled: false);
      return NotificationToggleResult.granted;
    }

    // 켜기: OS 권한 상태 확인
    final status = await Permission.notification.status;

    if (status.isPermanentlyDenied) {
      return NotificationToggleResult.permanentlyDenied;
    }

    final effectiveStatus =
        status.isGranted ? status : await Permission.notification.request();

    if (effectiveStatus.isGranted) {
      await _localStorage.setNotificationsEnabled(true);
      await _syncTopics(subscribe: true);
      state = state.copyWith(notificationsEnabled: true);
      return NotificationToggleResult.granted;
    }

    if (effectiveStatus.isPermanentlyDenied) {
      return NotificationToggleResult.permanentlyDenied;
    }

    return NotificationToggleResult.denied;
  }

  Future<void> _syncTopics({required bool subscribe}) async {
    final fcm = FCMService();
    for (final topic in _notificationTopics) {
      if (subscribe) {
        await fcm.subscribeToTopic(topic);
      } else {
        await fcm.unsubscribeFromTopic(topic);
      }
    }
  }

  Future<void> setLanguage(String language) async {
    state = state.copyWith(language: language);
    await _localStorage.setLanguage(language);
  }

  ThemeMode _parseThemeMode(String? value) {
    if (value == null) return ThemeMode.system;

    switch (value) {
      case 'ThemeMode.light':
        return ThemeMode.light;
      case 'ThemeMode.dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }
}

final settingsProvider =
    StateNotifierProvider<SettingsNotifier, AppSettings>((ref) {
  final localStorage = ref.watch(localStorageProvider);
  return SettingsNotifier(localStorage);
});
