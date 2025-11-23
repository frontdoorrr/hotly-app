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

  /// 확인 버튼
  ///
  /// In ko, this message translates to:
  /// **'확인'**
  String get common_ok;

  /// 취소 버튼
  ///
  /// In ko, this message translates to:
  /// **'취소'**
  String get common_cancel;

  /// 저장 버튼
  ///
  /// In ko, this message translates to:
  /// **'저장'**
  String get common_save;

  /// 닫기 버튼
  ///
  /// In ko, this message translates to:
  /// **'닫기'**
  String get common_close;

  /// 다음 버튼
  ///
  /// In ko, this message translates to:
  /// **'다음'**
  String get common_next;

  /// 이전 버튼
  ///
  /// In ko, this message translates to:
  /// **'이전'**
  String get common_previous;

  /// 시작하기 버튼
  ///
  /// In ko, this message translates to:
  /// **'시작하기'**
  String get common_start;

  /// 새로고침 버튼
  ///
  /// In ko, this message translates to:
  /// **'새로고침'**
  String get common_refresh;

  /// 재시도 버튼
  ///
  /// In ko, this message translates to:
  /// **'다시 시도'**
  String get common_retry;

  /// 전체 필터 태그
  ///
  /// In ko, this message translates to:
  /// **'전체'**
  String get common_all;

  /// 더보기 버튼
  ///
  /// In ko, this message translates to:
  /// **'더보기'**
  String get common_more;

  /// 상세보기 버튼
  ///
  /// In ko, this message translates to:
  /// **'상세보기'**
  String get common_detail;

  /// 미리보기 버튼
  ///
  /// In ko, this message translates to:
  /// **'미리보기'**
  String get common_preview;

  /// 홈 탭
  ///
  /// In ko, this message translates to:
  /// **'홈'**
  String get nav_home;

  /// 지도 탭
  ///
  /// In ko, this message translates to:
  /// **'지도'**
  String get nav_map;

  /// 저장 탭
  ///
  /// In ko, this message translates to:
  /// **'저장'**
  String get nav_saved;

  /// 프로필 탭
  ///
  /// In ko, this message translates to:
  /// **'프로필'**
  String get nav_profile;

  /// 로그인 텍스트
  ///
  /// In ko, this message translates to:
  /// **'로그인'**
  String get auth_login;

  /// 로그인 버튼 텍스트
  ///
  /// In ko, this message translates to:
  /// **'로그인하기'**
  String get auth_loginButton;

  /// 로그아웃 버튼
  ///
  /// In ko, this message translates to:
  /// **'로그아웃'**
  String get auth_logout;

  /// 로그아웃 성공 메시지
  ///
  /// In ko, this message translates to:
  /// **'로그아웃되었습니다'**
  String get auth_logoutSuccess;

  /// 회원가입 텍스트
  ///
  /// In ko, this message translates to:
  /// **'회원가입'**
  String get auth_signup;

  /// 가입하기 버튼
  ///
  /// In ko, this message translates to:
  /// **'가입하기'**
  String get auth_signupButton;

  /// 이메일 레이블
  ///
  /// In ko, this message translates to:
  /// **'이메일'**
  String get auth_email;

  /// 비밀번호 레이블
  ///
  /// In ko, this message translates to:
  /// **'비밀번호'**
  String get auth_password;

  /// 이름 레이블
  ///
  /// In ko, this message translates to:
  /// **'이름'**
  String get auth_name;

  /// 이용약관 링크
  ///
  /// In ko, this message translates to:
  /// **'이용약관'**
  String get auth_termsOfService;

  /// 개인정보처리방침 링크
  ///
  /// In ko, this message translates to:
  /// **'개인정보처리방침'**
  String get auth_privacyPolicy;

  /// 로그인 필요 메시지
  ///
  /// In ko, this message translates to:
  /// **'로그인이 필요합니다'**
  String get auth_loginRequired;

  /// 인증 필요 메시지
  ///
  /// In ko, this message translates to:
  /// **'인증이 필요합니다. 다시 로그인해주세요.'**
  String get auth_authRequired;

  /// 계정 탈퇴 버튼
  ///
  /// In ko, this message translates to:
  /// **'탈퇴하기'**
  String get auth_deleteAccount;

  /// 카카오 로그인 제공자
  ///
  /// In ko, this message translates to:
  /// **'카카오'**
  String get auth_providerKakao;

  /// 이메일 로그인 제공자
  ///
  /// In ko, this message translates to:
  /// **'이메일'**
  String get auth_providerEmail;

  /// 이메일 필수 입력 메시지
  ///
  /// In ko, this message translates to:
  /// **'이메일을 입력해주세요'**
  String get auth_emailRequired;

  /// 이메일 형식 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'올바른 이메일 형식이 아닙니다'**
  String get auth_emailInvalid;

  /// 비밀번호 필수 입력 메시지
  ///
  /// In ko, this message translates to:
  /// **'비밀번호를 입력해주세요'**
  String get auth_passwordRequired;

  /// 비밀번호 힌트 텍스트
  ///
  /// In ko, this message translates to:
  /// **'비밀번호를 입력하세요'**
  String get auth_passwordHint;

  /// 비밀번호 찾기 버튼
  ///
  /// In ko, this message translates to:
  /// **'비밀번호 찾기'**
  String get auth_forgotPassword;

  /// 소셜 로그인 구분선
  ///
  /// In ko, this message translates to:
  /// **'또는 소셜 로그인으로'**
  String get auth_orSocialLogin;

  /// 회원가입 유도 메시지
  ///
  /// In ko, this message translates to:
  /// **'계정이 없으신가요?'**
  String get auth_noAccount;

  /// 로그인 유도 메시지
  ///
  /// In ko, this message translates to:
  /// **'이미 계정이 있으신가요?'**
  String get auth_hasAccount;

  /// 이름 필수 입력 메시지
  ///
  /// In ko, this message translates to:
  /// **'이름을 입력해주세요'**
  String get auth_nameRequired;

  /// 비밀번호 길이 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'비밀번호는 6자 이상이어야 합니다'**
  String get auth_passwordTooShort;

  /// 앱 태그라인
  ///
  /// In ko, this message translates to:
  /// **'AI 기반 핫플 아카이빙'**
  String get app_tagline;

  /// 이름 힌트 텍스트
  ///
  /// In ko, this message translates to:
  /// **'이름을 입력하세요'**
  String get auth_nameHint;

  /// 이름 길이 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'이름은 2자 이상이어야 합니다'**
  String get auth_nameTooShort;

  /// 비밀번호 최소 길이 메시지
  ///
  /// In ko, this message translates to:
  /// **'비밀번호는 최소 6자 이상이어야 합니다'**
  String get auth_passwordMinLength;

  /// 비밀번호 확인 레이블
  ///
  /// In ko, this message translates to:
  /// **'비밀번호 확인'**
  String get auth_passwordConfirm;

  /// 비밀번호 확인 힌트
  ///
  /// In ko, this message translates to:
  /// **'비밀번호를 다시 입력하세요'**
  String get auth_passwordConfirmHint;

  /// 비밀번호 확인 필수 메시지
  ///
  /// In ko, this message translates to:
  /// **'비밀번호를 다시 입력해주세요'**
  String get auth_passwordConfirmRequired;

  /// 비밀번호 불일치 메시지
  ///
  /// In ko, this message translates to:
  /// **'비밀번호가 일치하지 않습니다'**
  String get auth_passwordMismatch;

  /// 약관 동의 필요 메시지
  ///
  /// In ko, this message translates to:
  /// **'이용약관 및 개인정보처리방침에 동의해주세요'**
  String get auth_agreeToTerms;

  /// 접속사
  ///
  /// In ko, this message translates to:
  /// **'및'**
  String get auth_and;

  /// 동의 텍스트
  ///
  /// In ko, this message translates to:
  /// **'에 동의합니다'**
  String get auth_agreeText;

  /// 이메일 인증 제목
  ///
  /// In ko, this message translates to:
  /// **'이메일 인증'**
  String get auth_emailVerification;

  /// 이메일 인증 발송 메시지
  ///
  /// In ko, this message translates to:
  /// **'가입하신 이메일로 인증 링크를 발송했습니다.\n이메일을 확인한 후 다시 로그인해주세요.'**
  String get auth_emailVerificationSent;

  /// 저장한 장소 화면 제목
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소'**
  String get place_savedPlaces;

  /// 저장한 장소가 없을 때 메시지
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소가 없습니다'**
  String get place_noSavedPlaces;

  /// 장소 저장 안내 메시지
  ///
  /// In ko, this message translates to:
  /// **'마음에 드는 장소를 저장해보세요'**
  String get place_savePlacePrompt;

  /// 로그인 후 장소 저장 안내
  ///
  /// In ko, this message translates to:
  /// **'로그인하고 마음에 드는 장소를 저장해보세요'**
  String get place_loginToSavePlaces;

  /// 장소 로딩 실패 메시지
  ///
  /// In ko, this message translates to:
  /// **'장소를 불러올 수 없습니다'**
  String get place_cannotLoadPlaces;

  /// 필터 결과 없음 메시지
  ///
  /// In ko, this message translates to:
  /// **'필터 조건에 맞는 장소가 없습니다'**
  String get place_noFilterResults;

  /// 다른 태그 선택 안내
  ///
  /// In ko, this message translates to:
  /// **'다른 태그를 선택해보세요'**
  String get place_tryOtherTags;

  /// 필터 초기화 버튼
  ///
  /// In ko, this message translates to:
  /// **'필터 초기화'**
  String get place_clearFilters;

  /// 장소 소개 섹션
  ///
  /// In ko, this message translates to:
  /// **'소개'**
  String get place_introduction;

  /// 저장됨 상태
  ///
  /// In ko, this message translates to:
  /// **'저장됨'**
  String get place_saved;

  /// 저장하기 버튼
  ///
  /// In ko, this message translates to:
  /// **'저장하기'**
  String get place_saveButton;

  /// 분석 신뢰도
  ///
  /// In ko, this message translates to:
  /// **'신뢰도'**
  String get place_confidence;

  /// 현재 위치 마커 텍스트
  ///
  /// In ko, this message translates to:
  /// **'현재 위치'**
  String get map_currentLocation;

  /// 데이트 코스 유형
  ///
  /// In ko, this message translates to:
  /// **'데이트'**
  String get course_date;

  /// 여행 코스 유형
  ///
  /// In ko, this message translates to:
  /// **'여행'**
  String get course_travel;

  /// 맛집투어 코스 유형
  ///
  /// In ko, this message translates to:
  /// **'맛집투어'**
  String get course_foodTour;

  /// 기타 코스 유형
  ///
  /// In ko, this message translates to:
  /// **'기타'**
  String get course_other;

  /// 도보 이동 수단
  ///
  /// In ko, this message translates to:
  /// **'도보'**
  String get course_walking;

  /// 차량 이동 수단
  ///
  /// In ko, this message translates to:
  /// **'차량'**
  String get course_driving;

  /// 링크 분석 버튼
  ///
  /// In ko, this message translates to:
  /// **'분석하기'**
  String get link_analyze;

  /// 프로필 화면 제목
  ///
  /// In ko, this message translates to:
  /// **'프로필'**
  String get profile_title;

  /// 저장 통계 레이블
  ///
  /// In ko, this message translates to:
  /// **'저장'**
  String get profile_saved;

  /// 좋아요 통계 레이블
  ///
  /// In ko, this message translates to:
  /// **'좋아요'**
  String get profile_likes;

  /// 코스 통계 레이블
  ///
  /// In ko, this message translates to:
  /// **'코스'**
  String get profile_courses;

  /// 프로필 편집 버튼
  ///
  /// In ko, this message translates to:
  /// **'프로필 편집'**
  String get profile_edit;

  /// 저장된 장소 탭
  ///
  /// In ko, this message translates to:
  /// **'저장된 장소'**
  String get profile_savedPlacesTab;

  /// 내 코스 탭
  ///
  /// In ko, this message translates to:
  /// **'내 코스'**
  String get profile_myCoursesTab;

  /// 저장된 장소 없음 메시지
  ///
  /// In ko, this message translates to:
  /// **'저장된 장소가 없습니다'**
  String get profile_noSavedPlaces;

  /// 장소 찾기 버튼
  ///
  /// In ko, this message translates to:
  /// **'장소 찾기'**
  String get profile_findPlaces;

  /// 생성한 코스 없음 메시지
  ///
  /// In ko, this message translates to:
  /// **'생성한 코스가 없습니다'**
  String get profile_noCourses;

  /// 코스 생성 안내 메시지
  ///
  /// In ko, this message translates to:
  /// **'나만의 데이트 코스를 만들어보세요'**
  String get profile_createCoursePrompt;

  /// 코스 만들기 버튼
  ///
  /// In ko, this message translates to:
  /// **'코스 만들기'**
  String get profile_createCourse;

  /// 로그인 안내 메시지
  ///
  /// In ko, this message translates to:
  /// **'로그인하고 나만의 장소를 저장해보세요'**
  String get profile_loginPrompt;

  /// 설정 섹션 제목
  ///
  /// In ko, this message translates to:
  /// **'설정'**
  String get settings_title;

  /// 테마 설정
  ///
  /// In ko, this message translates to:
  /// **'테마'**
  String get settings_theme;

  /// 언어 설정
  ///
  /// In ko, this message translates to:
  /// **'언어'**
  String get settings_language;

  /// 한국어 언어 옵션
  ///
  /// In ko, this message translates to:
  /// **'한국어'**
  String get settings_korean;

  /// 알림 설정
  ///
  /// In ko, this message translates to:
  /// **'알림 설정'**
  String get settings_notifications;

  /// 알림 설정 설명
  ///
  /// In ko, this message translates to:
  /// **'푸시 알림 받기'**
  String get settings_notificationsDesc;

  /// 시스템 테마
  ///
  /// In ko, this message translates to:
  /// **'시스템 설정'**
  String get settings_themeSystem;

  /// 라이트 테마
  ///
  /// In ko, this message translates to:
  /// **'라이트 모드'**
  String get settings_themeLight;

  /// 다크 테마
  ///
  /// In ko, this message translates to:
  /// **'다크 모드'**
  String get settings_themeDark;

  /// 테마 선택 다이얼로그 제목
  ///
  /// In ko, this message translates to:
  /// **'테마 선택'**
  String get settings_selectTheme;

  /// 언어 선택 다이얼로그 제목
  ///
  /// In ko, this message translates to:
  /// **'언어 선택'**
  String get settings_selectLanguage;

  /// 앱 정보
  ///
  /// In ko, this message translates to:
  /// **'앱 정보'**
  String get settings_appInfo;

  /// 앱 이름 레이블
  ///
  /// In ko, this message translates to:
  /// **'앱 이름'**
  String get settings_appName;

  /// 버전 레이블
  ///
  /// In ko, this message translates to:
  /// **'버전'**
  String get settings_version;

  /// 빌드 번호 레이블
  ///
  /// In ko, this message translates to:
  /// **'빌드 번호'**
  String get settings_buildNumber;

  /// 로그아웃 확인 메시지
  ///
  /// In ko, this message translates to:
  /// **'정말 로그아웃하시겠습니까?'**
  String get auth_logoutConfirm;

  /// 회원 탈퇴 제목
  ///
  /// In ko, this message translates to:
  /// **'회원 탈퇴'**
  String get auth_deleteAccountTitle;

  /// 회원 탈퇴 확인 메시지
  ///
  /// In ko, this message translates to:
  /// **'정말 탈퇴하시겠습니까?\n\n모든 데이터가 삭제되며 복구할 수 없습니다.'**
  String get auth_deleteAccountConfirm;

  /// 회원 탈퇴 성공 메시지
  ///
  /// In ko, this message translates to:
  /// **'회원 탈퇴가 완료되었습니다'**
  String get auth_deleteAccountSuccess;

  /// 회원 탈퇴 실패 메시지
  ///
  /// In ko, this message translates to:
  /// **'탈퇴 실패'**
  String get auth_deleteAccountFailed;

  /// 온보딩 관심사 - 카페
  ///
  /// In ko, this message translates to:
  /// **'카페'**
  String get onboarding_cafe;

  /// 온보딩 관심사 - 맛집
  ///
  /// In ko, this message translates to:
  /// **'맛집'**
  String get onboarding_restaurant;

  /// 온보딩 관심사 - 데이트
  ///
  /// In ko, this message translates to:
  /// **'데이트'**
  String get onboarding_date;

  /// 온보딩 관심사 - 뷰맛집
  ///
  /// In ko, this message translates to:
  /// **'뷰맛집'**
  String get onboarding_view;

  /// 온보딩 관심사 - 감성
  ///
  /// In ko, this message translates to:
  /// **'감성'**
  String get onboarding_mood;

  /// 온보딩 관심사 - 힐링
  ///
  /// In ko, this message translates to:
  /// **'힐링'**
  String get onboarding_healing;

  /// 온보딩 관심사 - 액티비티
  ///
  /// In ko, this message translates to:
  /// **'액티비티'**
  String get onboarding_activity;

  /// 온보딩 관심사 - 쇼핑
  ///
  /// In ko, this message translates to:
  /// **'쇼핑'**
  String get onboarding_shopping;

  /// 건너뛰기 버튼
  ///
  /// In ko, this message translates to:
  /// **'Skip'**
  String get common_skip;

  /// 온보딩 환영 메시지
  ///
  /// In ko, this message translates to:
  /// **'Hotly에 오신 것을 환영합니다!'**
  String get onboarding_welcome;

  /// 온보딩 환영 설명
  ///
  /// In ko, this message translates to:
  /// **'AI가 추천하는 핫플레이스와\n나만의 데이트 코스를 만들어보세요'**
  String get onboarding_welcomeDesc;

  /// 관심사 선택 제목
  ///
  /// In ko, this message translates to:
  /// **'관심사를 선택해주세요'**
  String get onboarding_selectInterests;

  /// 관심사 선택 설명
  ///
  /// In ko, this message translates to:
  /// **'선택한 관심사를 바탕으로 맞춤 장소를 추천해드려요'**
  String get onboarding_interestsDesc;

  /// 위치 권한 제목
  ///
  /// In ko, this message translates to:
  /// **'위치 권한'**
  String get onboarding_locationTitle;

  /// 위치 권한 설명
  ///
  /// In ko, this message translates to:
  /// **'현재 위치 주변의 핫플레이스를\n추천해드리기 위해 위치 권한이 필요해요'**
  String get onboarding_locationDesc;

  /// 권한 허용됨
  ///
  /// In ko, this message translates to:
  /// **'권한 허용됨 ✓'**
  String get onboarding_permissionGranted;

  /// 위치 권한 허용 버튼
  ///
  /// In ko, this message translates to:
  /// **'위치 권한 허용'**
  String get onboarding_locationAllow;

  /// 나중에 설정하기 버튼
  ///
  /// In ko, this message translates to:
  /// **'나중에 설정하기'**
  String get onboarding_later;

  /// 알림 권한 제목
  ///
  /// In ko, this message translates to:
  /// **'알림 권한'**
  String get onboarding_notificationTitle;

  /// 알림 권한 설명
  ///
  /// In ko, this message translates to:
  /// **'새로운 핫플레이스와 맞춤 추천 소식을\n알려드리기 위해 알림 권한이 필요해요'**
  String get onboarding_notificationDesc;

  /// 알림 권한 허용 버튼
  ///
  /// In ko, this message translates to:
  /// **'알림 권한 허용'**
  String get onboarding_notificationAllow;

  /// No description provided for @profile_nameHint.
  ///
  /// In ko, this message translates to:
  /// **'표시될 이름을 입력하세요'**
  String get profile_nameHint;

  /// No description provided for @profile_loggedInWith.
  ///
  /// In ko, this message translates to:
  /// **'계정으로 로그인'**
  String get profile_loggedInWith;

  /// No description provided for @profile_joinDate.
  ///
  /// In ko, this message translates to:
  /// **'가입일'**
  String get profile_joinDate;

  /// No description provided for @profile_photoChangeLater.
  ///
  /// In ko, this message translates to:
  /// **'프로필 사진 변경은 추후 지원 예정입니다'**
  String get profile_photoChangeLater;

  /// No description provided for @profile_updateSuccess.
  ///
  /// In ko, this message translates to:
  /// **'프로필이 업데이트되었습니다'**
  String get profile_updateSuccess;

  /// No description provided for @profile_updateFailed.
  ///
  /// In ko, this message translates to:
  /// **'프로필 업데이트 실패'**
  String get profile_updateFailed;

  /// No description provided for @course_newCourse.
  ///
  /// In ko, this message translates to:
  /// **'새 코스'**
  String get course_newCourse;

  /// No description provided for @course_title.
  ///
  /// In ko, this message translates to:
  /// **'코스 제목'**
  String get course_title;

  /// No description provided for @course_titleHint.
  ///
  /// In ko, this message translates to:
  /// **'예: 강남 데이트 코스'**
  String get course_titleHint;

  /// No description provided for @course_type.
  ///
  /// In ko, this message translates to:
  /// **'코스 타입'**
  String get course_type;

  /// No description provided for @course_places.
  ///
  /// In ko, this message translates to:
  /// **'장소'**
  String get course_places;

  /// No description provided for @course_totalDuration.
  ///
  /// In ko, this message translates to:
  /// **'총'**
  String get course_totalDuration;

  /// No description provided for @course_addPlacePrompt.
  ///
  /// In ko, this message translates to:
  /// **'장소를 추가해주세요'**
  String get course_addPlacePrompt;

  /// No description provided for @course_addPlace.
  ///
  /// In ko, this message translates to:
  /// **'장소 추가하기'**
  String get course_addPlace;

  /// No description provided for @course_searchInDevelopment.
  ///
  /// In ko, this message translates to:
  /// **'장소 검색 기능은 개발 중입니다'**
  String get course_searchInDevelopment;

  /// No description provided for @course_hour.
  ///
  /// In ko, this message translates to:
  /// **'시간'**
  String get course_hour;

  /// No description provided for @course_minute.
  ///
  /// In ko, this message translates to:
  /// **'분'**
  String get course_minute;

  /// No description provided for @place_similarPlaces.
  ///
  /// In ko, this message translates to:
  /// **'비슷한 장소'**
  String get place_similarPlaces;

  /// No description provided for @place_addToCourse.
  ///
  /// In ko, this message translates to:
  /// **'코스에 추가'**
  String get place_addToCourse;

  /// No description provided for @place_availableInCourseBuilder.
  ///
  /// In ko, this message translates to:
  /// **'이 기능은 코스 빌더 화면에서 사용할 수 있습니다.'**
  String get place_availableInCourseBuilder;

  /// No description provided for @map_viewOnMap.
  ///
  /// In ko, this message translates to:
  /// **'지도 보기'**
  String get map_viewOnMap;

  /// No description provided for @map_findRoute.
  ///
  /// In ko, this message translates to:
  /// **'경로 찾기'**
  String get map_findRoute;

  /// 일반 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'오류가 발생했습니다'**
  String get error_occurred;

  /// 연결 타임아웃 메시지
  ///
  /// In ko, this message translates to:
  /// **'연결 시간이 초과되었습니다. 다시 시도해주세요.'**
  String get error_connectionTimeout;

  /// 서버 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'서버 오류가 발생했습니다.'**
  String get error_serverError;

  /// 404 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'요청한 데이터를 찾을 수 없습니다.'**
  String get error_notFound;

  /// 요청 취소 메시지
  ///
  /// In ko, this message translates to:
  /// **'요청이 취소되었습니다.'**
  String get error_requestCancelled;

  /// 네트워크 오류 메시지
  ///
  /// In ko, this message translates to:
  /// **'네트워크 연결을 확인해주세요.'**
  String get error_checkNetwork;

  /// No description provided for @loginRequired.
  ///
  /// In ko, this message translates to:
  /// **'로그인이 필요합니다'**
  String get loginRequired;

  /// No description provided for @loginButton.
  ///
  /// In ko, this message translates to:
  /// **'로그인하기'**
  String get loginButton;

  /// No description provided for @savedPlaces.
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소'**
  String get savedPlaces;

  /// No description provided for @noSavedPlaces.
  ///
  /// In ko, this message translates to:
  /// **'저장한 장소가 없습니다'**
  String get noSavedPlaces;

  /// No description provided for @savePlacePrompt.
  ///
  /// In ko, this message translates to:
  /// **'마음에 드는 장소를 저장해보세요'**
  String get savePlacePrompt;

  /// No description provided for @loginToSavePlaces.
  ///
  /// In ko, this message translates to:
  /// **'로그인하고 마음에 드는 장소를 저장해보세요'**
  String get loginToSavePlaces;

  /// No description provided for @refresh.
  ///
  /// In ko, this message translates to:
  /// **'새로고침'**
  String get refresh;

  /// No description provided for @errorOccurred.
  ///
  /// In ko, this message translates to:
  /// **'오류가 발생했습니다'**
  String get errorOccurred;

  /// No description provided for @cannotLoadPlaces.
  ///
  /// In ko, this message translates to:
  /// **'장소를 불러올 수 없습니다'**
  String get cannotLoadPlaces;

  /// No description provided for @retry.
  ///
  /// In ko, this message translates to:
  /// **'다시 시도'**
  String get retry;

  /// No description provided for @noFilterResults.
  ///
  /// In ko, this message translates to:
  /// **'필터 조건에 맞는 장소가 없습니다'**
  String get noFilterResults;

  /// No description provided for @tryOtherTags.
  ///
  /// In ko, this message translates to:
  /// **'다른 태그를 선택해보세요'**
  String get tryOtherTags;

  /// No description provided for @clearFilters.
  ///
  /// In ko, this message translates to:
  /// **'필터 초기화'**
  String get clearFilters;

  /// No description provided for @currentLocation.
  ///
  /// In ko, this message translates to:
  /// **'현재 위치'**
  String get currentLocation;

  /// No description provided for @connectionTimeout.
  ///
  /// In ko, this message translates to:
  /// **'연결 시간이 초과되었습니다. 다시 시도해주세요.'**
  String get connectionTimeout;

  /// No description provided for @serverError.
  ///
  /// In ko, this message translates to:
  /// **'서버 오류가 발생했습니다.'**
  String get serverError;

  /// No description provided for @authRequired.
  ///
  /// In ko, this message translates to:
  /// **'인증이 필요합니다. 다시 로그인해주세요.'**
  String get authRequired;

  /// No description provided for @notFound.
  ///
  /// In ko, this message translates to:
  /// **'요청한 데이터를 찾을 수 없습니다.'**
  String get notFound;

  /// No description provided for @requestCancelled.
  ///
  /// In ko, this message translates to:
  /// **'요청이 취소되었습니다.'**
  String get requestCancelled;

  /// No description provided for @checkNetwork.
  ///
  /// In ko, this message translates to:
  /// **'네트워크 연결을 확인해주세요.'**
  String get checkNetwork;

  /// No description provided for @allPlaces.
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
