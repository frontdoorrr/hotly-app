import 'package:flutter/widgets.dart';
import 'package:frontend/l10n/app_localizations.dart';

/// Extension for convenient access to AppLocalizations
///
/// Usage:
/// ```dart
/// Text(context.l10n.appName)
/// ```
extension L10nExtension on BuildContext {
  /// Access to AppLocalizations instance
  AppLocalizations get l10n => AppLocalizations.of(this)!;
}
