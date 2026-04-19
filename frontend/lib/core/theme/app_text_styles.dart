import 'package:flutter/material.dart';

/// App Typography System — ArchyAI
///
/// Font stack: 'Google Sans' (primary) → 'Noto Sans KR' (fallback)
/// fontFamily is applied globally in app_theme.dart via ThemeData.fontFamily.
class AppTextStyles {
  AppTextStyles._();

  // Font family stack
  static const String fontFamily = 'Google Sans';
  static const List<String> fontFamilyFallback = ['Noto Sans KR', 'sans-serif'];

  // Font Sizes
  static const double fontSizeXs = 12.0;
  static const double fontSizeSm = 14.0;
  static const double fontSizeBase = 16.0;
  static const double fontSizeLg = 18.0;
  static const double fontSizeXl = 20.0;
  static const double fontSize2xl = 24.0;
  static const double fontSize3xl = 30.0;

  // Font Weights
  static const FontWeight fontWeightNormal = FontWeight.w500;
  static const FontWeight fontWeightMedium = FontWeight.w600;
  static const FontWeight fontWeightSemibold = FontWeight.w700;
  static const FontWeight fontWeightBold = FontWeight.w800;

  // ──────────────────────────────────────────
  // Text Styles
  // fontFamily / fontFamilyFallback is set at theme level,
  // so individual styles don't need to repeat it.
  // ──────────────────────────────────────────

  static const TextStyle h1 = TextStyle(
    fontSize: fontSize3xl,
    fontWeight: fontWeightBold,
    height: 1.3,
  );

  static const TextStyle h2 = TextStyle(
    fontSize: fontSize2xl,
    fontWeight: fontWeightBold,
    height: 1.3,
  );

  static const TextStyle h3 = TextStyle(
    fontSize: fontSizeXl,
    fontWeight: fontWeightSemibold,
    height: 1.4,
  );

  static const TextStyle h4 = TextStyle(
    fontSize: fontSizeLg,
    fontWeight: fontWeightSemibold,
    height: 1.4,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: fontSizeBase,
    fontWeight: fontWeightNormal,
    height: 1.5,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: fontSizeSm,
    fontWeight: fontWeightNormal,
    height: 1.5,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: fontSizeXs,
    fontWeight: fontWeightNormal,
    height: 1.5,
  );

  static const TextStyle labelLarge = TextStyle(
    fontSize: fontSizeBase,
    fontWeight: fontWeightMedium,
    height: 1.2,
  );

  static const TextStyle labelMedium = TextStyle(
    fontSize: fontSizeSm,
    fontWeight: fontWeightMedium,
    height: 1.2,
  );

  static const TextStyle labelSmall = TextStyle(
    fontSize: fontSizeXs,
    fontWeight: fontWeightMedium,
    height: 1.2,
  );

  static const TextStyle button = TextStyle(
    fontSize: fontSizeBase,
    fontWeight: fontWeightSemibold,
    height: 1.0,
  );

  // Aliases for backward compatibility
  static const TextStyle body1 = bodyLarge;
  static const TextStyle body2 = bodyMedium;
  static const TextStyle label1 = labelLarge;
  static const TextStyle label2 = labelMedium;
  static const TextStyle label3 = labelSmall;
}
