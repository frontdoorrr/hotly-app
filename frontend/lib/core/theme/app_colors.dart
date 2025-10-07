import 'package:flutter/material.dart';

/// App Color Palette
/// Based on design system color tokens
class AppColors {
  AppColors._();

  // Primary Colors
  static const Color primary50 = Color(0xFFFFF5F5);
  static const Color primary100 = Color(0xFFFED7D7);
  static const Color primary500 = Color(0xFFE53E3E); // Main brand color
  static const Color primary600 = Color(0xFFC53030);
  static const Color primary900 = Color(0xFF742A2A);

  // Primary alias
  static const Color primary = primary500;
  static const Color primaryLight = primary50;

  // Semantic Colors
  static const Color success = Color(0xFF38A169);
  static const Color warning = Color(0xFFD69E2E);
  static const Color error = Color(0xFFE53E3E);
  static const Color info = Color(0xFF3182CE);

  // Neutral Colors
  static const Color gray50 = Color(0xFFF7FAFC);
  static const Color gray100 = Color(0xFFEDF2F7);
  static const Color gray200 = Color(0xFFE2E8F0);
  static const Color gray500 = Color(0xFFA0ADB8);
  static const Color gray700 = Color(0xFF2D3748);
  static const Color gray900 = Color(0xFF1A202C);

  // Common Colors
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // Background Colors
  static const Color backgroundLight = gray50;
  static const Color backgroundDark = gray900;
  static const Color cardLight = white;
  static const Color cardDark = gray700;

  // Text Colors
  static const Color textPrimaryLight = gray900;
  static const Color textSecondaryLight = gray500;
  static const Color textPrimaryDark = white;
  static const Color textSecondaryDark = gray200;

  // Aliases for convenience (defaults to light theme)
  static const Color textPrimary = textPrimaryLight;
  static const Color textSecondary = textSecondaryLight;
  static const Color textTertiary = gray500; // Tertiary text color
  static const Color background = backgroundLight;
  static const Color surface = cardLight;

  // Border Colors
  static const Color borderLight = gray200;
  static const Color borderDark = gray700;

  // Alias for convenience (defaults to light theme)
  static const Color border = borderLight;
}
