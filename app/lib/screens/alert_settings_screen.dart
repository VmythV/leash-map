import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import 'share_screen.dart';

const _commonTz = [
  'UTC',
  'Asia/Shanghai',
  'Asia/Hong_Kong',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Europe/London',
  'Europe/Paris',
  'America/New_York',
  'America/Los_Angeles',
];

class AlertSettingsScreen extends StatefulWidget {
  const AlertSettingsScreen({super.key});
  @override
  State<AlertSettingsScreen> createState() => _AlertSettingsScreenState();
}

class _AlertSettingsScreenState extends State<AlertSettingsScreen> {
  AlertSettings? _s;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    context.read<AppState>().loadAlertSettings().then((s) => setState(() => _s = s));
  }

  Future<void> _save(Map<String, dynamic> patch) async {
    setState(() => _saving = true);
    final s = await context.read<AppState>().saveAlertSettings(patch);
    if (mounted) setState(() { _s = s; _saving = false; });
  }

  bool get _quietOn => _s != null && _s!.quietStart != null && _s!.quietEnd != null && _s!.quietStart != _s!.quietEnd;

  @override
  Widget build(BuildContext context) {
    final s = _s;
    return Scaffold(
      appBar: AppBar(
        title: const Text('提醒设置'),
        bottom: _saving ? const PreferredSize(preferredSize: Size.fromHeight(2), child: LinearProgressIndicator(minHeight: 2)) : null,
      ),
      body: s == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                const _Section('告警开关'),
                SwitchListTile(
                  title: const Text('离区提醒'),
                  subtitle: const Text('宠物离开安全区域时提醒'),
                  value: s.exitEnabled,
                  onChanged: (v) => _save({'exit_enabled': v}),
                ),
                SwitchListTile(
                  title: const Text('回家提醒'),
                  subtitle: const Text('宠物回到安全区域时提醒'),
                  value: s.enterEnabled,
                  onChanged: (v) => _save({'enter_enabled': v}),
                ),
                SwitchListTile(
                  title: const Text('低电提醒'),
                  value: s.lowBatteryEnabled,
                  onChanged: (v) => _save({'low_battery_enabled': v}),
                ),
                if (s.lowBatteryEnabled)
                  ListTile(
                    title: const Text('低电阈值'),
                    subtitle: Slider(
                      min: 5, max: 50, divisions: 9,
                      label: '${s.lowBatteryThreshold ?? 15}%',
                      value: (s.lowBatteryThreshold ?? 15).toDouble(),
                      onChanged: (v) => setState(() => _s = _withThreshold(v.round())),
                      onChangeEnd: (v) => _save({'low_battery_threshold': v.round()}),
                    ),
                    trailing: Text('${s.lowBatteryThreshold ?? 15}%'),
                  ),
                SwitchListTile(
                  title: const Text('离线提醒'),
                  value: s.offlineEnabled,
                  onChanged: (v) => _save({'offline_enabled': v}),
                ),
                const _Section('勿扰时段'),
                SwitchListTile(
                  title: const Text('开启勿扰'),
                  subtitle: const Text('时段内告警仍在应用内显示，但不推送'),
                  value: _quietOn,
                  onChanged: (v) => _save(v ? {'quiet_start': 22, 'quiet_end': 7} : {'quiet_start': 0, 'quiet_end': 0}),
                ),
                if (_quietOn)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(children: [
                      const Text('从'),
                      _HourPicker(value: s.quietStart!, onChanged: (h) => _save({'quiet_start': h})),
                      const Text('到'),
                      _HourPicker(value: s.quietEnd!, onChanged: (h) => _save({'quiet_end': h})),
                      const Text('（UTC）'),
                    ]),
                  ),
                const _Section('时区'),
                ListTile(
                  title: const Text('勿扰/生效时段所用时区'),
                  trailing: DropdownButton<String>(
                    value: _commonTz.contains(s.timezone) ? s.timezone : 'UTC',
                    items: _commonTz
                        .map((tz) => DropdownMenuItem(value: tz, child: Text(tz)))
                        .toList(),
                    onChanged: (v) => v == null ? null : _save({'timezone': v}),
                  ),
                ),
                const _Section('数据与隐私'),
                SwitchListTile(
                  title: const Text('暂停追踪'),
                  subtitle: const Text('暂停期间设备上报的位置将被丢弃，不记录、不告警'),
                  value: s.trackingPaused,
                  onChanged: (v) => _save({'tracking_paused': v}),
                ),
                ListTile(
                  title: const Text('位置历史保留'),
                  trailing: DropdownButton<int>(
                    value: [7, 30, 90, 365].contains(s.retentionDays) ? s.retentionDays : 30,
                    items: const [
                      DropdownMenuItem(value: 7, child: Text('7 天')),
                      DropdownMenuItem(value: 30, child: Text('30 天')),
                      DropdownMenuItem(value: 90, child: Text('90 天')),
                      DropdownMenuItem(value: 365, child: Text('1 年')),
                    ],
                    onChanged: (v) => v == null ? null : _save({'retention_days': v}),
                  ),
                ),
                ListTile(
                  leading: const Icon(Icons.group_outlined),
                  title: const Text('共享给家人'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const ShareScreen())),
                ),
              ],
            ),
    );
  }

  AlertSettings _withThreshold(int t) => AlertSettings(
        exitEnabled: _s!.exitEnabled, enterEnabled: _s!.enterEnabled,
        lowBatteryEnabled: _s!.lowBatteryEnabled, offlineEnabled: _s!.offlineEnabled,
        lowBatteryThreshold: t, quietStart: _s!.quietStart, quietEnd: _s!.quietEnd,
        timezone: _s!.timezone,
        trackingPaused: _s!.trackingPaused, retentionDays: _s!.retentionDays,
      );
}

class _Section extends StatelessWidget {
  final String title;
  const _Section(this.title);
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 6),
        child: Text(title, style: TextStyle(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.w600)),
      );
}

class _HourPicker extends StatelessWidget {
  final int value;
  final ValueChanged<int> onChanged;
  const _HourPicker({required this.value, required this.onChanged});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: DropdownButton<int>(
          value: value,
          items: List.generate(24, (h) => DropdownMenuItem(value: h, child: Text('$h:00'))),
          onChanged: (h) => h == null ? null : onChanged(h),
        ),
      );
}
