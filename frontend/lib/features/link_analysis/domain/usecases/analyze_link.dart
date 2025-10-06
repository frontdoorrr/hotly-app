import 'package:dartz/dartz.dart';
import '../entities/link_analysis_result.dart';
import '../repositories/link_analysis_repository.dart';

/// Use case for analyzing a link to extract place information
class AnalyzeLink {
  final LinkAnalysisRepository _repository;

  AnalyzeLink(this._repository);

  Future<Either<Exception, LinkAnalysisResult>> call({
    required String url,
    bool forceRefresh = false,
  }) async {
    // Validate URL
    if (!_repository.isUrlSupported(url)) {
      return Left(
        Exception(
          'Unsupported platform. Supported: Instagram, Naver Blog, YouTube',
        ),
      );
    }

    return await _repository.analyzeLink(
      url: url,
      forceRefresh: forceRefresh,
    );
  }
}
