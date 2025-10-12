import 'package:dartz/dartz.dart';
import '../entities/link_analysis_result.dart';

/// Repository interface for Link Analysis
abstract class LinkAnalysisRepository {
  /// Analyze a URL to extract place information
  Future<Either<Exception, LinkAnalysisResult>> analyzeLink({
    required String url,
    bool forceRefresh = false,
  });

  /// Get the status of an ongoing analysis
  Future<Either<Exception, LinkAnalysisResult>> getAnalysisStatus(
    String analysisId,
  );

  /// Cancel an ongoing analysis
  Future<Either<Exception, void>> cancelAnalysis(String analysisId);

  /// Save analyzed place to database
  Future<Either<Exception, Map<String, dynamic>>> saveAnalyzedPlace(
    String analysisId, {
    String? sourceUrl,
  });

  /// Validate if URL is supported
  bool isUrlSupported(String url);
}
