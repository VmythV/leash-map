import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../config.dart';

class SafeZoneScreen extends StatelessWidget {
  const SafeZoneScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(title: const Text('安全区域')),
      body: s.geofences.isEmpty
          ? const Center(child: Text('还没有安全区，点右下角添加。'))
          : ListView(
              padding: const EdgeInsets.all(12),
              children: s.geofences
                  .map((g) => Card(
                        child: ListTile(
                          leading: const Icon(Icons.shield_outlined),
                          title: Text(g.name),
                          subtitle: Text(
                              '中心 ${g.centerLat.toStringAsFixed(4)}, ${g.centerLng.toStringAsFixed(4)} · 半径 ${g.radiusM.toStringAsFixed(0)} m'),
                          trailing: Icon(g.enabled ? Icons.check_circle : Icons.cancel,
                              color: g.enabled ? Colors.green : Colors.grey),
                        ),
                      ))
                  .toList(),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _addDialog(context),
        icon: const Icon(Icons.add),
        label: const Text('添加安全区'),
      ),
    );
  }

  Future<void> _addDialog(BuildContext context) async {
    final s = context.read<AppState>();
    final nameCtrl = TextEditingController(text: '新的安全区');
    final radiusCtrl = TextEditingController(text: '150');
    // center on the current location if known, else the demo center
    final lat = s.latest?.lat ?? AppConfig.demoCenterLat;
    final lng = s.latest?.lng ?? AppConfig.demoCenterLng;

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('添加圆形安全区'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: '名称')),
          TextField(
            controller: radiusCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: '半径（米）'),
          ),
          const SizedBox(height: 8),
          Text('中心：${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}',
              style: const TextStyle(color: Colors.grey, fontSize: 12)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('创建')),
        ],
      ),
    );

    if (ok == true) {
      final radius = double.tryParse(radiusCtrl.text) ?? 150;
      await s.addGeofence(nameCtrl.text.trim(), lat, lng, radius < 20 ? 20 : radius);
    }
  }
}
