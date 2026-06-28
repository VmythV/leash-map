import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../config.dart';
import '../models.dart';
import '../util.dart';
import '../widgets/pet_map.dart';
import 'activity_screen.dart';
import 'alert_settings_screen.dart';
import 'alerts_screen.dart';
import 'bind_screen.dart';
import 'device_settings_screen.dart';
import 'safezone_screen.dart';
import 'trail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().bootstrap();
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();

    if (s.status == AppStatus.loading) {
      return const Scaffold(
        body: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('连接云端…'),
        ])),
      );
    }
    if (s.status == AppStatus.error) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.cloud_off, size: 48),
              const SizedBox(height: 12),
              Text('无法连接云端\n${s.error}', textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton(onPressed: s.bootstrap, child: const Text('重试')),
            ]),
          ),
        ),
      );
    }

    final gf = s.primaryGeofence;
    final center = gf != null
        ? LatLng(gf.centerLat, gf.centerLng)
        : (s.latest != null
            ? LatLng(s.latest!.lat, s.latest!.lng)
            : const LatLng(AppConfig.demoCenterLat, AppConfig.demoCenterLng));

    return Scaffold(
      appBar: AppBar(
        title: Text(s.pet?.name ?? 'LeashMap'),
        actions: [
          IconButton(
            tooltip: '设备设置',
            icon: const Icon(Icons.settings_remote),
            onPressed: () => _go(const DeviceSettingsScreen()),
          ),
          IconButton(
            tooltip: '提醒设置',
            icon: const Icon(Icons.tune),
            onPressed: () => _go(const AlertSettingsScreen()),
          ),
          IconButton(
            tooltip: '扫码绑定设备',
            icon: const Icon(Icons.qr_code_scanner),
            onPressed: _scanBind,
          ),
          Padding(
            padding: const EdgeInsets.only(right: 14),
            child: Row(children: [
              Icon(Icons.circle, size: 10, color: s.online ? Colors.green : Colors.grey),
              const SizedBox(width: 6),
              Text(s.online ? '在线' : '离线'),
            ]),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          PetMap(
            center: center,
            radiusM: gf?.radiusM ?? AppConfig.demoRadiusM,
            trail: s.liveTrail,
            follow: true,
          ),
          const SizedBox(height: 16),
          _StatusCard(state: s),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: _ActionButton(icon: Icons.timeline, label: '轨迹', onTap: () => _go(const TrailScreen()))),
            const SizedBox(width: 10),
            Expanded(child: _ActionButton(icon: Icons.insights, label: '活动', onTap: () => _go(const ActivityScreen()))),
            const SizedBox(width: 10),
            Expanded(child: _ActionButton(icon: Icons.shield_outlined, label: '安全区', onTap: () => _go(const SafeZoneScreen()))),
            const SizedBox(width: 10),
            Expanded(
              child: _ActionButton(
                icon: Icons.notifications_outlined,
                label: '告警',
                badge: s.openAlertCount,
                onTap: () => _go(const AlertsScreen()),
              ),
            ),
          ]),
          const SizedBox(height: 10),
          FilledButton.tonalIcon(
            onPressed: () => _toggleLost(s),
            icon: Icon(s.lostMode ? Icons.gps_fixed : Icons.travel_explore),
            label: Text(s.lostMode ? '寻宠模式：开（高频上报）' : '寻宠模式：关'),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: s.runDemo,
        icon: const Icon(Icons.directions_walk),
        label: const Text('模拟走动'),
      ),
    );
  }

  void _go(Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  Future<void> _scanBind() async {
    final deviceId = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const BindScreen()),
    );
    if (!mounted || deviceId == null) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已绑定设备 $deviceId')),
    );
  }

  Future<void> _toggleLost(AppState s) async {
    await s.toggleLostMode();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(s.lostMode ? '已开启寻宠模式，设备将提高上报频率' : '已关闭寻宠模式'),
    ));
  }
}

class _StatusCard extends StatelessWidget {
  final AppState state;
  const _StatusCard({required this.state});

  @override
  Widget build(BuildContext context) {
    final loc = state.latest;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.battery_full, size: 18),
            const SizedBox(width: 6),
            Text('${state.batteryPct ?? '—'}%'),
            const Spacer(),
            const Icon(Icons.access_time, size: 18),
            const SizedBox(width: 6),
            Text(fmtTime(loc?.ts)),
          ]),
          const Divider(height: 24),
          _kv('定位精度', loc == null ? '—' : '约 ${loc.accuracyM.toStringAsFixed(0)} 米'),
          _kv('定位来源', loc?.source ?? '—'),
          _kv('运动状态', loc?.motionState ?? '—'),
          _kv('坐标', loc == null ? '暂无定位' : '${loc.lat.toStringAsFixed(5)}, ${loc.lng.toStringAsFixed(5)}'),
        ]),
      ),
    );
  }

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [
          SizedBox(width: 84, child: Text(k, style: const TextStyle(color: Colors.grey))),
          Expanded(child: Text(v)),
        ]),
      );
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final int badge;
  final VoidCallback onTap;
  const _ActionButton({required this.icon, required this.label, required this.onTap, this.badge = 0});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
      child: Column(children: [
        Badge(
          isLabelVisible: badge > 0,
          label: Text('$badge'),
          child: Icon(icon),
        ),
        const SizedBox(height: 6),
        Text(label),
      ]),
    );
  }
}
