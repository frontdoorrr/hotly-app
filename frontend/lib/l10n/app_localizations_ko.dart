// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Korean (`ko`).
class AppLocalizationsKo extends AppLocalizations {
  AppLocalizationsKo([String locale = 'ko']) : super(locale);

  @override
  String get appName => 'Hotly';

  @override
  String get loginRequired => '로그인이 필요합니다';

  @override
  String get loginButton => '로그인하기';

  @override
  String get savedPlaces => '저장한 장소';

  @override
  String get noSavedPlaces => '저장한 장소가 없습니다';

  @override
  String get savePlacePrompt => '마음에 드는 장소를 저장해보세요';

  @override
  String get loginToSavePlaces => '로그인하고 마음에 드는 장소를 저장해보세요';

  @override
  String get refresh => '새로고침';

  @override
  String get errorOccurred => '오류가 발생했습니다';

  @override
  String get cannotLoadPlaces => '장소를 불러올 수 없습니다';

  @override
  String get retry => '다시 시도';

  @override
  String get noFilterResults => '필터 조건에 맞는 장소가 없습니다';

  @override
  String get tryOtherTags => '다른 태그를 선택해보세요';

  @override
  String get clearFilters => '필터 초기화';

  @override
  String get currentLocation => '현재 위치';

  @override
  String get connectionTimeout => '연결 시간이 초과되었습니다. 다시 시도해주세요.';

  @override
  String get serverError => '서버 오류가 발생했습니다.';

  @override
  String get authRequired => '인증이 필요합니다. 다시 로그인해주세요.';

  @override
  String get notFound => '요청한 데이터를 찾을 수 없습니다.';

  @override
  String get requestCancelled => '요청이 취소되었습니다.';

  @override
  String get checkNetwork => '네트워크 연결을 확인해주세요.';

  @override
  String get allPlaces => '전체';
}
