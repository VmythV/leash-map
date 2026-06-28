import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';

class ActivityScreen extends StatefulWidget {
  const ActivityScreen({super.key});
  @override
  State<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends State<ActivityScreen> {
  late Future<ActivitySummary> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<AppState>().loadActivity();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('活动数据（近 24 小时）')),
      body: FutureBuilder<ActivitySummary>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) return Center(child: Text('加载失败：${snap.error}'));
          final a = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(children: [
                Expanded(child: _StatCard(label: '运动距离', value: _km(a.distanceM))),
                const SizedBox(width: 12),
                Expanded(child: _StatCard(label: '活跃时长', value: '${a.activeMinutes.toStringAsFixed(0)} 分')),
              ]),
              const SizedBox(height: 16),
              Text('按小时分布（米）', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              _HourlyBars(byHour: a.byHourM),
              const SizedBox(height: 20),
              Text('常去区域', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              if (a.stops.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text('暂无明显停留点', style: TextStyle(color: Colors.grey)),
                )
              else
                ...a.stops.map((s) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.place_outlined),
                        title: Text('${s.lat.toStringAsFixed(5)}, ${s.lng.toStringAsFixed(5)}'),
                        subtitle: Text('停留约 ${_dur(s.durationS)} · ${s.count} 个点'),
                      ),
                    )),
            ],
          );
        },
      ),
    );
  }

  String _km(double m) => m >= 1000 ? '${(m / 1000).toStringAsFixed(2)} km' : '${m.toStringAsFixed(0)} m';
  String _dur(int s) => s >= 3600 ? '${(s / 3600).toStringAsFixed(1)} 小时' : '${(s / 60).toStringAsFixed(0)} 分';
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  const _StatCard({required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        child: Column(children: [
          Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(color: Colors.grey)),
        ]),
      ),
    );
  }
}

class _HourlyBars extends StatelessWidget {
  final List<double> byHour;
  const _HourlyBars({required this.byHour});
  @override
  Widget build(BuildContext context) {
    final maxV = byHour.isEmpty ? 1.0 : (byHour.reduce((a, b) => a > b ? a : b)).clamp(1.0, double.infinity);
    return SizedBox(
      height: 120,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: List.generate(24, (h) {
          final v = h < byHour.length ? byHour[h] : 0.0;
          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 1),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Container(
                    height: (v / maxV * 96).clamp(2, 96).toDouble(),
                    decoration: BoxDecoration(
                      color: v > 0 ? const Color(0xFF3B82F6) : const Color(0xFF2A2F3A),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  if (h % 6 == 0)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text('$h', style: const TextStyle(fontSize: 9, color: Colors.grey)),
                    ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }
}
