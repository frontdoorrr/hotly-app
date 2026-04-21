import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '_shared.dart';

class EventCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const EventCard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final startDate = data['start_date'] as String?;
    final endDate = data['end_date'] as String?;
    final dateRange = [startDate, endDate].where((d) => d != null).join(' ~ ');

    final venue = _parseVenue(data['venue']);

    return TypeInfoCard(
      children: [
        if (dateRange.isNotEmpty)
          TypeInfoRow(icon: Icons.calendar_today, text: dateRange),
        TypeInfoRow(icon: Icons.access_time, text: data['time'] as String?),
        TypeInfoRow(icon: Icons.location_on, text: venue?['name'] as String?),
        TypeInfoRow(icon: Icons.map_outlined, text: venue?['address'] as String?),
        TypeInfoRow(icon: Icons.person_outline, text: data['organizer'] as String?),
        TypeInfoRow(
          icon: Icons.confirmation_number_outlined,
          text: data['ticket_price'] as String?,
        ),
        if (data['registration_required'] == true)
          TypeInfoRow(
            icon: Icons.app_registration,
            text: '사전 등록 필요',
            color: Colors.orange,
          ),
        if (data['booking_url'] != null) ...[
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _launch(data['booking_url'] as String?),
              icon: const Icon(Icons.open_in_new, size: 16),
              label: const Text('예매하기'),
              style: OutlinedButton.styleFrom(
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8)),
              ),
            ),
          ),
        ],
      ],
    );
  }

  /// venue 필드가 Map 또는 JSON 문자열로 올 수 있는 경우를 방어 처리.
  static Map<String, dynamic>? _parseVenue(Object? raw) {
    if (raw == null) return null;
    if (raw is Map<String, dynamic>) return raw;
    if (raw is String) {
      try {
        final decoded = jsonDecode(raw);
        if (decoded is Map<String, dynamic>) return decoded;
        return {'name': raw};
      } catch (_) {
        return {'name': raw};
      }
    }
    return null;
  }

  Future<void> _launch(String? url) async {
    if (url == null) return;
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) await launchUrl(uri);
  }
}
