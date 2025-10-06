import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Supabase Service
///
/// Supabase 클라이언트 초기화 및 관리
class SupabaseService {
  static SupabaseClient? _client;

  /// Supabase 초기화
  static Future<void> initialize({
    required String url,
    required String anonKey,
  }) async {
    await Supabase.initialize(
      url: url,
      anonKey: anonKey,
      authOptions: const FlutterAuthClientOptions(
        authFlowType: AuthFlowType.pkce, // PKCE flow for OAuth
      ),
    );
    _client = Supabase.instance.client;
  }

  /// Supabase 클라이언트 반환
  static SupabaseClient get client {
    if (_client == null) {
      throw Exception('Supabase not initialized. Call SupabaseService.initialize() first.');
    }
    return _client!;
  }
}

/// Supabase Client Provider
final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return SupabaseService.client;
});
