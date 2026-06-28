import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';

/// Extract a device id from a scanned/typed value. Accepts a bare `dev_...`
/// id or a URL carrying `?device=dev_...` (e.g. leashmap://bind?device=dev_x).
String? parseDeviceId(String raw) {
  final v = raw.trim();
  if (v.isEmpty) return null;
  final uri = Uri.tryParse(v);
  final q = uri?.queryParameters['device'];
  if (q != null && q.startsWith('dev_')) return q;
  if (v.startsWith('dev_')) return v;
  return null;
}

class BindScreen extends StatefulWidget {
  const BindScreen({super.key});
  @override
  State<BindScreen> createState() => _BindScreenState();
}

class _BindScreenState extends State<BindScreen> {
  final MobileScannerController _controller = MobileScannerController();
  final TextEditingController _manual = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _controller.dispose();
    _manual.dispose();
    super.dispose();
  }

  Future<void> _bind(String deviceId) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await context.read<AppState>().addDevice(deviceId);
      if (!mounted) return;
      Navigator.of(context).pop(deviceId);
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('绑定失败：$e')));
    }
  }

  void _onDetect(BarcodeCapture capture) {
    if (_busy) return;
    for (final b in capture.barcodes) {
      final id = parseDeviceId(b.rawValue ?? '');
      if (id != null) {
        _bind(id);
        return;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('添加设备')),
      body: Column(
        children: [
          Expanded(
            child: Stack(
              alignment: Alignment.center,
              children: [
                MobileScanner(
                  controller: _controller,
                  onDetect: _onDetect,
                  errorBuilder: (context, error) => _ScannerUnavailable(error: error),
                ),
                IgnorePointer(
                  child: Container(
                    width: 220,
                    height: 220,
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.white70, width: 2),
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
                const Positioned(
                  bottom: 16,
                  child: Text('将设备二维码对准取景框',
                      style: TextStyle(color: Colors.white, backgroundColor: Colors.black54)),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('或手动输入设备 ID', style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                    child: TextField(
                      controller: _manual,
                      decoration: const InputDecoration(
                        hintText: 'dev_xxx',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  FilledButton(
                    onPressed: _busy
                        ? null
                        : () {
                            final id = parseDeviceId(_manual.text);
                            if (id == null) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('请输入有效的设备 ID（dev_ 开头）')),
                              );
                            } else {
                              _bind(id);
                            }
                          },
                    child: const Text('绑定'),
                  ),
                ]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ScannerUnavailable extends StatelessWidget {
  final Object error;
  const _ScannerUnavailable({required this.error});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black,
      alignment: Alignment.center,
      padding: const EdgeInsets.all(24),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.no_photography, color: Colors.white54, size: 40),
        const SizedBox(height: 12),
        const Text('相机不可用，请使用下方手动输入',
            style: TextStyle(color: Colors.white70), textAlign: TextAlign.center),
        const SizedBox(height: 6),
        Text('$error', style: const TextStyle(color: Colors.white30, fontSize: 11), textAlign: TextAlign.center),
      ]),
    );
  }
}
