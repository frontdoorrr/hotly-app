import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../providers/link_analysis_provider.dart';
import 'link_analysis_result_view.dart';

/// Bottom sheet for link input and analysis
class LinkInputBottomSheet extends ConsumerStatefulWidget {
  const LinkInputBottomSheet({super.key});

  @override
  ConsumerState<LinkInputBottomSheet> createState() =>
      _LinkInputBottomSheetState();

  /// Show the bottom sheet
  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const LinkInputBottomSheet(),
    );
  }
}

class _LinkInputBottomSheetState extends ConsumerState<LinkInputBottomSheet> {
  final _textController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _checkClipboard();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  /// Check clipboard for URL and auto-fill
  Future<void> _checkClipboard() async {
    try {
      final clipboardData = await Clipboard.getData(Clipboard.kTextPlain);
      final text = clipboardData?.text ?? '';

      if (text.isNotEmpty && _isValidUrl(text)) {
        _textController.text = text;
        ref.read(linkAnalysisProvider.notifier).setInputUrl(text);
      }
    } catch (e) {
      // Clipboard access failed, ignore
    }
  }

  bool _isValidUrl(String text) {
    final urlPattern = RegExp(
      r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
    );
    return urlPattern.hasMatch(text);
  }

  void _analyzeLink() {
    if (_formKey.currentState?.validate() ?? false) {
      ref
          .read(linkAnalysisProvider.notifier)
          .analyzeUrl(_textController.text.trim());
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(linkAnalysisProvider);
    final hasResult = state.result != null;

    return DraggableScrollableSheet(
      initialChildSize: hasResult ? 0.9 : 0.5,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(20),
            ),
          ),
          child: Column(
            children: [
              // Handle bar
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
                padding: const EdgeInsets.all(20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '링크 분석',
                      style: AppTextStyles.h2,
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () {
                        ref.read(linkAnalysisProvider.notifier).clearAnalysis();
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
                        controller: _textController,
                        decoration: InputDecoration(
                          hintText: 'https://instagram.com/p/...',
                          prefixIcon: const Icon(Icons.link),
                          suffixIcon: _textController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    _textController.clear();
                                    ref
                                        .read(linkAnalysisProvider.notifier)
                                        .setInputUrl('');
                                  },
                                )
                              : null,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'URL을 입력해주세요';
                          }
                          if (!_isValidUrl(value)) {
                            return '유효한 URL을 입력해주세요';
                          }
                          return null;
                        },
                        onChanged: (value) {
                          ref
                              .read(linkAnalysisProvider.notifier)
                              .setInputUrl(value);
                        },
                        onFieldSubmitted: (_) => _analyzeLink(),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '지원: Instagram, Naver Blog, YouTube',
                        style: AppTextStyles.bodySmall.copyWith(
                          color: AppColors.textTertiary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: state.isLoading ? null : _analyzeLink,
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
                                    valueColor: AlwaysStoppedAnimation<Color>(
                                      Colors.white,
                                    ),
                                  ),
                                )
                              : const Text('분석하기'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Result view
              if (hasResult)
                Expanded(
                  child: LinkAnalysisResultView(
                    scrollController: scrollController,
                  ),
                ),

              // Error message
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
                            style: AppTextStyles.body2.copyWith(
                              color: Colors.red[700],
                            ),
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
