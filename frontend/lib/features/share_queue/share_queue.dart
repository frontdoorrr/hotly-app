/// Share Queue Feature
///
/// iOS Share Extension을 통해 공유된 링크를 관리하고
/// 일괄 분석하는 기능을 제공합니다.
///
/// 주요 기능:
/// - iOS Share Extension에서 공유된 URL 수신
/// - 로컬 저장소에 큐 저장
/// - 일괄 AI 분석 처리
/// - 분석 결과 확인 및 장소 저장

// Domain Layer
export 'domain/entities/share_queue_item.dart';

// Data Layer
export 'data/services/share_queue_storage_service.dart';

// Presentation Layer - Providers
export 'presentation/providers/share_queue_provider.dart';

// Presentation Layer - Widgets
export 'presentation/widgets/share_queue_badge.dart';
export 'presentation/widgets/batch_processing_sheet.dart';

// Presentation Layer - Screens
export 'presentation/screens/share_queue_results_screen.dart';
