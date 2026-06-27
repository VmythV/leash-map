import 'dart:math';

import 'package:flutter/material.dart';

import '../models.dart';

/// A self-contained map: projects WGS84 points onto a canvas around a center,
/// drawing the safe-zone circle, the trail, and the current marker. No external
/// map tiles, so it runs fully offline.
class MiniMap extends StatelessWidget {
  final LatLng center;
  final double radiusM;
  final List<LatLng> trail;
  final double spanM;

  const MiniMap({
    super.key,
    required this.center,
    required this.radiusM,
    required this.trail,
    this.spanM = 700,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: AspectRatio(
        aspectRatio: 1,
        child: CustomPaint(
          painter: _MapPainter(center, radiusM, trail, spanM),
          child: const SizedBox.expand(),
        ),
      ),
    );
  }
}

class _MapPainter extends CustomPainter {
  final LatLng center;
  final double radiusM;
  final List<LatLng> trail;
  final double spanM;

  _MapPainter(this.center, this.radiusM, this.trail, this.spanM);

  static const double _mPerDeg = 111320.0;

  Offset _project(LatLng p, Size size, double mpp) {
    final dn = (p.lat - center.lat) * _mPerDeg;
    final de = (p.lng - center.lng) * _mPerDeg * cos(center.lat * pi / 180);
    return Offset(size.width / 2 + de / mpp, size.height / 2 - dn / mpp);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final mpp = spanM / size.width;
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF131722));

    // grid
    final grid = Paint()..color = const Color(0xFF1C2230)..strokeWidth = 1;
    for (double g = 0; g <= size.width; g += 50) {
      canvas.drawLine(Offset(g, 0), Offset(g, size.height), grid);
      canvas.drawLine(Offset(0, g), Offset(size.width, g), grid);
    }

    // safe zone
    final c = _project(center, size, mpp);
    final r = radiusM / mpp;
    canvas.drawCircle(c, r, Paint()..color = const Color(0x1A3B82F6));
    canvas.drawCircle(
      c,
      r,
      Paint()
        ..color = const Color(0xFF3B82F6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5,
    );

    // trail
    if (trail.isNotEmpty) {
      final path = Path();
      for (var i = 0; i < trail.length; i++) {
        final o = _project(trail[i], size, mpp);
        i == 0 ? path.moveTo(o.dx, o.dy) : path.lineTo(o.dx, o.dy);
      }
      canvas.drawPath(
        path,
        Paint()
          ..color = const Color(0xFF22C55E)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.5,
      );

      final last = _project(trail.last, size, mpp);
      final outside = (last - c).distance > r;
      canvas.drawCircle(last, 7, Paint()..color = outside ? const Color(0xFFEF4444) : const Color(0xFF22C55E));
      canvas.drawCircle(
        last,
        7,
        Paint()
          ..color = Colors.white
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _MapPainter old) =>
      old.trail.length != trail.length ||
      old.center.lat != center.lat ||
      old.center.lng != center.lng ||
      old.radiusM != radiusM;
}
