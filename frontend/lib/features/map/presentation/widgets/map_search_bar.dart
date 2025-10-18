import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/map_provider.dart';

/// Search bar for map screen
class MapSearchBar extends ConsumerStatefulWidget {
  final Function(double latitude, double longitude)? onPlaceSelected;

  const MapSearchBar({super.key, this.onPlaceSelected});

  @override
  ConsumerState<MapSearchBar> createState() => _MapSearchBarState();
}

class _MapSearchBarState extends ConsumerState<MapSearchBar> {
  final _controller = TextEditingController();
  bool _showResults = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mapProvider);

    return Column(
      children: [
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: TextField(
            controller: _controller,
            decoration: InputDecoration(
              hintText: '장소, 주소 검색',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _controller.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _controller.clear();
                        setState(() => _showResults = false);
                        ref.read(mapProvider.notifier).clearSearch();
                      },
                    )
                  : null,
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
            ),
            onChanged: (value) {
              setState(() => _showResults = value.isNotEmpty);
              if (value.length >= 2) {
                ref.read(mapProvider.notifier).searchPlaces(
                      query: value,
                      radiusKm: 5,
                    );
              }
            },
            onSubmitted: (value) async {
              if (value.isNotEmpty) {
                await ref.read(mapProvider.notifier).searchPlaces(query: value);

                // Move to first search result after search completes
                final results = ref.read(mapProvider).searchResults;
                if (results.isNotEmpty) {
                  final firstResult = results.first;
                  widget.onPlaceSelected?.call(
                    firstResult.latitude,
                    firstResult.longitude,
                  );
                  ref.read(mapProvider.notifier).selectSearchResult(firstResult);
                }

                setState(() => _showResults = false);
                _controller.clear();
              }
            },
          ),
        ),

        // Search results
        if (_showResults && state.searchResults.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 8),
            constraints: const BoxConstraints(maxHeight: 300),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: state.searchResults.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final result = state.searchResults[index];
                return ListTile(
                  leading: Icon(
                    Icons.location_on,
                    color: AppColors.primary,
                  ),
                  title: Text(result.placeName),
                  subtitle: Text(
                    result.address,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: result.distance != null
                      ? Text(
                          '${(result.distance! / 1000).toStringAsFixed(1)}km',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        )
                      : null,
                  onTap: () {
                    // Select search result
                    ref.read(mapProvider.notifier).selectSearchResult(result);

                    // Convert search results to place format for markers
                    final searchPlaces = state.searchResults
                        .map((r) => {
                              'id': r.placeId,
                              'name': r.placeName,
                              'latitude': r.latitude,
                              'longitude': r.longitude,
                              'address': r.address,
                            })
                        .toList();

                    // Update placesOnMap with search results
                    ref.read(mapProvider.notifier).state =
                        ref.read(mapProvider).copyWith(
                              placesOnMap: searchPlaces,
                            );

                    // Move camera to selected place
                    widget.onPlaceSelected?.call(
                      result.latitude,
                      result.longitude,
                    );

                    setState(() => _showResults = false);
                    _controller.clear();
                  },
                );
              },
            ),
          ),
      ],
    );
  }
}
