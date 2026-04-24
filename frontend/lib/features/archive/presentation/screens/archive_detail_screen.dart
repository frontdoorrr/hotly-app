import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/archived_content.dart';
import '../providers/archive_provider.dart';
import '../widgets/archive_result_card.dart';

/// 상세 화면 재분석 진행 여부 (로컬 UI 상태)
final _reanalyzingProvider = StateProvider.autoDispose<bool>((_) => false);

class ArchiveDetailScreen extends ConsumerWidget {
  final String archiveId;

  const ArchiveDetailScreen({super.key, required this.archiveId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncValue = ref.watch(archiveDetailProvider(archiveId));
    final l10n = context.l10n;

    return asyncValue.when(
      loading: () => Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              Text(l10n.archive_cannotLoad, style: AppTextStyles.body2),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => ref.invalidate(archiveDetailProvider(archiveId)),
                child: Text(l10n.error_retry),
              ),
            ],
          ),
        ),
      ),
      data: (content) => _DetailView(content: content),
    );
  }
}

class _DetailView extends ConsumerWidget {
  final ArchivedContent content;

  const _DetailView({required this.content});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = context.l10n;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          content.title ?? l10n.archive_detailTitle,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: l10n.archive_delete,
            onPressed: () => _confirmDelete(context, ref),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ArchiveResultCard(content: content, compact: false),

            // 앱 언어와 저장된 콘텐츠 언어가 다를 때 재분석 옵션 제공
            _LanguageMismatchBanner(content: content),

            const SizedBox(height: 16),

            // insights (장소 타입은 숨김)
            if (content.contentType != 'place' &&
                content.insights.isNotEmpty) ...[
              _SectionTitle(l10n.archive_insights),
              const SizedBox(height: 8),
              ...content.insights.map(
                (insight) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.lightbulb_outline,
                          size: 16, color: AppColors.primary),
                      const SizedBox(width: 6),
                      Expanded(
                          child: Text(insight, style: AppTextStyles.body2)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // 키워드 서브
            if (content.keywordsSub.isNotEmpty) ...[
              _SectionTitle(l10n.archive_relatedKeywords),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  ...content.keywordsMain.map((k) => _Chip(k, primary: true)),
                  ...content.keywordsSub.map((k) => _Chip(k)),
                ],
              ),
              const SizedBox(height: 16),
            ],

            // 아카이빙 메타
            _buildMeta(context),

            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: _BottomBar(url: content.url),
    );
  }

  Widget _buildMeta(BuildContext context) {
    final l10n = context.l10n;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        children: [
          _MetaRow(
            label: l10n.archive_platform,
            value: _platformLabel(context, content.platform),
          ),
          if (content.author != null)
            _MetaRow(label: l10n.archive_author, value: content.author!),
          if (content.publishedAt != null)
            _MetaRow(
              label: l10n.archive_publishedAt,
              value: _formatDate(content.publishedAt!),
            ),
          _MetaRow(
            label: l10n.archive_archivedAt,
            value: _formatDate(content.archivedAt),
          ),
          _MetaRow(
            label: 'URL',
            value: content.url,
            onTap: () {
              Clipboard.setData(ClipboardData(text: content.url));
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(l10n.archive_urlCopied),
                  duration: const Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  String _platformLabel(BuildContext context, Platform p) => switch (p) {
        Platform.youtube => 'YouTube',
        Platform.instagram => 'Instagram',
        Platform.naver_blog => context.l10n.archive_platformNaverBlog,
      };

  String _formatDate(DateTime dt) =>
      '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final l10n = context.l10n;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l10n.archive_deleteConfirmTitle),
        content: Text(l10n.archive_deleteConfirmBody),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(l10n.common_cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(l10n.archive_delete,
                style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      await ref.read(archiveListProvider.notifier).delete(content.id);
      if (context.mounted) Navigator.of(context).pop();
    }
  }
}

// ------------------------------------------------------------------
// Bottom bar — 원본 링크 열기
// ------------------------------------------------------------------

class _BottomBar extends StatelessWidget {
  final String url;
  const _BottomBar({required this.url});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: ElevatedButton.icon(
          onPressed: () => _openUrl(context),
          icon: const Icon(Icons.open_in_new, size: 18),
          label: Text(l10n.archive_openOriginalLink),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _openUrl(BuildContext context) async {
    final uri = Uri.tryParse(url);
    if (uri == null || !await canLaunchUrl(uri)) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.archive_cannotOpenLink)),
        );
      }
      return;
    }
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

// ------------------------------------------------------------------
// 공통 소형 위젯들
// ------------------------------------------------------------------

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) =>
      Text(text, style: AppTextStyles.h4);
}

class _Chip extends StatelessWidget {
  final String label;
  final bool primary;
  const _Chip(this.label, {this.primary = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: primary
            ? AppColors.primary.withOpacity(0.1)
            : Colors.grey[100],
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        '#$label',
        style: AppTextStyles.bodySmall.copyWith(
          color: primary ? AppColors.primary : AppColors.textSecondary,
        ),
      ),
    );
  }
}

class _LanguageMismatchBanner extends ConsumerWidget {
  final ArchivedContent content;
  const _LanguageMismatchBanner({required this.content});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stored = content.language;
    if (stored == null || stored.isEmpty) return const SizedBox.shrink();
    final current = Localizations.localeOf(context).languageCode;
    if (stored == current) return const SizedBox.shrink();

    final l10n = context.l10n;
    final isLoading = ref.watch(_reanalyzingProvider);

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.06),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.primary.withOpacity(0.25)),
        ),
        child: Row(
          children: [
            const Icon(Icons.translate, size: 18, color: AppColors.primary),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                isLoading
                    ? l10n.archive_reanalyzing
                    : l10n.archive_reanalyzeInCurrentLanguage,
                style: AppTextStyles.bodySmall
                    .copyWith(color: AppColors.textPrimary),
              ),
            ),
            if (isLoading)
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              TextButton(
                onPressed: () => _reanalyze(context, ref, current),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  minimumSize: const Size(0, 32),
                ),
                child: Text(l10n.common_apply),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _reanalyze(
    BuildContext context,
    WidgetRef ref,
    String language,
  ) async {
    ref.read(_reanalyzingProvider.notifier).state = true;
    final l10n = context.l10n;
    try {
      final repo = ref.read(archiveRepositoryProvider);
      final result =
          await repo.archiveUrl(content.url, force: true, language: language);
      if (!context.mounted) return;
      result.fold(
        (error) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(l10n.archive_reanalyzeFailed)),
          );
        },
        (_) {
          ref.invalidate(archiveDetailProvider(content.id));
          ref.invalidate(recentArchiveProvider);
          ref.read(archiveListProvider.notifier).load(refresh: true);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(l10n.archive_reanalyzeSuccess)),
          );
        },
      );
    } finally {
      if (context.mounted) {
        ref.read(_reanalyzingProvider.notifier).state = false;
      }
    }
  }
}

class _MetaRow extends StatelessWidget {
  final String label;
  final String value;
  final VoidCallback? onTap;

  const _MetaRow({required this.label, required this.value, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 60,
            child: Text(
              label,
              style: AppTextStyles.bodySmall
                  .copyWith(color: AppColors.textSecondary),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: onTap,
              child: Text(
                value,
                style: AppTextStyles.bodySmall.copyWith(
                  color: onTap != null ? AppColors.primary : AppColors.textPrimary,
                  decoration: onTap != null ? TextDecoration.underline : null,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
