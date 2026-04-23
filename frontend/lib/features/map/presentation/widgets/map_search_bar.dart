import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/l10n/l10n_extension.dart';
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
  Timer? _debounceTimer;

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final searchResults = ref.watch(mapProvider.select((s) => s.searchResults));

    return Column(
      mainAxisSize: MainAxisSize.min,
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
              hintText: context.l10n.map_searchHint,
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
              _debounceTimer?.cancel();
              if (value.length >= 2) {
                _debounceTimer = Timer(const Duration(milliseconds: 300), () {
                  ref.read(mapProvider.notifier).searchPlaces(
                        query: value,
                        radiusKm: 5,
                      );
                });
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
        if (_showResults && searchResults.isNotEmpty)
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
              padding: EdgeInsets.zero,
              itemCount: searchResults.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final result = searchResults[index];
                return ListTile(
                  leading: Icon(
                    Icons.location_on,
                    color: AppColors.primary,
                  ),
                  title: Text(
                    result.placeName,
                    style: const TextStyle(color: Colors.black87),
                  ),
                  subtitle: Text(
                    result.address,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.black54),
                  ),
                  trailing: result.distance != null
                      ? Text(
                          '${(result.distance! / 1000).toStringAsFixed(1)}km',
                          style: const TextStyle(
                            color: Colors.black45,
                            fontSize: 12,
                          ),
                        )
                      : null,
                  onTap: () {
                    ref.read(mapProvider.notifier).selectSearchResult(result);

                    final searchPlaces = searchResults
                        .map((r) => {
                              'id': r.placeId,
                              'name': r.placeName,
                              'latitude': r.latitude,
                              'longitude': r.longitude,
                              'address': r.address,
                            })
                        .toList();

                    ref.read(mapProvider.notifier).updatePlacesOnMap(searchPlaces);

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
