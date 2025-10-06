import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/storage/local_storage.dart';

part 'settings_provider.freezed.dart';

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
    final notificationsEnabled = _localStorage.notificationsEnabled;
    final language = _localStorage.language;

    state = state.copyWith(
      themeMode: _parseThemeMode(themeString),
      notificationsEnabled: notificationsEnabled,
      language: language,
    );
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    await _localStorage.setThemeMode(mode.toString());
  }

  Future<void> setNotifications(bool enabled) async {
    state = state.copyWith(notificationsEnabled: enabled);
    await _localStorage.setNotificationsEnabled(enabled);
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
