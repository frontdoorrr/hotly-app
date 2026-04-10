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

    return TypeInfoCard(
      children: [
        if (dateRange.isNotEmpty)
          TypeInfoRow(icon: Icons.calendar_today, text: dateRange),
        TypeInfoRow(icon: Icons.access_time, text: data['time'] as String?),
        TypeInfoRow(icon: Icons.location_on, text: data['venue_name'] as String?),
        TypeInfoRow(icon: Icons.map_outlined, text: data['venue_address'] as String?),
        TypeInfoRow(icon: Icons.person_outline, text: data['organizer'] as String?),
        TypeInfoRow(
          icon: Icons.confirmation_number_outlined,
          text: data['ticket_price'] as String?,
        ),
        if (data['pre_registration_required'] == true)
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

  Future<void> _launch(String? url) async {
    if (url == null) return;
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) await launchUrl(uri);
  }
}
