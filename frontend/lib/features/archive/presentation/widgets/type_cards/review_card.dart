import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/theme/app_text_styles.dart';
import '_shared.dart';

class ReviewCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const ReviewCard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final pros = (data['pros'] as List?)?.cast<String>();
    final cons = (data['cons'] as List?)?.cast<String>();
    final recommendedFor = (data['recommended_for'] as List?)?.cast<String>();
    final priceAmount = data['price'];
    final priceCurrency = (data['price_currency'] as String?) ?? 'KRW';
    final rating = (data['rating'] as num?)?.toDouble();

    return TypeInfoCard(
      children: [
        // 제품명 + 브랜드
        if (data['product_name'] != null)
          Row(
            children: [
              Expanded(
                child: Text(
                  data['product_name'] as String,
                  style: AppTextStyles.bodyLarge,
                ),
              ),
              if (data['brand'] != null)
                Text(
                  data['brand'] as String,
                  style: AppTextStyles.bodySmall
                      .copyWith(color: AppColors.textSecondary),
                ),
            ],
          ),

        // 평점
        if (rating != null) ...[
          const SizedBox(height: 8),
          Row(
            children: [
              ...List.generate(5, (i) {
                if (i < rating.floor()) {
                  return const Icon(Icons.star, color: Colors.amber, size: 18);
                } else if (i < rating) {
                  return const Icon(Icons.star_half, color: Colors.amber, size: 18);
                }
                return const Icon(Icons.star_border, color: Colors.amber, size: 18);
              }),
              const SizedBox(width: 6),
              Text(rating.toStringAsFixed(1), style: AppTextStyles.bodyLarge),
              Text(
                ' / 5.0',
                style: AppTextStyles.bodySmall
                    .copyWith(color: AppColors.textSecondary),
              ),
            ],
          ),
        ],

        // 가격
        if (priceAmount != null)
          TypeInfoRow(
            icon: Icons.payments_outlined,
            text: '${_formatPrice(priceAmount)} $priceCurrency',
          ),

        // 장점
        if (pros != null && pros.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(
            '장점',
            style: AppTextStyles.bodySmall.copyWith(color: Colors.green[700]),
          ),
          const SizedBox(height: 4),
          ...pros
              .take(4)
              .map((p) => _BulletRow(text: p, color: Colors.green)),
        ],

        // 단점
        if (cons != null && cons.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(
            '단점',
            style: AppTextStyles.bodySmall.copyWith(color: Colors.red[700]),
          ),
          const SizedBox(height: 4),
          ...cons.take(4).map((c) => _BulletRow(text: c, color: Colors.red)),
        ],

        // 추천 대상
        if (recommendedFor != null && recommendedFor.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(
            '추천 대상',
            style: AppTextStyles.bodySmall
                .copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: recommendedFor
                .map(
                  (r) => Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      r,
                      style: AppTextStyles.bodySmall
                          .copyWith(color: Colors.blue[700]),
                    ),
                  ),
                )
                .toList(),
          ),
        ],

        // 구매 링크
        if (data['purchase_url'] != null) ...[
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _launch(data['purchase_url'] as String?),
              icon: const Icon(Icons.open_in_new, size: 16),
              label: const Text('구매하기'),
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

  String _formatPrice(dynamic amount) {
    if (amount is num) {
      final str = amount.toInt().toString();
      return str.replaceAllMapped(
          RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]},');
    }
    return amount.toString();
  }

  Future<void> _launch(String? url) async {
    if (url == null) return;
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) await launchUrl(uri);
  }
}

class _BulletRow extends StatelessWidget {
  final String text;
  final Color color;
  const _BulletRow({required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.circle, size: 6, color: color),
          const SizedBox(width: 6),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}
