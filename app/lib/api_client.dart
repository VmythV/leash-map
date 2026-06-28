import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'models.dart';

/// Thin REST client for the LeashMap App API (docs/api/openapi.yaml).
class ApiClient {
  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? AppConfig.baseUrl;

  final String baseUrl;
  String? _token;

  Map<String, String> get _headers => {
        'content-type': 'application/json',
        if (_token != null) 'authorization': 'Bearer $_token',
      };

  Uri _u(String path, [Map<String, String>? q]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: q);

  Never _fail(http.Response r) {
    String msg = 'HTTP ${r.statusCode}';
    try {
      msg = (jsonDecode(r.body)['error']?['message'] as String?) ?? msg;
    } catch (_) {}
    throw ApiException(msg, r.statusCode);
  }

  dynamic _json(http.Response r) {
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return r.body.isEmpty ? null : jsonDecode(r.body);
    }
    _fail(r);
  }

  String? get token => _token;

  Future<String> createSession({String? displayName}) async {
    final r = await http.post(_u('/v1/auth/demo-session'),
        headers: _headers, body: jsonEncode({'display_name': displayName}));
    _token = (_json(r) as Map<String, dynamic>)['token'] as String;
    return _token!;
  }

  Future<List<Pet>> listPets() async {
    final r = await http.get(_u('/v1/pets'), headers: _headers);
    final data = (_json(r) as Map<String, dynamic>)['data'] as List;
    return data.map((e) => Pet.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Pet> createPet(String name, {String species = 'dog'}) async {
    final r = await http.post(_u('/v1/pets'),
        headers: _headers, body: jsonEncode({'name': name, 'species': species}));
    return Pet.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<void> bindDevice(String deviceId, String petId) async {
    final r = await http.post(_u('/v1/devices/bind'),
        headers: _headers, body: jsonEncode({'device_id': deviceId, 'pet_id': petId}));
    _json(r);
  }

  Future<LatestLocation> latestLocation(String petId) async {
    final r = await http.get(_u('/v1/pets/$petId/location/latest'), headers: _headers);
    return LatestLocation.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<TrailData> trail(String petId, DateTime from, DateTime to) async {
    final r = await http.get(
      _u('/v1/pets/$petId/trail', {
        'from': from.toUtc().toIso8601String(),
        'to': to.toUtc().toIso8601String(),
      }),
      headers: _headers,
    );
    return TrailData.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<ActivitySummary> activity(String petId, DateTime from, DateTime to) async {
    final r = await http.get(
      _u('/v1/pets/$petId/activity', {
        'from': from.toUtc().toIso8601String(),
        'to': to.toUtc().toIso8601String(),
      }),
      headers: _headers,
    );
    return ActivitySummary.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<DeviceConfig> getDeviceConfig(String deviceId) async {
    final r = await http.get(_u('/v1/devices/$deviceId/config'), headers: _headers);
    return DeviceConfig.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<DeviceConfig> updateDeviceConfig(String deviceId, Map<String, dynamic> patch) async {
    final r = await http.put(_u('/v1/devices/$deviceId/config'),
        headers: _headers, body: jsonEncode(patch));
    return DeviceConfig.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<AlertSettings> getAlertSettings(String petId) async {
    final r = await http.get(_u('/v1/pets/$petId/alert-settings'), headers: _headers);
    return AlertSettings.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<AlertSettings> updateAlertSettings(String petId, Map<String, dynamic> patch) async {
    final r = await http.put(_u('/v1/pets/$petId/alert-settings'),
        headers: _headers, body: jsonEncode(patch));
    return AlertSettings.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<Geofence> updateGeofence(String petId, String geoId, Map<String, dynamic> patch) async {
    final r = await http.patch(_u('/v1/pets/$petId/geofences/$geoId'),
        headers: _headers, body: jsonEncode(patch));
    return Geofence.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<List<Geofence>> listGeofences(String petId) async {
    final r = await http.get(_u('/v1/pets/$petId/geofences'), headers: _headers);
    final data = (_json(r) as Map<String, dynamic>)['data'] as List;
    return data.map((e) => Geofence.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Geofence> createGeofence(String petId,
      {required String name,
      required double centerLat,
      required double centerLng,
      required double radiusM}) async {
    final r = await http.post(
      _u('/v1/pets/$petId/geofences'),
      headers: _headers,
      body: jsonEncode({
        'name': name,
        'center_lat': centerLat,
        'center_lng': centerLng,
        'radius_m': radiusM,
        'enabled': true,
      }),
    );
    return Geofence.fromJson(_json(r) as Map<String, dynamic>);
  }

  Future<List<Alert>> listAlerts({String? status}) async {
    final r = await http.get(
      _u('/v1/alerts', status == null ? null : {'status': status}),
      headers: _headers,
    );
    final data = (_json(r) as Map<String, dynamic>)['data'] as List;
    return data.map((e) => Alert.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Alert> ackAlert(String alertId) async {
    final r = await http.post(_u('/v1/alerts/$alertId/ack'), headers: _headers);
    return Alert.fromJson(_json(r) as Map<String, dynamic>);
  }

  /// Toggle lost-pet mode — enqueues a set_mode command toward the device.
  Future<void> setLostMode(String petId, bool on) async {
    final r = await http.post(_u('/v1/pets/$petId/lost-mode'),
        headers: _headers, body: jsonEncode({'on': on}));
    _json(r);
  }

  /// Local-only demo helper: drive in-process movement for a device.
  Future<void> demoRun(String deviceId, {String mode = 'exit_zone'}) async {
    final r = await http.post(_u('/demo/run'),
        headers: _headers,
        body: jsonEncode({'device_id': deviceId, 'mode': mode, 'count': 14, 'interval': 0.7}));
    _json(r);
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);
  @override
  String toString() => 'ApiException($statusCode): $message';
}
