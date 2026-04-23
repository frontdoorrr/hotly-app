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

  SettingsNotifier(this._localStorage) : super(const AppSettings()) {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final themeString = _localStorage.themeMode;
    final language = _localStorage.language;

    bool notificationsEnabled = _localStorage.notificationsEnabled;
    // 앱 설정이 ON이더라도 실제 OS 권한이 없으면 OFF로 동기화
    if (notificationsEnabled) {
      final status = await Permission.notification.status;
      if (!status.isGranted) {
        notificationsEnabled = false;
        await _localStorage.setNotificationsEnabled(false);
      }
    }

    state = state.copyWith(
      themeMode: _parseThemeMode(themeString),
      notificationsEnabled: notificationsEnabled,
      language: language,
    );
  }

  // 화면 진입 시 OS 권한 상태와 앱 설정을 재동기화
  Future<void> syncWithOsPermission() async {
    if (!state.notificationsEnabled) return;
    final status = await Permission.notification.status;
    if (!status.isGranted) {
      state = state.copyWith(notificationsEnabled: false);
      await _localStorage.setNotificationsEnabled(false);
    }
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    await _localStorage.setThemeMode(mode.toString());
  }

  Future<NotificationToggleResult> setNotifications(bool enabled) async {
    if (!enabled) {
      state = state.copyWith(notificationsEnabled: false);
      await _localStorage.setNotificationsEnabled(false);
      await FCMService().unsubscribeFromTopic('all_users');
      await FCMService().unsubscribeFromTopic('recommendations');
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
      state = state.copyWith(notificationsEnabled: true);
      await _localStorage.setNotificationsEnabled(true);
      await FCMService().subscribeToTopic('all_users');
      await FCMService().subscribeToTopic('recommendations');
      return NotificationToggleResult.granted;
    }

    if (effectiveStatus.isPermanentlyDenied) {
      return NotificationToggleResult.permanentlyDenied;
    }

    return NotificationToggleResult.denied;
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
