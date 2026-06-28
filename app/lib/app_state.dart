import 'dart:async';

import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'config.dart';
import 'models.dart';
import 'sse_client.dart';

enum AppStatus { loading, ready, error }

/// Central app state: session, selected pet, live location/alerts over SSE.
class AppState extends ChangeNotifier {
  final ApiClient api = ApiClient();
  final SseClient sse = SseClient();

  AppStatus status = AppStatus.loading;
  String? error;

  String? deviceId;
  Pet? pet;
  Geofence? primaryGeofence;
  List<Geofence> geofences = [];
  AppLocation? latest;
  int? batteryPct;
  bool online = false;
  final List<LatLng> liveTrail = [];
  List<Alert> alerts = [];

  StreamSubscription<SseEvent>? _sseSub;

  int get openAlertCount => alerts.where((a) => a.status == 'open').length;

  Future<void> bootstrap() async {
    try {
      status = AppStatus.loading;
      notifyListeners();

      final token = await api.createSession(displayName: 'May');
      final pets = await api.listPets();
      pet = pets.isNotEmpty ? pets.first : await api.createPet('Buddy');

      deviceId = 'dev_app_${token.substring(token.length - 6)}';
      await api.bindDevice(deviceId!, pet!.id);

      geofences = await api.listGeofences(pet!.id);
      if (geofences.isEmpty) {
        final gf = await api.createGeofence(
          pet!.id,
          name: '家',
          centerLat: AppConfig.demoCenterLat,
          centerLng: AppConfig.demoCenterLng,
          radiusM: AppConfig.demoRadiusM,
        );
        geofences = [gf];
      }
      primaryGeofence = geofences.first;

      final ll = await api.latestLocation(pet!.id);
      _applyLatest(ll);
      alerts = await api.listAlerts();

      _subscribe(token);
      status = AppStatus.ready;
      notifyListeners();
    } catch (e) {
      error = e.toString();
      status = AppStatus.error;
      notifyListeners();
    }
  }

  void _applyLatest(LatestLocation ll) {
    latest = ll.location;
    if (ll.device != null) {
      online = ll.device!.online;
      batteryPct = ll.device!.batteryPct;
    }
    if (ll.location != null) {
      liveTrail.add(LatLng(ll.location!.lat, ll.location!.lng));
    }
  }

  void _subscribe(String token) {
    _sseSub?.cancel();
    _sseSub = sse.connect(token: token, petId: pet!.id).listen(_onEvent);
  }

  void _onEvent(SseEvent e) {
    switch (e.event) {
      case 'location.updated':
        latest = AppLocation.fromJson(e.data);
        liveTrail.add(LatLng(latest!.lat, latest!.lng));
        online = true;
        notifyListeners();
        break;
      case 'device.battery_updated':
        batteryPct = (e.data['battery_pct'] as num?)?.toInt();
        notifyListeners();
        break;
      case 'device.status_updated':
        online = e.data['online'] as bool? ?? online;
        notifyListeners();
        break;
      case 'alert.created':
        alerts.insert(0, _alertFromEvent(e.data));
        notifyListeners();
        break;
    }
  }

  Alert _alertFromEvent(Map<String, dynamic> d) => Alert(
        id: d['alert_id'] as String,
        petId: d['pet_id'] as String? ?? '',
        deviceId: d['device_id'] as String?,
        type: d['type'] as String,
        severity: d['severity'] as String,
        status: d['status'] as String? ?? 'open',
        message: d['message'] as String,
        createdAt: (d['created_at'] ?? '') as String,
      );

  /// Bind a (scanned or typed) device id to the current pet, then refresh.
  Future<void> rebindDevice(String newDeviceId) async {
    await api.bindDevice(newDeviceId, pet!.id);
    deviceId = newDeviceId;
    liveTrail.clear();
    final ll = await api.latestLocation(pet!.id);
    _applyLatest(ll);
    notifyListeners();
  }

  bool lostMode = false;

  Future<void> toggleLostMode() async {
    lostMode = !lostMode;
    notifyListeners();
    await api.setLostMode(pet!.id, lostMode);
  }

  Future<void> runDemo() async {
    if (deviceId != null) {
      liveTrail.clear();
      notifyListeners();
      await api.demoRun(deviceId!);
    }
  }

  Future<TrailData> loadTodayTrail() {
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, now.day).subtract(const Duration(days: 1));
    return api.trail(pet!.id, start, now.add(const Duration(minutes: 1)));
  }

  Future<ActivitySummary> loadActivity() {
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, now.day).subtract(const Duration(days: 1));
    return api.activity(pet!.id, start, now.add(const Duration(minutes: 1)));
  }

  Future<void> addGeofence(String name, double lat, double lng, double radiusM) async {
    await api.createGeofence(pet!.id, name: name, centerLat: lat, centerLng: lng, radiusM: radiusM);
    geofences = await api.listGeofences(pet!.id);
    primaryGeofence = geofences.first;
    notifyListeners();
  }

  Future<void> patchGeofence(String geoId, Map<String, dynamic> fields) async {
    await api.updateGeofence(pet!.id, geoId, fields);
    geofences = await api.listGeofences(pet!.id);
    primaryGeofence = geofences.isNotEmpty ? geofences.first : null;
    notifyListeners();
  }

  Future<AlertSettings> loadAlertSettings() => api.getAlertSettings(pet!.id);

  Future<AlertSettings> saveAlertSettings(Map<String, dynamic> patch) =>
      api.updateAlertSettings(pet!.id, patch);

  Future<void> refreshAlerts() async {
    alerts = await api.listAlerts();
    notifyListeners();
  }

  Future<void> ack(String alertId) async {
    await api.ackAlert(alertId);
    await refreshAlerts();
  }

  @override
  void dispose() {
    _sseSub?.cancel();
    sse.close();
    super.dispose();
  }
}
