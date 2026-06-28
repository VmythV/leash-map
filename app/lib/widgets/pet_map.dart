import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' as ll;

import '../models.dart' as m;

/// Real-map view (flutter_map + OpenStreetMap tiles). Draws the safe-zone
/// circle, the trail polyline, and the current-position marker. Input is WGS84,
/// which OSM consumes directly — no GCJ-02 conversion needed (that is only
/// required if/when switching to AMap/Tencent for China).
///
/// When [follow] is true the camera smoothly tracks the latest point; a manual
/// pan/zoom releases follow, and the locate button re-enables it.
class PetMap extends StatefulWidget {
  final m.LatLng center;
  final double radiusM;
  final List<m.LatLng> trail;
  final bool fitTrail;
  final bool follow;

  const PetMap({
    super.key,
    required this.center,
    required this.radiusM,
    required this.trail,
    this.fitTrail = false,
    this.follow = false,
  });

  @override
  State<PetMap> createState() => _PetMapState();
}

class _PetMapState extends State<PetMap> with SingleTickerProviderStateMixin {
  final MapController _map = MapController();
  late final AnimationController _anim;
  bool _ready = false;
  bool _following = false;

  ll.LatLng? _from, _to;

  ll.LatLng _c(m.LatLng p) => ll.LatLng(p.lat, p.lng);
  m.LatLng? get _last => widget.trail.isNotEmpty ? widget.trail.last : null;

  @override
  void initState() {
    super.initState();
    _following = widget.follow;
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 500))
      ..addListener(_onTick);
  }

  @override
  void dispose() {
    _anim.dispose();
    _map.dispose();
    super.dispose();
  }

  void _onTick() {
    if (_from == null || _to == null) return;
    final t = Curves.easeInOut.transform(_anim.value);
    final lat = lerpDouble(_from!.latitude, _to!.latitude, t)!;
    final lng = lerpDouble(_from!.longitude, _to!.longitude, t)!;
    _map.move(ll.LatLng(lat, lng), _map.camera.zoom);
  }

  void _animateTo(ll.LatLng dest) {
    if (!_ready) return;
    _from = _map.camera.center;
    _to = dest;
    _anim.forward(from: 0);
  }

  @override
  void didUpdateWidget(covariant PetMap old) {
    super.didUpdateWidget(old);
    final last = _last;
    if (_following && last != null) {
      final prev = old.trail.isNotEmpty ? old.trail.last : null;
      if (prev == null || prev.lat != last.lat || prev.lng != last.lng) {
        _animateTo(_c(last));
      }
    }
  }

  void _onPositionChanged(MapCamera camera, bool hasGesture) {
    if (hasGesture && _following) {
      setState(() => _following = false); // user took control
    }
  }

  void _recenter() {
    setState(() => _following = true);
    final last = _last;
    if (last != null) _animateTo(_c(last));
  }

  @override
  Widget build(BuildContext context) {
    final pts = widget.trail.map(_c).toList();
    final last = pts.isNotEmpty ? pts.last : null;

    CameraFit? fit;
    if (widget.fitTrail && pts.length >= 2) {
      fit = CameraFit.coordinates(coordinates: pts, padding: const EdgeInsets.all(40));
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: AspectRatio(
        aspectRatio: 1,
        child: Stack(
          children: [
            FlutterMap(
              mapController: _map,
              options: MapOptions(
                initialCenter: last ?? _c(widget.center),
                initialZoom: 15,
                initialCameraFit: fit,
                onMapReady: () => _ready = true,
                onPositionChanged: _onPositionChanged,
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.pinchZoom |
                      InteractiveFlag.drag |
                      InteractiveFlag.doubleTapZoom,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.leashmap.app',
                ),
                CircleLayer(circles: [
                  CircleMarker(
                    point: _c(widget.center),
                    radius: widget.radiusM,
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
            if (widget.follow)
              Positioned(
                right: 10,
                bottom: 10,
                child: FloatingActionButton.small(
                  heroTag: 'petmap_follow',
                  onPressed: _recenter,
                  backgroundColor: _following ? const Color(0xFF3B82F6) : null,
                  child: Icon(_following ? Icons.my_location : Icons.location_searching),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
