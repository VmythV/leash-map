import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';

class ShareScreen extends StatefulWidget {
  const ShareScreen({super.key});
  @override
  State<ShareScreen> createState() => _ShareScreenState();
}

class _ShareScreenState extends State<ShareScreen> {
  List<String>? _shares;
  final _input = TextEditingController();
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    context.read<AppState>().loadShares().then((v) => setState(() => _shares = v));
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    final uid = _input.text.trim();
    if (uid.isEmpty) return;
    setState(() => _busy = true);
    try {
      final v = await context.read<AppState>().addShare(uid);
      if (mounted) setState(() { _shares = v; _busy = false; _input.clear(); });
    } catch (e) {
      if (mounted) {
        setState(() => _busy = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('添加失败：$e')));
      }
    }
  }

  Future<void> _remove(String uid) async {
    final v = await context.read<AppState>().removeShare(uid);
    if (mounted) setState(() => _shares = v);
  }

  @override
  Widget build(BuildContext context) {
    final s = context.read<AppState>();
    final myId = s.userId ?? '—';
    final shares = _shares;
    return Scaffold(
      appBar: AppBar(title: const Text('共享给家人')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              title: const Text('我的用户 ID'),
              subtitle: Text(myId),
              trailing: IconButton(
                icon: const Icon(Icons.copy),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: myId));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('已复制，发给家人即可被共享')),
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextField(
                controller: _input,
                decoration: const InputDecoration(
                  labelText: '添加共享成员（输入对方用户 ID）',
                  hintText: 'usr_xxx',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(width: 10),
            FilledButton(onPressed: _busy ? null : _add, child: const Text('添加')),
          ]),
          const SizedBox(height: 16),
          Text('已共享成员（可查看位置/轨迹/活动）', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          if (shares == null)
            const Center(child: CircularProgressIndicator())
          else if (shares.isEmpty)
            const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Text('暂无共享成员', style: TextStyle(color: Colors.grey)))
          else
            ...shares.map((u) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.person_outline),
                    title: Text(u),
                    trailing: IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () => _remove(u)),
                  ),
                )),
        ],
      ),
    );
  }
}
