import 'package:flutter/material.dart';

/// App Color Palette — ArchyAI Dark Theme
class AppColors {
  AppColors._();

  // ──────────────────────────────────────────
  // Brand — Teal
  // ──────────────────────────────────────────
  static const Color teal400 = Color(0xFF1D9E75); // 브랜드 메인
  static const Color teal600 = Color(0xFF0D7A57); // 버튼 hover / secondary
  static const Color brandSubtle = Color(0xFF0A2318); // 연한 브랜드 배경

  // Primary aliases
  static const Color primary = teal400;
  static const Color primaryLight = brandSubtle;
  static const Color primary50 = brandSubtle;
  static const Color primary100 = brandSubtle;
  static const Color primary500 = teal400;
  static const Color primary600 = teal600;
  static const Color primary900 = Color(0xFF07150F);

  // ──────────────────────────────────────────
  // Semantic
  // ──────────────────────────────────────────
  static const Color success = Color(0xFF38A169);
  static const Color warning = Color(0xFFD69E2E);
  static const Color error = Color(0xFFE53E3E);
  static const Color info = Color(0xFF3182CE);

  // ──────────────────────────────────────────
  // Dark Background Scale
  // ──────────────────────────────────────────
  static const Color bgBase = Color(0xFF090C10);       // 최하층 배경
  static const Color bgElevated = Color(0xFF0D1118);   // 살짝 올라온 배경
  static const Color surfaceDefault = Color(0xFF141620); // 카드 / 시트 배경
  static const Color borderSubtle = Color(0xFF1A2030);  // 구분선 / 보더

  // Gray scale aliases (backward compat)
  static const Color gray50 = bgElevated;
  static const Color gray100 = Color(0xFF111620);
  static const Color gray200 = borderSubtle;
  static const Color gray500 = Color(0xFF5A7A72);
  static const Color gray700 = surfaceDefault;
  static const Color gray900 = bgBase;

  // ──────────────────────────────────────────
  // Common
  // ──────────────────────────────────────────
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // ──────────────────────────────────────────
  // Text (dark-theme optimized)
  // ──────────────────────────────────────────
  static const Color textPrimary = Color(0xFFD4EEE8);
  static const Color textSecondary = Color(0xFF8AADA6);
  static const Color textTertiary = Color(0xFF5A7A72);

  // Legacy aliases
  static const Color textPrimaryLight = textPrimary;
  static const Color textSecondaryLight = textSecondary;
  static const Color textPrimaryDark = textPrimary;
  static const Color textSecondaryDark = textSecondary;

  // ──────────────────────────────────────────
  // Background / Surface aliases
  // ──────────────────────────────────────────
  static const Color background = bgBase;
  static const Color surface = surfaceDefault;
  static const Color backgroundLight = bgElevated;
  static const Color backgroundDark = bgBase;
  static const Color cardLight = surfaceDefault;
  static const Color cardDark = surfaceDefault;

  // ──────────────────────────────────────────
  // Border aliases
  // ──────────────────────────────────────────
  static const Color border = borderSubtle;
  static const Color borderLight = borderSubtle;
  static const Color borderDark = borderSubtle;
}
