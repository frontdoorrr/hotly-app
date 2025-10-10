import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';
import 'app_text_styles.dart';

/// App Theme Configuration
class AppTheme {
  AppTheme._();

  // Spacing System
  static const double space0 = 0.0;
  static const double space1 = 4.0;
  static const double space2 = 8.0;
  static const double space3 = 12.0;
  static const double space4 = 16.0;
  static const double space5 = 20.0;
  static const double space6 = 24.0;
  static const double space8 = 32.0;
  static const double space10 = 40.0;
  static const double space12 = 48.0;
  static const double space16 = 64.0;

  // Border Radius
  static const double radiusNone = 0.0;
  static const double radiusSm = 2.0;
  static const double radiusBase = 4.0;
  static const double radiusMd = 6.0;
  static const double radiusLg = 8.0;
  static const double radiusXl = 12.0;
  static const double radius2xl = 16.0;
  static const double radiusFull = 9999.0;

  // Light Theme
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      primaryColor: AppColors.primary500,
      scaffoldBackgroundColor: AppColors.backgroundLight,
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary500,
        onPrimary: AppColors.white,
        secondary: AppColors.primary600,
        onSecondary: AppColors.white,
        error: AppColors.error,
        onError: AppColors.white,
        surface: AppColors.cardLight,
        onSurface: AppColors.textPrimaryLight,
      ),
      textTheme: GoogleFonts.notoSansKrTextTheme(
        TextTheme(
          displayLarge: AppTextStyles.h1,
          displayMedium: AppTextStyles.h2,
          displaySmall: AppTextStyles.h3,
          headlineMedium: AppTextStyles.h4,
          titleLarge: AppTextStyles.h3, // 섹션 제목용 (오늘의 추천, 인기 장소 등)
          bodyLarge: AppTextStyles.bodyLarge,
          bodyMedium: AppTextStyles.bodyMedium,
          bodySmall: AppTextStyles.bodySmall,
          labelLarge: AppTextStyles.labelLarge,
          labelMedium: AppTextStyles.labelMedium,
          labelSmall: AppTextStyles.labelSmall,
        ),
      ),
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.textPrimaryLight,
        systemOverlayStyle: SystemUiOverlayStyle.dark,
        titleTextStyle: GoogleFonts.notoSansKr(
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.cardLight,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusLg),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary500,
          foregroundColor: AppColors.white,
          textStyle: AppTextStyles.button,
          padding: const EdgeInsets.symmetric(
            horizontal: space6,
            vertical: space4,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusLg),
          ),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary500,
          textStyle: AppTextStyles.button,
          padding: const EdgeInsets.symmetric(
            horizontal: space6,
            vertical: space4,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusLg),
          ),
          side: const BorderSide(
            color: AppColors.primary500,
            width: 1.5,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primary500,
          textStyle: AppTextStyles.button,
          padding: const EdgeInsets.symmetric(
            horizontal: space4,
            vertical: space3,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.gray50,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          borderSide: const BorderSide(color: AppColors.borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          borderSide: const BorderSide(color: AppColors.borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          borderSide: const BorderSide(
            color: AppColors.primary500,
            width: 2,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          borderSide: const BorderSide(color: AppColors.error),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: space4,
          vertical: space3,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.white,
        selectedItemColor: AppColors.primary500,
        unselectedItemColor: AppColors.gray500,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }

  // Dark Theme
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      primaryColor: AppColors.primary500,
      scaffoldBackgroundColor: AppColors.backgroundDark,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.primary500,
        onPrimary: AppColors.white,
        secondary: AppColors.primary600,
        onSecondary: AppColors.white,
        error: AppColors.error,
        onError: AppColors.white,
        surface: AppColors.cardDark,
        onSurface: AppColors.textPrimaryDark,
      ),
      textTheme: GoogleFonts.notoSansKrTextTheme(
        TextTheme(
          displayLarge: AppTextStyles.h1,
          displayMedium: AppTextStyles.h2,
          displaySmall: AppTextStyles.h3,
          headlineMedium: AppTextStyles.h4,
          titleLarge: AppTextStyles.h3, // 섹션 제목용 (오늘의 추천, 인기 장소 등)
          bodyLarge: AppTextStyles.bodyLarge,
          bodyMedium: AppTextStyles.bodyMedium,
          bodySmall: AppTextStyles.bodySmall,
          labelLarge: AppTextStyles.labelLarge,
          labelMedium: AppTextStyles.labelMedium,
          labelSmall: AppTextStyles.labelSmall,
        ),
      ),
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: AppColors.cardDark,
        foregroundColor: AppColors.textPrimaryDark,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: GoogleFonts.notoSansKr(
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.cardDark,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusLg),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.cardDark,
        selectedItemColor: AppColors.primary500,
        unselectedItemColor: AppColors.gray500,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }
}
