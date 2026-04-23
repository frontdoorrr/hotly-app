import 'package:flutter/material.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
import '../../../archive/presentation/widgets/archive_list_view.dart';

class DiscoverScreen extends StatelessWidget {
  const DiscoverScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.nav_discover),
        automaticallyImplyLeading: false,
      ),
      body: const ArchiveListView(),
    );
  }
}
