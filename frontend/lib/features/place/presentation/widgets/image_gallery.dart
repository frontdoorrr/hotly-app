import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../../core/theme/app_colors.dart';

class ImageGallery extends StatefulWidget {
  final List<String> imageUrls;
  final String? heroTag;

  const ImageGallery({
    super.key,
    required this.imageUrls,
    this.heroTag,
  });

  @override
  State<ImageGallery> createState() => _ImageGalleryState();
}

class _ImageGalleryState extends State<ImageGallery> {
  int _currentPage = 0;
  final PageController _pageController = PageController();

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.imageUrls.isEmpty) {
      return Container(
        color: AppColors.surface,
        child: const Center(
          child: Icon(
            Icons.image_not_supported,
            size: 64,
            color: AppColors.textSecondary,
          ),
        ),
      );
    }

    return Stack(
      children: [
        PageView.builder(
          controller: _pageController,
          itemCount: widget.imageUrls.length,
          onPageChanged: (index) {
            setState(() => _currentPage = index);
          },
          itemBuilder: (context, index) {
            final imageWidget = CachedNetworkImage(
              imageUrl: widget.imageUrls[index],
              fit: BoxFit.cover,
              width: double.infinity,
              placeholder: (context, url) => Container(
                color: AppColors.surface,
                child: const Center(
                  child: CircularProgressIndicator(),
                ),
              ),
              errorWidget: (context, url, error) => Container(
                color: AppColors.surface,
                child: const Icon(
                  Icons.broken_image,
                  size: 64,
                  color: AppColors.textSecondary,
                ),
              ),
            );

            // Only wrap first image with Hero
            if (index == 0 && widget.heroTag != null) {
              return Hero(
                tag: widget.heroTag!,
                child: imageWidget,
              );
            }

            return imageWidget;
          },
        ),

        // Page Indicator
        if (widget.imageUrls.length > 1)
          Positioned(
            bottom: 16,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                widget.imageUrls.length,
                (index) => Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _currentPage == index
                        ? Colors.white
                        : Colors.white.withOpacity(0.5),
                  ),
                ),
              ),
            ),
          ),

        // Image Counter
        if (widget.imageUrls.length > 1)
          Positioned(
            top: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.6),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                '${_currentPage + 1}/${widget.imageUrls.length}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
