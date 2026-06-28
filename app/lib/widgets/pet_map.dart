import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' as ll;

import '../models.dart' as m;

/// Real-map view (flutter_map + OpenStreetMap tiles). Draws the safe-zone
/// circle, the trail polyline, and the current-position marker. Input is WGS84,
/// which OSM consumes directly — no GCJ-02 conversion needed (that is only
/// required if/when switching to AMap/Tencent for China).
class PetMap extends StatelessWidget {
  final m.LatLng center;
  final double radiusM;
  final List<m.LatLng> trail;
  final bool fitTrail;

  const PetMap({
    super.key,
    required this.center,
    required this.radiusM,
    required this.trail,
    this.fitTrail = false,
  });

  ll.LatLng _c(m.LatLng p) => ll.LatLng(p.lat, p.lng);

  @override
  Widget build(BuildContext context) {
    final pts = trail.map(_c).toList();
    final last = pts.isNotEmpty ? pts.last : null;

    CameraFit? fit;
    if (fitTrail && pts.length >= 2) {
      fit = CameraFit.coordinates(coordinates: pts, padding: const EdgeInsets.all(40));
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: AspectRatio(
        aspectRatio: 1,
        child: FlutterMap(
          options: MapOptions(
            initialCenter: _c(center),
            initialZoom: 15,
            initialCameraFit: fit,
            interactionOptions: const InteractionOptions(
              flags: InteractiveFlag.pinchZoom | InteractiveFlag.drag | InteractiveFlag.doubleTapZoom,
            ),
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.leashmap.app',
            ),
            CircleLayer(circles: [
              CircleMarker(
                point: _c(center),
                radius: radiusM,
                useRadiusInMeter: true,
                color: const Color(0x223B82F6),
                borderColor: const Color(0xFF3B82F6),
                borderStrokeWidth: 2,
              ),
            ]),
            if (pts.length >= 2)
              PolylineLayer(polylines: [
                Polyline(points: pts, color: const Color(0xFF22C55E), strokeWidth: 4),
              ]),
            if (last != null)
              MarkerLayer(markers: [
                Marker(
                  point: last,
                  width: 36,
                  height: 36,
                  child: const Icon(Icons.location_on, color: Color(0xFFEF4444), size: 36),
                ),
              ]),
            const RichAttributionWidget(attributions: [
              TextSourceAttribution('© OpenStreetMap contributors'),
            ]),
          ],
        ),
      ),
    );
  }
}
