import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';

/// Error View Widget - 에러 상태 표시
class ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  final IconData icon;

  const ErrorView({
    super.key,
    required this.message,
    this.onRetry,
    this.icon = Icons.error_outline,
  });

  /// Network error
  factory ErrorView.network({VoidCallback? onRetry}) {
    return ErrorView(
      message: '네트워크 연결을 확인해주세요',
      icon: Icons.wifi_off,
      onRetry: onRetry,
    );
  }

  /// Server error
  factory ErrorView.server({VoidCallback? onRetry}) {
    return ErrorView(
      message: '서버에 문제가 발생했습니다\n잠시 후 다시 시도해주세요',
      icon: Icons.cloud_off,
      onRetry: onRetry,
    );
  }

  /// Not found error
  factory ErrorView.notFound() {
    return const ErrorView(
      message: '요청하신 데이터를 찾을 수 없습니다',
      icon: Icons.search_off,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: AppColors.error,
            ),
            const SizedBox(height: 24),
            Text(
              message,
              style: AppTextStyles.body1.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('다시 시도'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Empty State View Widget - 빈 상태 표시
class EmptyView extends StatelessWidget {
  final String message;
  final String? subtitle;
  final IconData icon;
  final VoidCallback? onAction;
  final String? actionLabel;

  const EmptyView({
    super.key,
    required this.message,
    this.subtitle,
    this.icon = Icons.inbox_outlined,
    this.onAction,
    this.actionLabel,
  });

  /// Empty search results
  factory EmptyView.search({String? query}) {
    return EmptyView(
      message: query != null ? '"$query"에 대한 검색 결과가 없습니다' : '검색 결과가 없습니다',
      subtitle: '다른 키워드로 검색해보세요',
      icon: Icons.search_off,
    );
  }

  /// Empty places list
  factory EmptyView.places({VoidCallback? onAddPlace}) {
    return EmptyView(
      message: '저장된 장소가 없습니다',
      subtitle: '마음에 드는 장소를 저장해보세요',
      icon: Icons.place_outlined,
      onAction: onAddPlace,
      actionLabel: '장소 찾아보기',
    );
  }

  /// Empty courses list
  factory EmptyView.courses({VoidCallback? onCreateCourse}) {
    return EmptyView(
      message: '생성된 코스가 없습니다',
      subtitle: '나만의 데이트 코스를 만들어보세요',
      icon: Icons.route_outlined,
      onAction: onCreateCourse,
      actionLabel: '코스 만들기',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 80,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 24),
            Text(
              message,
              style: AppTextStyles.heading3.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 8),
              Text(
                subtitle!,
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.textTertiary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (onAction != null && actionLabel != null) ...[
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: onAction,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                ),
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Loading View Widget - 로딩 상태 표시
class LoadingView extends StatelessWidget {
  final String? message;

  const LoadingView({
    super.key,
    this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(
              message!,
              style: AppTextStyles.body2.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
