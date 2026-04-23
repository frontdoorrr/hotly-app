import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../providers/archive_provider.dart';
import 'archive_result_card.dart';

String _localizeError(BuildContext context, String code) {
  final l10n = context.l10n;
  switch (code) {
    case 'error_unsupportedLink':    return l10n.error_unsupportedLink;
    case 'error_accessDenied':       return l10n.error_accessDenied;
    case 'error_archiveNotFound':    return l10n.error_archiveNotFound;
    case 'error_privateOrDeleted':   return l10n.error_privateOrDeleted;
    case 'error_rateLimited':        return l10n.error_rateLimited;
    case 'error_serviceUnavailable': return l10n.error_serviceUnavailable;
    default:                         return l10n.error_unknown;
  }
}

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
  final _sheetController = DraggableScrollableController();

  @override
  void initState() {
    super.initState();
    _checkClipboard();
  }

  @override
  void dispose() {
    _controller.dispose();
    _sheetController.dispose();
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

    ref.listen<ArchiveInputState>(archiveInputProvider, (prev, next) {
      if (prev?.result == null && next.result != null) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted || !_sheetController.isAttached) return;
          _sheetController.animateTo(
            0.9,
            duration: const Duration(milliseconds: 400),
            curve: Curves.easeInOut,
          );
        });
      }
    });

    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      controller: _sheetController,
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
                    Text(context.l10n.archiveInput_title, style: AppTextStyles.h2),
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

              // 폼 ↔ 결과 전환 (AnimatedSwitcher)
              Expanded(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  transitionBuilder: (child, animation) => FadeTransition(
                    opacity: animation,
                    child: SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(0, 0.04),
                        end: Offset.zero,
                      ).animate(CurvedAnimation(
                        parent: animation,
                        curve: Curves.easeOut,
                      )),
                      child: child,
                    ),
                  ),
                  child: hasResult
                      ? KeyedSubtree(
                          key: const ValueKey('result'),
                          child: SingleChildScrollView(
                            controller: hasResult ? scrollController : null,
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
                                    child: Text(context.l10n.archiveInput_doneButton),
                                  ),
                                ),
                                const SizedBox(height: 24),
                              ],
                            ),
                          ),
                        )
                      : KeyedSubtree(
                          key: const ValueKey('form'),
                          child: SingleChildScrollView(
                            controller: hasResult ? null : scrollController,
                            padding: EdgeInsets.fromLTRB(20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 16),
                            child: Form(
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    context.l10n.archiveInput_supportedPlatforms,
                                    style: AppTextStyles.body2.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  TextFormField(
                                    controller: _controller,
                                    decoration: InputDecoration(
                                      hintText: 'https://instagram.com/p/...',
                                      hintStyle: const TextStyle(color: Color(0xFFBDBDBD)),
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
                                      if (v == null || v.isEmpty) return context.l10n.archiveInput_urlRequired;
                                      if (!_isValidUrl(v)) return context.l10n.archiveInput_urlInvalid;
                                      return null;
                                    },
                                    onChanged: (v) =>
                                        ref.read(archiveInputProvider.notifier).setInputUrl(v),
                                    onFieldSubmitted: (_) => _submit(),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    context.l10n.archiveInput_supportedPlatforms,
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
                                                valueColor: AlwaysStoppedAnimation(Colors.white),
                                              ),
                                            )
                                          : Text(context.l10n.archiveInput_archiveButton),
                                    ),
                                  ),
                                  // 에러
                                  AnimatedSwitcher(
                                    duration: const Duration(milliseconds: 200),
                                    child: (state.error != null)
                                        ? Padding(
                                            key: const ValueKey('error'),
                                            padding: const EdgeInsets.only(top: 12),
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
                                                      _localizeError(context, state.error!),
                                                      style: AppTextStyles.body2
                                                          .copyWith(color: Colors.red[700]),
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          )
                                        : const SizedBox.shrink(key: ValueKey('no-error')),
                                  ),
                                ],
                              ),
                            ),
                          ),
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
