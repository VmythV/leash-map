import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';

const _ledPatterns = {
  'off': '熄灭',
  'solid': '常亮',
  'blink': '循环闪烁',
  'morse': '摩斯码',
};
const _powerModes = {
  'normal': '日常',
  'saver': '省电',
  'high_accuracy': '高精度',
};

class DeviceSettingsScreen extends StatefulWidget {
  const DeviceSettingsScreen({super.key});
  @override
  State<DeviceSettingsScreen> createState() => _DeviceSettingsScreenState();
}

class _DeviceSettingsScreenState extends State<DeviceSettingsScreen> {
  DeviceConfig? _c;
  bool _saving = false;
  final _morse = TextEditingController();

  @override
  void initState() {
    super.initState();
    context.read<AppState>().loadDeviceConfig().then((c) {
      setState(() {
        _c = c;
        _morse.text = c.ledMorse;
      });
    });
  }

  @override
  void dispose() {
    _morse.dispose();
    super.dispose();
  }

  Future<void> _save(Map<String, dynamic> patch) async {
    setState(() => _saving = true);
    final c = await context.read<AppState>().saveDeviceConfig(patch);
    if (mounted) setState(() { _c = c; _saving = false; });
  }

  @override
  Widget build(BuildContext context) {
    final c = _c;
    return Scaffold(
      appBar: AppBar(
        title: const Text('设备设置'),
        bottom: _saving ? const PreferredSize(preferredSize: Size.fromHeight(2), child: LinearProgressIndicator(minHeight: 2)) : null,
      ),
      body: c == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('指示灯（无蜂鸣器）', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: c.ledPattern,
                  decoration: const InputDecoration(labelText: '亮灯模式', border: OutlineInputBorder(), isDense: true),
                  items: _ledPatterns.entries
                      .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                      .toList(),
                  onChanged: (v) => v == null ? null : _save({'led_pattern': v}),
                ),
                if (c.ledPattern == 'morse')
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Row(children: [
                      Expanded(
                        child: TextField(
                          controller: _morse,
                          maxLength: 15,
                          decoration: const InputDecoration(
                            labelText: '摩斯码消息',
                            hintText: 'SOS',
                            border: OutlineInputBorder(),
                            isDense: true,
                            counterText: '',
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      FilledButton(
                        onPressed: () => _save({'led_morse': _morse.text.trim().isEmpty ? 'SOS' : _morse.text.trim()}),
                        child: const Text('应用'),
                      ),
                    ]),
                  ),
                const Divider(height: 32),
                Text('功耗模式', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: c.powerMode,
                  decoration: const InputDecoration(labelText: '功耗', border: OutlineInputBorder(), isDense: true),
                  items: _powerModes.entries
                      .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                      .toList(),
                  onChanged: (v) => v == null ? null : _save({'power_mode': v}),
                ),
                const SizedBox(height: 12),
                Text('改动会通过下行命令在设备下次上报时下发。',
                    style: TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
    );
  }
}
