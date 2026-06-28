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

/// Per-device settings (LED / power / name). Targets a specific device id.
class DeviceSettingsScreen extends StatefulWidget {
  final String deviceId;
  const DeviceSettingsScreen({super.key, required this.deviceId});
  @override
  State<DeviceSettingsScreen> createState() => _DeviceSettingsScreenState();
}

class _DeviceSettingsScreenState extends State<DeviceSettingsScreen> {
  DeviceConfig? _c;
  bool _saving = false;
  final _morse = TextEditingController();
  final _name = TextEditingController();

  @override
  void initState() {
    super.initState();
    context.read<AppState>().api.getDeviceConfig(widget.deviceId).then((c) {
      setState(() {
        _c = c;
        _morse.text = c.ledMorse;
        _name.text = c.name ?? '';
      });
    });
  }

  @override
  void dispose() {
    _morse.dispose();
    _name.dispose();
    super.dispose();
  }

  Future<void> _save(Map<String, dynamic> patch) async {
    setState(() => _saving = true);
    final c = await context.read<AppState>().api.updateDeviceConfig(widget.deviceId, patch);
    if (mounted) setState(() { _c = c; _saving = false; });
  }

  @override
  Widget build(BuildContext context) {
    final c = _c;
    return Scaffold(
      appBar: AppBar(
        title: Text(c?.name?.isNotEmpty == true ? c!.name! : widget.deviceId),
        bottom: _saving ? const PreferredSize(preferredSize: Size.fromHeight(2), child: LinearProgressIndicator(minHeight: 2)) : null,
      ),
      body: c == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('设备名称', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                    child: TextField(
                      controller: _name,
                      maxLength: 40,
                      decoration: InputDecoration(
                        hintText: widget.deviceId,
                        border: const OutlineInputBorder(),
                        isDense: true,
                        counterText: '',
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  FilledButton(
                    onPressed: () => _save({'name': _name.text.trim()}),
                    child: const Text('保存'),
                  ),
                ]),
                const Divider(height: 32),
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
                const Text('改动会通过下行命令在设备下次上报时下发。',
                    style: TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
    );
  }
}
