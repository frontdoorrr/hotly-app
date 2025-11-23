import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:frontend/core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/sharing/share_service.dart';
import '../../../../shared/widgets/atoms/app_button.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../providers/place_detail_provider.dart';
import '../widgets/image_gallery.dart';

class PlaceDetailScreen extends ConsumerWidget {
  final String placeId;

  const PlaceDetailScreen({
    super.key,
    required this.placeId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(placeDetailProvider(placeId));

    if (state.isLoading || state.place == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (state.error != null) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 64,
                color: AppColors.error,
              ),
              const SizedBox(height: 16),
              Text(
                context.l10n.place_cannotLoadPlaces,
                style: AppTextStyles.h4,
              ),
              const SizedBox(height: 8),
              Text(
                state.error!.message,
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () =>
                    ref.read(placeDetailProvider(placeId).notifier).refresh(),
                child: Text(context.l10n.common_retry),
              ),
            ],
          ),
        ),
      );
    }

    final place = state.place!;
    final imageUrls = place.imageUrl != null ? [place.imageUrl!] : <String>[];

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Expandable AppBar with Image Gallery
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            backgroundColor: AppColors.primary,
            flexibleSpace: FlexibleSpaceBar(
              background: ImageGallery(
                imageUrls: imageUrls,
                heroTag: 'place_image_${place.id}',
              ),
            ),
            actions: [
              // Like Button
              IconButton(
                icon: Icon(
                  state.isLiked ? Icons.favorite : Icons.favorite_border,
                  color: state.isLiked ? AppColors.error : Colors.white,
                ),
                onPressed: () {
                  ref.read(placeDetailProvider(placeId).notifier).toggleLike();
                },
              ),
              // Share Button
              IconButton(
                icon: const Icon(Icons.share, color: Colors.white),
                onPressed: () => _sharePlace(ref, place.name),
              ),
              const SizedBox(width: 8),
            ],
          ),

          // Place Info Section
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Name + Rating
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          place.name,
                          style: AppTextStyles.h2.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      if (place.rating > 0) ...[
                        const Icon(Icons.star, color: Colors.amber, size: 20),
                        const SizedBox(width: 4),
                        Text(
                          place.rating.toStringAsFixed(1),
                          style: AppTextStyles.h4.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ],
                  ),

                  const SizedBox(height: 12),

                  // Tags
                  if (place.tags.isNotEmpty)
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: place.tags.map((tag) {
                        return Chip(
                          label: Text('#$tag'),
                          labelStyle: AppTextStyles.label2,
                          visualDensity: VisualDensity.compact,
                          backgroundColor: AppColors.primaryLight,
                        );
                      }).toList(),
                    ),

                  const SizedBox(height: 20),

                  // Address Section
                  if (place.address != null)
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on,
                          size: 20,
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            place.address!,
                            style: AppTextStyles.body1,
                          ),
                        ),
                      ],
                    ),

                  const SizedBox(height: 16),

                  // Action Buttons
                  if (place.latitude != null && place.longitude != null)
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.map),
                            label: Text(context.l10n.map_viewOnMap),
                            onPressed: () => _openMap(
                              place.latitude!,
                              place.longitude!,
                              place.name,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.directions),
                            label: Text(context.l10n.map_findRoute),
                            onPressed: () => _openDirections(
                              place.latitude!,
                              place.longitude!,
                              place.name,
                            ),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),

          // Description Section
          if (place.description != null && place.description!.isNotEmpty)
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(),
                    const SizedBox(height: 16),
                    Text(
                      context.l10n.place_introduction,
                      style: AppTextStyles.h4.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      place.description!,
                      style: AppTextStyles.body1.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.6,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // Similar Places Section
          if (state.similarPlaces.isNotEmpty)
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(),
                    const SizedBox(height: 16),
                    Text(
                      context.l10n.place_similarPlaces,
                      style: AppTextStyles.h4.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),

          if (state.similarPlaces.isNotEmpty)
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final similarPlace = state.similarPlaces[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: PlaceCard(
                        place: similarPlace,
                        onTap: () {
                          // Navigate to another place detail
                          Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (context) => PlaceDetailScreen(
                                placeId: similarPlace.id,
                              ),
                            ),
                          );
                        },
                      ),
                    );
                  },
                  childCount: state.similarPlaces.length,
                ),
              ),
            ),

          // Bottom spacing
          const SliverToBoxAdapter(
            child: SizedBox(height: 80),
          ),
        ],
      ),

      // Bottom Action Bar
      bottomNavigationBar: SafeArea(
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.background,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: AppButton(
                  text: state.isSaved ? context.l10n.place_saved : context.l10n.place_saveButton,
                  variant: state.isSaved
                      ? ButtonVariant.secondary
                      : ButtonVariant.outline,
                  icon: Icon(
                    state.isSaved ? Icons.bookmark : Icons.bookmark_border,
                  ),
                  onPressed: () {
                    ref
                        .read(placeDetailProvider(placeId).notifier)
                        .toggleSave();
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppButton(
                  text: context.l10n.place_addToCourse,
                  variant: ButtonVariant.primary,
                  icon: const Icon(Icons.add),
                  onPressed: () {
                    // TODO: Show course selection bottom sheet
                    _showAddToCourseBottomSheet(context);
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _sharePlace(WidgetRef ref, String placeName) async {
    final placeState = ref.read(placeDetailProvider(placeId));
    if (placeState.place != null) {
      await ShareService.sharePlace(
        placeId: placeState.place!.id,
        placeName: placeState.place!.name,
        address: placeState.place!.address,
        imageUrl: placeState.place!.imageUrl,
      );
    }
  }

  Future<void> _openMap(double lat, double lng, String name) async {
    // Kakao Map URL scheme
    final kakaoUrl = Uri.parse(
      'kakaomap://look?p=$lat,$lng',
    );

    // Google Maps fallback
    final googleMapsUrl = Uri.parse(
      'https://www.google.com/maps/search/?api=1&query=$lat,$lng',
    );

    if (await canLaunchUrl(kakaoUrl)) {
      await launchUrl(kakaoUrl);
    } else if (await canLaunchUrl(googleMapsUrl)) {
      await launchUrl(googleMapsUrl, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _openDirections(double lat, double lng, String name) async {
    // Kakao Navi URL scheme
    final kakaoNaviUrl = Uri.parse(
      'kakaonavi://route?ep=$lat,$lng&by=CAR',
    );

    // Google Maps directions fallback
    final googleMapsUrl = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=$lat,$lng',
    );

    if (await canLaunchUrl(kakaoNaviUrl)) {
      await launchUrl(kakaoNaviUrl);
    } else if (await canLaunchUrl(googleMapsUrl)) {
      await launchUrl(googleMapsUrl, mode: LaunchMode.externalApplication);
    }
  }

  void _showAddToCourseBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                context.l10n.place_addToCourse,
                style: AppTextStyles.h3.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                context.l10n.place_availableInCourseBuilder,
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              AppButton(
                text: context.l10n.common_ok,
                variant: ButtonVariant.primary,
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
        );
      },
    );
  }
}
