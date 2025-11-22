// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'Hotly';

  @override
  String get loginRequired => 'Login required';

  @override
  String get loginButton => 'Log in';

  @override
  String get savedPlaces => 'Saved Places';

  @override
  String get noSavedPlaces => 'No saved places';

  @override
  String get savePlacePrompt => 'Save places you like';

  @override
  String get loginToSavePlaces => 'Log in to save your favorite places';

  @override
  String get refresh => 'Refresh';

  @override
  String get errorOccurred => 'An error occurred';

  @override
  String get cannotLoadPlaces => 'Cannot load places';

  @override
  String get retry => 'Retry';

  @override
  String get noFilterResults => 'No places match the filter';

  @override
  String get tryOtherTags => 'Try selecting other tags';

  @override
  String get clearFilters => 'Clear filters';

  @override
  String get currentLocation => 'Current location';

  @override
  String get connectionTimeout => 'Connection timed out. Please try again.';

  @override
  String get serverError => 'Server error occurred.';

  @override
  String get authRequired => 'Authentication required. Please log in again.';

  @override
  String get notFound => 'Requested data not found.';

  @override
  String get requestCancelled => 'Request was cancelled.';

  @override
  String get checkNetwork => 'Please check your network connection.';

  @override
  String get allPlaces => 'All';
}
