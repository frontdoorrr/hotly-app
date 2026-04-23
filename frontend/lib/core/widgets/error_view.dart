import 'package:flutter/material.dart';
import '../l10n/l10n_extension.dart';
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
    return _LocalizedNetworkErrorView(onRetry: onRetry);
  }

  /// Server error
  factory ErrorView.server({VoidCallback? onRetry}) {
    return _LocalizedServerErrorView(onRetry: onRetry);
  }

  /// Not found error
  factory ErrorView.notFound() {
    return const _LocalizedNotFoundErrorView();
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
                label: Text(context.l10n.error_retry),
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

class _LocalizedNetworkErrorView extends ErrorView {
  const _LocalizedNetworkErrorView({VoidCallback? onRetry})
      : super(message: '', icon: Icons.wifi_off, onRetry: onRetry);

  @override
  Widget build(BuildContext context) {
    return ErrorView(
      message: context.l10n.error_networkCheck,
      icon: Icons.wifi_off,
      onRetry: onRetry,
    );
  }
}

class _LocalizedServerErrorView extends ErrorView {
  const _LocalizedServerErrorView({VoidCallback? onRetry})
      : super(message: '', icon: Icons.cloud_off, onRetry: onRetry);

  @override
  Widget build(BuildContext context) {
    return ErrorView(
      message: context.l10n.error_serverProblem,
      icon: Icons.cloud_off,
      onRetry: onRetry,
    );
  }
}

class _LocalizedNotFoundErrorView extends ErrorView {
  const _LocalizedNotFoundErrorView()
      : super(message: '', icon: Icons.search_off);

  @override
  Widget build(BuildContext context) {
    return ErrorView(
      message: context.l10n.error_dataNotFound,
      icon: Icons.search_off,
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
    return _LocalizedSearchEmptyView(query: query);
  }

  /// Empty places list
  factory EmptyView.places({VoidCallback? onAddPlace}) {
    return _LocalizedPlacesEmptyView(onAddPlace: onAddPlace);
  }

  /// Empty courses list
  factory EmptyView.courses({VoidCallback? onCreateCourse}) {
    return _LocalizedCoursesEmptyView(onCreateCourse: onCreateCourse);
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
              style: AppTextStyles.h3.copyWith(
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

class _LocalizedSearchEmptyView extends EmptyView {
  final String? query;
  const _LocalizedSearchEmptyView({this.query})
      : super(message: '', icon: Icons.search_off);

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return EmptyView(
      message: query != null
          ? l10n.error_searchNoResults(query!)
          : l10n.error_searchEmpty,
      subtitle: l10n.error_searchTryOther,
      icon: Icons.search_off,
    );
  }
}

class _LocalizedPlacesEmptyView extends EmptyView {
  final VoidCallback? onAddPlace;
  const _LocalizedPlacesEmptyView({this.onAddPlace})
      : super(message: '', icon: Icons.place_outlined);

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return EmptyView(
      message: l10n.error_noSavedPlaces,
      subtitle: l10n.error_savePlacePrompt,
      icon: Icons.place_outlined,
      onAction: onAddPlace,
      actionLabel: l10n.error_browsePlaces,
    );
  }
}

class _LocalizedCoursesEmptyView extends EmptyView {
  final VoidCallback? onCreateCourse;
  const _LocalizedCoursesEmptyView({this.onCreateCourse})
      : super(message: '', icon: Icons.route_outlined);

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return EmptyView(
      message: l10n.error_noCourses,
      subtitle: l10n.error_createCoursePrompt,
      icon: Icons.route_outlined,
      onAction: onCreateCourse,
      actionLabel: l10n.error_createCourse,
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
