import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 앱 분석 요청에 사용할 언어 코드 ('ko' | 'en').
/// UI에서 Localizations.localeOf(context).languageCode를 읽어 업데이트한다.
final languageCodeProvider = StateProvider<String>((ref) => 'ko');
