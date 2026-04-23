import 'package:flutter/material.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
import '../widgets/archive_input_sheet.dart';
import '../widgets/archive_list_view.dart';


class ArchiveScreen extends StatelessWidget {
  const ArchiveScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.nav_archive),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_link),
            tooltip: context.l10n.common_addLink,
            onPressed: () => ArchiveInputSheet.show(context),
          ),
        ],
      ),
      body: const ArchiveListView(),
    );
  }
}
