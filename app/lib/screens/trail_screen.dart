import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../config.dart';
import '../models.dart';
import '../widgets/pet_map.dart';

class TrailScreen extends StatefulWidget {
  const TrailScreen({super.key});
  @override
  State<TrailScreen> createState() => _TrailScreenState();
}

class _TrailScreenState extends State<TrailScreen> {
  late Future<TrailData> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<AppState>().loadTodayTrail();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.read<AppState>();
    final gf = s.primaryGeofence;

    return Scaffold(
      appBar: AppBar(title: const Text('轨迹回放（近 24 小时）')),
      body: FutureBuilder<TrailData>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('加载失败：${snap.error}'));
          }
          final trail = snap.data!;
          final points = trail.points.map((p) => LatLng(p.lat, p.lng)).toList();
          final center = gf != null
              ? LatLng(gf.centerLat, gf.centerLng)
              : (points.isNotEmpty ? points.first : const LatLng(AppConfig.demoCenterLat, AppConfig.demoCenterLng));

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              PetMap(center: center, radiusM: gf?.radiusM ?? AppConfig.demoRadiusM, trail: points, fitTrail: true),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _stat('轨迹点', '${trail.pointCount}'),
                      _stat('距离', '${trail.distanceM.toStringAsFixed(0)} m'),
                    ],
                  ),
                ),
              ),
              if (points.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 24),
                  child: Center(child: Text('暂无轨迹。回到首页点「模拟走动」后再试。')),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _stat(String k, String v) => Column(children: [
        Text(v, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Text(k, style: const TextStyle(color: Colors.grey)),
      ]);
}
