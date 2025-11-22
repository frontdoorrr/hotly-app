import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_ko.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ko')
  ];

  /// 앱 이름
  ///
  /// In ko, this message translates to:
  /// **'Hotly'**
  String get appName;

  /// 로그인 필요 메시지
  ///
  /// In ko, this message translates to:
  /// **'로그인이 필요합니다'**
  String get loginRequired;

  /// 로그인 버튼 텍스트
  ///
  /// In ko, this message translates to:
  /// **'로그인하기'**
  String get loginButton;

  /// 저장한 장소 화면 제목
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소'**
  String get savedPlaces;

  /// 저장한 장소가 없을 때 메시지
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소가 없습니다'**
  String get noSavedPlaces;

  /// 장소 저장 안내 메시지
  ///
  /// In ko, this message translates to:
  /// **'마음에 드는 장소를 저장해보세요'**
  String get savePlacePrompt;

  /// 로그인 후 장소 저장 안내
  ///
  /// In ko, this message translates to:
  /// **'로그인하고 마음에 드는 장소를 저장해보세요'**
  String get loginToSavePlaces;

  /// 새로고침 버튼
  ///
  /// In ko, this message translates to:
  /// **'새로고침'**
  String get refresh;

  /// 일반 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'오류가 발생했습니다'**
  String get errorOccurred;

  /// 장소 로딩 실패 메시지
  ///
  /// In ko, this message translates to:
  /// **'장소를 불러올 수 없습니다'**
  String get cannotLoadPlaces;

  /// 재시도 버튼
  ///
  /// In ko, this message translates to:
  /// **'다시 시도'**
  String get retry;

  /// 필터 결과 없음 메시지
  ///
  /// In ko, this message translates to:
  /// **'필터 조건에 맞는 장소가 없습니다'**
  String get noFilterResults;

  /// 다른 태그 선택 안내
  ///
  /// In ko, this message translates to:
  /// **'다른 태그를 선택해보세요'**
  String get tryOtherTags;

  /// 필터 초기화 버튼
  ///
  /// In ko, this message translates to:
  /// **'필터 초기화'**
  String get clearFilters;

  /// 현재 위치 마커 텍스트
  ///
  /// In ko, this message translates to:
  /// **'현재 위치'**
  String get currentLocation;

  /// 연결 타임아웃 메시지
  ///
  /// In ko, this message translates to:
  /// **'연결 시간이 초과되었습니다. 다시 시도해주세요.'**
  String get connectionTimeout;

  /// 서버 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'서버 오류가 발생했습니다.'**
  String get serverError;

  /// 인증 필요 메시지
  ///
  /// In ko, this message translates to:
  /// **'인증이 필요합니다. 다시 로그인해주세요.'**
  String get authRequired;

  /// 404 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'요청한 데이터를 찾을 수 없습니다.'**
  String get notFound;

  /// 요청 취소 메시지
  ///
  /// In ko, this message translates to:
  /// **'요청이 취소되었습니다.'**
  String get requestCancelled;

  /// 네트워크 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'네트워크 연결을 확인해주세요.'**
  String get checkNetwork;

  /// 전체 장소 필터 태그
  ///
  /// In ko, this message translates to:
  /// **'전체'**
  String get allPlaces;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ko'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'ko':
      return AppLocalizationsKo();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
