import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/dio_client.dart';
import '../../data/datasources/link_analysis_remote_datasource.dart';
import '../../data/repositories/link_analysis_repository_impl.dart';
import '../../domain/entities/link_analysis_result.dart';
import '../../domain/repositories/link_analysis_repository.dart';
import '../../domain/usecases/analyze_link.dart';

part 'link_analysis_provider.freezed.dart';

/// Link Analysis State
@freezed
class LinkAnalysisState with _$LinkAnalysisState {
  const factory LinkAnalysisState({
    LinkAnalysisResult? result,
    @Default(false) bool isLoading,
    @Default(false) bool isPolling,
    String? error,
    String? inputUrl,
  }) = _LinkAnalysisState;
}

/// Link Analysis State Notifier
class LinkAnalysisNotifier extends StateNotifier<LinkAnalysisState> {
  final AnalyzeLink _analyzeLink;
  final LinkAnalysisRepository _repository;

  LinkAnalysisNotifier(this._analyzeLink, this._repository)
      : super(const LinkAnalysisState());

  /// Analyze a URL
  Future<void> analyzeUrl(String url, {bool forceRefresh = false}) async {
    state = state.copyWith(
      isLoading: true,
      error: null,
      inputUrl: url,
    );

    final result = await _analyzeLink(url: url, forceRefresh: forceRefresh);

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error.toString(),
        );
      },
      (analysisResult) {
        state = state.copyWith(
          isLoading: false,
          result: analysisResult,
        );

        // If analysis is in progress, start polling
        if (analysisResult.status == AnalysisStatus.inProgress) {
          _startPolling(analysisResult.analysisId);
        }
      },
    );
  }

  /// Start polling for analysis status
  Future<void> _startPolling(String analysisId) async {
    state = state.copyWith(isPolling: true);

    // Poll every 2 seconds for up to 60 seconds
    for (int i = 0; i < 30; i++) {
      await Future.delayed(const Duration(seconds: 2));

      // Stop polling if state was cleared or cancelled
      if (!mounted || !state.isPolling) {
        return;
      }

      final result = await _repository.getAnalysisStatus(analysisId);

      // Check if analysis failed
      final hasError = result.fold(
        (error) {
          state = state.copyWith(
            isPolling: false,
            error: error.toString(),
          );
          return true;
        },
        (analysisResult) {
          state = state.copyWith(result: analysisResult);

          // Stop polling if completed or failed
          if (analysisResult.status == AnalysisStatus.completed ||
              analysisResult.status == AnalysisStatus.failed) {
            state = state.copyWith(isPolling: false);
            return true;
          }
          return false;
        },
      );

      // Exit loop if analysis is done
      if (hasError) {
        return;
      }
    }

    // Timeout after 60 seconds
    if (state.isPolling) {
      state = state.copyWith(
        isPolling: false,
        error: 'Analysis timeout. Please try again.',
      );
    }
  }

  /// Cancel ongoing analysis
  Future<void> cancelAnalysis() async {
    if (state.result?.analysisId != null) {
      await _repository.cancelAnalysis(state.result!.analysisId);
    }

    state = state.copyWith(
      isPolling: false,
      isLoading: false,
    );
  }

  /// Clear current analysis
  void clearAnalysis() {
    state = const LinkAnalysisState();
  }

  /// Set input URL
  void setInputUrl(String url) {
    state = state.copyWith(inputUrl: url);
  }
}

/// Provider for LinkAnalysisRepository
final linkAnalysisRepositoryProvider = Provider<LinkAnalysisRepository>((ref) {
  final dio = ref.watch(dioProvider);
  final remoteDataSource = LinkAnalysisRemoteDataSource(dio);
  return LinkAnalysisRepositoryImpl(remoteDataSource);
});

/// Provider for AnalyzeLink use case
final analyzeLinkUseCaseProvider = Provider<AnalyzeLink>((ref) {
  final repository = ref.watch(linkAnalysisRepositoryProvider);
  return AnalyzeLink(repository);
});

/// Provider for LinkAnalysisNotifier
final linkAnalysisProvider =
    StateNotifierProvider<LinkAnalysisNotifier, LinkAnalysisState>((ref) {
  final analyzeLink = ref.watch(analyzeLinkUseCaseProvider);
  final repository = ref.watch(linkAnalysisRepositoryProvider);
  return LinkAnalysisNotifier(analyzeLink, repository);
});
