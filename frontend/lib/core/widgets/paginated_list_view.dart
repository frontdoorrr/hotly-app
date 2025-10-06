import 'package:flutter/material.dart';
import 'package:infinite_scroll_pagination/infinite_scroll_pagination.dart';

/// Paginated List View with infinite scroll
class PaginatedListView<T> extends StatefulWidget {
  final Future<List<T>> Function(int page) fetchData;
  final Widget Function(BuildContext, T) itemBuilder;
  final Widget? separator;
  final int pageSize;
  final Widget? emptyWidget;
  final Widget? errorWidget;

  const PaginatedListView({
    super.key,
    required this.fetchData,
    required this.itemBuilder,
    this.separator,
    this.pageSize = 20,
    this.emptyWidget,
    this.errorWidget,
  });

  @override
  State<PaginatedListView<T>> createState() => _PaginatedListViewState<T>();
}

class _PaginatedListViewState<T> extends State<PaginatedListView<T>> {
  final PagingController<int, T> _pagingController = PagingController(
    firstPageKey: 0,
  );

  @override
  void initState() {
    super.initState();
    _pagingController.addPageRequestListener((pageKey) {
      _fetchPage(pageKey);
    });
  }

  Future<void> _fetchPage(int pageKey) async {
    try {
      final newItems = await widget.fetchData(pageKey);
      final isLastPage = newItems.length < widget.pageSize;

      if (isLastPage) {
        _pagingController.appendLastPage(newItems);
      } else {
        final nextPageKey = pageKey + 1;
        _pagingController.appendPage(newItems, nextPageKey);
      }
    } catch (error) {
      _pagingController.error = error;
    }
  }

  @override
  Widget build(BuildContext context) {
    return PagedListView<int, T>.separated(
      pagingController: _pagingController,
      builderDelegate: PagedChildBuilderDelegate<T>(
        itemBuilder: (context, item, index) => widget.itemBuilder(context, item),
        firstPageErrorIndicatorBuilder: (context) =>
            widget.errorWidget ??
            _buildErrorIndicator(context, () => _pagingController.refresh()),
        newPageErrorIndicatorBuilder: (context) =>
            _buildErrorIndicator(context, () => _pagingController.retryLastFailedRequest()),
        noItemsFoundIndicatorBuilder: (context) =>
            widget.emptyWidget ?? _buildEmptyIndicator(context),
      ),
      separatorBuilder: (context, index) =>
          widget.separator ?? const SizedBox.shrink(),
    );
  }

  Widget _buildErrorIndicator(BuildContext context, VoidCallback onRetry) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          const Text('데이터를 불러오지 못했습니다'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: onRetry,
            child: const Text('다시 시도'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyIndicator(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_outlined, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('데이터가 없습니다'),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pagingController.dispose();
    super.dispose();
  }
}
