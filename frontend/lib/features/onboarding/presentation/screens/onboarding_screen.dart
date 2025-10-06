import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/atoms/app_button.dart';
import '../providers/onboarding_provider.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final PageController _pageController = PageController();

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onPageChanged(int page) {
    ref.read(onboardingProvider.notifier).goToStep(page);
  }

  Future<void> _handleComplete() async {
    await ref.read(onboardingProvider.notifier).completeOnboarding();
    if (!mounted) return;
    context.go('/');
  }

  void _handleSkip() {
    ref.read(onboardingProvider.notifier).skipOnboarding();
    context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final onboardingState = ref.watch(onboardingProvider);

    return Scaffold(
      appBar: AppBar(
        actions: [
          TextButton(
            onPressed: _handleSkip,
            child: Text(
              'Skip',
              style: AppTextStyles.button.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Progress Indicator
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: List.generate(4, (index) {
                return Expanded(
                  child: Container(
                    height: 4,
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    decoration: BoxDecoration(
                      color: index <= onboardingState.currentStep
                          ? AppColors.primary
                          : AppColors.border,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                );
              }),
            ),
          ),

          // PageView
          Expanded(
            child: PageView(
              controller: _pageController,
              onPageChanged: _onPageChanged,
              children: [
                _WelcomeStep(),
                _InterestsStep(),
                _LocationPermissionStep(),
                _NotificationPermissionStep(),
              ],
            ),
          ),

          // Navigation Buttons
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                if (onboardingState.currentStep > 0)
                  Expanded(
                    child: AppButton(
                      text: '이전',
                      type: AppButtonType.outline,
                      onPressed: () {
                        _pageController.previousPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      },
                    ),
                  ),
                if (onboardingState.currentStep > 0) const SizedBox(width: 12),
                Expanded(
                  child: AppButton(
                    text: onboardingState.currentStep == 3 ? '시작하기' : '다음',
                    type: AppButtonType.primary,
                    onPressed: () {
                      if (onboardingState.currentStep == 3) {
                        _handleComplete();
                      } else {
                        _pageController.nextPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _WelcomeStep extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.local_fire_department,
            size: 120,
            color: AppColors.primary,
          ),
          const SizedBox(height: 32),
          Text(
            'Hotly에 오신 것을 환영합니다!',
            style: AppTextStyles.h1.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            'AI가 추천하는 핫플레이스와\n나만의 데이트 코스를 만들어보세요',
            style: AppTextStyles.body1.copyWith(
              color: AppColors.textSecondary,
              height: 1.6,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _InterestsStep extends ConsumerWidget {
  final List<String> interests = [
    '카페',
    '맛집',
    '데이트',
    '뷰맛집',
    '감성',
    '힐링',
    '액티비티',
    '쇼핑',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedInterests = ref.watch(
      onboardingProvider.select((s) => s.selectedInterests),
    );

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '관심사를 선택해주세요',
            style: AppTextStyles.h2.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '선택한 관심사를 바탕으로 맞춤 장소를 추천해드려요',
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: interests.map((interest) {
              final isSelected = selectedInterests.contains(interest);
              return ChoiceChip(
                label: Text(interest),
                selected: isSelected,
                onSelected: (_) {
                  ref
                      .read(onboardingProvider.notifier)
                      .toggleInterest(interest);
                },
                selectedColor: AppColors.primary,
                labelStyle: AppTextStyles.button.copyWith(
                  color: isSelected ? Colors.white : AppColors.textPrimary,
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _LocationPermissionStep extends ConsumerWidget {
  Future<void> _requestLocationPermission(WidgetRef ref) async {
    final status = await Permission.location.request();
    ref
        .read(onboardingProvider.notifier)
        .setLocationPermission(status.isGranted);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final granted = ref.watch(
      onboardingProvider.select((s) => s.locationPermissionGranted),
    );

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.location_on,
            size: 100,
            color: granted ? AppColors.success : AppColors.primary,
          ),
          const SizedBox(height: 32),
          Text(
            '위치 권한',
            style: AppTextStyles.h2.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            '현재 위치 주변의 핫플레이스를\n추천해드리기 위해 위치 권한이 필요해요',
            style: AppTextStyles.body1.copyWith(
              color: AppColors.textSecondary,
              height: 1.6,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          AppButton(
            text: granted ? '권한 허용됨 ✓' : '위치 권한 허용',
            type: granted ? AppButtonType.secondary : AppButtonType.primary,
            onPressed: granted ? null : () => _requestLocationPermission(ref),
          ),
          const SizedBox(height: 16),
          TextButton(
            onPressed: () {
              // Skip this step
              ref.read(onboardingProvider.notifier).nextStep();
            },
            child: Text(
              '나중에 설정하기',
              style: AppTextStyles.button.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NotificationPermissionStep extends ConsumerWidget {
  Future<void> _requestNotificationPermission(WidgetRef ref) async {
    final status = await Permission.notification.request();
    ref
        .read(onboardingProvider.notifier)
        .setNotificationPermission(status.isGranted);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final granted = ref.watch(
      onboardingProvider.select((s) => s.notificationPermissionGranted),
    );

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.notifications_active,
            size: 100,
            color: granted ? AppColors.success : AppColors.primary,
          ),
          const SizedBox(height: 32),
          Text(
            '알림 권한',
            style: AppTextStyles.h2.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            '새로운 핫플레이스와 맞춤 추천 소식을\n알려드리기 위해 알림 권한이 필요해요',
            style: AppTextStyles.body1.copyWith(
              color: AppColors.textSecondary,
              height: 1.6,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          AppButton(
            text: granted ? '권한 허용됨 ✓' : '알림 권한 허용',
            type: granted ? AppButtonType.secondary : AppButtonType.primary,
            onPressed:
                granted ? null : () => _requestNotificationPermission(ref),
          ),
          const SizedBox(height: 16),
          TextButton(
            onPressed: () {
              // Can still complete without notification
            },
            child: Text(
              '나중에 설정하기',
              style: AppTextStyles.button.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
