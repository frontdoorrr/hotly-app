import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../providers/archive_provider.dart';
import 'archive_result_card.dart';

/// URL 입력 + 분석 결과 표시 바텀시트
class ArchiveInputSheet extends ConsumerStatefulWidget {
  const ArchiveInputSheet({super.key});

  @override
  ConsumerState<ArchiveInputSheet> createState() => _ArchiveInputSheetState();

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const ArchiveInputSheet(),
    );
  }
}

class _ArchiveInputSheetState extends ConsumerState<ArchiveInputSheet> {
  final _controller = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _checkClipboard();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _checkClipboard() async {
    try {
      final data = await Clipboard.getData(Clipboard.kTextPlain);
      final text = data?.text ?? '';
      if (text.isNotEmpty && _isValidUrl(text)) {
        _controller.text = text;
        ref.read(archiveInputProvider.notifier).setInputUrl(text);
      }
    } catch (_) {}
  }

  bool _isValidUrl(String text) {
    final pattern = RegExp(
      r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
    );
    return pattern.hasMatch(text);
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(archiveInputProvider.notifier).archiveUrl(_controller.text.trim());
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(archiveInputProvider);
    final hasResult = state.result != null;

    return DraggableScrollableSheet(
      initialChildSize: hasResult ? 0.9 : 0.5,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: const EdgeInsets.only(top: 12, bottom: 8),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('링크 아카이브', style: AppTextStyles.h2),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () {
                        ref.read(archiveInputProvider.notifier).clear();
                        Navigator.of(context).pop();
                      },
                    ),
                  ],
                ),
              ),

              // Input form
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SNS 링크를 붙여넣으세요',
                        style: AppTextStyles.body2.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _controller,
                        decoration: InputDecoration(
                          hintText: 'https://instagram.com/p/...',
                          prefixIcon: const Icon(Icons.link),
                          suffixIcon: _controller.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    _controller.clear();
                                    ref.read(archiveInputProvider.notifier).setInputUrl('');
                                  },
                                )
                              : null,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        validator: (v) {
                          if (v == null || v.isEmpty) return 'URL을 입력해주세요';
                          if (!_isValidUrl(v)) return '유효한 URL을 입력해주세요';
                          return null;
                        },
                        onChanged: (v) =>
                            ref.read(archiveInputProvider.notifier).setInputUrl(v),
                        onFieldSubmitted: (_) => _submit(),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '지원: Instagram · Naver Blog · YouTube',
                        style: AppTextStyles.bodySmall
                            .copyWith(color: AppColors.textTertiary),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: state.isLoading ? null : _submit,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: state.isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor:
                                        AlwaysStoppedAnimation(Colors.white),
                                  ),
                                )
                              : const Text('아카이브'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // 결과
              if (hasResult)
                Expanded(
                  child: SingleChildScrollView(
                    controller: scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ArchiveResultCard(content: state.result!),
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton(
                            onPressed: () {
                              // 아카이빙 완료 — 목록 새로고침 후 닫기
                              ref
                                  .read(archiveListProvider.notifier)
                                  .load(refresh: true);
                              ref.read(archiveInputProvider.notifier).clear();
                              Navigator.of(context).pop();
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            child: const Text('완료'),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
                ),

              // 에러
              if (state.error != null && !hasResult)
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.red[50],
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.red[200]!),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red[700]),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            state.error!,
                            style: AppTextStyles.body2
                                .copyWith(color: Colors.red[700]),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}
