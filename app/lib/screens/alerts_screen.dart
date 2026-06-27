import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import '../util.dart';

class AlertsScreen extends StatelessWidget {
  const AlertsScreen({super.key});

  Color _color(String type) {
    switch (type) {
      case 'exit_zone':
        return const Color(0xFFEF4444);
      case 'low_battery':
        return const Color(0xFFEAB308);
      default:
        return const Color(0xFF64748B);
    }
  }

  IconData _icon(String type) {
    switch (type) {
      case 'exit_zone':
        return Icons.run_circle_outlined;
      case 'low_battery':
        return Icons.battery_alert;
      default:
        return Icons.wifi_off;
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('告警'),
        actions: [IconButton(onPressed: s.refreshAlerts, icon: const Icon(Icons.refresh))],
      ),
      body: s.alerts.isEmpty
          ? const Center(child: Text('暂无告警'))
          : ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: s.alerts.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, i) {
                final Alert a = s.alerts[i];
                final open = a.status == 'open';
                return Card(
                  child: ListTile(
                    leading: Icon(_icon(a.type), color: _color(a.type)),
                    title: Text(a.message),
                    subtitle: Text('${alertTypeLabel[a.type] ?? a.type} · ${a.status} · ${fmtTime(a.createdAt)}'),
                    trailing: open
                        ? TextButton(onPressed: () => s.ack(a.id), child: const Text('确认'))
                        : const Icon(Icons.done_all, color: Colors.green),
                  ),
                );
              },
            ),
    );
  }
}
