import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import '../util.dart';
import 'bind_screen.dart';

class DevicesScreen extends StatefulWidget {
  const DevicesScreen({super.key});
  @override
  State<DevicesScreen> createState() => _DevicesScreenState();
}

class _DevicesScreenState extends State<DevicesScreen> {
  List<DeviceInfo>? _devices;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final d = await context.read<AppState>().loadDevices();
    if (mounted) setState(() => _devices = d);
  }

  Future<void> _addDevice() async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => const BindScreen()));
    await _reload();
  }

  Future<void> _unbind(DeviceInfo d) async {
    final app = context.read<AppState>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('解绑设备'),
        content: Text('确定解绑 ${d.deviceId}？该设备之后的上报将不再归属此宠物。'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('解绑')),
        ],
      ),
    );
    if (ok == true) {
      await app.unbindDevice(d.deviceId);
      await _reload();
    }
  }

  @override
  Widget build(BuildContext context) {
    final devices = _devices;
    return Scaffold(
      appBar: AppBar(title: const Text('设备管理')),
      body: devices == null
          ? const Center(child: CircularProgressIndicator())
          : devices.isEmpty
              ? const Center(child: Text('还没有绑定设备，点右下角添加。'))
              : ListView(
                  padding: const EdgeInsets.all(12),
                  children: devices
                      .map((d) => Card(
                            child: ListTile(
                              leading: Icon(Icons.sensors, color: d.online ? Colors.green : Colors.grey),
                              title: Row(children: [
                                Text(d.deviceId),
                                if (d.primary)
                                  const Padding(
                                    padding: EdgeInsets.only(left: 8),
                                    child: Chip(
                                      label: Text('主设备', style: TextStyle(fontSize: 11)),
                                      visualDensity: VisualDensity.compact,
                                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                    ),
                                  ),
                              ]),
                              subtitle: Text(
                                  '${d.online ? "在线" : "离线"} · 电量 ${d.batteryPct ?? "—"}% · 最近 ${fmtTime(d.lastSeenAt)}'),
                              trailing: IconButton(
                                icon: const Icon(Icons.link_off),
                                onPressed: () => _unbind(d),
                              ),
                            ),
                          ))
                      .toList(),
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addDevice,
        icon: const Icon(Icons.add),
        label: const Text('添加设备'),
      ),
    );
  }
}
