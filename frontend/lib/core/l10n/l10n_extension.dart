import 'package:flutter/widgets.dart';
import 'package:hotly_app/l10n/app_localizations.dart';

extension L10nExtension on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this)!;
}

/// 에러 코드 문자열을 현재 언어에 맞는 메시지로 변환한다.
/// ApiException.message 및 Exception('error_xxx') 패턴 모두 지원.
String localizeApiError(BuildContext context, String? code) {
  final l10n = context.l10n;
  switch (code) {
    case 'error_connectionTimeout':  return l10n.error_connectionTimeout;
    case 'error_serverError':        return l10n.error_serverError;
    case 'error_unauthorized':       return l10n.error_unauthorized;
    case 'error_notFound':           return l10n.error_notFound;
    case 'error_requestCancelled':   return l10n.error_requestCancelled;
    case 'error_checkNetwork':       return l10n.error_checkNetwork;
    case 'error_unsupportedLink':    return l10n.error_unsupportedLink;
    case 'error_accessDenied':       return l10n.error_accessDenied;
    case 'error_archiveNotFound':    return l10n.error_archiveNotFound;
    case 'error_privateOrDeleted':   return l10n.error_privateOrDeleted;
    case 'error_rateLimited':        return l10n.error_rateLimited;
    case 'error_serviceUnavailable': return l10n.error_serviceUnavailable;
    case 'error_instagramBlocked':       return l10n.error_instagramBlocked;
    case 'error_instagramParseError':    return l10n.error_instagramParseError;
    case 'error_instagramDownloadError': return l10n.error_instagramDownloadError;
    default:                         return l10n.error_unknown;
  }
}
